from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import get_current_user, require_role
from common.db import get_cursor

router = APIRouter(prefix="/suppliers", tags=["suppliers"], dependencies=[Depends(get_current_user)])


class SupplierIn(BaseModel):
    name: str
    ansprechpartner: Optional[str] = None
    email: Optional[str] = None
    telefon: Optional[str] = None
    adresse: Optional[str] = None
    lieferbedingungen: Optional[str] = None
    lieferzeit_standard: Optional[str] = None
    zahlungsbedingungen: Optional[str] = None
    liefertreue_pct: Optional[float] = None


@router.get("")
def list_suppliers(q: str = Query(default=""), include_inactive: bool = Query(default=False)):
    conditions = ["(%s = '' OR name ILIKE %s)"]
    params = [q, f"%{q}%"]
    if not include_inactive:
        conditions.append("active = true")
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT s.*, (
                SELECT COUNT(DISTINCT so.canonical_article_id) FROM supplier_offers so WHERE so.supplier_id = s.id
            ) AS anzahl_artikel
            FROM suppliers s
            WHERE {' AND '.join(conditions)}
            ORDER BY s.name
            """,
            params,
        )
        return cur.fetchall()


@router.get("/{supplier_id}")
def get_supplier(supplier_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM suppliers WHERE id = %s", (supplier_id,))
        supplier = cur.fetchone()
        if not supplier:
            raise HTTPException(status_code=404, detail="Lieferant nicht gefunden")
        cur.execute(
            """
            SELECT a.id, a.artikelnummer, a.canonical_name, co.price
            FROM current_offers co
            JOIN canonical_articles a ON a.id = co.canonical_article_id
            WHERE co.supplier_id = %s
            ORDER BY a.canonical_name
            """,
            (supplier_id,),
        )
        supplier["artikel"] = cur.fetchall()
    return supplier


@router.post("", dependencies=[Depends(require_role("admin", "einkauf"))])
def create_supplier(body: SupplierIn):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM suppliers WHERE name = %s", (body.name,))
        if cur.fetchone():
            raise HTTPException(status_code=409, detail="Ein Lieferant mit diesem Namen existiert bereits")
        cur.execute(
            """
            INSERT INTO suppliers (name, ansprechpartner, email, telefon, adresse, lieferbedingungen,
                                    lieferzeit_standard, zahlungsbedingungen, liefertreue_pct)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
            """,
            (
                body.name, body.ansprechpartner, body.email, body.telefon, body.adresse,
                body.lieferbedingungen, body.lieferzeit_standard, body.zahlungsbedingungen, body.liefertreue_pct,
            ),
        )
        new_id = cur.fetchone()["id"]
    return get_supplier(new_id)


@router.put("/{supplier_id}", dependencies=[Depends(require_role("admin", "einkauf"))])
def update_supplier(supplier_id: int, body: SupplierIn):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM suppliers WHERE id = %s", (supplier_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Lieferant nicht gefunden")
        cur.execute(
            """
            UPDATE suppliers SET name=%s, ansprechpartner=%s, email=%s, telefon=%s, adresse=%s,
                lieferbedingungen=%s, lieferzeit_standard=%s, zahlungsbedingungen=%s, liefertreue_pct=%s
            WHERE id = %s
            """,
            (
                body.name, body.ansprechpartner, body.email, body.telefon, body.adresse,
                body.lieferbedingungen, body.lieferzeit_standard, body.zahlungsbedingungen, body.liefertreue_pct,
                supplier_id,
            ),
        )
    return get_supplier(supplier_id)


@router.delete("/{supplier_id}", dependencies=[Depends(require_role("admin", "einkauf"))])
def delete_supplier(supplier_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM suppliers WHERE id = %s", (supplier_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Lieferant nicht gefunden")
        cur.execute("SELECT COUNT(*) AS n FROM supplier_offers WHERE supplier_id = %s", (supplier_id,))
        if cur.fetchone()["n"] > 0:
            cur.execute("UPDATE suppliers SET active = false WHERE id = %s", (supplier_id,))
            return {"status": "deactivated", "reason": "Lieferant hat verknuepfte Angebote, daher deaktiviert statt geloescht"}
        cur.execute("DELETE FROM suppliers WHERE id = %s", (supplier_id,))
    return {"status": "deleted"}
