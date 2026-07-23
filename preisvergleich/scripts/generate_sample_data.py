"""Erzeugt Beispiel-Excel- und PDF-Preislisten (Kunden + Grosshaendler) mit
bewusst ueberlappenden Artikeln (gleiche EAN, unterschiedliche Bezeichnungen ohne
EAN), um Import + Matching einmal komplett durchzuspielen.

Aufruf: python scripts/generate_sample_data.py [ziel-verzeichnis]
"""
import os
import sys

import pandas as pd
from fpdf import FPDF

OUT_DIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data")


def write_excel(path, rows):
    pd.DataFrame(rows).to_excel(path, index=False)
    print(f"geschrieben: {path} ({len(rows)} Zeilen)")


def write_pdf(path, headers, rows):
    pdf = FPDF(orientation="L")
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    # Artikelbezeichnung braucht deutlich mehr Platz als die uebrigen Spalten,
    # sonst schneidet pdfplumber beim Tabellen-Parsing ueberlaufenden Text ab
    weights = [3.0] + [1.0] * (len(headers) - 1)
    total_weight = sum(weights)
    col_widths = [pdf.epw * w / total_weight for w in weights]

    for h, w in zip(headers, col_widths):
        pdf.cell(w, 8, str(h), border=1)
    pdf.ln()
    for row in rows:
        for value, w in zip(row, col_widths):
            pdf.cell(w, 8, str(value), border=1)
        pdf.ln()
    pdf.output(path)
    print(f"geschrieben: {path} ({len(rows)} Zeilen)")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Grosshaendler Nord: legt P1, P2, P3 per EAN an, P5 ohne EAN als neuer Artikel
    write_excel(
        os.path.join(OUT_DIR, "grosshandel_nord.xlsx"),
        [
            {"Artikelbezeichnung": "Bio Apfel Elstar 1kg", "Artikelnummer": "GN-001", "EAN": "4000000000011", "Einkaufspreis": "1,10", "Einheit": "Kiste"},
            {"Artikelbezeichnung": "Vollmilch 3,5% 1L", "Artikelnummer": "GN-002", "EAN": "4000000000028", "Einkaufspreis": "0,85", "Einheit": "Kiste"},
            {"Artikelbezeichnung": "Butter 250g", "Artikelnummer": "GN-003", "EAN": "4000000000035", "Einkaufspreis": "2,05", "Einheit": "Karton"},
            {"Artikelbezeichnung": "Kaffee Arabica 500g ganze Bohne", "Artikelnummer": "GN-005", "EAN": "", "Einkaufspreis": "6,90", "Einheit": "Packung"},
        ],
    )

    # Grosshaendler Sued: matched P1, P2 per EAN, legt P4 ohne EAN neu an
    write_excel(
        os.path.join(OUT_DIR, "grosshandel_sued.xlsx"),
        [
            {"Artikelbezeichnung": "Bio Apfel Elstar 1kg", "Artikelnummer": "GS-11", "EAN": "4000000000011", "Einkaufspreis": "1,18", "Einheit": "Kiste"},
            {"Artikelbezeichnung": "Vollmilch 3,5% 1L", "Artikelnummer": "GS-12", "EAN": "4000000000028", "Einkaufspreis": "0,88", "Einheit": "Kiste"},
            {"Artikelbezeichnung": "Bio-Eier 10er Freiland", "Artikelnummer": "GS-14", "EAN": "", "Einkaufspreis": "2,30", "Einheit": "Palette"},
        ],
    )

    # Frischehof (PDF): matched P1, P3 per EAN, testet semantische Naehe zu P5 (Kaffee)
    write_pdf(
        os.path.join(OUT_DIR, "frischehof_preisliste.pdf"),
        ["Artikelbezeichnung", "Artikelnummer", "EAN", "Einkaufspreis", "Einheit"],
        [
            ["Bio Apfel Elstar 1kg", "FH-21", "4000000000011", "1,25", "Kiste"],
            ["Butter 250g", "FH-23", "4000000000035", "2,20", "Karton"],
            ["Kaffeebohnen Arabica 500 g", "FH-25", "", "7,20", "Packung"],
        ],
    )

    # Kunde Muster GmbH (OrKan Cloud Export): P1, P2 per EAN, P4 mit abweichender
    # Bezeichnung ohne EAN (semantischer Match-Test gegen Grosshaendler Sued)
    write_excel(
        os.path.join(OUT_DIR, "customer_muster_gmbh.xlsx"),
        [
            {"Bezeichnung": "Bio Apfel Elstar 1kg", "Lieferant": "Hof Sonnenschein", "Artikelnummer": "A-100", "EAN": "4000000000011", "Einkaufspreis": "1,30"},
            {"Bezeichnung": "Vollmilch 3,5% 1L", "Lieferant": "Hof Sonnenschein", "Artikelnummer": "A-101", "EAN": "4000000000028", "Einkaufspreis": "0,99"},
            {"Bezeichnung": "Eier Freilandhaltung 10 Stk Bio", "Lieferant": "Hof Sonnenschein", "Artikelnummer": "A-104", "EAN": "", "Einkaufspreis": "2,49"},
        ],
    )

    # Kunde Beispiel Handel: P1, P3 mit abweichenden Bezeichnungen ohne EAN,
    # P4 mit fast identischer Bezeichnung wie Grosshaendler Sued
    write_excel(
        os.path.join(OUT_DIR, "customer_beispiel_handel.xlsx"),
        [
            {"Bezeichnung": "Apfel Elstar Bio, 1 kg", "Lieferant": "Obsthof Meier", "Artikelnummer": "BH-30", "EAN": "", "Einkaufspreis": "1,35"},
            {"Bezeichnung": "Butter 250g", "Lieferant": "Molkerei Krause", "Artikelnummer": "BH-33", "EAN": "4000000000035", "Einkaufspreis": "2,10"},
            {"Bezeichnung": "Bio Eier 10er Freiland", "Lieferant": "Hof Sonnenschein", "Artikelnummer": "BH-34", "EAN": "", "Einkaufspreis": "2,45"},
        ],
    )

    print(f"\nBeispieldaten liegen in: {OUT_DIR}")


if __name__ == "__main__":
    main()
