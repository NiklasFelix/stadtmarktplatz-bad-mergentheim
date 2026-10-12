"""Die eine Wahrheit darüber, welches Feld wohin gehört.

Drei Dinge hingen bisher lose nebeneinander und liefen deshalb auseinander:
die im Bestätigungsschritt zuordenbaren Felder, die 39 Spalten der Importdatei
und die Spalten des Datenpools. Hier stehen sie in **einer** Tabelle.

Wer ein Feld ergänzt, trägt es genau hier ein – Spaltenerkennung, Anreicherung
und Herkunftsnachweis im Report ziehen sich alles Weitere daraus.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Feld:
    """Ein Feld, das der Kunde zuordnen kann."""

    #: interner Name, zugleich Schlüssel in der Zuordnung
    name: str
    #: Spalte in der 39-Spalten-Importdatei
    importspalte: str
    #: Spalte im Datenpool; ``None`` bedeutet: der Pool kennt das Feld nicht
    poolspalte: str | None
    #: Beschriftung in der Oberfläche
    beschriftung: str
    #: Kopfzeilen-Schreibweisen in Kundendateien, beste zuerst
    synonyme: tuple[str, ...] = ()
    #: Bezeichnungsfelder werden von Füllwerten wie "0" bereinigt
    ist_text: bool = False


#: Reihenfolge = Reihenfolge in der Oberfläche.
FELDER: tuple[Feld, ...] = (
    Feld(
        "Artikelnummer", "Artikelnummer des Lieferanten", "ArtikelNrLieferant",
        "Artikelnummer (nötig)",
        ("artikelnummerdeslieferanten", "lieferantenartikelnummer",
         "lieferantartikelnummer", "artikelnummer", "artikelnr", "artikelnummern",
         "artnr", "artnummer", "artikelcode", "bestellnummer", "bestellnr",
         "sachnummer", "materialnummer", "idhnummer", "idh", "artikel"),
    ),
    Feld(
        "Lieferant", "Lieferant", "Lieferanten_alle", "Lieferant",
        ("lieferant", "lieferantenname", "lieferantname", "grosshaendler",
         "haendler", "bezugsquelle", "supplier"),
        ist_text=True,
    ),
    Feld(
        "Bezeichnung1", "Bezeichnung1", "BezArtikel1", "Bezeichnung",
        ("bezeichnung1", "artikelbezeichnung", "bezeichnung", "benennung",
         "artikeltext", "produktbezeichnung", "beschreibung", "artikelname",
         "bezeichnunga", "text", "name"),
        ist_text=True,
    ),
    Feld(
        "Bezeichnung2", "Bezeichnung2", "BezArtikel2", "Bezeichnung Zeile 2",
        ("bezeichnung2", "zusatzbezeichnung", "bezeichnungb", "zusatz"),
        ist_text=True,
    ),
    Feld(
        "Bezeichnung3", "Bezeichnung3", "BezArtikel3", "Bezeichnung Zeile 3",
        ("bezeichnung3", "bezeichnungc"),
        ist_text=True,
    ),
    Feld(
        "BezeichnungLang", "Bezeichnung lang", "BezArtikelLang", "Lange Bezeichnung",
        ("bezeichnunglang", "langbezeichnung", "langtext", "beschreibunglang"),
        ist_text=True,
    ),
    Feld(
        "Verwendungszweck", "Verwendungszweck", None, "Verwendungszweck",
        ("verwendungszweck", "zweck", "einsatzgebiet", "verwendung"),
        ist_text=True,
    ),
    Feld(
        "Artikelgruppe", "Artikelgruppe", "BezArtikelGruppe", "Artikelgruppe",
        ("artikelgruppe", "warengruppe", "produktgruppe", "materialgruppe",
         "kategorie", "gruppe"),
        ist_text=True,
    ),
    Feld(
        "Artikeluntergruppe", "Artikeluntergruppe", None, "Artikeluntergruppe",
        ("artikeluntergruppe", "untergruppe", "unterkategorie"),
        ist_text=True,
    ),
    Feld(
        "Lagerort", "Lagerort", "Lagerort", "Lagerort",
        ("lagerort", "lagerbereich"),
        ist_text=True,
    ),
    Feld(
        "Lagerortbezeichnung", "Lagerortbezeichnung", "BezLagerort",
        "Lagerortbezeichnung",
        ("lagerortbezeichnung", "bezlagerort", "lagerortname"),
        ist_text=True,
    ),
    Feld(
        "Lagerplatz", "Lagerplatz", None, "Lagerplatz",
        ("lagerplatz", "regalplatz", "stellplatz", "fach", "regal"),
        ist_text=True,
    ),
    Feld(
        "LagerMin", "Lager Min", "LagerMin", "Lager Min",
        ("lagermin", "mindestbestand", "meldebestand", "minbestand",
         "mindestmenge", "min"),
    ),
    Feld(
        "LagerMax", "Lager Max", "LagerMax", "Lager Max",
        ("lagermax", "hoechstbestand", "maxbestand", "sollbestand",
         "maximalbestand", "max"),
    ),
    Feld(
        "Einheit", "Lagereinheit", "LagerEinheit", "Einheit",
        ("lagereinheit", "mengeneinheit", "basiseinheit", "einheit", "me"),
    ),
    Feld(
        "MengeneinheitVPE", "Mengeneinheit(VPE)", "VpeEinheit",
        "Einheit der Verpackung",
        ("mengeneinheitvpe", "vpeeinheit", "verpackungseinheit", "vpe"),
    ),
    Feld(
        "Menge", "Menge(VPE)", "MengeProVPE", "Menge je Verpackung",
        ("mengeprovpe", "mengevpe", "menge", "anzahl", "stueckzahl",
         "stckzahl", "stk", "inhalt"),
    ),
    # Abweichende Bestelleinheit: Gelagert wird im Gebinde (1 Pack), bestellt
    # werden kann trotzdem stückweise (100 Stück). LagerMin/LagerMax zählen
    # weiterhin in Lagereinheiten.
    Feld(
        "AbwBestellmenge", "Abw. Bestellmenge", "AbwBestellmenge",
        "Abweichende Bestellmenge",
        ("abwbestellmenge", "abweichendebestellmenge", "bestellmenge",
         "abwbestellung", "bestellmengeabweichend"),
    ),
    Feld(
        "AbwBestelleinheit", "Abw. Bestelleinheit", "AbwBestelleinheit",
        "Abweichende Bestelleinheit",
        ("abwbestelleinheit", "abweichendebestelleinheit", "bestelleinheit",
         "abwbestelleinh", "bestelleinheitabweichend"),
    ),
    Feld(
        "Werksnummer", "Werksnummer", "Werksnummer", "Werksnummer",
        ("werksnummer", "werksnr"),
    ),
    Feld(
        "Herstellernummer", "Herstellernummer", "HerstellerNr", "Herstellernummer",
        ("herstellerartikelnummer", "herstellernummer", "herstellernr",
         "hstnr", "mpn"),
    ),
    Feld(
        "EAN", "EAN", "EAN", "EAN / Barcode",
        ("eannummer", "ean13", "ean", "gtin", "barcode", "strichcode"),
    ),
    Feld(
        "Matchcode", "Matchcode", "KurzBezeichnung", "Matchcode / Kurzbezeichnung",
        ("matchcode", "kurzbezeichnung", "kurztext", "suchbegriff", "kurzname"),
        ist_text=True,
    ),
    Feld(
        "HTNCode", "HTN-Code", None, "HTN-Code",
        ("htncode", "htn"),
    ),
    Feld(
        "Artikelbild", "Artikelbild", "Bild", "Bildname",
        ("artikelbild", "bildname", "bilddatei", "bild", "foto", "abbildung"),
        # Ein "0" im Bildnamen ist ein Füllwert, kein Dateiname.
        ist_text=True,
    ),
)

#: Schlüsselfeld – ohne dieses geht gar nichts.
FELD_ARTIKELNUMMER = "Artikelnummer"

NACH_NAME: dict[str, Feld] = {f.name: f for f in FELDER}
ZIELFELDER: list[str] = [f.name for f in FELDER]

#: Felder, in denen Füllwerte wie "0" oder "-" entfernt werden.
TEXTFELDER: set[str] = {f.name for f in FELDER if f.ist_text}

#: Felder, die der Pool anreichern kann.
AUS_POOL: list[Feld] = [f for f in FELDER if f.poolspalte]


def feld(name: str) -> Feld:
    return NACH_NAME[name]


def beschriftungen() -> dict[str, str]:
    return {f.name: f.beschriftung for f in FELDER}
