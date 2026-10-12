"""Einstellungen, alle über Umgebungsvariablen überschreibbar.

Die Anwendung läuft in zwei Betriebsarten:

* **Normal** (Quellcode, Server, Docker): alles liegt im Projektverzeichnis.
* **Gebündelt** (Desktop-``.exe`` von PyInstaller): Pool, Formatvorlage und
  Oberfläche stecken schreibgeschützt im Paket; Queue und Ergebnisdateien
  landen im Benutzerprofil, weil im Paket nicht geschrieben werden kann.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

BASIS = Path(__file__).resolve().parent.parent


def gebuendelt() -> bool:
    """Läuft die Anwendung als eingepackte .exe?"""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


if gebuendelt():
    #: Mitgelieferte, schreibgeschützte Dateien im Paket.
    RESSOURCEN = Path(sys._MEIPASS)
    #: Alles, was geschrieben werden muss, kommt ins Benutzerprofil.
    BENUTZERDATEN = (
        Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "OrKan-Matching"
    )
else:
    RESSOURCEN = BASIS
    BENUTZERDATEN = BASIS


def _pfad(env: str, standard: str, basis: Path) -> Path:
    wert = os.environ.get(env, "").strip()
    p = Path(wert) if wert else basis / standard
    return p if p.is_absolute() else basis / p


def _zahl(env: str, standard: int) -> int:
    try:
        return int(os.environ.get(env, "").strip() or standard)
    except ValueError:
        return standard


POOL_PFAD = _pfad("POOL_PFAD", "daten/Datenpool_bereinigt.csv", RESSOURCEN)
VORLAGE_PFAD = _pfad("VORLAGE_PFAD", "referenz/Importformat_39_Spalten_Vorlage.csv", RESSOURCEN)
STATIC_PFAD = _pfad("STATIC_PFAD", "app/static", RESSOURCEN)

QUEUE_PFAD = _pfad("QUEUE_PFAD", "daten/neuaufnahmen_queue.csv", BENUTZERDATEN)
ARBEITSVERZEICHNIS = _pfad("ARBEITSVERZEICHNIS", "arbeitsdaten", BENUTZERDATEN)

ADMIN_USER = os.environ.get("ADMIN_USER", "").strip()
ADMIN_PASSWORT = os.environ.get("ADMIN_PASSWORT", "")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODELL = os.environ.get("ANTHROPIC_MODELL", "claude-sonnet-5").strip()

#: Verzeichnis mit den Artikelbildern. Auf dem Server fest konfiguriert –
#: im Kundenformular ist der Pfad bewusst NICHT eingebbar, sonst könnte man sich
#: beliebige Verzeichnisse des Servers als ZIP herunterladen.
BILDPOOL_PFAD = os.environ.get("BILDPOOL_PFAD", "").strip()

#: Darf der Bildordner in der Oberfläche eingegeben werden?
#: In der Desktop-Fassung immer – dort gehört der Rechner dem Anwender.
#: Auf einem Server standardmäßig NICHT: Ein dort eingetippter Pfad zeigt auf den
#: Server, und ein frei wählbarer Pfad wäre ein Datenleck. Für den Einzelplatz-
#: betrieb (start.bat) lässt sich die Eingabe mit BILDPOOL_EINGABE=1 freischalten.
BILDPOOL_EINGABE = os.environ.get("BILDPOOL_EINGABE", "").strip().lower() in (
    "1", "true", "ja", "yes", "on"
)

#: Obergrenze für das Bild-ZIP, damit ein Auftrag nicht die Platte füllt.
MAX_ZIP_MB = _zahl("MAX_ZIP_MB", 500)

MAX_UPLOAD_MB = _zahl("MAX_UPLOAD_MB", 20)
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024
MAX_ZEILEN = _zahl("MAX_ZEILEN", 20000)
ERGEBNIS_TTL_STUNDEN = _zahl("ERGEBNIS_TTL_STUNDEN", 24)

CSV_TRENNZEICHEN = ";"
CSV_KODIERUNG = "utf-8-sig"


def ki_pdf_aktiv() -> bool:
    """KI-Extraktion für unstrukturierte PDFs nur mit hinterlegtem API-Key."""
    return bool(ANTHROPIC_API_KEY)


def admin_aktiv() -> bool:
    return bool(ADMIN_USER and ADMIN_PASSWORT)


def pool_schreibbar() -> bool:
    """Im Desktop-Paket liegt der Pool schreibgeschützt im Programm.

    Das Übernehmen geprüfter Neuaufnahmen bleibt deshalb dem Server
    vorbehalten – sonst wären die Änderungen beim Schließen wieder weg.
    """
    return not gebuendelt()
