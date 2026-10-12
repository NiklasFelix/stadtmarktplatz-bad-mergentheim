"""Matching-Kern: Normalisierung, Ungültige-Nummern-Regel, MinMax, Lagerort."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app import matching, pool as pool_modul


# ---------------------------------------------------------------------------
# Referenzimplementierung – wörtlich aus referenz/abgleich_referenz.py.
# Dient als Vergleichsmaßstab für die beschleunigte Fassung in app/matching.py.
# ---------------------------------------------------------------------------
def _tokens_referenz(s):
    import re

    return set(re.sub(r"[^a-z0-9äöüß ]", " ", str(s).lower()).split())


def minmax_referenz(pool_df, bez1, gruppe):
    kand = pool_df[pool_df["LagerMin"].notna()]
    if pd.notna(gruppe):
        g = kand[kand["BezArtikelGruppe"].str.strip().str.lower() == str(gruppe).strip().lower()]
        if len(g) >= 3:
            kand = g
    tok = _tokens_referenz(bez1)
    if tok:
        sim = kand["BezArtikel1"].fillna("").map(lambda b: len(tok & _tokens_referenz(b)))
        top = kand[sim >= max(1, sim.max() - 0)] if sim.max() > 0 else kand
        if len(top) >= 3:
            kand = top
    mn = pd.to_numeric(kand["LagerMin"], errors="coerce").median()
    mx = pd.to_numeric(kand["LagerMax"], errors="coerce").median()
    if pd.isna(mn):
        mn, mx = 1, 2
    return int(round(mn)), int(round(max(mx, mn + 1) if pd.notna(mx) else mn * 2))


# ---------------------------------------------------------------------------
# Normalisierung
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "eingabe,erwartet",
    [
        ("cus18h", "CUS18H"),
        ("  CUS18H  ", "CUS18H"),
        ("CuS18h\n", "CUS18H"),
        ("01.001.90", "01.001.90"),
        (387500140020, "387500140020"),
    ],
)
def test_normalisierung(eingabe, erwartet):
    assert matching.normiere_artikelnummer(eingabe) == erwartet


def test_normalisierung_findet_artikel_unabhaengig_von_schreibweise(pool):
    for schreibweise in ("cus18h", " CUS18H ", "CuS18H"):
        treffer = pool.finde(matching.normiere_artikelnummer(schreibweise))
        assert treffer is not None
        assert treffer["BezArtikel1"] == "Kupfer Pressfitting Bogen 90"


# ---------------------------------------------------------------------------
# Ungültige Nummern
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nummer", ["1", "12", "123", "1234", "0001"])
def test_rein_numerisch_bis_vier_stellen_ist_ungueltig(nummer):
    assert matching.ist_ungueltige_nummer(nummer)


@pytest.mark.parametrize(
    "nummer", ["12345", "CUS18H", "01.001.90", "A123", "123-4", "387500140020"]
)
def test_gueltige_nummern(nummer):
    assert not matching.ist_ungueltige_nummer(nummer)


def test_ungueltige_nummern_kommen_nicht_in_importdatei(pool):
    liste = pd.DataFrame({"Artikelnummer": ["CUS18H", "123", "9999"]})
    ergebnis = matching.abgleich(liste, pool)

    assert ergebnis.anzahl_ungueltig == 2
    assert ergebnis.anzahl_gefunden == 1
    assert len(ergebnis.importzeilen) == 1
    assert ergebnis.neuaufnahmen == []
    ungueltig = [z for z in ergebnis.reportzeilen if z["Status"] == matching.STATUS_UNGUELTIG]
    assert {z["Artikelnummer"] for z in ungueltig} == {"123", "9999"}


# ---------------------------------------------------------------------------
# MinMax
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "bez1,gruppe",
    [
        ("Kupfer Pressfitting Bogen 90°", "Pressfittings"),
        ("Gewindestange M10", None),
        ("Gewindestange M10", "Befestigungstechnik"),
        ("Völlig unbekannter Artikel", "Gibt-es-nicht"),
        (np.nan, np.nan),
        ("", ""),
        ("Tauchsägeblatt", "Befestigungstechnik"),
    ],
)
def test_minmax_stimmt_mit_referenz_ueberein(pool, bez1, gruppe):
    assert matching.minmax_von_aehnlichen(pool, bez1, gruppe) == minmax_referenz(
        pool.df, bez1, gruppe
    )


def test_minmax_stimmt_auch_auf_echtem_pool_mit_referenz_ueberein(echter_pool_pfad):
    """Stichprobe gegen den Produktivpool – die Beschleunigung darf nichts ändern."""
    echt = pool_modul.laden(echter_pool_pfad)
    stichprobe = echt.df.sample(n=40, random_state=7)

    for _, zeile in stichprobe.iterrows():
        bez1, gruppe = zeile["BezArtikel1"], zeile["BezArtikelGruppe"]
        assert matching.minmax_von_aehnlichen(echt, bez1, gruppe) == minmax_referenz(
            echt.df, bez1, gruppe
        ), f"Abweichung bei {zeile['ArtikelNrLieferant']}"


def test_minmax_nutzt_gleiche_gruppe(pool):
    """Vier Pressfittings: Min 4/6/2/3 → Median 3,5 → 4; Max 8/12/5/9 → Median 8,5 → 8."""
    mn, mx = matching.minmax_von_aehnlichen(pool, "Irgendein Pressfitting", "Pressfittings")
    assert (mn, mx) == (4, 8)


def test_minmax_ohne_treffer_liefert_plausible_werte(pool):
    mn, mx = matching.minmax_von_aehnlichen(pool, "xyz", "xyz")
    assert mn >= 1 and mx > mn


def test_artikel_ohne_lagermin_ist_kein_minmax_kandidat(pool):
    assert "OHNE-MIN" not in set(pool.df.iloc[pool.kandidaten]["ArtikelNrLieferant"])


# ---------------------------------------------------------------------------
# Lagerort
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "bez,gruppe,erwartet",
    [
        ("Kupfer Pressfitting Bogen", "Pressfittings", "Kupferpress"),
        ("Kupfer Lötfitting", "Fittings", "Kupferloet"),
        ("Edelstahl Pressfitting", "Fittings", "Edelstahlpress"),
        ("C-Stahl Pressfitting", "Fittings", "C-Stahl-Press"),
        ("Mepla Rohr", "Rohre", "Mepla"),
        ("Mapress Bogen", "Fittings", "Mapress"),
        ("Gewindestange M10", "Befestigung", "Gewindestangen"),
        ("Irgendwas", "Sanitaer", "Sanitaer"),
        ("Irgendwas", np.nan, "Allgemein"),
    ],
)
def test_lagerort_regeln(bez, gruppe, erwartet):
    assert matching.lagerort(bez, gruppe) == erwartet


def test_lagerort_wird_auf_24_zeichen_gekuerzt():
    lang = "Eine sehr lange Artikelgruppenbezeichnung"
    assert len(matching.lagerort("neutral", lang)) == 24


# ---------------------------------------------------------------------------
# Abgleich insgesamt
# ---------------------------------------------------------------------------
def test_mehrere_lieferanten_werden_ausgewiesen(pool):
    ergebnis = matching.abgleich(pd.DataFrame({"Artikelnummer": ["GWS-M10"]}), pool)
    assert ergebnis.reportzeilen[0]["Status"] == matching.STATUS_LIEFERANT_WAEHLEN


def test_lieferant_aus_kundenliste_hat_vorrang(pool):
    liste = pd.DataFrame({"Artikelnummer": ["GWS-M10"], "Lieferant": ["Mein Großhandel"]})
    ergebnis = matching.abgleich(liste, pool)
    assert ergebnis.importzeilen[0]["Lieferant"] == "Mein Großhandel"


def test_ohne_lieferant_wird_erster_pool_lieferant_genommen(pool):
    ergebnis = matching.abgleich(pd.DataFrame({"Artikelnummer": ["GWS-M10"]}), pool)
    assert ergebnis.importzeilen[0]["Lieferant"] == "Adolf Würth"


def test_neuaufnahme_wird_befuellt_und_hat_kein_bild(pool):
    liste = pd.DataFrame([{
        "Artikelnummer": "NEU-KPF-2815",
        "Bezeichnung1": "Kupfer Pressfitting Bogen 90°",
        "Bezeichnung2": "28mm",
        "Artikelgruppe": "Pressfittings",
        "Lieferant": "Gerhard Sprügel GmbH",
    }])
    ergebnis = matching.abgleich(liste, pool, kunde="Testbetrieb")

    assert ergebnis.anzahl_neu == 1
    neu = ergebnis.neuaufnahmen[0]
    assert neu["ArtikelNrLieferant"] == "NEU-KPF-2815"
    assert neu["Lagerort"] == "Kupferpress"
    assert neu["Lager"] == "Standard Lager"
    assert neu["Quellen"] == "Kundenliste-Testbetrieb"
    assert neu["NeuAusKundenliste"] == "Ja"
    assert pd.isna(neu["Bild"])
    assert int(neu["LagerMin"]) >= 1 and int(neu["LagerMax"]) > int(neu["LagerMin"])

    zeile = ergebnis.reportzeilen[0]
    assert zeile["Status"] == matching.STATUS_NEU
    assert zeile["Bild_vorhanden"] == "Nein"
    assert ergebnis.importzeilen[0]["Artikelbild"] is np.nan or pd.isna(
        ergebnis.importzeilen[0]["Artikelbild"]
    )


def test_neuaufnahme_erscheint_in_der_importdatei(pool):
    liste = pd.DataFrame({"Artikelnummer": ["CUS18H", "NEU-XY-1"]})
    ergebnis = matching.abgleich(liste, pool)
    nummern = [z["Artikelnummer des Lieferanten"] for z in ergebnis.importzeilen]
    assert nummern == ["CUS18H", "NEU-XY-1"]


def test_trefferquote(pool):
    liste = pd.DataFrame({"Artikelnummer": ["CUS18H", "CUS22H", "CUS28H", "NEU-1"]})
    ergebnis = matching.abgleich(liste, pool)
    assert ergebnis.anzahl_gesamt == 4
    assert ergebnis.trefferquote == 0.75


def test_leere_artikelnummern_werden_uebergangen(pool):
    liste = pd.DataFrame({"Artikelnummer": ["CUS18H", None, "", "   "]})
    ergebnis = matching.abgleich(liste, pool)
    assert ergebnis.anzahl_gesamt == 1


def test_fehlende_spalte_meldet_klaren_fehler(pool):
    with pytest.raises(ValueError, match="Artikelnummer"):
        matching.abgleich(pd.DataFrame({"Nummer": ["CUS18H"]}), pool)
