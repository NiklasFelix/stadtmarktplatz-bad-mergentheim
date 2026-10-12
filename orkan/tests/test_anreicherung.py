"""Vorrang der Kundenangaben, Anreicherung aus dem Pool, Herkunftsnachweis.

Früher kam bei einem gefundenen Artikel **alles** aus dem Pool – einzige
Ausnahme war der Lieferant. Kundenangaben wurden stillschweigend verworfen.
Diese Tests halten das neue Verhalten fest.
"""
from __future__ import annotations

import io

import pandas as pd
import pytest

from app import felder, matching, parsing

# Der Mini-Testpool kennt CUS28H mit Bild und gepflegter Bezeichnung.
ARTIKEL = "CUS28H"
POOL_BEZ = "Kupfer Pressfitting Muffe"
POOL_BILD = "cus28h.jpg"


def _kunde(**felder_):
    return pd.DataFrame([{"Artikelnummer": ARTIKEL, **felder_}])


def _zeile(pool, anreicherung=None, **felder_):
    ergebnis = matching.abgleich(_kunde(**felder_), pool, anreicherung=anreicherung)
    return ergebnis.importzeilen[0]


# ---------------------------------------------------------------------------
# Standard: Kundenangaben gewinnen
# ---------------------------------------------------------------------------
def test_ohne_kundenangabe_reichert_der_pool_an(pool):
    z = _zeile(pool)
    assert z["Bezeichnung1"] == POOL_BEZ
    assert z["Artikelbild"] == POOL_BILD


def test_kundenangabe_schlaegt_den_pool(pool):
    z = _zeile(pool, Bezeichnung1="Meine eigene Bezeichnung")
    assert z["Bezeichnung1"] == "Meine eigene Bezeichnung"
    # Felder ohne Kundenangabe kommen weiterhin aus dem Pool
    assert z["Artikelbild"] == POOL_BILD


def test_bildname_vom_kunden_gewinnt(pool):
    """Der ausdrücklich gewünschte Fall: eigener Bildname statt Pool-Bild."""
    z = _zeile(pool, Artikelbild="mein_bild.jpg")
    assert z["Artikelbild"] == "mein_bild.jpg"


@pytest.mark.parametrize(
    "feldname,importspalte,wert",
    [
        ("Bezeichnung1", "Bezeichnung1", "Eigene Bezeichnung"),
        ("Artikelbild", "Artikelbild", "eigenes.jpg"),
        ("Einheit", "Lagereinheit", "Karton"),
        ("Menge", "Menge(VPE)", "50"),
        ("Artikelgruppe", "Artikelgruppe", "Meine Gruppe"),
        ("Lagerort", "Lagerort", "Regal 7"),
        ("LagerMin", "Lager Min", "12"),
        ("LagerMax", "Lager Max", "40"),
        ("Matchcode", "Matchcode", "KURZ"),
        ("Verwendungszweck", "Verwendungszweck", "Sanitaerinstallation"),
        ("Lagerplatz", "Lagerplatz", "A-03"),
        ("HTNCode", "HTN-Code", "HTN-9"),
    ],
)
def test_jedes_zugeordnete_feld_hat_vorrang(pool, feldname, importspalte, wert):
    assert _zeile(pool, **{feldname: wert})[importspalte] == wert


def test_menge_landet_endlich_in_der_importdatei(pool):
    """`Menge` wurde früher angeboten, aber nirgends verwendet."""
    assert _zeile(pool, Menge="50")["Menge(VPE)"] == "50"


# ---------------------------------------------------------------------------
# Modus je Feld
# ---------------------------------------------------------------------------
def test_modus_pool_bevorzugen(pool):
    a = matching.Anreicherung(je_feld={"Bezeichnung1": matching.MODUS_POOL})
    z = _zeile(pool, a, Bezeichnung1="Meine Bezeichnung", Artikelbild="mein.jpg")

    assert z["Bezeichnung1"] == POOL_BEZ          # Pool gewinnt
    assert z["Artikelbild"] == "mein.jpg"          # anderes Feld unverändert


def test_modus_pool_nimmt_kundenwert_wenn_der_pool_leer_ist(pool):
    a = matching.Anreicherung(je_feld={"Lagerplatz": matching.MODUS_POOL})
    # "Lagerplatz" kennt der Pool gar nicht – dann gilt die Kundenangabe.
    assert _zeile(pool, a, Lagerplatz="A-03")["Lagerplatz"] == "A-03"


def test_modus_nur_meine_daten(pool):
    a = matching.Anreicherung(je_feld={"Bezeichnung1": matching.MODUS_NUR_KUNDE})
    z = _zeile(pool, a, Bezeichnung1="Nur meine")
    assert z["Bezeichnung1"] == "Nur meine"

    # ohne Kundenangabe bleibt das Feld leer statt aus dem Pool zu kommen
    z2 = _zeile(pool, a)
    assert pd.isna(z2["Bezeichnung1"])
    assert z2["Artikelbild"] == POOL_BILD  # andere Felder unberührt


def test_schalter_aus_holt_nichts_aus_dem_pool(pool):
    a = matching.Anreicherung(aktiv=False)
    z = _zeile(pool, a, Bezeichnung1="Meine Bezeichnung")

    assert z["Bezeichnung1"] == "Meine Bezeichnung"
    assert pd.isna(z["Artikelbild"])
    assert pd.isna(z["Lieferant"])


def test_unbekannter_modus_faellt_auf_den_standard_zurueck(pool):
    a = matching.Anreicherung(je_feld={"Bezeichnung1": "quatsch"})
    assert a.modus("Bezeichnung1") == matching.MODUS_ERGAENZEN


# ---------------------------------------------------------------------------
# Leere Werte und Füllwerte
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("leerwert", ["", "   ", None])
def test_leere_kundenangabe_zaehlt_nicht_als_angabe(pool, leerwert):
    assert _zeile(pool, Bezeichnung1=leerwert)["Bezeichnung1"] == POOL_BEZ


def test_fuellwert_wird_beim_einlesen_entfernt_und_der_pool_ergaenzt():
    """"0" in der Bezeichnung ist keine Angabe – das erledigt schon das Einlesen."""
    roh = pd.DataFrame({"Artikelnummer": [ARTIKEL], "Bezeichnung": ["0"]})
    liste = parsing.baue_kundenliste(
        roh, {"Artikelnummer": "Artikelnummer", "Bezeichnung1": "Bezeichnung"}
    )
    assert pd.isna(liste["Bezeichnung1"].iloc[0])


def test_null_bei_lager_min_bleibt_erhalten():
    """Bei Mengenfeldern ist 0 ein gültiger Wert und kein Füllwert."""
    roh = pd.DataFrame({"Artikelnummer": [ARTIKEL], "Lager Min": ["0"]})
    liste = parsing.baue_kundenliste(
        roh, {"Artikelnummer": "Artikelnummer", "LagerMin": "Lager Min"}
    )
    assert liste["LagerMin"].iloc[0] == "0"


# ---------------------------------------------------------------------------
# Pauschalwerte für MinMax
# ---------------------------------------------------------------------------
def test_pauschale_minmax_wenn_niemand_werte_liefert(pool):
    """Neue Regel aus dem Datenpool-Export: dann gilt 1/2 mit Einheit Stück."""
    a = matching.Anreicherung(aktiv=False)  # kein Pool, keine Kundenangabe
    z = _zeile(pool, a)

    assert (z["Lager Min"], z["Lager Max"]) == (
        matching.PAUSCHAL_MIN, matching.PAUSCHAL_MAX
    )
    assert z["Lagereinheit"] == matching.PAUSCHAL_EINHEIT


def test_vorhandene_werte_werden_nie_durch_pauschale_ersetzt(pool):
    z = _zeile(pool, LagerMin="7", LagerMax="21", Einheit="Karton")
    assert (z["Lager Min"], z["Lager Max"]) == ("7", "21")
    assert z["Lagereinheit"] == "Karton"


def test_neuaufnahme_nimmt_kundenwerte_vor_dem_vorschlag(pool):
    liste = pd.DataFrame([{
        "Artikelnummer": "NEU-ANR-1",
        "Bezeichnung1": "Kupfer Pressfitting Bogen",
        "LagerMin": "9", "LagerMax": "18", "Lagerort": "Mein Regal",
    }])
    ergebnis = matching.abgleich(liste, pool)
    neu = ergebnis.neuaufnahmen[0]

    assert neu["LagerMin"] == "9" and neu["LagerMax"] == "18"
    assert neu["Lagerort"] == "Mein Regal"
    assert pd.isna(neu["Bild"])  # Bild bleibt im Pool immer leer


def test_neuaufnahme_ohne_kundenwerte_nutzt_den_vorschlag(pool):
    liste = pd.DataFrame([{
        "Artikelnummer": "NEU-ANR-2",
        "Bezeichnung1": "Kupfer Pressfitting Bogen",
        "Artikelgruppe": "Pressfittings",
    }])
    neu = matching.abgleich(liste, pool).neuaufnahmen[0]

    assert neu["Lagerort"] == "Kupferpress"          # aus den Lagerort-Regeln
    assert int(neu["LagerMin"]) >= 1                  # aus ähnlichen Artikeln
    assert int(neu["LagerMax"]) > int(neu["LagerMin"])


# ---------------------------------------------------------------------------
# Herkunftsnachweis im Report
# ---------------------------------------------------------------------------
def test_report_weist_die_herkunft_aus(pool):
    ergebnis = matching.abgleich(
        _kunde(Bezeichnung1="Meine Bezeichnung", Artikelbild="mein.jpg"), pool
    )
    zeile = ergebnis.reportzeilen[0]

    assert "Bezeichnung" in zeile["Von Ihnen"]
    assert "Bildname" in zeile["Von Ihnen"]
    assert "Lieferant" in zeile["Aus dem Datenpool"]


def test_herkunft_wird_gezaehlt(pool):
    ergebnis = matching.abgleich(_kunde(Bezeichnung1="Meine Bezeichnung"), pool)
    z = ergebnis.herkunft_zaehler

    assert z[matching.HERKUNFT_KUNDE] >= 2       # Artikelnummer + Bezeichnung
    assert z[matching.HERKUNFT_POOL] >= 1


def test_lange_herkunftsliste_wird_gekuerzt(pool):
    zeile = matching.abgleich(_kunde(), pool).reportzeilen[0]
    text = zeile["Aus dem Datenpool"]
    assert "weitere" in text, text
    assert len(text) < 200


def test_ungueltige_nummer_hat_keine_herkunft(pool):
    zeile = matching.abgleich(pd.DataFrame({"Artikelnummer": ["123"]}), pool).reportzeilen[0]
    assert zeile["Status"] == matching.STATUS_UNGUELTIG
    assert zeile["Von Ihnen"] == "" and zeile["Aus dem Datenpool"] == ""


# ---------------------------------------------------------------------------
# Feldtabelle und Spaltenerkennung
# ---------------------------------------------------------------------------
def test_alle_felder_zeigen_auf_eine_gueltige_importspalte():
    from app import export

    spalten = set(export.vorlagenspalten())
    for f in felder.FELDER:
        assert f.importspalte in spalten, f.name


def test_feste_und_zugeordnete_spalten_decken_die_vorlage_ab():
    from app import export

    belegt = {f.importspalte for f in felder.FELDER} | set(matching.FESTE_SPALTEN)
    assert belegt == set(export.vorlagenspalten())


def test_deutlich_mehr_felder_als_frueher():
    assert len(felder.FELDER) >= 23


@pytest.mark.parametrize(
    "header,feldname",
    [
        ("Bildname", "Artikelbild"),
        ("Bild", "Artikelbild"),
        ("Artikelbild", "Artikelbild"),
        ("Lagerort", "Lagerort"),
        ("Lagerplatz", "Lagerplatz"),
        ("Mindestbestand", "LagerMin"),
        ("Lager Max", "LagerMax"),
        ("Matchcode", "Matchcode"),
        ("Verwendungszweck", "Verwendungszweck"),
        ("Artikeluntergruppe", "Artikeluntergruppe"),
        ("VPE", "MengeneinheitVPE"),
        ("HTN-Code", "HTNCode"),
    ],
)
def test_neue_felder_werden_erkannt(header, feldname):
    df = pd.DataFrame({"Artikelnummer": ["CUS18H"], header: ["x"]})
    assert parsing.erkenne_spalten(df).zuordnung.get(feldname) == header


def test_mengeneinheit_bleibt_die_lagereinheit():
    """"Mengeneinheit" meint die Einheit des Artikels, nicht die der Verpackung."""
    df = pd.DataFrame({"Artikelnummer": ["CUS18H"], "Mengeneinheit": ["Stk"]})
    assert parsing.erkenne_spalten(df).zuordnung.get("Einheit") == "Mengeneinheit"


# ---------------------------------------------------------------------------
# Ausgabeformat bleibt unangetastet
# ---------------------------------------------------------------------------
def test_feste_werte_bleiben_fest(pool):
    z = _zeile(pool, Bezeichnung1="Egal")
    assert z["Satzart"] == "ST"
    assert z["Bestellfähig"] == "True"
    assert z["Bestand"] == "0"
    assert z["Lager/Gebäude"] == "Standard Lager"
    assert pd.isna(z["Artikelnr."]) and pd.isna(z["EK-Preis"])


def test_importdatei_hat_weiterhin_39_spalten(pool):
    from app import export

    ergebnis = matching.abgleich(_kunde(Bezeichnung1="Egal", Artikelbild="x.jpg"), pool)
    tabelle = export.importtabelle_bauen(ergebnis.importzeilen)
    assert list(tabelle.columns) == export.vorlagenspalten()


# ---------------------------------------------------------------------------
# Weg über die Weboberfläche
# ---------------------------------------------------------------------------
def test_einstellung_kommt_ueber_die_schnittstelle_an(klient):
    inhalt = (
        "Artikelnummer;Bezeichnung;Bildname\n"
        f"{ARTIKEL};Meine Bezeichnung;mein_bild.jpg\n"
    )
    hoch = klient.post(
        "/api/upload", files={"datei": ("l.csv", io.BytesIO(inhalt.encode()), "text/csv")}
    )
    assert hoch.status_code == 200
    job = hoch.json()
    assert job["zuordnung"]["Artikelbild"] == "Bildname"

    antwort = klient.post("/api/verarbeiten", json={
        "job_id": job["job_id"], "zuordnung": job["zuordnung"],
        "anreichern": True,
        "anreicherung_je_feld": {"Bezeichnung1": matching.MODUS_POOL},
    })
    assert antwort.status_code == 200, antwort.text
    ergebnis = antwort.json()

    tabelle = pd.read_csv(
        io.BytesIO(klient.get(ergebnis["downloads"]["csv"]).content),
        sep=";", dtype=str, encoding="utf-8-sig",
    )
    assert tabelle["Bezeichnung1"].iloc[0] == POOL_BEZ        # Pool bevorzugt
    assert tabelle["Artikelbild"].iloc[0] == "mein_bild.jpg"  # Kunde gewinnt
    assert ergebnis["zusammenfassung"]["herkunft"][matching.HERKUNFT_KUNDE] >= 1


def test_status_liefert_felder_und_modi(klient):
    daten = klient.get("/api/status").json()
    namen = [f["name"] for f in daten["felder"]]

    assert "Artikelbild" in namen and "Lagerort" in namen
    assert len(namen) >= 23
    assert set(daten["modi"]) == set(matching.MODI)
    assert daten["felder"][0]["beschriftung"]


# ---------------------------------------------------------------------------
# Min und Max können aus verschiedenen Quellen kommen
# ---------------------------------------------------------------------------
def test_min_groesser_max_wird_entschaerft(pool):
    """Kunde liefert nur Min, der Pool nur Max – das kann unsinnig werden."""
    z = _zeile(pool, LagerMin="500", LagerMax="3")
    assert (z["Lager Min"], z["Lager Max"]) == ("500", 501)


def test_min_aus_kundenliste_und_max_aus_dem_pool_bleiben_plausibel(pool):
    z = _zeile(pool, LagerMin="500")
    minimum = int(z["Lager Min"])
    maximum = int(z["Lager Max"])
    assert maximum > minimum


def test_stimmige_werte_bleiben_unangetastet(pool):
    z = _zeile(pool, LagerMin="3", LagerMax="9")
    assert (z["Lager Min"], z["Lager Max"]) == ("3", "9")


def test_beschriftungen_enthalten_kein_komma():
    """Sonst ist die Herkunftsliste im Report nicht mehr lesbar."""
    for f in felder.FELDER:
        assert "," not in f.beschriftung, f.name


# ---------------------------------------------------------------------------
# Abweichende Bestelleinheit (Poolerweiterung auf 28 Spalten)
# ---------------------------------------------------------------------------
# Handwerksbetriebe lagern im Gebinde (1 Pack), bestellen aber in der
# Basiseinheit (100 Stück). Der Pool führt dafür AbwBestellmenge und
# AbwBestelleinheit; beide landen in der Importdatei.
def test_abweichende_bestelleinheit_kommt_aus_dem_pool(pool):
    z = _zeile(pool)
    assert z["Abw. Bestellmenge"] == "100"
    assert z["Abw. Bestelleinheit"] == "Stück"
    # Die Lagerangaben bleiben davon unberührt: gezählt wird in Packs.
    assert z["Lagereinheit"] == "Pack"
    assert z["Lager Min"] == "2"


def test_kundenangabe_schlaegt_die_bestelleinheit_aus_dem_pool(pool):
    z = _zeile(pool, AbwBestellmenge="50", AbwBestelleinheit="Karton")
    assert z["Abw. Bestellmenge"] == "50"
    assert z["Abw. Bestelleinheit"] == "Karton"


def test_ohne_angaben_bleibt_die_bestelleinheit_leer(pool):
    """Leer heißt: keine abweichende Bestelleinheit, es gilt die Lagereinheit."""
    # CUS22H ist im Testpool ein gewöhnlicher Stückartikel ohne Gebinde.
    z = matching.abgleich(
        pd.DataFrame([{"Artikelnummer": "CUS22H"}]), pool
    ).importzeilen[0]
    assert pd.isna(z["Abw. Bestellmenge"])
    assert pd.isna(z["Abw. Bestelleinheit"])


@pytest.mark.parametrize("kopf_menge,kopf_einheit", [
    ("Abw. Bestellmenge", "Abw. Bestelleinheit"),
    ("Abweichende Bestellmenge", "Abweichende Bestelleinheit"),
    ("AbwBestellmenge", "AbwBestelleinheit"),
])
def test_die_neuen_spalten_werden_in_der_kundendatei_erkannt(kopf_menge, kopf_einheit):
    """Bringt der Kunde eigene Spalten mit, sollen sie ohne Handarbeit passen."""
    df = pd.DataFrame(columns=["Artikelnummer", kopf_menge, kopf_einheit])
    erkannt = parsing.erkenne_spalten(df).zuordnung
    assert erkannt.get("AbwBestellmenge") == kopf_menge
    assert erkannt.get("AbwBestelleinheit") == kopf_einheit


def test_beide_felder_sind_zuordenbar(pool):
    namen = {f.name for f in felder.FELDER}
    assert {"AbwBestellmenge", "AbwBestelleinheit"} <= namen


def test_die_importdatei_hat_weiterhin_39_spalten(pool):
    z = _zeile(pool)
    assert len(z) == 39


# ---------------------------------------------------------------------------
# Platzhalterwörter aus dem Pool
# ---------------------------------------------------------------------------
# Im echten Pool steht bei 1.988 Artikeln das Wort „leer" in LagerEinheit statt
# einer leeren Zelle. Ungefiltert erscheint beim Kunden die Einheit „leer".
@pytest.mark.parametrize("platzhalter", ["leer", "Leer", "LEER", "n/a", "keine"])
def test_platzhalterwoerter_aus_dem_pool_gelten_als_leer(pool, platzhalter):
    pool.df.loc[pool.df["ArtikelNrLieferant"] == "CUS22H", "LagerEinheit"] = platzhalter
    z = matching.abgleich(
        pd.DataFrame([{"Artikelnummer": "CUS22H"}]), pool
    ).importzeilen[0]
    assert pd.isna(z["Lagereinheit"])


def test_die_null_bleibt_ein_gueltiger_lagerwert(pool):
    """Zahlen sind keine Platzhalter – LagerMin 0 heißt wirklich null."""
    pool.df.loc[pool.df["ArtikelNrLieferant"] == "CUS22H", "LagerMin"] = "0"
    z = matching.abgleich(
        pd.DataFrame([{"Artikelnummer": "CUS22H"}]), pool
    ).importzeilen[0]
    assert str(z["Lager Min"]) == "0"


def test_kundenangabe_ersetzt_den_platzhalter(pool):
    pool.df.loc[pool.df["ArtikelNrLieferant"] == "CUS22H", "LagerEinheit"] = "leer"
    z = matching.abgleich(
        pd.DataFrame([{"Artikelnummer": "CUS22H", "Einheit": "Pack"}]), pool
    ).importzeilen[0]
    assert z["Lagereinheit"] == "Pack"
