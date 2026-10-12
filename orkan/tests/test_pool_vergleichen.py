"""Der Vergleich zweier Pool-Stände (`werkzeuge/pool_vergleichen.py`).

Die Frage, die dieses Werkzeug beantwortet: Ist beim neuen Export etwas
verlorengegangen? Ein Fehlalarm ist hier fast so schädlich wie ein übersehener
Verlust – meldet es ständig Verluste, sieht bald niemand mehr hin.
"""
from __future__ import annotations

import pandas as pd

from werkzeuge.pool_pruefen import SPALTEN
from werkzeuge.pool_vergleichen import vergleiche


def _schreibe(pfad, zeilen: list[dict]):
    voll = []
    for z in zeilen:
        eintrag = dict.fromkeys(SPALTEN, "")
        eintrag.update(z)
        voll.append(eintrag)
    pd.DataFrame(voll, columns=SPALTEN).to_csv(
        pfad, sep=";", index=False, encoding="utf-8-sig"
    )
    return pfad


def _art(nr="CUS18H", **felder):
    return {"ArtikelNrLieferant": nr, "BezArtikel1": "Kupferbogen 90", **felder}


# ---------------------------------------------------------------------------
# Der Normalfall: der Pool wächst
# ---------------------------------------------------------------------------
def test_reines_wachstum_ist_kein_verlust(tmp_path):
    alt = _schreibe(tmp_path / "a.csv", [_art("A1")])
    neu = _schreibe(tmp_path / "n.csv", [_art("A1"), _art("A2"), _art("A3")])

    verluste, _, bericht = vergleiche(alt, neu)
    assert verluste == []
    assert any("neu: 2" in z for z in bericht)


def test_neu_gefuellte_felder_sind_kein_verlust(tmp_path):
    alt = _schreibe(tmp_path / "a.csv", [_art("A1", Bild="")])
    neu = _schreibe(tmp_path / "n.csv", [_art("A1", Bild="rohr.jpg")])

    verluste, _, _ = vergleiche(alt, neu)
    assert verluste == []


# ---------------------------------------------------------------------------
# Echte Verluste
# ---------------------------------------------------------------------------
def test_verschwundener_artikel_ist_ein_verlust(tmp_path):
    alt = _schreibe(tmp_path / "a.csv", [_art("A1"), _art("A2")])
    neu = _schreibe(tmp_path / "n.csv", [_art("A1")])

    verluste, _, _ = vergleiche(alt, neu)
    assert any("ersatzlos verschwunden" in v and "'A2'" in v for v in verluste)


def test_geleertes_feld_ist_ein_verlust(tmp_path):
    alt = _schreibe(tmp_path / "a.csv", [_art("A1", Bild="rohr.jpg")])
    neu = _schreibe(tmp_path / "n.csv", [_art("A1", Bild="")])

    verluste, _, _ = vergleiche(alt, neu)
    assert any("Bild" in v and "keinen mehr" in v for v in verluste)


def test_fehlende_spalte_ist_ein_verlust(tmp_path):
    alt = _schreibe(tmp_path / "a.csv", [_art("A1")])
    df = pd.DataFrame([dict.fromkeys(SPALTEN[:-1], "") | {"ArtikelNrLieferant": "A1"}],
                      columns=SPALTEN[:-1])
    neu = tmp_path / "n.csv"
    df.to_csv(neu, sep=";", index=False, encoding="utf-8-sig")

    verluste, _, _ = vergleiche(alt, neu)
    assert any("Spalten fehlen" in v for v in verluste)


# ---------------------------------------------------------------------------
# Kein Fehlalarm: die beiden Fälle, die im echten Export vorkamen
# ---------------------------------------------------------------------------
def test_nur_andere_schreibweise_ist_kein_verlust(tmp_path):
    """Dubletten-Zusammenführung: 130S25 und 130s25 werden zu einem Artikel."""
    alt = _schreibe(tmp_path / "a.csv", [_art("130S25"), _art("130s25")])
    neu = _schreibe(tmp_path / "n.csv", [_art("130S25")])

    verluste, _, bericht = vergleiche(alt, neu)
    assert verluste == []
    assert any("zusammengeführt" in z for z in bericht)


def test_in_ein_nachbarfeld_gewanderter_text_ist_kein_verlust(tmp_path):
    """Die 25-Zeichen-Grenze verteilt Bezeichnungen zwischen den Feldern um."""
    alt = _schreibe(tmp_path / "a.csv", [
        _art("VD331/005", BezArtikel1="Rotguss Verschraubung",
             BezArtikel2="Nr. 3331 DN20", BezArtikel3="DN20"),
    ])
    neu = _schreibe(tmp_path / "n.csv", [
        _art("VD331/005", BezArtikel1="Verschraubung mit AG und",
             BezArtikel2="IG Nr. 3331 DN20 DN20", BezArtikel3=""),
    ])

    verluste, hinweise, _ = vergleiche(alt, neu)
    assert verluste == []
    assert any("gewandert" in h for h in hinweise)


def test_wirklich_verschwundene_bezeichnung_bleibt_ein_verlust(tmp_path):
    """Die Umverteilungs-Ausnahme darf echten Verlust nicht verdecken."""
    alt = _schreibe(tmp_path / "a.csv", [
        _art("A1", BezArtikel1="Rotguss", BezArtikel2="", BezArtikel3="Sonderbau"),
    ])
    neu = _schreibe(tmp_path / "n.csv", [
        _art("A1", BezArtikel1="Rotguss", BezArtikel2="", BezArtikel3=""),
    ])

    verluste, _, _ = vergleiche(alt, neu)
    assert any("BezArtikel3" in v for v in verluste)


# ---------------------------------------------------------------------------
# Hinweise
# ---------------------------------------------------------------------------
def test_ersetzter_wert_wird_gemeldet_aber_nicht_als_verlust(tmp_path):
    alt = _schreibe(tmp_path / "a.csv", [_art("A1", Bild="alt.jpg")])
    neu = _schreibe(tmp_path / "n.csv", [_art("A1", Bild="neu.jpg")])

    verluste, hinweise, _ = vergleiche(alt, neu)
    assert verluste == []
    assert any("ersetzt" in h and "Bild" in h for h in hinweise)


def test_bildabdeckung_steht_im_bericht(tmp_path):
    alt = _schreibe(tmp_path / "a.csv", [_art("A1"), _art("A2")])
    neu = _schreibe(tmp_path / "n.csv", [_art("A1", Bild="x.jpg"), _art("A2", Bild="y.jpg")])

    _, _, bericht = vergleiche(alt, neu)
    assert any("Bilder" in z and "100 %" in z for z in bericht)


def test_fehlende_datei_wird_gemeldet(tmp_path):
    alt = _schreibe(tmp_path / "a.csv", [_art("A1")])
    verluste, _, _ = vergleiche(alt, tmp_path / "gibtesnicht.csv")
    assert any("nicht gefunden" in v for v in verluste)
