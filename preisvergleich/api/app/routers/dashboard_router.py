from fastapi import APIRouter, Depends

from app.auth import get_current_user
from common.db import get_cursor

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(get_current_user)])


@router.get("/kpis")
def kpis():
    with get_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS n FROM canonical_articles WHERE active = true")
        articles = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM suppliers WHERE active = true")
        suppliers = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM customers")
        customers = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM supplier_offers WHERE created_at >= now() - interval '30 days'")
        price_updates_30d = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM canonical_articles WHERE created_at >= now() - interval '30 days' AND active = true")
        new_articles_30d = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM article_matches WHERE status = 'needs_review'")
        open_reviews = cur.fetchone()["n"]

        cur.execute(
            "SELECT COUNT(*) AS n FROM canonical_articles WHERE active = true AND (ean IS NULL OR jsonb_array_length(bilder) = 0 OR warengruppe IS NULL OR gewicht IS NULL)"
        )
        incomplete = cur.fetchone()["n"]

        max_points = articles * 4
        cur.execute(
            """
            SELECT
                COUNT(*) FILTER (WHERE ean IS NULL) AS ean_missing,
                COUNT(*) FILTER (WHERE jsonb_array_length(bilder) = 0) AS bild_missing,
                COUNT(*) FILTER (WHERE warengruppe IS NULL) AS wg_missing,
                COUNT(*) FILTER (WHERE gewicht IS NULL) AS gewicht_missing
            FROM canonical_articles WHERE active = true
            """
        )
        gaps = cur.fetchone()
        lost = sum(gaps.values())
        quality_score = round(100 * (1 - lost / max_points), 1) if max_points else 100.0

    return {
        "anzahl_artikel": articles,
        "anzahl_lieferanten": suppliers,
        "anzahl_kunden": customers,
        "preisaenderungen_30_tage": price_updates_30d,
        "neue_artikel_30_tage": new_articles_30d,
        "offene_dublettenpruefungen": open_reviews,
        "unvollstaendige_artikel": incomplete,
        "datenqualitaets_score": quality_score,
    }


@router.get("/activity")
def activity():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT 'import' AS typ, ib.imported_at AS zeitpunkt,
                   'Preisliste importiert: ' || s.name || ' (' || ib.row_count || ' Zeilen)' AS beschreibung
            FROM import_batches ib JOIN sources s ON s.id = ib.source_id
            ORDER BY ib.imported_at DESC LIMIT 10
            """
        )
        imports = cur.fetchall()
        cur.execute(
            """
            SELECT 'artikel' AS typ, created_at AS zeitpunkt, 'Neuer Artikel angelegt: ' || canonical_name AS beschreibung
            FROM canonical_articles WHERE active = true ORDER BY created_at DESC LIMIT 10
            """
        )
        articles = cur.fetchall()
    combined = sorted(imports + articles, key=lambda r: r["zeitpunkt"], reverse=True)
    return combined[:15]
