import io

import pandas as pd
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from fpdf import FPDF

from app.auth import get_current_user
from common.db import get_cursor

router = APIRouter(prefix="/export", tags=["export"], dependencies=[Depends(get_current_user)])


def _fetch_article_export_rows() -> list:
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT a.artikelnummer, a.canonical_name, a.ean, a.hersteller, a.warengruppe, a.kategorie,
                   COUNT(DISTINCT co.supplier_id) AS anzahl_lieferanten,
                   MIN(co.price) AS guenstigster_preis,
                   MAX(co.price) AS teuerster_preis
            FROM canonical_articles a
            LEFT JOIN current_offers co ON co.canonical_article_id = a.id
            WHERE a.active = true
            GROUP BY a.id
            ORDER BY a.canonical_name
            """
        )
        return cur.fetchall()


@router.get("/articles.csv")
def export_articles_csv():
    rows = _fetch_article_export_rows()
    df = pd.DataFrame(rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=artikel_export.csv"},
    )


@router.get("/articles.xlsx")
def export_articles_xlsx():
    rows = _fetch_article_export_rows()
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Artikel")
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=artikel_export.xlsx"},
    )


@router.get("/articles.pdf")
def export_articles_pdf():
    rows = _fetch_article_export_rows()
    pdf = FPDF(orientation="L")
    pdf.add_page()
    pdf.set_font("Helvetica", size=14)
    pdf.cell(0, 10, "Artikel- und Preisuebersicht", ln=True)
    pdf.set_font("Helvetica", size=9)

    headers = ["Artikelnr.", "Bezeichnung", "EAN", "Hersteller", "Warengruppe", "Lieferanten", "Guenstigster", "Teuerster"]
    widths = [25, 60, 30, 35, 40, 22, 25, 25]
    for h, w in zip(headers, widths):
        pdf.cell(w, 8, h, border=1)
    pdf.ln()
    for r in rows:
        values = [
            r["artikelnummer"] or "", (r["canonical_name"] or "")[:35], r["ean"] or "-", (r["hersteller"] or "-")[:20],
            (r["warengruppe"] or "-")[:20], str(r["anzahl_lieferanten"]),
            f"{r['guenstigster_preis']:.2f}" if r["guenstigster_preis"] else "-",
            f"{r['teuerster_preis']:.2f}" if r["teuerster_preis"] else "-",
        ]
        for v, w in zip(values, widths):
            pdf.cell(w, 7, str(v), border=1)
        pdf.ln()

    buf = io.BytesIO(pdf.output())
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=artikel_export.pdf"},
    )


@router.get("/preisvergleich/{article_id}.pdf")
def export_price_comparison_pdf(article_id: str):
    with get_cursor() as cur:
        cur.execute("SELECT canonical_name, artikelnummer FROM canonical_articles WHERE id = %s", (article_id,))
        article = cur.fetchone()
        cur.execute(
            """
            SELECT s.name AS supplier_name, co.price, co.lieferzeit_tage, co.verfuegbarkeit, co.bewertung
            FROM current_offers co JOIN suppliers s ON s.id = co.supplier_id
            WHERE co.canonical_article_id = %s ORDER BY co.price ASC NULLS LAST
            """,
            (article_id,),
        )
        offers = cur.fetchall()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=14)
    title = f"Preisvergleich: {article['canonical_name']}" if article else "Preisvergleich"
    pdf.cell(0, 10, title, ln=True)
    pdf.set_font("Helvetica", size=10)
    headers = ["Lieferant", "Preis", "Lieferzeit (Tage)", "Verfuegbarkeit", "Bewertung"]
    widths = [55, 30, 35, 40, 30]
    for h, w in zip(headers, widths):
        pdf.cell(w, 8, h, border=1)
    pdf.ln()
    for o in offers:
        values = [
            o["supplier_name"], f"{o['price']:.2f} EUR" if o["price"] else "-",
            str(o["lieferzeit_tage"] or "-"), o["verfuegbarkeit"] or "-", str(o["bewertung"] or "-"),
        ]
        for v, w in zip(values, widths):
            pdf.cell(w, 8, str(v), border=1)
        pdf.ln()

    buf = io.BytesIO(pdf.output())
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=preisvergleich_{article_id}.pdf"},
    )
