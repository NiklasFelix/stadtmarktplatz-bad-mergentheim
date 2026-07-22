"""Verarbeitet alle noch nicht gematchten staging_items: EAN-Abgleich zuerst,
sonst semantisches Matching mit Schwellenwerten. Unsichere Zuordnungen werden
mit status='needs_review' markiert statt automatisch als Angebot uebernommen.

Aufruf: python matching/run_matching.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.db import get_cursor
from actions import process_staging_item


def fetch_unmatched(cur):
    cur.execute(
        """
        SELECT s.* FROM staging_items s
        LEFT JOIN article_matches m ON m.staging_item_id = s.id
        WHERE m.id IS NULL
        ORDER BY s.id
        """
    )
    return cur.fetchall()


def main():
    with get_cursor() as cur:
        items = fetch_unmatched(cur)
        print(f"{len(items)} offene staging_items gefunden")

        summary = {"auto_accepted": 0, "needs_review": 0, "skipped": 0}
        for item in items:
            result = process_staging_item(cur, item)
            summary[result["status"]] = summary.get(result["status"], 0) + 1
            label = f"[{result['status']}] {result['method']}"
            if result.get("similarity") is not None:
                label += f" (similarity={result['similarity']:.3f})"
            print(f"staging_item {item['id']}: {item['description']!r} -> {label}")

        print("Zusammenfassung:", summary)


if __name__ == "__main__":
    main()
