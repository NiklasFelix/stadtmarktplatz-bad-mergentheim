import sys
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user, require_role
from common.db import get_cursor

# actions.py liegt in preisvergleich/matching/ und ist dort ein flaches Modul
# (kein Package), damit run_matching.py es ohne PYTHONPATH-Konfiguration direkt
# nutzen kann. Fuer die API muss das Verzeichnis daher explizit ergaenzt werden.
_MATCHING_DIR = Path(__file__).resolve().parents[3] / "matching"
if str(_MATCHING_DIR) not in sys.path:
    sys.path.insert(0, str(_MATCHING_DIR))
from actions import confirm_match, reject_match  # noqa: E402

router = APIRouter(prefix="/reviews", tags=["reviews"], dependencies=[Depends(get_current_user)])


@router.get("")
def list_needs_review():
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT m.id AS match_id, m.similarity_score, s.description AS staging_description,
                   s.supplier_name_raw, s.price, s.ean, c.canonical_name, c.id AS canonical_article_id
            FROM article_matches m
            JOIN staging_items s ON s.id = m.staging_item_id
            JOIN canonical_articles c ON c.id = m.canonical_article_id
            WHERE m.status = 'needs_review'
            ORDER BY m.created_at
            """
        )
        return cur.fetchall()


@router.post("/{match_id}/confirm", dependencies=[Depends(require_role("admin", "einkauf"))])
def confirm(match_id: int, user: dict = Depends(get_current_user)):
    with get_cursor() as cur:
        try:
            confirm_match(cur, match_id, user["name"])
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    return {"status": "confirmed", "match_id": match_id}


@router.post("/{match_id}/reject", dependencies=[Depends(require_role("admin", "einkauf"))])
def reject(match_id: int, user: dict = Depends(get_current_user)):
    with get_cursor() as cur:
        try:
            reject_match(cur, match_id, user["name"])
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
    return {"status": "rejected_and_new_article_created", "match_id": match_id}
