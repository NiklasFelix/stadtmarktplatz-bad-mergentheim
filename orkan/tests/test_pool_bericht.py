"""Der Überblicksbericht (`werkzeuge/pool_bericht.py`).

Sein Zweck ist Sparsamkeit: eine Frage, ein Aufruf, wenige Zeilen Ausgabe –
statt für jede Auswertung ein neues Wegwerf-Skript.
"""
from __future__ import annotations

import pandas as pd

from werkzeuge import pool_bericht
from werkzeuge.pool_pruefen import SPALTEN


def _schreibe(pfad, zeilen):
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
    return {"ArtikelNrLieferant": nr, "BezArtikel1": "Kupferbogen 90",
            "KurzBezeichnung": "ST", "LagerMin": "2", "LagerMax": "8", **felder}


def test_der_bericht_bleibt_kurz(tmp_path):
    """Er soll in einen Blick passen – und in eine Unterhaltung."""
    pfad = _schreibe(tmp_path / "p.csv", [_art(f"A{i}") for i in range(50)])
    zeilen = pool_bericht.bericht(pool_bericht.lies(pfad), pfad)
    assert len(zeilen) <= 8
    assert all(len(z) < 200 for z in zeilen)


def test_die_kennzahlen_stimmen(tmp_path):
    pfad = _schreibe(tmp_path / "p.csv", [
        _art("A1", Bild="rohr.jpg"),
        _art("72 011 23"),
        _art("0000100951687", Bild="rohr.jpg"),
    ])
    text = "\n".join(pool_bericht.bericht(pool_bericht.lies(pfad), pfad))
    assert "3 Zeilen" in text
    assert "2 von 3" in text and "1 verschiedene" in text
    assert "Leerzeichen 1" in text and "führende Null 1" in text


def test_verstoesse_tauchen_im_bericht_auf(tmp_path):
    pfad = _schreibe(tmp_path / "p.csv", [
        _art("A1", LagerEinheit="PCE"),
        _art("A2", LagerEinheit="leer", MengeProVPE="0"),
        _art("A3", KurzBezeichnung="SF"),
    ])
    text = "\n".join(pool_bericht.bericht(pool_bericht.lies(pfad), pfad))
    assert "Codes 1" in text
    assert "MengeProVPE=0 1" in text
    assert "SF" in text


def test_der_vergleich_nennt_neue_und_verschwundene(tmp_path):
    alt = _schreibe(tmp_path / "a.csv", [_art("A1"), _art("A2")])
    neu = _schreibe(tmp_path / "n.csv", [_art("A1"), _art("A3")])
    text = "\n".join(pool_bericht.vergleich(pool_bericht.lies(alt), pool_bericht.lies(neu)))
    assert "neu 1" in text and "verschwunden 1" in text
    assert "'A3'" in text and "'A2'" in text


def test_der_vergleich_zeigt_geleerte_und_gefuellte_felder(tmp_path):
    alt = _schreibe(tmp_path / "a.csv", [_art("A1", Bild="rohr.jpg"), _art("A2")])
    neu = _schreibe(tmp_path / "n.csv", [_art("A1"), _art("A2", Bild="bogen.jpg")])
    text = "\n".join(pool_bericht.vergleich(pool_bericht.lies(alt), pool_bericht.lies(neu)))
    assert "Bild 2 (-1 +1)" in text


def test_ohne_unterschied_sagt_er_das_auch(tmp_path):
    a = _schreibe(tmp_path / "a.csv", [_art("A1")])
    b = _schreibe(tmp_path / "b.csv", [_art("A1")])
    text = "\n".join(pool_bericht.vergleich(pool_bericht.lies(a), pool_bericht.lies(b)))
    assert "keine Änderung" in text


def test_fehlende_datei_wird_gemeldet(tmp_path, capsys):
    assert pool_bericht.main([str(tmp_path / "gibtesnicht.csv")]) == 1
    assert "nicht gefunden" in capsys.readouterr().out
