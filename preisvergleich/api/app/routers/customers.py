from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.auth import get_current_user, require_role
from common.db import get_cursor

router = APIRouter(prefix="/customers", tags=["customers"], dependencies=[Depends(get_current_user)])


class CustomerIn(BaseModel):
    name: str
    branche: Optional[str] = None
    standorte: int = 1
    ansprechpartner: Optional[str] = None
    email: Optional[str] = None
    telefon: Optional[str] = None
    einkaufsvolumen: Optional[float] = None


def _next_customer_number(cur) -> str:
    cur.execute("SELECT customer_number FROM customers ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if not row:
        return "K-3001"
    last_num = int(row["customer_number"].split("-")[1])
    return f"K-{last_num + 1}"


@router.get("")
def list_customers(q: str = Query(default="")):
    with get_cursor() as cur:
        cur.execute(
            "SELECT * FROM customers WHERE (%s = '' OR name ILIKE %s) ORDER BY name",
            (q, f"%{q}%"),
        )
        return cur.fetchall()


@router.get("/{customer_id}")
def get_customer(customer_id: int):
    with get_cursor() as cur:
        cur.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
        customer = cur.fetchone()
        if not customer:
            raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    return customer


@router.post("", dependencies=[Depends(require_role("admin", "einkauf"))])
def create_customer(body: CustomerIn):
    with get_cursor() as cur:
        number = _next_customer_number(cur)
        cur.execute(
            """
            INSERT INTO customers (customer_number, name, branche, standorte, ansprechpartner, email, telefon, einkaufsvolumen)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
            """,
            (number, body.name, body.branche, body.standorte, body.ansprechpartner, body.email, body.telefon, body.einkaufsvolumen),
        )
        new_id = cur.fetchone()["id"]
    return get_customer(new_id)


@router.put("/{customer_id}", dependencies=[Depends(require_role("admin", "einkauf"))])
def update_customer(customer_id: int, body: CustomerIn):
    with get_cursor() as cur:
        cur.execute("SELECT id FROM customers WHERE id = %s", (customer_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
        cur.execute(
            """
            UPDATE customers SET name=%s, branche=%s, standorte=%s, ansprechpartner=%s, email=%s,
                telefon=%s, einkaufsvolumen=%s
            WHERE id = %s
            """,
            (body.name, body.branche, body.standorte, body.ansprechpartner, body.email, body.telefon, body.einkaufsvolumen, customer_id),
        )
    return get_customer(customer_id)


@router.delete("/{customer_id}", dependencies=[Depends(require_role("admin", "einkauf"))])
def delete_customer(customer_id: int):
    with get_cursor() as cur:
        cur.execute("DELETE FROM customers WHERE id = %s RETURNING id", (customer_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Kunde nicht gefunden")
    return {"status": "deleted"}
