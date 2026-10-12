"""PDF-Eingabe: Tabellen-PDFs offline, KI-Fallback nur mit API-Key."""
from __future__ import annotations

import pandas as pd
import pytest

from app import config, parsing, pdf_extract

reportlab = pytest.importorskip("reportlab", reason="reportlab nur für die PDF-Tests nötig")

from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.units import mm  # noqa: E402
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle  # noqa: E402
from reportlab.lib import colors  # noqa: E402


def _tabellen_pdf(pfad, zeilen) -> None:
    """Ein PDF mit einer echten, umrandeten Tabelle erzeugen."""
    doc = SimpleDocTemplate(str(pfad), pagesize=A4, topMargin=20 * mm)
    tabelle = Table(zeilen)
    tabelle.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ]))
    doc.build([tabelle])


def test_tabellen_pdf_wird_ohne_ki_gelesen(tmp_path):
    pfad = tmp_path / "liste.pdf"
    _tabellen_pdf(pfad, [
        ["Artikelnummer", "Bezeichnung", "Lieferant"],
        ["CUS18H", "Kupfer Pressfitting Bogen", "Spruegel"],
        ["GWS-M10", "Gewindestange M10", "Wuerth"],
        ["01.001.90", "OrKan-Systemschiene", "OrKan"],
    ])

    roh = parsing.lies_datei(pfad)

    assert roh.quelle == "PDF"
    assert roh.ki_genutzt is False  # offline gelesen, kein API-Aufruf
    assert list(roh.df.columns) == ["Artikelnummer", "Bezeichnung", "Lieferant"]
    assert list(roh.df["Artikelnummer"]) == ["CUS18H", "GWS-M10", "01.001.90"]


def test_pdf_spalten_werden_erkannt_und_abgeglichen(tmp_path, pool):
    from app import matching

    pfad = tmp_path / "liste.pdf"
    _tabellen_pdf(pfad, [
        ["Art-Nr.", "Benennung"],
        ["CUS18H", "Bogen 90"],
        ["NEU-PDF-1", "Unbekannter Artikel"],
    ])

    roh = parsing.lies_datei(pfad)
    zuordnung = parsing.erkenne_spalten(roh.df).zuordnung
    assert zuordnung["Artikelnummer"] == "Art-Nr."

    liste = parsing.baue_kundenliste(roh.df, zuordnung)
    ergebnis = matching.abgleich(liste, pool)
    assert ergebnis.anzahl_gefunden == 1
    assert ergebnis.anzahl_neu == 1


def test_mehrseitiges_pdf_wird_zusammengefuehrt(tmp_path):
    pfad = tmp_path / "lang.pdf"
    zeilen = [["Artikelnummer", "Bezeichnung"]]
    zeilen += [[f"ART-{i:04d}", f"Artikel {i}"] for i in range(120)]
    _tabellen_pdf(pfad, zeilen)

    roh = parsing.lies_datei(pfad)
    assert len(roh.df) == 120
    assert roh.df["Artikelnummer"].iloc[-1] == "ART-0119"


def test_ohne_api_key_kommt_bei_scan_pdf_ein_klarer_hinweis(tmp_path, monkeypatch):
    """Ein PDF ohne auslesbare Tabelle darf ohne API-Key nicht still scheitern."""
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    assert not config.ki_pdf_aktiv()

    pfad = tmp_path / "leer.pdf"
    doc = SimpleDocTemplate(str(pfad), pagesize=A4)
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    doc.build([Paragraph("Angebot Nr. 4711 – vielen Dank für Ihre Anfrage.",
                         getSampleStyleSheet()["Normal"])])

    with pytest.raises(ValueError) as fehler:
        parsing.lies_datei(pfad)
    assert "Excel" in str(fehler.value)  # verständlicher Hinweis statt Absturz


def test_ki_wird_nur_bei_gesetztem_key_versucht(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-ant-testschluessel")
    assert config.ki_pdf_aktiv()

    gerufen = {}

    def falsche_ki(pfad):
        gerufen["ja"] = True
        return pd.DataFrame({"Artikelnummer": ["KI-1"], "Bezeichnung1": ["Aus dem Scan"]})

    monkeypatch.setattr(pdf_extract, "_extrahiere_mit_ki", falsche_ki)

    pfad = tmp_path / "scan.pdf"
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    SimpleDocTemplate(str(pfad), pagesize=A4).build(
        [Paragraph("Gescanntes Angebot", getSampleStyleSheet()["Normal"])]
    )

    roh = pdf_extract.lies_pdf(pfad)
    assert gerufen.get("ja") is True
    assert roh.ki_genutzt is True
    assert list(roh.df["Artikelnummer"]) == ["KI-1"]


def test_tabellen_pdf_ruft_die_ki_gar_nicht_auf(tmp_path, monkeypatch):
    """Kostenkontrolle: bei lesbarer Tabelle darf kein API-Aufruf passieren."""
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "sk-ant-testschluessel")

    def darf_nicht_aufgerufen_werden(pfad):
        raise AssertionError("KI wurde trotz lesbarer Tabelle aufgerufen")

    monkeypatch.setattr(pdf_extract, "_extrahiere_mit_ki", darf_nicht_aufgerufen_werden)

    pfad = tmp_path / "liste.pdf"
    _tabellen_pdf(pfad, [["Artikelnummer"], ["CUS18H"], ["GWS-M10"]])

    roh = pdf_extract.lies_pdf(pfad)
    assert roh.ki_genutzt is False
    assert len(roh.df) == 2
