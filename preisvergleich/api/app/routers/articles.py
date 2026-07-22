from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import require_api_key
from common.db import get_cursor

router = APIRouter(prefix="/articles", tags=["articles"], dependencies=[Depends(require_api_key)])


@router.get("")
def search_articles(q: str = Query(default="", description="Suchbegriff (Teilstring der Artikelbezeichnung)")):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, ean, canonical_name, description, review_status, created_at
            FROM canonical_articles
            WHERE %s = '' OR canonical_name ILIKE %s
            ORDER BY canonical_name
            LIMIT 100
            """,
            (q, f"%{q}%"),
        )
        return cur.fetchall()


@router.get("/{article_id}/offers")
def get_offers(article_id: UUID):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT o.supplier_id, s.name AS supplier_name, o.price, o.currency, o.unit,
                   o.article_number_at_supplier, o.valid_from
            FROM current_offers o
            JOIN suppliers s ON s.id = o.supplier_id
            WHERE o.canonical_article_id = %s
            ORDER BY o.price ASC
            """,
            (str(article_id),),
        )
        offers = cur.fetchall()
    if not offers:
        raise HTTPException(status_code=404, detail="Keine aktuellen Angebote fuer diesen Artikel gefunden")
    return offers


@router.get("/{article_id}/cheapest")
def get_cheapest(article_id: UUID):
    offers = get_offers(article_id)
    return offers[0]
