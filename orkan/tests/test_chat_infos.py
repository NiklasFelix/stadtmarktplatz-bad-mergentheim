"""Das Sammeln der Chat-Dateien (`werkzeuge/chat_infos_packen.py`).

Der Zweck des Werkzeugs ist, dass im Ordner nie eine alte Fassung liegenbleibt
und dass veraltete Zahlen in den Anweisungen auffallen. Beides wird hier
festgehalten – samt der Fehlalarme, die die erste Fassung produziert hat.
"""
from __future__ import annotations

import pytest

from werkzeuge import chat_infos_packen as packen

KENNZAHLEN = {"zeilen": 94_610, "spalten": 28, "mit_bild": 78_426}


@pytest.fixture
def projekt(tmp_path, monkeypatch):
    """Ein Miniaturprojekt mit denselben Dateinamen wie das echte."""
    monkeypatch.setattr(packen, "PROJEKT", tmp_path)
    monkeypatch.setattr(packen, "ZIEL", tmp_path / "EXPORT CHAT INFOS")
    monkeypatch.setattr(packen, "POOL", tmp_path / "daten" / "pool.csv")
    for name, _ in packen.IMMER + packen.AUFGABEN:
        pfad = tmp_path / name
        pfad.parent.mkdir(parents=True, exist_ok=True)
        pfad.write_text(f"Inhalt von {pfad.name}", encoding="utf-8")
    return tmp_path


# ---------------------------------------------------------------------------
# Sammeln
# ---------------------------------------------------------------------------
def test_alle_dateien_landen_im_ordner(projekt):
    assert packen.main() == 0

    ziel = projekt / "EXPORT CHAT INFOS"
    erwartet = {p.rsplit("/", 1)[-1] for p, _ in packen.IMMER + packen.AUFGABEN}
    assert erwartet <= {d.name for d in ziel.iterdir()}
    assert (ziel / "LIESMICH.md").exists()


def test_die_skripte_liegen_ohne_unterordner_daneben(projekt):
    """Im Ordner soll alles flach liegen, damit man es einfach anhängen kann."""
    packen.main()
    ziel = projekt / "EXPORT CHAT INFOS"
    assert (ziel / "pool_pruefen.py").exists()
    assert not (ziel / "werkzeuge").exists()


def test_alte_dateien_bleiben_nicht_liegen(projekt):
    """Sonst schickt man irgendwann eine Anweisung mit, die es nicht mehr gibt."""
    ziel = projekt / "EXPORT CHAT INFOS"
    ziel.mkdir()
    (ziel / "PROMPT-VON-GESTERN.md").write_text("veraltet", encoding="utf-8")

    packen.main()
    assert not (ziel / "PROMPT-VON-GESTERN.md").exists()


def test_fehlende_quelldatei_ist_ein_fehler(projekt):
    (projekt / packen.AUFGABEN[0][0]).unlink()
    assert packen.main() == 1


# ---------------------------------------------------------------------------
# Aktualitätsprüfung
# ---------------------------------------------------------------------------
def _anforderungen(projekt, text):
    (projekt / "EXPORT-ANFORDERUNGEN.md").write_text(text, encoding="utf-8")


def test_passende_zahlen_ergeben_keine_warnung(projekt):
    _anforderungen(projekt, "Der Pool hat 94.610 Zeilen, davon 78.426 mit Bildname.")
    assert packen.pruefe_aktualitaet(KENNZAHLEN) == []


def test_veraltete_zeilenzahl_faellt_auf(projekt):
    _anforderungen(projekt, "Der Pool hat 93.117 Zeilen.")
    warnungen = packen.pruefe_aktualitaet(KENNZAHLEN)
    assert any("93.117" in w for w in warnungen)


def test_veraltete_bildzahl_faellt_auf(projekt):
    _anforderungen(projekt, "Davon 76.907 Artikel mit Bildname.")
    warnungen = packen.pruefe_aktualitaet(KENNZAHLEN)
    assert any("76.907" in w for w in warnungen)


# --- Fehlalarme aus der Praxis ---------------------------------------------
def test_andere_kennzahlen_loesen_keinen_fehlalarm_aus(projekt):
    """`Quellen` enthält 71.550 Semikolons – das ist keine Artikelzahl."""
    _anforderungen(projekt, "| Spalte | betroffene Werte |\n| `Quellen` | 71.550 |")
    assert packen.pruefe_aktualitaet(KENNZAHLEN) == []


def test_kleine_zahlen_werden_nicht_geprueft(projekt):
    """Stückzahlen wie 6.149 Artikelnummern mit Leerzeichen sind keine Poolgröße."""
    _anforderungen(projekt, "6.149 Artikel haben ein Leerzeichen in der Nummer.")
    assert packen.pruefe_aktualitaet(KENNZAHLEN) == []


def test_auch_die_aufgabendateien_werden_geprueft(projekt):
    (projekt / "PROMPT-BILDNAMEN-ERGAENZEN.md").write_text(
        "Ausgangslage: 86.693 Artikel.", encoding="utf-8"
    )
    warnungen = packen.pruefe_aktualitaet(KENNZAHLEN)
    assert any("PROMPT-BILDNAMEN" in w for w in warnungen)


def test_veraltete_angabe_macht_den_lauf_rot(projekt, monkeypatch):
    """Der Ordner wird trotzdem gefüllt – aber der Rückgabewert warnt."""
    monkeypatch.setattr(packen, "pool_kennzahlen", lambda: KENNZAHLEN)
    _anforderungen(projekt, "Der Pool hat 93.117 Zeilen.")

    assert packen.main() == 1
    assert (projekt / "EXPORT CHAT INFOS" / "EXPORT-ANFORDERUNGEN.md").exists()


def test_ohne_pool_laeuft_das_sammeln_trotzdem(projekt):
    """Auf einem Rechner ohne Pooldatei soll das Werkzeug nicht scheitern."""
    assert packen.pool_kennzahlen() is None
    assert packen.main() == 0
