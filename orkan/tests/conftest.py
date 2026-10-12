"""Testumgebung: eigener Mini-Pool, eigene Queue, eigenes Arbeitsverzeichnis.

Die Umgebungsvariablen werden gesetzt, *bevor* ``app.config`` importiert wird –
der echte Produktivpool wird von den Tests nie angefasst.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

_TMP = Path(tempfile.mkdtemp(prefix="orkan-tests-"))
PROJEKT = Path(__file__).resolve().parent.parent

POOL_SPALTEN = [
    "ArtikelNrLieferant", "BezArtikel1", "BezArtikel2", "BezArtikel3", "BezArtikelLang",
    "KurzBezeichnung", "BezArtikelGruppe", "Lager", "Lagerort", "BezLagerort",
    "LagerMin", "LagerMax", "LagerEinheit", "VpeEinheit", "MengeProVPE",
    "AbwBestellmenge", "AbwBestelleinheit",
    "Werksnummer", "HerstellerNr", "EAN", "Bild", "Lieferanten_alle",
    "Anz_Lieferanten", "Vorkommen", "Quellen", "VermutlichTestdaten",
    "HatKonflikt", "KritischerKonflikt",
]


def _pool_zeile(nr, bez1, gruppe, mn, mx, **rest):
    zeile = dict.fromkeys(POOL_SPALTEN, "")
    zeile.update({
        "ArtikelNrLieferant": nr, "BezArtikel1": bez1, "BezArtikelGruppe": gruppe,
        "LagerMin": mn, "LagerMax": mx, "Lager": "Standard Lager",
        "Lagerort": gruppe, "BezLagerort": gruppe, "LagerEinheit": "Stück",
        "Lieferanten_alle": "Gerhard Sprügel GmbH", "Anz_Lieferanten": "1.0",
        "Vorkommen": "1", "Quellen": "Test",
    })
    zeile.update(rest)
    return zeile


def _mini_pool() -> pd.DataFrame:
    zeilen = [
        _pool_zeile("CUS18H", "Kupfer Pressfitting Bogen 90", "Pressfittings", "4", "8",
                    KurzBezeichnung="CU18", EAN="4004478000001"),
        _pool_zeile("CUS22H", "Kupfer Pressfitting Bogen 45", "Pressfittings", "6", "12"),
        # Gebindeartikel: gelagert wird das Pack, bestellt werden kann stückweise.
        _pool_zeile("CUS28H", "Kupfer Pressfitting Muffe", "Pressfittings", "2", "5",
                    Bild="cus28h.jpg", LagerEinheit="Pack", MengeProVPE="100",
                    VpeEinheit="Stück", AbwBestellmenge="100",
                    AbwBestelleinheit="Stück"),
        _pool_zeile("CUS35H", "Kupfer Pressfitting T-Stueck", "Pressfittings", "3", "9"),
        _pool_zeile("GWS-M10", "Gewindestange M10", "Befestigungstechnik", "10", "20",
                    Lieferanten_alle="Adolf Würth; Gerhard Sprügel GmbH",
                    Anz_Lieferanten="2.0"),
        _pool_zeile("GWS-M12", "Gewindestange M12", "Befestigungstechnik", "12", "24"),
        _pool_zeile("GWS-M16", "Gewindestange M16", "Befestigungstechnik", "8", "16"),
        _pool_zeile("01.001.90", "OrKan-Systemschiene 90", "OrKan-Verbrauchsmaterial", "17", "34"),
        _pool_zeile("387500140020", "Tauchsägeblatt", "Befestigungstechnik", "2", "4",
                    EAN="4004478123456"),
        # Führende Nullen und lange reine Zahlen: genau das zerstört Excel,
        # wenn die Spalte nicht als Text formatiert ist.
        _pool_zeile("0000100951687", "Lüsterklemmen 4qmm", "Elektro", "5", "10",
                    Werksnummer="0015051500001", HerstellerNr="109757008001"),
        _pool_zeile("02983", "Dichtring", "Sanitaer", "20", "40"),
        # Leerzeichen als Gruppierung – im echten Pool 5.635 Stück, alle gültig.
        _pool_zeile("72 011 23", "Waschtischarmatur", "Sanitaer", "1", "3"),
        # Lieferantenkürzel ganz ohne Ziffer – im echten Pool 1.240 Stück.
        _pool_zeile("QBSHNS", "Schlauchbrause", "Sanitaer", "2", "6"),
        # Artikel ohne LagerMin – darf nie MinMax-Kandidat sein
        _pool_zeile("OHNE-MIN", "Artikel ohne Bestandsangabe", "Sonstiges", "", ""),
    ]
    return pd.DataFrame(zeilen, columns=POOL_SPALTEN)


_POOL_PFAD = _TMP / "pool.csv"
_mini_pool().to_csv(_POOL_PFAD, sep=";", index=False, encoding="utf-8-sig")

os.environ["POOL_PFAD"] = str(_POOL_PFAD)
os.environ["QUEUE_PFAD"] = str(_TMP / "neuaufnahmen_queue.csv")
os.environ["ARBEITSVERZEICHNIS"] = str(_TMP / "arbeitsdaten")
os.environ["ADMIN_USER"] = "pruefer"
os.environ["ADMIN_PASSWORT"] = "geheim"
os.environ.pop("ANTHROPIC_API_KEY", None)


@pytest.fixture
def pool():
    from app import pool as pool_modul

    return pool_modul.neu_laden()


@pytest.fixture(autouse=True)
def eigene_benutzerdaten(monkeypatch):
    """Kein Test darf in die echte Einstellungsdatei schreiben.

    ``bildpool.setze_pfad`` merkt sich den Bildordner in
    ``BENUTZERDATEN/einstellungen.json``. Im Entwicklungsbetrieb ist das der
    Projektordner – ein Test hat damit einmal den eingestellten Bildordner
    durch ein Testverzeichnis ersetzt, das es nach dem Lauf nicht mehr gab.
    """
    from app import bildpool, config

    ordner = _TMP / "benutzerdaten"
    ordner.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(config, "BENUTZERDATEN", ordner)
    bildpool.zuruecksetzen()
    yield
    bildpool.zuruecksetzen()


@pytest.fixture(autouse=True)
def saubere_queue():
    """Queue vor jedem Test leeren."""
    from app import config

    Path(config.QUEUE_PFAD).unlink(missing_ok=True)
    yield
    Path(config.QUEUE_PFAD).unlink(missing_ok=True)


@pytest.fixture(scope="session")
def echter_pool_pfad() -> Path:
    """Der echte Datenpool – nur lesend, für die Vergleichstests."""
    pfad = PROJEKT / "daten" / "Datenpool_bereinigt.csv"
    if not pfad.exists():
        pytest.skip("Echter Datenpool nicht vorhanden.")
    return pfad


@pytest.fixture
def klient():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
