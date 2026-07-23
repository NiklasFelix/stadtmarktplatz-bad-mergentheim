"""Liest eine Excel-Preisliste (Kunde oder Lieferant) ein und schreibt sie
unveraendert (als raw_row) in staging_items.

Aufruf:
    python import/import_excel.py <datei.xlsx> --source-name "Lieferant Mustermann" --source-type supplier
"""
import argparse
import os
import sys
from datetime import date

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from column_mapping import build_staging_record, map_headers
from staging import import_rows


def read_excel_rows(path: str, sheet) -> list:
    df = pd.read_excel(path, sheet_name=sheet, dtype=object)
    header_map = map_headers(list(df.columns))
    rows = df.to_dict(orient="records")
    return header_map, rows


def main():
    parser = argparse.ArgumentParser(description="Excel-Preisliste in Staging importieren")
    parser.add_argument("file")
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--source-type", required=True, choices=["customer", "supplier"])
    parser.add_argument("--sheet", default=0)
    args = parser.parse_args()

    header_map, rows = read_excel_rows(args.file, args.sheet)

    default_supplier = args.source_name if args.source_type == "supplier" else None
    records = [
        build_staging_record(row, header_map, default_supplier, date.today())
        for row in rows
    ]

    result = import_rows(
        source_name=args.source_name,
        source_type=args.source_type,
        file_name=os.path.basename(args.file),
        file_type="excel",
        records=records,
    )
    print(f"Importiert: {result['row_count']} Zeilen (source_id={result['source_id']}, batch_id={result['batch_id']})")


if __name__ == "__main__":
    main()
