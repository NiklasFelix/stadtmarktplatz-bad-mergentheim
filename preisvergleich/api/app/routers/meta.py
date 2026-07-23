from fastapi import APIRouter, Depends

from app.auth import get_current_user
from common.db import get_cursor

router = APIRouter(prefix="/meta", tags=["meta"], dependencies=[Depends(get_current_user)])


@router.get("/warengruppen")
def warengruppen():
    with get_cursor() as cur:
        cur.execute(
            "SELECT DISTINCT warengruppe FROM canonical_articles WHERE warengruppe IS NOT NULL ORDER BY warengruppe"
        )
        return [r["warengruppe"] for r in cur.fetchall()]


@router.get("/kategorien")
def kategorien():
    with get_cursor() as cur:
        cur.execute(
            "SELECT DISTINCT kategorie FROM canonical_articles WHERE kategorie IS NOT NULL ORDER BY kategorie"
        )
        return [r["kategorie"] for r in cur.fetchall()]
