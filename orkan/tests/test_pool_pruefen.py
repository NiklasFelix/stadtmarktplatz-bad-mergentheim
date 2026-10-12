"""Der Prüfer für neue Datenpool-Exporte (`werkzeuge/pool_pruefen.py`)."""
from __future__ import annotations

import pandas as pd
import pytest

from werkzeuge.pool_pruefen import SPALTEN, pruefe, sieht_nach_text_aus


def _schreibe(pfad, zeilen: list[dict], *, bom: bool = True, spalten=None):
    spalten = spalten or SPALTEN
    voll = []
    for z in zeilen:
        eintrag = dict.fromkeys(SPALTEN, "")
        eintrag.update(z)
        voll.append(eintrag)
    df = pd.DataFrame(voll, columns=spalten) if voll else pd.DataFrame(columns=spalten)
    df.to_csv(pfad, sep=";", index=False, encoding="utf-8-sig" if bom else "utf-8")
    return pfad


def _gut(**felder):
    # KurzBezeichnung ist die Satzart und steht im Pool durchgaengig auf ST.
    return {"ArtikelNrLieferant": "CUS18H", "BezArtikel1": "Kupferbogen 90",
            "KurzBezeichnung": "ST", "LagerMin": "2", "LagerMax": "8", **felder}


def test_saubere_datei_hat_weder_fehler_noch_warnungen(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [
        _gut(), _gut(ArtikelNrLieferant="GWS-M10", BezArtikel1="Gewindestange"),
    ])
    assert pruefe(pfad) == ([], [])


def test_fehlendes_bom_ist_ein_fehler(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut()], bom=False)
    fehler, _ = pruefe(pfad)
    assert any("BOM" in f for f in fehler)


def test_vertauschte_spalten_sind_ein_fehler(tmp_path):
    gedreht = [SPALTEN[1], SPALTEN[0]] + SPALTEN[2:]
    pfad = _schreibe(tmp_path / "pool.csv", [_gut()], spalten=gedreht)
    fehler, _ = pruefe(pfad)
    assert any("Reihenfolge" in f for f in fehler)


def test_fehlende_spalte_ist_ein_fehler(tmp_path):
    pfad = tmp_path / "pool.csv"
    pd.DataFrame(columns=SPALTEN[:-1]).to_csv(pfad, sep=";", index=False, encoding="utf-8-sig")
    fehler, _ = pruefe(pfad)
    assert any("fehlend" in f for f in fehler)


def test_doppelte_artikelnummer_ist_ein_fehler(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(), _gut()])
    fehler, _ = pruefe(pfad)
    assert any("doppelte" in f for f in fehler)


def test_leere_artikelnummer_ist_ein_fehler(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(ArtikelNrLieferant="")])
    fehler, _ = pruefe(pfad)
    assert any("ohne Artikelnummer" in f for f in fehler)


@pytest.mark.parametrize("spalte", ["ArtikelNrLieferant", "EAN", "Werksnummer", "HerstellerNr"])
def test_wissenschaftliche_notation_ist_ein_fehler(tmp_path, spalte):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(**{spalte: "4,04478E+12"})])
    fehler, _ = pruefe(pfad)
    assert any("wissenschaftlicher Notation" in f and spalte in f for f in fehler)


def test_fehlende_datei_wird_gemeldet(tmp_path):
    fehler, _ = pruefe(tmp_path / "gibtesnicht.csv")
    assert any("nicht gefunden" in f for f in fehler)


# ---------------------------------------------------------------------------
# Warnungen
# ---------------------------------------------------------------------------
def test_bezeichnung_im_nummernfeld_wird_gewarnt(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(ArtikelNrLieferant="Andreas Funkner")])
    _, warnungen = pruefe(pfad)
    assert any("nach Bezeichnung oder Name" in w for w in warnungen)


def test_fehlende_bezeichnung_wird_gewarnt(tmp_path):
    pfad = tmp_path / "pool.csv"
    zeile = dict.fromkeys(SPALTEN, "")
    zeile.update({"ArtikelNrLieferant": "CUS18H", "LagerMin": "2", "LagerMax": "8"})
    pd.DataFrame([zeile], columns=SPALTEN).to_csv(
        pfad, sep=";", index=False, encoding="utf-8-sig", na_rep=""
    )
    _, warnungen = pruefe(pfad)
    assert any("ohne Bezeichnung" in w for w in warnungen)


def test_min_groesser_max_wird_gewarnt(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(LagerMin="9", LagerMax="3")])
    _, warnungen = pruefe(pfad)
    assert any("größer als LagerMax" in w for w in warnungen)


# ---------------------------------------------------------------------------
# Echte Pool-Schreibweisen dürfen nicht anschlagen
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "nummer", ["72 011 23", "QBSHNS", "01.001.90", "0000100951687", "CUS18H", "ALLARDSP"]
)
def test_gueltige_pool_nummern_gelten_nicht_als_text(nummer):
    assert not sieht_nach_text_aus(nummer)


@pytest.mark.parametrize("nummer", ["Michael Seiler", "Andreas Funkner", "Abflussreiniger Buzil"])
def test_namen_werden_als_text_erkannt(nummer):
    assert sieht_nach_text_aus(nummer)


def test_pruefer_akzeptiert_den_echten_pool(echter_pool_pfad):
    """Der produktiv eingesetzte Pool darf keine harten Fehler auslösen."""
    fehler, _ = pruefe(echter_pool_pfad)
    assert fehler == [], fehler


# ---------------------------------------------------------------------------
# Bildnamen (Grundlage für das ZIP zur Importdatei)
# ---------------------------------------------------------------------------
def test_bildname_mit_pfadanteil_ist_ein_fehler(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(Bild=r"bilder\rohr.jpg")])
    fehler, _ = pruefe(pfad)
    assert any("Pfadanteil" in f for f in fehler)


def test_bildname_ohne_endung_wird_gewarnt(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(Bild="FSOFTFP")])
    _, warnungen = pruefe(pfad)
    assert any("ohne Dateiendung" in w for w in warnungen)


def test_bildname_auf_pdf_wird_gewarnt(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(Bild="datenblatt.pdf")])
    _, warnungen = pruefe(pfad)
    assert any("kein Bildformat" in w for w in warnungen)


@pytest.mark.parametrize(
    "name",
    ["Panzerschlauch.jpeg", "441095050125_Detail.jpg", "Winkel 45 RG.jpeg",
     "schutzschlauchVlies.png", "bild.WEBP"],
)
def test_echte_bildnamen_werden_nicht_beanstandet(tmp_path, name):
    """Auch Leerzeichen und Großschreibung der Endung sind in Ordnung."""
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(Bild=name)])
    fehler, warnungen = pruefe(pfad)
    assert fehler == []
    assert not any("Bildname" in w for w in warnungen)


def test_leere_bildspalte_ist_kein_problem(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(), _gut(ArtikelNrLieferant="GWS-M10")])
    fehler, warnungen = pruefe(pfad)
    assert fehler == []
    assert not any("Bildname" in w for w in warnungen)


# ---------------------------------------------------------------------------
# Abgleich gegen den Bildpool (--bildordner)
# ---------------------------------------------------------------------------
def _bildordner(tmp_path, *namen, unterordner: str = ""):
    ordner = tmp_path / "bilder"
    ziel = ordner / unterordner if unterordner else ordner
    ziel.mkdir(parents=True, exist_ok=True)
    for name in namen:
        (ziel / name).write_bytes(b"\xff\xd8\xff")
    return ordner


def test_ohne_bildordner_wird_nicht_gegen_dateien_geprueft(tmp_path):
    """Der Standardaufruf bleibt unverändert."""
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(Bild="gibtesnicht.jpg")])
    assert pruefe(pfad) == ([], [])


def test_vorhandene_bilder_ergeben_nur_eine_kennzahl(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(Bild="rohr.jpg")])
    ordner = _bildordner(tmp_path, "rohr.jpg")

    fehler, warnungen = pruefe(pfad, ordner)
    assert fehler == []
    assert any("Bildpool" in w for w in warnungen)
    assert not any("liegen" in w for w in warnungen)


def test_bilder_werden_auch_in_unterordnern_gefunden(tmp_path):
    """Genau wie app/bildpool.py sucht der Prüfer rekursiv."""
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(Bild="rohr.jpg")])
    ordner = _bildordner(tmp_path, "rohr.jpg", unterordner="Sanitaer/2024")

    fehler, warnungen = pruefe(pfad, ordner)
    assert fehler == []
    assert not any("liegen" in w for w in warnungen)


def test_grossschreibung_spielt_keine_rolle(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(Bild="ROHR.JPG")])
    ordner = _bildordner(tmp_path, "rohr.jpg")

    fehler, warnungen = pruefe(pfad, ordner)
    assert not any("liegen" in w for w in warnungen)


def test_einzelne_fehlende_bilder_sind_nur_eine_warnung(tmp_path):
    """Lücken im Bildbestand sind Alltag und dürfen den Export nicht blockieren."""
    zeilen = [_gut(ArtikelNrLieferant=f"A{i}", Bild=f"da{i}.jpg") for i in range(9)]
    zeilen.append(_gut(ArtikelNrLieferant="X", Bild="fehlt.jpg"))
    pfad = _schreibe(tmp_path / "pool.csv", zeilen)
    ordner = _bildordner(tmp_path, *[f"da{i}.jpg" for i in range(9)])

    fehler, warnungen = pruefe(pfad, ordner)
    assert fehler == []
    assert any("'fehlt.jpg'" in w for w in warnungen)


def test_mehrheitlich_fehlende_bilder_sind_ein_fehler(tmp_path):
    """Dann stimmt die Zuordnung nicht – so darf der Pool nicht übernommen werden."""
    zeilen = [_gut(ArtikelNrLieferant=f"A{i}", Bild=f"fehlt{i}.jpg") for i in range(9)]
    zeilen.append(_gut(ArtikelNrLieferant="X", Bild="da.jpg"))
    pfad = _schreibe(tmp_path / "pool.csv", zeilen)
    ordner = _bildordner(tmp_path, "da.jpg")

    fehler, _ = pruefe(pfad, ordner)
    assert any("nicht im Bildordner" in f for f in fehler)


def test_falscher_bildordner_wird_gemeldet(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(Bild="rohr.jpg")])
    fehler, _ = pruefe(pfad, tmp_path / "gibtesnicht")
    assert any("Bildordner nicht gefunden" in f for f in fehler)


def test_mehrfach_verwendete_bilder_zaehlen_einmal(tmp_path):
    """Ein Bild für mehrere Artikel ist der Normalfall im Pool."""
    pfad = _schreibe(tmp_path / "pool.csv", [
        _gut(ArtikelNrLieferant="A1", Bild="familie.jpg"),
        _gut(ArtikelNrLieferant="A2", Bild="familie.jpg"),
        _gut(ArtikelNrLieferant="A3", Bild="familie.jpg"),
    ])
    ordner = _bildordner(tmp_path, "familie.jpg")

    fehler, warnungen = pruefe(pfad, ordner)
    assert fehler == []
    assert any("1 verschiedene Namen" in w for w in warnungen)


# ---------------------------------------------------------------------------
# Veralteter Export erkennen
# ---------------------------------------------------------------------------
# Aus der Praxis: Der Datenpool-Chat lieferte einen Export, der auf einer alten
# Kopie aufsetzte und alle Korrekturen zurückgedreht hätte – 1.991 Platzhalter,
# 1.850 Nullen, 685 Einheiten-Codes. Auffallen musste das beim Prüfen.
def test_platzhalterwort_ist_ein_fehler(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(LagerEinheit="leer")])
    fehler, _ = pruefe(pfad)
    assert any("Platzhalterwort" in f for f in fehler)


def test_einheiten_als_kuerzel_sind_ein_fehler(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(LagerEinheit="PCE")])
    fehler, _ = pruefe(pfad)
    assert any("ausgeschrieben" in f for f in fehler)


def test_menge_pro_vpe_null_ist_ein_fehler(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(MengeProVPE="0")])
    fehler, _ = pruefe(pfad)
    assert any("MengeProVPE = 0" in f for f in fehler)


def test_andere_satzart_als_st_ist_ein_fehler(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(KurzBezeichnung="SF")])
    fehler, _ = pruefe(pfad)
    assert any("Satzart" in f and "'SF'" in f for f in fehler)


def test_halb_gefuellte_bestellangabe_ist_ein_fehler(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(AbwBestelleinheit="Stück")])
    fehler, _ = pruefe(pfad)
    assert any("Bestellfelder" in f for f in fehler)


def test_vollstaendige_bestellangabe_geht_durch(tmp_path):
    pfad = _schreibe(tmp_path / "pool.csv", [
        _gut(MengeProVPE="100", AbwBestellmenge="100", AbwBestelleinheit="Stück"),
    ])
    assert pruefe(pfad) == ([], [])


def test_unbekannt_ist_nur_ein_hinweis(tmp_path):
    """„Unbekannt“ könnte bewusst so gemeint sein – das darf nicht blockieren."""
    pfad = _schreibe(tmp_path / "pool.csv", [_gut(Lagerort="Unbekannt")])
    fehler, warnungen = pruefe(pfad)
    assert fehler == []
    assert any("Unbekannt" in w for w in warnungen)
