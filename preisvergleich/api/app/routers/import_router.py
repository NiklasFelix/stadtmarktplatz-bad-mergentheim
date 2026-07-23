import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.auth import get_current_user, require_role
from common.db import get_cursor

_IMPORT_DIR = Path(__file__).resolve().parents[3] / "import"
_MATCHING_DIR = Path(__file__).resolve().parents[3] / "matching"
for _d in (_IMPORT_DIR, _MATCHING_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from column_mapping import build_staging_record, map_headers  # noqa: E402
from staging import create_import_batch, ensure_source  # noqa: E402
from actions import process_staging_item  # noqa: E402

router = APIRouter(prefix="/import", tags=["import"], dependencies=[Depends(require_role("admin", "einkauf"))])

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


@router.post("/upload")
async def upload_import(
    file: UploadFile = File(...),
    source_name: str = Form(...),
    source_type: str = Form(...),
    user: dict = Depends(get_current_user),
):
    if source_type not in ("customer", "supplier"):
        raise HTTPException(status_code=400, detail="source_type muss 'customer' oder 'supplier' sein")

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Nicht unterstuetztes Dateiformat '{ext}'. Erlaubt: .xlsx, .xls, .csv")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Die hochgeladene Datei ist leer")

    try:
        if ext == ".csv":
            df = pd.read_csv(pd.io.common.BytesIO(content), dtype=object)
        else:
            df = pd.read_excel(pd.io.common.BytesIO(content), dtype=object)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Datei konnte nicht gelesen werden: {exc}")

    if df.empty:
        raise HTTPException(status_code=400, detail="Die Datei enthaelt keine Datenzeilen")

    header_map = map_headers(list(df.columns))
    default_supplier = source_name if source_type == "supplier" else None
    file_type = "excel" if ext != ".csv" else "excel"  # gemeinsame Verarbeitung, file_type-Spalte kennt nur excel/pdf

    errors = []
    records = []
    for i, row in enumerate(df.to_dict(orient="records"), start=1):
        record = build_staging_record(row, header_map, default_supplier, date.today())
        if not record["description"] and record["price"] is None:
            errors.append({"row_number": i, "message": "Weder Bezeichnung noch Preis erkennbar - Zeile uebersprungen", "raw_row": record["raw_row"]})
            continue
        records.append(record)

    with get_cursor() as cur:
        source_id = ensure_source(cur, source_name, source_type)
        batch_id = create_import_batch(cur, source_id, file.filename, file_type)

        inserted_ids = []
        for i, record in enumerate(records, start=1):
            cur.execute(
                """
                INSERT INTO staging_items
                    (batch_id, source_id, row_number, raw_row, description, supplier_name_raw,
                     article_number_raw, ean, price, unit, valid_from)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
                """,
                (
                    batch_id, source_id, i, __import__("json").dumps(record["raw_row"]), record["description"],
                    record["supplier_name_raw"], record["article_number_raw"], record["ean"], record["price"],
                    record["unit"], record["valid_from"],
                ),
            )
            inserted_ids.append(cur.fetchone()["id"])
        cur.execute("UPDATE import_batches SET row_count = %s WHERE id = %s", (len(records), batch_id))

        for err in errors:
            cur.execute(
                "INSERT INTO import_errors (batch_id, row_number, message, raw_row) VALUES (%s,%s,%s,%s)",
                (batch_id, err["row_number"], err["message"], __import__("json").dumps(err["raw_row"])),
            )

        # Matching sofort ausfuehren, damit die importierten Daten unmittelbar sichtbar sind
        match_summary = {"auto_accepted": 0, "needs_review": 0, "skipped": 0}
        for staging_id in inserted_ids:
            cur.execute("SELECT * FROM staging_items WHERE id = %s", (staging_id,))
            item = cur.fetchone()
            result = process_staging_item(cur, item)
            match_summary[result["status"]] = match_summary.get(result["status"], 0) + 1

    return {
        "batch_id": batch_id,
        "source_id": source_id,
        "file_name": file.filename,
        "rows_total": len(df),
        "rows_imported": len(records),
        "rows_failed": len(errors),
        "errors": errors,
        "match_summary": match_summary,
    }


@router.get("/history")
def import_history(user: dict = Depends(get_current_user)):
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT ib.id AS batch_id, ib.file_name, ib.file_type, ib.row_count, ib.imported_at,
                   s.name AS source_name, s.type AS source_type,
                   (SELECT COUNT(*) FROM import_errors ie WHERE ie.batch_id = ib.id) AS error_count
            FROM import_batches ib
            JOIN sources s ON s.id = ib.source_id
            ORDER BY ib.imported_at DESC
            LIMIT 100
            """
        )
        return cur.fetchall()


@router.get("/history/{batch_id}/errors")
def import_batch_errors(batch_id: int, user: dict = Depends(get_current_user)):
    with get_cursor() as cur:
        cur.execute(
            "SELECT row_number, message, raw_row, created_at FROM import_errors WHERE batch_id = %s ORDER BY row_number",
            (batch_id,),
        )
        return cur.fetchall()
