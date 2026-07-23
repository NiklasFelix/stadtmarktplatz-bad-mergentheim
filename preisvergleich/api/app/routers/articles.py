from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import get_current_user, require_role
from common.db import get_cursor

router = APIRouter(prefix="/articles", tags=["articles"], dependencies=[Depends(get_current_user)])

ARTICLE_FIELDS = """
    id, artikelnummer, herstellernummer, ean, canonical_name, description, hersteller,
    warengruppe, kategorie, masse, gewicht, verpackungseinheit, mindestbestellmenge,
    technische_daten, dokumente, zertifikate, bilder, active, created_at, updated_at
"""


class ArticleIn(BaseModel):
    canonical_name: str
    description: Optional[str] = None
    ean: Optional[str] = None
    herstellernummer: Optional[str] = None
    hersteller: Optional[str] = None
    warengruppe: Optional[str] = None
    kategorie: Optional[str] = None
    masse: Optional[str] = None
    gewicht: Optional[str] = None
    verpackungseinheit: Optional[str] = None
    mindestbestellmenge: Optional[str] = None
    technische_daten: dict = {}
    dokumente: list = []
    zertifikate: list = []
    bilder: list = []


class OfferIn(BaseModel):
    supplier_id: int
    price: Optional[float] = None
    currency: str = "EUR"
    unit: Optional[str] = None
    lieferzeit_tage: Optional[float] = None
    verfuegbarkeit: Optional[str] = None
    bewertung: Optional[float] = None
    rabatt_pct: float = 0
    staffelpreise: list = []
    article_number_at_supplier: Optional[str] = None


def _row_to_article(row: dict) -> dict:
    return row


@router.get("")
def search_articles(
    q: str = Query(default=""),
    warengruppe: str = Query(default=""),
    kategorie: str = Query(default=""),
    supplier_id: Optional[int] = Query(default=None),
    price_min: Optional[float] = Query(default=None),
    price_max: Optional[float] = Query(default=None),
    lieferzeit_max: Optional[float] = Query(default=None),
    include_inactive: bool = Query(default=False),
):
    conditions = ["(%s = '' OR a.canonical_name ILIKE %s OR a.artikelnummer ILIKE %s OR a.ean ILIKE %s)"]
    params = [q, f"%{q}%", f"%{q}%", f"%{q}%"]

    if not include_inactive:
        conditions.append("a.active = true")
    if warengruppe:
        conditions.append("a.warengruppe = %s")
        params.append(warengruppe)
    if kategorie:
        conditions.append("a.kategorie = %s")
        params.append(kategorie)

    having = []
    if supplier_id is not None:
        conditions.append("EXISTS (SELECT 1 FROM current_offers co WHERE co.canonical_article_id = a.id AND co.supplier_id = %s)")
        params.append(supplier_id)
    if price_min is not None:
        having.append("MIN(co.price) >= %s")
    if price_max is not None:
        having.append("MIN(co.price) <= %s")
    if lieferzeit_max is not None:
        having.append("MIN(co.lieferzeit_tage) <= %s")

    having_params = []
    if price_min is not None:
        having_params.append(price_min)
    if price_max is not None:
        having_params.append(price_max)
    if lieferzeit_max is not None:
        having_params.append(lieferzeit_max)

    having_clause = f"HAVING {' AND '.join(having)}" if having else ""

    sql = f"""
        SELECT a.id, a.artikelnummer, a.ean, a.canonical_name, a.hersteller, a.warengruppe, a.kategorie,
               a.active, a.created_at, a.updated_at,
               COUNT(DISTINCT co.supplier_id) AS anzahl_lieferanten,
               MIN(co.price) AS guenstigster_preis,
               (a.ean IS NOT NULL AND a.warengruppe IS NOT NULL AND jsonb_array_length(a.bilder) > 0) AS vollstaendig
        FROM canonical_articles a
        LEFT JOIN current_offers co ON co.canonical_article_id = a.id
        WHERE {' AND '.join(conditions)}
        GROUP BY a.id
        {having_clause}
        ORDER BY a.canonical_name
        LIMIT 200
    """
    with get_cursor() as cur:
        cur.execute(sql, params + having_params)
        return cur.fetchall()


@router.get("/{article_id}")
def get_article(article_id: UUID):
    with get_cursor() as cur:
        cur.execute(f"SELECT {ARTICLE_FIELDS} FROM canonical_articles WHERE id = %s", (str(article_id),))
        article = cur.fetchone()
        if not article:
            raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
        cur.execute(
            """
            SELECT o.offer_id, o.supplier_id, s.name AS supplier_name, o.price, o.currency, o.unit,
                   o.article_number_at_supplier, o.valid_from, o.lieferzeit_tage, o.verfuegbarkeit,
                   o.bewertung, o.rabatt_pct, o.staffelpreise
            FROM current_offers o
            JOIN suppliers s ON s.id = o.supplier_id
            WHERE o.canonical_article_id = %s
            ORDER BY o.price ASC NULLS LAST
            """,
            (str(article_id),),
        )
        article["offers"] = cur.fetchall()
    return article


@router.get("/{article_id}/price-history")
def get_price_history(article_id: UUID):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT so.supplier_id, s.name AS supplier_name, so.price, so.valid_from
            FROM supplier_offers so
            JOIN suppliers s ON s.id = so.supplier_id
            WHERE so.canonical_article_id = %s AND so.price IS NOT NULL
            ORDER BY so.valid_from ASC
            """,
            (str(article_id),),
        )
        return cur.fetchall()


@router.post("", dependencies=[Depends(require_role("admin", "einkauf"))])
def create_article(body: ArticleIn):
    with get_cursor() as cur:
        if body.ean:
            cur.execute("SELECT id FROM canonical_articles WHERE ean = %s", (body.ean,))
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="Ein Artikel mit dieser EAN existiert bereits")
        cur.execute(
            """
            INSERT INTO canonical_articles
                (canonical_name, description, ean, herstellernummer, hersteller, warengruppe, kategorie,
                 masse, gewicht, verpackungseinheit, mindestbestellmenge, technische_daten, dokumente,
                 zertifikate, bilder)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
            """,
            (
                body.canonical_name, body.description, body.ean, body.herstellernummer, body.hersteller,
                body.warengruppe, body.kategorie, body.masse, body.gewicht, body.verpackungseinheit,
                body.mindestbestellmenge, _json(body.technische_daten), _json(body.dokumente),
                _json(body.zertifikate), _json(body.bilder),
            ),
        )
        new_id = cur.fetchone()["id"]
        cur.execute(f"SELECT {ARTICLE_FIELDS} FROM canonical_articles WHERE id = %s", (new_id,))
        return cur.fetchone()


@router.put("/{article_id}", dependencies=[Depends(require_role("admin", "einkauf"))])
def update_article(article_id: UUID, body: ArticleIn):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM canonical_articles WHERE id = %s", (str(article_id),))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
        cur.execute(
            """
            UPDATE canonical_articles SET
                canonical_name=%s, description=%s, ean=%s, herstellernummer=%s, hersteller=%s,
                warengruppe=%s, kategorie=%s, masse=%s, gewicht=%s, verpackungseinheit=%s,
                mindestbestellmenge=%s, technische_daten=%s, dokumente=%s, zertifikate=%s, bilder=%s
            WHERE id = %s
            """,
            (
                body.canonical_name, body.description, body.ean, body.herstellernummer, body.hersteller,
                body.warengruppe, body.kategorie, body.masse, body.gewicht, body.verpackungseinheit,
                body.mindestbestellmenge, _json(body.technische_daten), _json(body.dokumente),
                _json(body.zertifikate), _json(body.bilder), str(article_id),
            ),
        )
        cur.execute(f"SELECT {ARTICLE_FIELDS} FROM canonical_articles WHERE id = %s", (str(article_id),))
        return cur.fetchone()


@router.delete("/{article_id}", dependencies=[Depends(require_role("admin", "einkauf"))])
def delete_article(article_id: UUID):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM canonical_articles WHERE id = %s", (str(article_id),))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
        cur.execute("DELETE FROM supplier_offers WHERE canonical_article_id = %s", (str(article_id),))
        cur.execute("DELETE FROM article_matches WHERE canonical_article_id = %s", (str(article_id),))
        cur.execute("DELETE FROM canonical_articles WHERE id = %s", (str(article_id),))
    return {"status": "deleted", "id": str(article_id)}


def _manual_entry_source_and_batch(cur) -> tuple:
    """Manuelle Eingaben ueber die API brauchen ebenfalls eine source_id/batch_id
    (Herkunftsnachweis wie bei Datei-Importen) - hier eine feste 'Manuelle Eingabe'-Quelle,
    pro Aufruf ein neuer Batch mit einer Zeile."""
    cur.execute("SELECT id FROM sources WHERE name = 'Manuelle Eingabe' AND type = 'supplier'")
    source = cur.fetchone()
    if not source:
        cur.execute("INSERT INTO sources (name, type) VALUES ('Manuelle Eingabe', 'supplier') RETURNING id")
        source = cur.fetchone()
    cur.execute(
        "INSERT INTO import_batches (source_id, file_name, file_type, row_count) VALUES (%s,'manuelle-eingabe','excel',1) RETURNING id",
        (source["id"],),
    )
    batch = cur.fetchone()
    return source["id"], batch["id"]


@router.post("/{article_id}/offers", dependencies=[Depends(require_role("admin", "einkauf"))])
def add_offer(article_id: UUID, body: OfferIn):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM canonical_articles WHERE id = %s", (str(article_id),))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Artikel nicht gefunden")
        cur.execute("SELECT id FROM suppliers WHERE id = %s", (body.supplier_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Lieferant nicht gefunden")

        source_id, batch_id = _manual_entry_source_and_batch(cur)
        cur.execute(
            "INSERT INTO staging_items (batch_id, source_id, raw_row, description, price) VALUES (%s,%s,'{}'::jsonb,%s,%s) RETURNING id",
            (batch_id, source_id, body.article_number_at_supplier or "manuelle Eingabe", body.price),
        )
        staging_id = cur.fetchone()["id"]

        cur.execute(
            """
            INSERT INTO supplier_offers
                (canonical_article_id, supplier_id, source_id, staging_item_id, article_number_at_supplier,
                 price, currency, unit, lieferzeit_tage, verfuegbarkeit, bewertung, rabatt_pct, staffelpreise, valid_from)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, CURRENT_DATE)
            RETURNING id
            """,
            (
                str(article_id), body.supplier_id, source_id, staging_id, body.article_number_at_supplier,
                body.price, body.currency, body.unit, body.lieferzeit_tage, body.verfuegbarkeit, body.bewertung,
                body.rabatt_pct, _json(body.staffelpreise),
            ),
        )
        offer_id = cur.fetchone()["id"]
    return {"status": "created", "offer_id": offer_id}


@router.put("/{article_id}/offers/{offer_id}", dependencies=[Depends(require_role("admin", "einkauf"))])
def update_offer(article_id: UUID, offer_id: int, body: OfferIn):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM supplier_offers WHERE id = %s AND canonical_article_id = %s", (offer_id, str(article_id)))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Angebot nicht gefunden")
        cur.execute(
            """
            UPDATE supplier_offers SET
                price=%s, currency=%s, unit=%s, lieferzeit_tage=%s, verfuegbarkeit=%s, bewertung=%s,
                rabatt_pct=%s, staffelpreise=%s, article_number_at_supplier=%s
            WHERE id = %s
            """,
            (
                body.price, body.currency, body.unit, body.lieferzeit_tage, body.verfuegbarkeit, body.bewertung,
                body.rabatt_pct, _json(body.staffelpreise), body.article_number_at_supplier, offer_id,
            ),
        )
    return {"status": "updated"}


@router.delete("/{article_id}/offers/{offer_id}", dependencies=[Depends(require_role("admin", "einkauf"))])
def delete_offer(article_id: UUID, offer_id: int):
    with get_cursor() as cur:
        cur.execute("DELETE FROM supplier_offers WHERE id = %s AND canonical_article_id = %s", (offer_id, str(article_id)))
    return {"status": "deleted"}


@router.get("/{article_id}/offers")
def get_offers(article_id: UUID):
    article = get_article(article_id)
    if not article["offers"]:
        raise HTTPException(status_code=404, detail="Keine aktuellen Angebote fuer diesen Artikel gefunden")
    return article["offers"]


@router.get("/{article_id}/cheapest")
def get_cheapest(article_id: UUID):
    offers = get_offers(article_id)
    return offers[0]


def _json(value):
    import json

    return json.dumps(value)
