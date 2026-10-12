"""Die Oberfläche selbst – Dinge, die im Betrieb schiefgegangen sind.

Das JavaScript läuft im Browser und wird von pytest nicht ausgeführt. Diese
Tests halten deshalb nur die wenigen Stellen fest, an denen ein Rückfall einen
Anwender direkt trifft.
"""
from __future__ import annotations

import re

import pytest

from app import main


@pytest.fixture(scope="module")
def seite() -> str:
    return (main.STATIC / "index.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def skript(seite: str) -> str:
    return seite.split("<script>", 1)[1].split("</script>", 1)[0]


# ---------------------------------------------------------------------------
# Der Fehler vom Kollegen: "cannot read properties of null (reading 'felder')"
# ---------------------------------------------------------------------------
# Ursache: Wird eine Datei hereingezogen, bevor /api/status geantwortet hat,
# greift zeigeZuordnung() auf zustand.status.felder zu – und das ist dann null.
def test_der_upload_wartet_auf_den_status(skript: str):
    koerper = _funktion(skript, "async function hochladen")
    assert "statusAbwarten" in koerper, (
        "hochladen() muss auf den Status warten, sonst kennt zeigeZuordnung() "
        "die Felder nicht"
    )
    # Das Warten muss vor dem Anzeigen der Zuordnung stehen.
    assert koerper.index("statusAbwarten") < koerper.index("zeigeZuordnung")


def test_es_gibt_einen_zweiten_versuch_fuer_den_status(skript: str):
    koerper = _funktion(skript, "async function statusAbwarten")
    assert koerper.count("statusBereit") >= 2 and "statusHolen()" in koerper


def test_ohne_status_kommt_eine_deutsche_meldung_statt_eines_absturzes(skript: str):
    koerper = _funktion(skript, "async function hochladen")
    assert "noch nicht bereit" in koerper
    assert "F5" in koerper, "Der Anwender braucht einen konkreten nächsten Schritt"


def test_der_status_verschluckt_seinen_fehler_nicht(skript: str):
    """Sonst sucht man den Grund vergeblich."""
    koerper = _funktion(skript, "async function statusHolen")
    assert "console.error" in koerper


# ---------------------------------------------------------------------------
# Grundsätzliches
# ---------------------------------------------------------------------------
def test_nichts_wird_aus_dem_internet_nachgeladen(seite: str):
    """Der Server hat nicht zwingend Internet, die .exe ohnehin nicht."""
    verweise = re.findall(r'(?:src|href)\s*=\s*"(https?:)?//[^"]+"', seite)
    assert verweise == []


def test_die_oberflaeche_kennt_hellen_und_dunklen_modus(seite: str):
    assert "prefers-color-scheme: dark" in seite
    assert "prefers-reduced-motion" in seite


def _funktion(skript: str, kopf: str) -> str:
    """Rumpf einer Funktion herausschneiden (bis zur schließenden Klammer)."""
    start = skript.index(kopf)
    tiefe, i = 0, skript.index("{", start)
    for pos in range(i, len(skript)):
        if skript[pos] == "{":
            tiefe += 1
        elif skript[pos] == "}":
            tiefe -= 1
            if tiefe == 0:
                return skript[start:pos + 1]
    raise AssertionError(f"Funktion {kopf!r} nicht geschlossen")
