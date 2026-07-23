"""Kernlogik fuer das Matching: EAN-Abgleich, semantisches Matching und die
Uebernahme bestaetigter/abgelehnter manueller Reviews. Wird sowohl vom
Batch-Skript (run_matching.py) als auch von der API (Review-Endpunkte) genutzt.
"""
from common.config import SEMANTIC_AUTO_ACCEPT_THRESHOLD, SEMANTIC_REVIEW_THRESHOLD
from embeddings import get_embedding


def _vec_literal(embedding: list) -> str:
    return "[" + ",".join(repr(float(x)) for x in embedding) + "]"


def ensure_supplier(cur, supplier_name: str) -> int:
    cur.execute("SELECT supplier_id FROM supplier_aliases WHERE alias_name = %s", (supplier_name,))
    row = cur.fetchone()
    if row:
        return row["supplier_id"]

    cur.execute("SELECT id FROM suppliers WHERE name = %s", (supplier_name,))
    row = cur.fetchone()
    if row:
        supplier_id = row["id"]
    else:
        cur.execute("INSERT INTO suppliers (name) VALUES (%s) RETURNING id", (supplier_name,))
        supplier_id = cur.fetchone()["id"]

    cur.execute(
        "INSERT INTO supplier_aliases (supplier_id, alias_name) VALUES (%s, %s) ON CONFLICT (alias_name) DO NOTHING",
        (supplier_id, supplier_name),
    )
    return supplier_id


def find_by_ean(cur, ean: str):
    cur.execute("SELECT id FROM canonical_articles WHERE ean = %s", (ean,))
    return cur.fetchone()


def find_best_semantic_match(cur, embedding: list):
    vec = _vec_literal(embedding)
    cur.execute(
        """
        SELECT id, canonical_name, 1 - (embedding <=> %s::vector) AS similarity
        FROM canonical_articles
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT 1
        """,
        (vec, vec),
    )
    return cur.fetchone()


def create_canonical_article(cur, ean: str | None, name: str, description: str, embedding: list | None) -> str:
    vec = _vec_literal(embedding) if embedding is not None else None
    cur.execute(
        """
        INSERT INTO canonical_articles (ean, canonical_name, description, embedding)
        VALUES (%s, %s, %s, %s::vector)
        RETURNING id
        """,
        (ean, name, description, vec),
    )
    return cur.fetchone()["id"]


def create_match(cur, staging_item_id: int, canonical_article_id: str, method: str, status: str, similarity=None) -> int:
    cur.execute(
        """
        INSERT INTO article_matches (staging_item_id, canonical_article_id, match_method, similarity_score, status)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
        """,
        (staging_item_id, canonical_article_id, method, similarity, status),
    )
    return cur.fetchone()["id"]


def create_offer_for_staging_item(cur, staging_item: dict, canonical_article_id: str):
    supplier_name = staging_item["supplier_name_raw"] or "Unbekannt"
    supplier_id = ensure_supplier(cur, supplier_name)
    cur.execute(
        """
        INSERT INTO supplier_offers
            (canonical_article_id, supplier_id, source_id, staging_item_id,
             article_number_at_supplier, price, currency, unit, valid_from)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            canonical_article_id,
            supplier_id,
            staging_item["source_id"],
            staging_item["id"],
            staging_item["article_number_raw"],
            staging_item["price"],
            staging_item["currency"],
            staging_item["unit"],
            staging_item["valid_from"],
        ),
    )


def process_staging_item(cur, staging_item: dict) -> dict:
    """Matched einen einzelnen staging_item-Datensatz. Legt bei Bedarf einen neuen
    kanonischen Artikel an. Erzeugt nur bei auto_accepted-Matches sofort ein Angebot -
    unsichere (needs_review) Zuordnungen warten auf manuelle Bestaetigung."""
    description = staging_item["description"] or ""

    if staging_item["ean"]:
        existing = find_by_ean(cur, staging_item["ean"])
        if existing:
            match_id = create_match(cur, staging_item["id"], existing["id"], "ean_exact", "auto_accepted", 1.0)
            create_offer_for_staging_item(cur, staging_item, existing["id"])
            return {"status": "auto_accepted", "method": "ean_exact", "match_id": match_id}

        embedding = get_embedding(description) if description else None
        canonical_id = create_canonical_article(cur, staging_item["ean"], description, description, embedding)
        match_id = create_match(cur, staging_item["id"], canonical_id, "new_article", "auto_accepted", None)
        create_offer_for_staging_item(cur, staging_item, canonical_id)
        return {"status": "auto_accepted", "method": "new_article", "match_id": match_id}

    if not description:
        return {"status": "skipped", "method": None, "match_id": None}

    embedding = get_embedding(description)
    best = find_best_semantic_match(cur, embedding)

    if best and best["similarity"] >= SEMANTIC_AUTO_ACCEPT_THRESHOLD:
        match_id = create_match(cur, staging_item["id"], best["id"], "semantic", "auto_accepted", best["similarity"])
        create_offer_for_staging_item(cur, staging_item, best["id"])
        return {"status": "auto_accepted", "method": "semantic", "match_id": match_id, "similarity": float(best["similarity"])}

    if best and best["similarity"] >= SEMANTIC_REVIEW_THRESHOLD:
        match_id = create_match(cur, staging_item["id"], best["id"], "semantic", "needs_review", best["similarity"])
        return {"status": "needs_review", "method": "semantic", "match_id": match_id, "similarity": float(best["similarity"])}

    canonical_id = create_canonical_article(cur, None, description, description, embedding)
    match_id = create_match(cur, staging_item["id"], canonical_id, "new_article", "auto_accepted", None)
    create_offer_for_staging_item(cur, staging_item, canonical_id)
    return {"status": "auto_accepted", "method": "new_article", "match_id": match_id}


def confirm_match(cur, match_id: int, reviewed_by: str):
    cur.execute("SELECT * FROM article_matches WHERE id = %s", (match_id,))
    match = cur.fetchone()
    if not match:
        raise ValueError("Match nicht gefunden")
    cur.execute(
        "UPDATE article_matches SET status = 'confirmed', reviewed_at = now(), reviewed_by = %s WHERE id = %s",
        (reviewed_by, match_id),
    )
    cur.execute("SELECT * FROM staging_items WHERE id = %s", (match["staging_item_id"],))
    staging_item = cur.fetchone()
    create_offer_for_staging_item(cur, staging_item, match["canonical_article_id"])


def reject_match(cur, match_id: int, reviewed_by: str):
    """Bei Ablehnung ist der Vorschlag falsch: der staging_item wird stattdessen als
    eigenstaendiger neuer Artikel angelegt. article_matches.staging_item_id ist UNIQUE,
    daher wird die bestehende Zeile auf den neuen kanonischen Artikel umgehaengt statt
    eine zweite Zeile einzufuegen."""
    cur.execute("SELECT * FROM article_matches WHERE id = %s", (match_id,))
    match = cur.fetchone()
    if not match:
        raise ValueError("Match nicht gefunden")
    cur.execute("SELECT * FROM staging_items WHERE id = %s", (match["staging_item_id"],))
    staging_item = cur.fetchone()
    description = staging_item["description"] or ""
    embedding = get_embedding(description) if description else None
    canonical_id = create_canonical_article(cur, staging_item["ean"], description, description, embedding)
    cur.execute(
        """
        UPDATE article_matches
        SET canonical_article_id = %s, match_method = 'new_article', similarity_score = NULL,
            status = 'confirmed', reviewed_at = now(), reviewed_by = %s
        WHERE id = %s
        """,
        (canonical_id, reviewed_by, match_id),
    )
    create_offer_for_staging_item(cur, staging_item, canonical_id)
