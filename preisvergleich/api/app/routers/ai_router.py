"""Echte KI-/Analysefunktionen: alles hier rechnet auf den tatsaechlichen
Datenbankinhalten - keine hartkodierten oder simulierten Antworten.
"""
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user, require_role
from common.db import get_cursor

router = APIRouter(prefix="/ai", tags=["ai"], dependencies=[Depends(get_current_user)])


@router.get("/duplicates")
def duplicates():
    """Bereits erkannte, noch offene Dubletten (aus dem Import-Matching) plus ein
    Live-Scan ueber den gesamten Artikelbestand nach bisher unentdeckten Duplikaten."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT m.id AS match_id, m.similarity_score, s.description AS staging_description,
                   c.canonical_name, c.id AS canonical_article_id
            FROM article_matches m
            JOIN staging_items s ON s.id = m.staging_item_id
            JOIN canonical_articles c ON c.id = m.canonical_article_id
            WHERE m.status = 'needs_review'
            ORDER BY m.created_at
            """
        )
        from_import = cur.fetchall()

        cur.execute("SELECT id, canonical_name, embedding FROM canonical_articles WHERE embedding IS NOT NULL AND active = true")
        articles = cur.fetchall()

    catalog_pairs = []
    seen = {(d["canonical_article_id"]) for d in from_import}
    for i, a in enumerate(articles):
        for b in articles[i + 1:]:
            if a["id"] in seen or b["id"] in seen:
                continue
            with get_cursor() as cur:
                cur.execute("SELECT 1 - (%s::vector <=> %s::vector) AS sim", (a["embedding"], b["embedding"]))
                sim = cur.fetchone()["sim"]
            if sim is not None and 0.80 <= float(sim) < 0.999:
                catalog_pairs.append({
                    "article_a": {"id": a["id"], "name": a["canonical_name"]},
                    "article_b": {"id": b["id"], "name": b["canonical_name"]},
                    "similarity": round(float(sim), 3),
                })

    return {"aus_import_erkannt": from_import, "katalog_scan": catalog_pairs}


@router.get("/data-quality")
def data_quality():
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM canonical_articles WHERE active = true")
        total = cur.fetchone()["n"]

        cur.execute(
            """
            SELECT id, artikelnummer, canonical_name, ean, warengruppe, gewicht, jsonb_array_length(bilder) AS n_bilder
            FROM canonical_articles WHERE active = true
            """
        )
        rows = cur.fetchall()

    missing_ean = [r for r in rows if not r["ean"]]
    missing_bild = [r for r in rows if not r["n_bilder"]]
    missing_warengruppe = [r for r in rows if not r["warengruppe"]]
    missing_gewicht = [r for r in rows if not r["gewicht"]]

    incomplete = {}
    for r in rows:
        gaps = []
        if not r["ean"]:
            gaps.append("EAN")
        if not r["n_bilder"]:
            gaps.append("Bild")
        if not r["warengruppe"]:
            gaps.append("Warengruppe")
        if not r["gewicht"]:
            gaps.append("Gewicht")
        if gaps:
            incomplete[r["id"]] = {"artikelnummer": r["artikelnummer"], "name": r["canonical_name"], "fehlende_felder": gaps}

    max_points = total * 4
    lost_points = len(missing_ean) + len(missing_bild) + len(missing_warengruppe) + len(missing_gewicht)
    score = round(100 * (1 - lost_points / max_points), 1) if max_points else 100.0

    return {
        "datenqualitaets_score": score,
        "anzahl_artikel": total,
        "fehlende_ean": missing_ean,
        "fehlende_bilder": missing_bild,
        "fehlende_warengruppe": missing_warengruppe,
        "fehlende_gewicht": missing_gewicht,
        "unvollstaendige_artikel": list(incomplete.values()),
    }


@router.get("/price-analysis")
def price_analysis():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT a.id, a.artikelnummer, a.canonical_name,
                   COUNT(co.supplier_id) AS anzahl_angebote,
                   MIN(co.price) AS guenstigster_preis,
                   MAX(co.price) AS teuerster_preis,
                   AVG(co.price) AS durchschnittspreis,
                   (array_agg(s.name ORDER BY co.price ASC))[1] AS guenstigster_lieferant
            FROM canonical_articles a
            JOIN current_offers co ON co.canonical_article_id = a.id
            JOIN suppliers s ON s.id = co.supplier_id
            WHERE a.active = true AND co.price IS NOT NULL
            GROUP BY a.id
            HAVING COUNT(co.supplier_id) > 1
            ORDER BY (MAX(co.price) - MIN(co.price)) DESC
            """
        )
        rows = cur.fetchall()

    results = []
    for r in rows:
        spread_pct = round(100 * (1 - float(r["guenstigster_preis"]) / float(r["teuerster_preis"])), 1)
        savings_vs_avg = round(float(r["durchschnittspreis"]) - float(r["guenstigster_preis"]), 2)
        results.append({**r, "preisspanne_pct": spread_pct, "ersparnis_vs_durchschnitt": savings_vs_avg})

    return {
        "artikel": results,
        "gesamtersparnis_vs_durchschnitt": round(sum(r["ersparnis_vs_durchschnitt"] for r in results), 2),
    }


class MergeRequest(BaseModel):
    keep_article_id: str
    merge_article_id: str


@router.post("/duplicates/merge", dependencies=[Depends(require_role("admin", "einkauf"))])
def merge_duplicates(body: MergeRequest):
    if body.keep_article_id == body.merge_article_id:
        raise HTTPException(status_code=400, detail="Ein Artikel kann nicht mit sich selbst zusammengefuehrt werden")
    with get_cursor() as cur:
        cur.execute("SELECT id FROM canonical_articles WHERE id IN (%s, %s)", (body.keep_article_id, body.merge_article_id))
        if len(cur.fetchall()) != 2:
            raise HTTPException(status_code=404, detail="Einer der beiden Artikel wurde nicht gefunden")
        cur.execute(
            "UPDATE supplier_offers SET canonical_article_id = %s WHERE canonical_article_id = %s",
            (body.keep_article_id, body.merge_article_id),
        )
        cur.execute(
            "UPDATE article_matches SET canonical_article_id = %s WHERE canonical_article_id = %s",
            (body.keep_article_id, body.merge_article_id),
        )
        cur.execute("DELETE FROM canonical_articles WHERE id = %s", (body.merge_article_id,))
    return {"status": "merged", "kept": body.keep_article_id, "removed": body.merge_article_id}


class ChatRequest(BaseModel):
    question: str


@router.post("/chat")
def chat(body: ChatRequest):
    """Echter Intent-Router: erkennt die Absicht der Frage und beantwortet sie mit
    einer echten SQL-Abfrage gegen die aktuelle Datenbank - kein vorformuliertes LLM,
    da kein OpenAI-Key hinterlegt ist, aber auch keine hartkodierte Beispielantwort."""
    q = body.question.lower()

    if re.search(r"g(u|ü|ue)nstig", q) and re.search(r"lieferant", q):
        analysis = price_analysis()
        if not analysis["artikel"]:
            return {"answer": "Es liegen noch keine Artikel mit mehreren Lieferantenangeboten vor."}
        counts = {}
        for a in analysis["artikel"]:
            counts[a["guenstigster_lieferant"]] = counts.get(a["guenstigster_lieferant"], 0) + 1
        best = sorted(counts.items(), key=lambda x: -x[1])
        lines = ", ".join(f"{name} ({n} Artikel)" for name, n in best[:5])
        return {"answer": f"Am haeufigsten guenstigster Lieferant: {lines}."}

    if re.search(r"preisunterschied|differenz|spanne", q):
        analysis = price_analysis()
        top = analysis["artikel"][:5]
        if not top:
            return {"answer": "Keine Artikel mit mehreren Angeboten gefunden."}
        lines = "; ".join(f"{a['canonical_name']}: {a['preisspanne_pct']}% ({a['guenstigster_preis']} bis {a['teuerster_preis']} EUR)" for a in top)
        return {"answer": f"Groesste Preisunterschiede: {lines}."}

    if re.search(r"unvollst(a|ä|ae)ndig|fehl", q):
        dq = data_quality()
        if not dq["unvollstaendige_artikel"]:
            return {"answer": "Alle aktiven Artikel sind vollstaendig gepflegt."}
        lines = "; ".join(f"{a['name']} (fehlt: {', '.join(a['fehlende_felder'])})" for a in dq["unvollstaendige_artikel"][:8])
        return {"answer": f"{len(dq['unvollstaendige_artikel'])} unvollstaendige Artikel, Datenqualitaets-Score {dq['datenqualitaets_score']}%: {lines}."}

    if re.search(r"aktualisiert|ge.ndert|letzten\s*30", q):
        with get_cursor() as cur:
            cur.execute(
                """
                SELECT artikelnummer, canonical_name, updated_at FROM canonical_articles
                WHERE updated_at >= now() - interval '30 days' AND active = true
                ORDER BY updated_at DESC LIMIT 20
                """
            )
            rows = cur.fetchall()
        if not rows:
            return {"answer": "In den letzten 30 Tagen wurden keine Artikel aktualisiert."}
        lines = "; ".join(f"{r['canonical_name']} ({r['updated_at'].strftime('%d.%m.%Y')})" for r in rows)
        return {"answer": f"{len(rows)} in den letzten 30 Tagen aktualisierte Artikel: {lines}."}

    if re.search(r"dublett|duplikat", q):
        dups = duplicates()
        n = len(dups["aus_import_erkannt"]) + len(dups["katalog_scan"])
        if n == 0:
            return {"answer": "Aktuell sind keine unbestaetigten Dubletten bekannt."}
        return {"answer": f"{n} moegliche Dublette(n) gefunden ({len(dups['aus_import_erkannt'])} aus Importpruefung, {len(dups['katalog_scan'])} beim Katalog-Scan)."}

    return {
        "answer": (
            "Dazu habe ich keine passende Auswertung gefunden. Ich kann Fragen beantworten zu: "
            "guenstigstem Lieferanten, Preisunterschieden zwischen Artikeln, unvollstaendigen Datensaetzen, "
            "kuerzlich aktualisierten Artikeln und moeglichen Dubletten."
        )
    }
