"""Artikellisten aus PDF-Dateien lesen.

Zwei Wege:

1. ``pdfplumber`` für PDFs mit echten Tabellen – schnell, kostenlos, offline.
2. Als Rückfallebene die Anthropic-API für Scans und unstrukturierte PDFs.
   Ohne ``ANTHROPIC_API_KEY`` ist dieser Weg sauber deaktiviert.
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import pandas as pd

from . import config
from .parsing import Rohtabelle, zelle_zu_text

#: So viele plausible Zeilen muss eine Tabelle liefern, damit wir ihr trauen.
MINDESTZEILEN = 2

_NUMMER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-/]{2,}$")


def _sieht_nach_artikelnummer_aus(text: str) -> bool:
    return bool(_NUMMER.match(text.strip())) and any(z.isdigit() for z in text)


# ---------------------------------------------------------------------------
# Weg 1: echte Tabellen
# ---------------------------------------------------------------------------
def _tabellen_aus_pdf(pfad: Path) -> pd.DataFrame | None:
    import pdfplumber

    beste: pd.DataFrame | None = None
    with pdfplumber.open(pfad) as pdf:
        gesammelt: list[pd.DataFrame] = []
        kopf: list[str] | None = None
        for seite in pdf.pages:
            for tabelle in seite.extract_tables() or []:
                zeilen = [
                    [zelle_zu_text(z) for z in zeile]
                    for zeile in tabelle
                    if any(zelle_zu_text(z) for z in zeile)
                ]
                if len(zeilen) < 2:
                    continue
                # Erste Zeile als Kopfzeile deuten; Folgeseiten erben ihn.
                erste = zeilen[0]
                hat_kopf = not any(_sieht_nach_artikelnummer_aus(z) for z in erste if z)
                if hat_kopf:
                    kopf = [z or f"Spalte {i + 1}" for i, z in enumerate(erste)]
                    daten = zeilen[1:]
                elif kopf and len(kopf) == len(erste):
                    daten = zeilen
                else:
                    kopf = [f"Spalte {i + 1}" for i in range(len(erste))]
                    daten = zeilen
                if not daten:
                    continue
                breite = len(kopf)
                daten = [(z + [""] * breite)[:breite] for z in daten]
                gesammelt.append(pd.DataFrame(daten, columns=kopf))

    if gesammelt:
        # Nur Blöcke mit gleichem Kopf zusammenführen.
        nach_kopf: dict[tuple, list[pd.DataFrame]] = {}
        for teil in gesammelt:
            nach_kopf.setdefault(tuple(teil.columns), []).append(teil)
        for teile in nach_kopf.values():
            zusammen = pd.concat(teile, ignore_index=True)
            if beste is None or len(zusammen) > len(beste):
                beste = zusammen

    if beste is not None and len(beste) >= MINDESTZEILEN:
        return beste
    return None


# ---------------------------------------------------------------------------
# Weg 2: Anthropic-API für Scans und Fließtext-PDFs
# ---------------------------------------------------------------------------
_SCHEMA = {
    "type": "object",
    "properties": {
        "artikel": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "Artikelnummer": {"type": "string"},
                    "Bezeichnung1": {"type": "string"},
                    "Lieferant": {"type": "string"},
                    "Menge": {"type": "string"},
                    "EAN": {"type": "string"},
                },
                "required": [
                    "Artikelnummer", "Bezeichnung1", "Lieferant", "Menge", "EAN",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["artikel"],
    "additionalProperties": False,
}

_ANWEISUNG = """Diese PDF-Datei ist die Artikelliste eines Handwerksbetriebs (Sanitär,
Heizung, Klima). Lies alle Artikelzeilen aus.

Regeln:
- Übernimm die Werte exakt so, wie sie im Dokument stehen. Erfinde nichts.
- Wenn ein Feld im Dokument fehlt, gib einen leeren String zurück.
- Artikelnummern sind Nummern des Lieferanten (z. B. "CUS18H", "01.001.90",
  "387500140020"). Übernimm sie zeichengenau, ohne führende Nullen zu entfernen.
- Reine Überschriften, Seitenzahlen, Summenzeilen und Adressblöcke sind keine Artikel.
- Gib jede Artikelzeile genau einmal zurück."""


def _extrahiere_mit_ki(pfad: Path) -> pd.DataFrame:
    import anthropic

    daten = base64.standard_b64encode(pfad.read_bytes()).decode("utf-8")
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    with client.messages.stream(
        model=config.ANTHROPIC_MODELL,
        max_tokens=32000,
        output_config={"format": {"type": "json_schema", "schema": _SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": daten,
                        },
                    },
                    {"type": "text", "text": _ANWEISUNG},
                ],
            }
        ],
    ) as stream:
        antwort = stream.get_final_message()

    if antwort.stop_reason == "refusal":
        raise ValueError(
            "Die automatische PDF-Auswertung wurde abgelehnt. "
            "Bitte laden Sie die Liste als Excel- oder CSV-Datei hoch."
        )

    text = next((b.text for b in antwort.content if b.type == "text"), "")
    if not text:
        raise ValueError("Aus der PDF-Datei konnten keine Artikel gelesen werden.")

    artikel = json.loads(text).get("artikel", [])
    if not artikel:
        raise ValueError(
            "In der PDF-Datei wurden keine Artikelzeilen gefunden. "
            "Bitte prüfen Sie die Datei oder laden Sie eine Excel-Liste hoch."
        )
    return pd.DataFrame(artikel)


# ---------------------------------------------------------------------------
def lies_pdf(pfad: Path) -> Rohtabelle:
    """Artikelliste aus einem PDF holen – erst Tabellen, dann KI."""
    fehler_tabelle = ""
    try:
        tabelle = _tabellen_aus_pdf(pfad)
    except Exception as e:  # defekte PDFs sollen den KI-Weg nicht blockieren
        tabelle, fehler_tabelle = None, str(e)

    if tabelle is not None:
        return Rohtabelle(
            df=tabelle, quelle="PDF", hinweis="Tabelle direkt aus dem PDF gelesen"
        )

    if not config.ki_pdf_aktiv():
        raise ValueError(
            "In dieser PDF-Datei wurde keine auslesbare Tabelle gefunden"
            + (f" ({fehler_tabelle})" if fehler_tabelle else "")
            + ". Bitte laden Sie die Liste als Excel- oder CSV-Datei hoch."
        )

    return Rohtabelle(
        df=_extrahiere_mit_ki(pfad),
        quelle="PDF",
        hinweis="PDF automatisch ausgewertet – bitte die Zuordnung kurz prüfen",
        ki_genutzt=True,
    )
