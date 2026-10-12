"""Spaltenerkennung, Trennzeichen, Bereinigung der Kundeneingaben."""
from __future__ import annotations

import pandas as pd
import pytest

from app import parsing


# ---------------------------------------------------------------------------
# Spaltenerkennung – Header-Varianten
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "header",
    [
        "Artikelnummer",
        "Artikelnr",
        "Art-Nr.",
        "Art.-Nr",
        "ArtNr",
        "Artikelnummer des Lieferanten",
        "Lieferantenartikelnummer",
        "Bestellnummer",
        "Bestell-Nr.",
        "ARTIKELNUMMER",
        "artikelnummer ",
        "Sachnummer",
        "IDH-Nummer",
    ],
)
def test_artikelnummer_spalte_wird_erkannt(header):
    df = pd.DataFrame({header: ["CUS18H", "CUS22H"], "Preis": ["1,10", "2,20"]})
    assert parsing.erkenne_spalten(df).artikelnummer_spalte == header


@pytest.mark.parametrize(
    "header,feld",
    [
        ("Lieferant", "Lieferant"),
        ("Lieferantenname", "Lieferant"),
        ("Bezeichnung", "Bezeichnung1"),
        ("Artikelbezeichnung", "Bezeichnung1"),
        ("Benennung", "Bezeichnung1"),
        ("Bezeichnung2", "Bezeichnung2"),
        ("Warengruppe", "Artikelgruppe"),
        ("Artikelgruppe", "Artikelgruppe"),
        ("EAN", "EAN"),
        ("GTIN", "EAN"),
        ("Mengeneinheit", "Einheit"),
        ("Menge", "Menge"),
        ("Herstellernummer", "Herstellernummer"),
    ],
)
def test_optionale_spalten_werden_erkannt(header, feld):
    df = pd.DataFrame({"Artikelnummer": ["CUS18H"], header: ["x"]})
    assert parsing.erkenne_spalten(df).zuordnung.get(feld) == header


def test_hersteller_und_artikelnummer_werden_nicht_verwechselt():
    df = pd.DataFrame({
        "Herstellerartikelnummer": ["H-1"],
        "Artikelnummer": ["CUS18H"],
    })
    zuordnung = parsing.erkenne_spalten(df).zuordnung
    assert zuordnung["Artikelnummer"] == "Artikelnummer"
    assert zuordnung["Herstellernummer"] == "Herstellerartikelnummer"


def test_eine_spalte_wird_nur_einmal_vergeben():
    df = pd.DataFrame({"Artikelnummer": ["CUS18H"], "Bezeichnung": ["Bogen"]})
    zuordnung = parsing.erkenne_spalten(df).zuordnung
    assert len(set(zuordnung.values())) == len(zuordnung)


def test_ohne_passenden_header_gewinnt_die_nummernartigste_spalte():
    df = pd.DataFrame({
        "Spalte A": ["Kupferbogen 90 Grad", "Gewindestange lang", "Muffe rund"],
        "Spalte B": ["CUS18H", "GWS-M10", "01.001.90"],
        "Spalte C": ["1", "2", "3"],
    })
    erkannt = parsing.erkenne_spalten(df)
    assert erkannt.artikelnummer_spalte == "Spalte B"
    assert "Artikelnummer" in erkannt.unsicher


def test_verfuegbare_spalten_werden_mitgeliefert():
    df = pd.DataFrame({"Artikelnummer": ["A123"], "Extra": ["x"]})
    assert parsing.erkenne_spalten(df).verfuegbare_spalten == ["Artikelnummer", "Extra"]


# ---------------------------------------------------------------------------
# Bereinigung
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("wert", ["4,04478E+12", "4.04478E+12", "1E5", " 2,5e-3 ", "4,04478E12"])
def test_wissenschaftliche_notation_wird_entfernt(wert):
    assert parsing.ist_wissenschaftlich(wert)
    assert parsing.bereinige_bezeichnung(wert) == ""
    assert parsing.bereinige_nummer(wert) == ""


@pytest.mark.parametrize("wert", ["CUS18H", "4004478000001", "E5-Bogen", "Bogen 90"])
def test_normale_werte_bleiben_erhalten(wert):
    assert not parsing.ist_wissenschaftlich(wert)
    assert parsing.bereinige_bezeichnung(wert) == wert


@pytest.mark.parametrize("wert", ["0", "0,0", "-", "n/a", "NULL", "keine"])
def test_fuellwerte_in_bezeichnungen_werden_entfernt(wert):
    assert parsing.bereinige_bezeichnung(wert) == ""


def test_fuellwert_null_bleibt_in_nummernfeldern():
    """In Artikelnummern ist eine 0 kein Füllwert, sondern ein Zeichen."""
    assert parsing.bereinige_nummer("01.001.90") == "01.001.90"


def test_excel_gleitkommazahlen_werden_zu_ganzen_nummern():
    assert parsing.zelle_zu_text(387500140020.0) == "387500140020"
    assert parsing.zelle_zu_text(12345.0) == "12345"
    assert parsing.zelle_zu_text(1.5) == "1.5"


def test_kundenliste_bauen_bereinigt_und_wirft_leere_zeilen_raus():
    df = pd.DataFrame({
        "Nr": ["CUS18H", "4,04478E+12", "", "GWS-M10"],
        "Text": ["Bogen", "Muffe", "Rohr", "0"],
    })
    liste = parsing.baue_kundenliste(df, {"Artikelnummer": "Nr", "Bezeichnung1": "Text"})

    assert list(liste["Artikelnummer"]) == ["CUS18H", "GWS-M10"]
    assert liste["Bezeichnung1"].iloc[0] == "Bogen"
    assert pd.isna(liste["Bezeichnung1"].iloc[1])  # "0" war ein Füllwert


def test_kundenliste_ohne_artikelnummer_spalte_meldet_fehler():
    with pytest.raises(ValueError, match="Artikelnummern"):
        parsing.baue_kundenliste(pd.DataFrame({"A": [1]}), {"Bezeichnung1": "A"})


# ---------------------------------------------------------------------------
# Trennzeichenerkennung
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("trenner", [";", ",", "\t", "|"])
def test_csv_trennzeichen_werden_erkannt(tmp_path, trenner):
    pfad = tmp_path / "liste.csv"
    zeilen = ["Artikelnummer|Bezeichnung", "CUS18H|Bogen 90", "GWS-M10|Gewindestange"]
    pfad.write_text("\n".join(z.replace("|", trenner) for z in zeilen), encoding="utf-8")

    roh = parsing.lies_datei(pfad)
    assert list(roh.df.columns) == ["Artikelnummer", "Bezeichnung"]
    assert len(roh.df) == 2


def test_csv_mit_umlauten_in_cp1252(tmp_path):
    pfad = tmp_path / "liste.csv"
    pfad.write_bytes("Artikelnummer;Bezeichnung\nCUS18H;Tauchsägeblatt\n".encode("cp1252"))
    roh = parsing.lies_datei(pfad)
    assert roh.df["Bezeichnung"].iloc[0] == "Tauchsägeblatt"


def test_excel_wird_gelesen(tmp_path):
    pfad = tmp_path / "liste.xlsx"
    pd.DataFrame({"Art-Nr.": ["CUS18H"], "Lieferant": ["Sprügel"]}).to_excel(pfad, index=False)

    roh = parsing.lies_datei(pfad)
    zuordnung = parsing.erkenne_spalten(roh.df).zuordnung
    assert zuordnung["Artikelnummer"] == "Art-Nr."
    assert zuordnung["Lieferant"] == "Lieferant"


def test_unbekanntes_format_meldet_klaren_fehler(tmp_path):
    pfad = tmp_path / "liste.docx"
    pfad.write_bytes(b"nicht wirklich ein Word-Dokument")
    with pytest.raises(ValueError, match="nicht unterstützt"):
        parsing.lies_datei(pfad)
