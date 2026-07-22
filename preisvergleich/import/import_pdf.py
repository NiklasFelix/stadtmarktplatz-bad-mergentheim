"""Liest eine PDF-Preisliste (typischerweise Grosshaendler) ein und schreibt sie
unveraendert (als raw_row) in staging_items.

Annahme: jede Tabelle auf jeder Seite hat dieselbe Kopfzeile (erste Zeile der
ersten gefundenen Tabelle). Bei stark abweichenden PDF-Layouts muss dieser
Importer pro Lieferant angepasst werden.

Aufruf:
    python import/import_pdf.py <datei.pdf> --source-name "Grosshaendler XY" --source-type supplier
"""
import argparse
import os
import sys
from datetime import date

import pdfplumber

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from column_mapping import build_staging_record, map_headers
from staging import import_rows


def read_pdf_rows(path: str):
    header = None
    rows = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                if not table:
                    continue
                if header is None:
                    header = table[0]
                    data_rows = table[1:]
                else:
                    data_rows = table[1:] if table[0] == header else table
                for row in data_rows:
                    rows.append(dict(zip(header, row)))
    if header is None:
        raise ValueError("Keine Tabelle im PDF gefunden")
    header_map = map_headers(header)
    return header_map, rows


def main():
    parser = argparse.ArgumentParser(description="PDF-Preisliste in Staging importieren")
    parser.add_argument("file")
    parser.add_argument("--source-name", required=True)
    parser.add_argument("--source-type", required=True, choices=["customer", "supplier"])
    args = parser.parse_args()

    header_map, rows = read_pdf_rows(args.file)

    default_supplier = args.source_name if args.source_type == "supplier" else None
    records = [
        build_staging_record(row, header_map, default_supplier, date.today())
        for row in rows
    ]

    result = import_rows(
        source_name=args.source_name,
        source_type=args.source_type,
        file_name=os.path.basename(args.file),
        file_type="pdf",
        records=records,
    )
    print(f"Importiert: {result['row_count']} Zeilen (source_id={result['source_id']}, batch_id={result['batch_id']})")


if __name__ == "__main__":
    main()
