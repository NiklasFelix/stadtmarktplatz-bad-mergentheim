"""Das Übergabepaket (`werkzeuge/uebergabe_packen.py`).

Ein unvollständiges Paket merkt man erst, wenn die übernehmende Person davor
sitzt. Beim ersten Lauf fehlte `desktop.py` – damit ließ sich weder die `.exe`
bauen noch die Testsuite starten.
"""
from __future__ import annotations

import re
from pathlib import Path

from werkzeuge import uebergabe_packen as packen

PROJEKT = Path(__file__).resolve().parent.parent


def _namen() -> set[str]:
    return {n for n, _ in packen.DATEIEN} | {n for n, _ in packen.ORDNER}


def test_alles_was_das_paket_verspricht_gibt_es_auch():
    fehlend = [n for n in _namen() if not (PROJEKT / n).exists()]
    assert fehlend == [], f"Im Projekt nicht vorhanden: {fehlend}"


def test_was_die_bauanleitung_braucht_ist_dabei():
    """Ohne diese Dateien lässt sich die .exe nicht bauen."""
    spec = (PROJEKT / "orkan.spec").read_text(encoding="utf-8")
    gebraucht = set(re.findall(r"'([^']+\.(?:py|csv))'", spec))
    dabei = _namen()
    for pfad in gebraucht:
        assert pfad in dabei or any(pfad.startswith(o + "/") for o in dabei), (
            f"{pfad} wird von orkan.spec gebraucht, fehlt aber im Paket"
        )


def test_die_anwendung_und_ihre_tests_sind_dabei():
    for pflicht in ("app", "tests", "werkzeuge", "referenz", "desktop.py",
                    "requirements.txt", "daten/Datenpool_bereinigt.csv"):
        assert pflicht in _namen(), f"{pflicht} fehlt im Paket"


def test_der_einstieg_ist_benannt():
    """Die übernehmende Person muss wissen, wo sie anfängt."""
    assert "UEBERGABE.md" in _namen()
    assert (PROJEKT / "UEBERGABE.md").exists()
    text = packen.liesmich()
    assert "UEBERGABE.md" in text


def test_kundendaten_gehen_nicht_mit():
    """Die Prüf-Queue enthält Artikelnummern echter Kunden."""
    assert "daten/neuaufnahmen_queue.csv" not in _namen()


def test_der_zweite_pool_bleibt_draussen():
    """Sonst liegt die 24-MB-Datei doppelt im Paket."""
    assert "EXPORT CHAT INFOS" not in _namen()
    assert "chat_infos_packen" in packen.liesmich()
