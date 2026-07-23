import json

from common.db import get_cursor


def ensure_source(cur, name: str, source_type: str) -> int:
    cur.execute("SELECT id FROM sources WHERE name = %s AND type = %s", (name, source_type))
    row = cur.fetchone()
    if row:
        return row["id"]
    cur.execute(
        "INSERT INTO sources (name, type) VALUES (%s, %s) RETURNING id",
        (name, source_type),
    )
    return cur.fetchone()["id"]


def create_import_batch(cur, source_id: int, file_name: str, file_type: str) -> int:
    cur.execute(
        "INSERT INTO import_batches (source_id, file_name, file_type) VALUES (%s, %s, %s) RETURNING id",
        (source_id, file_name, file_type),
    )
    return cur.fetchone()["id"]


def insert_staging_items(cur, batch_id: int, source_id: int, records: list) -> int:
    count = 0
    for i, record in enumerate(records, start=1):
        cur.execute(
            """
            INSERT INTO staging_items
                (batch_id, source_id, row_number, raw_row, description, supplier_name_raw,
                 article_number_raw, ean, price, unit, valid_from)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                batch_id,
                source_id,
                i,
                json.dumps(record["raw_row"]),
                record["description"],
                record["supplier_name_raw"],
                record["article_number_raw"],
                record["ean"],
                record["price"],
                record["unit"],
                record["valid_from"],
            ),
        )
        count += 1
    cur.execute("UPDATE import_batches SET row_count = %s WHERE id = %s", (count, batch_id))
    return count


def import_rows(source_name: str, source_type: str, file_name: str, file_type: str, records: list) -> dict:
    with get_cursor() as cur:
        source_id = ensure_source(cur, source_name, source_type)
        batch_id = create_import_batch(cur, source_id, file_name, file_type)
        count = insert_staging_items(cur, batch_id, source_id, records)
    return {"source_id": source_id, "batch_id": batch_id, "row_count": count}
