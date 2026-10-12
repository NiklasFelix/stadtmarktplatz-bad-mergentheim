"""Einlesen der Kundendatei und tolerante Spaltenerkennung.

Kunden liefern ihre Listen in ganz unterschiedlicher Form. Dieses Modul liest
Excel, CSV und PDF ein, rät die Bedeutung der Spalten und bereitet die Werte so
auf, dass der Abgleich damit arbeiten kann.
"""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from . import felder

# ---------------------------------------------------------------------------
# Zielfelder und ihre Header-Varianten – alles aus der zentralen Feldtabelle
# ---------------------------------------------------------------------------
FELD_ARTIKELNUMMER = felder.FELD_ARTIKELNUMMER

SYNONYME: dict[str, list[str]] = {f.name: list(f.synonyme) for f in felder.FELDER}

#: Felder, die der Kunde zuordnen kann.
ZIELFELDER = list(felder.ZIELFELDER)

_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def normiere_header(wert) -> str:
    """Header auf Vergleichsform bringen: klein, ohne Umlaute und Sonderzeichen."""
    text = str(wert or "").strip().lower().translate(_UMLAUTE)
    return re.sub(r"[^a-z0-9]", "", text)


# ---------------------------------------------------------------------------
# Werte bereinigen
# ---------------------------------------------------------------------------
#: z. B. "4,04478E+12" – aus Excel verunglückte lange Nummern, nicht mehr rettbar
WISSENSCHAFTLICH = re.compile(r"^\s*[+-]?\d+(?:[.,]\d+)?\s*[eE]\s*[+-]?\d+\s*$")
#: Füllwerte, die in Bezeichnungsfeldern nichts zu suchen haben
FUELLWERTE = {"0", "0.0", "0,0", "-", "--", "n/a", "na", "null", "nan", "none", "keine"}


def zelle_zu_text(wert) -> str:
    """Zellwert in sauberen Text wandeln; 12345.0 wird wieder zu 12345."""
    if wert is None:
        return ""
    if isinstance(wert, float):
        if pd.isna(wert):
            return ""
        if wert.is_integer():
            return str(int(wert))
        return str(wert)
    if isinstance(wert, int):
        return str(wert)
    return str(wert).strip()


def ist_wissenschaftlich(wert) -> bool:
    return bool(WISSENSCHAFTLICH.match(str(wert or "")))


def bereinige_bezeichnung(wert) -> str:
    """Wissenschaftliche Notation und Füllwerte aus Kundeneingaben entfernen."""
    text = zelle_zu_text(wert)
    if not text:
        return ""
    if ist_wissenschaftlich(text):
        return ""
    if text.strip().lower() in FUELLWERTE:
        return ""
    return text


def bereinige_nummer(wert) -> str:
    """Für Nummernfelder: kaputte wissenschaftliche Notation verwerfen."""
    text = zelle_zu_text(wert)
    if not text or ist_wissenschaftlich(text):
        return ""
    if text.strip().lower() in {"nan", "none", "null"}:
        return ""
    return text


#: Felder, in denen Füllwerte wie "0" entfernt werden (aus der Feldtabelle).
_BEZEICHNUNGSFELDER = felder.TEXTFELDER


# ---------------------------------------------------------------------------
# Dateien einlesen
# ---------------------------------------------------------------------------
@dataclass
class Rohtabelle:
    """Was aus der hochgeladenen Datei herausgelesen wurde."""

    df: pd.DataFrame
    quelle: str
    hinweis: str = ""
    #: Bei PDFs: wurde die KI-Extraktion genutzt?
    ki_genutzt: bool = False


def _kodierung_finden(pfad: Path) -> str:
    for kodierung in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with pfad.open("r", encoding=kodierung) as f:
                f.read(200_000)
            return kodierung
        except (UnicodeDecodeError, LookupError):
            continue
    return "latin-1"


def _trennzeichen_finden(probe: str) -> str:
    """Trennzeichen erkennen: Semikolon, Komma oder Tabulator."""
    kandidaten = [";", ",", "\t", "|"]
    try:
        return csv.Sniffer().sniff(probe, delimiters="".join(kandidaten)).delimiter
    except csv.Error:
        pass
    zeilen = [z for z in probe.splitlines() if z.strip()][:20]
    if not zeilen:
        return ";"
    bester, beste_punkte = ";", -1.0
    for zeichen in kandidaten:
        anzahlen = [z.count(zeichen) for z in zeilen]
        if not anzahlen or max(anzahlen) == 0:
            continue
        # Gleichmäßig verteilte Trenner sprechen für die richtige Wahl.
        gleichmaessig = sum(1 for a in anzahlen if a == anzahlen[0]) / len(anzahlen)
        punkte = anzahlen[0] * gleichmaessig
        if punkte > beste_punkte:
            bester, beste_punkte = zeichen, punkte
    return bester


def lies_csv(pfad: Path) -> Rohtabelle:
    kodierung = _kodierung_finden(pfad)
    with pfad.open("r", encoding=kodierung, errors="replace") as f:
        probe = f.read(64_000)
    trenner = _trennzeichen_finden(probe)
    df = pd.read_csv(
        pfad, sep=trenner, dtype=object, encoding=kodierung,
        engine="python", on_bad_lines="skip", keep_default_na=False,
    )
    name = {";": "Semikolon", ",": "Komma", "\t": "Tabulator", "|": "Strich"}.get(trenner, trenner)
    return Rohtabelle(df=df, quelle="CSV", hinweis=f"Trennzeichen erkannt: {name}")


def lies_excel(pfad: Path) -> Rohtabelle:
    motor = "xlrd" if pfad.suffix.lower() == ".xls" else "openpyxl"
    try:
        blaetter = pd.read_excel(pfad, dtype=object, sheet_name=None, engine=motor)
    except Exception:
        blaetter = pd.read_excel(pfad, dtype=object, sheet_name=None)
    if not blaetter:
        raise ValueError("Die Excel-Datei enthält keine Tabellenblätter.")
    # Das Blatt mit den meisten Zeilen gewinnt.
    name, df = max(blaetter.items(), key=lambda kv: len(kv[1]))
    hinweis = f"Tabellenblatt „{name}“ verwendet" if len(blaetter) > 1 else ""
    return Rohtabelle(df=df, quelle="Excel", hinweis=hinweis)


def lies_datei(pfad: Path) -> Rohtabelle:
    """Hochgeladene Datei einlesen – Format wird an der Endung erkannt."""
    endung = pfad.suffix.lower()
    if endung in (".xlsx", ".xlsm", ".xls"):
        roh = lies_excel(pfad)
    elif endung == ".csv":
        roh = lies_csv(pfad)
    elif endung == ".pdf":
        from .pdf_extract import lies_pdf  # spät importiert, pdfplumber ist schwer

        roh = lies_pdf(pfad)
    elif endung in (".txt", ".tsv"):
        roh = lies_csv(pfad)
    else:
        raise ValueError(
            f"Dateiformat „{endung or 'unbekannt'}“ wird nicht unterstützt. "
            "Bitte laden Sie eine Excel-, CSV- oder PDF-Datei hoch."
        )

    roh.df = roh.df.dropna(axis=1, how="all")
    roh.df.columns = [str(s).strip() for s in roh.df.columns]
    return roh


# ---------------------------------------------------------------------------
# Spaltenerkennung
# ---------------------------------------------------------------------------
_NUMMERNARTIG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-/ ]{2,}$")


def _nummern_punkte(werte: pd.Series) -> float:
    """Wie sehr sieht diese Spalte nach Artikelnummern aus? 0 bis 1."""
    texte = [zelle_zu_text(w) for w in werte.head(500)]
    gefuellt = [t for t in texte if t]
    if not gefuellt:
        return 0.0
    passend = sum(
        1 for t in gefuellt
        if _NUMMERNARTIG.match(t) and any(z.isdigit() for z in t) and len(t) >= 3
    )
    anteil = passend / len(gefuellt)
    # Artikelnummern sind überwiegend eindeutig – das trennt sie von Gruppen.
    eindeutigkeit = len(set(gefuellt)) / len(gefuellt)
    return anteil * (0.5 + 0.5 * eindeutigkeit)


@dataclass
class Spaltenzuordnung:
    """Welche Spalte der Kundendatei welches Feld liefert."""

    zuordnung: dict[str, str] = field(default_factory=dict)
    #: Felder, bei denen die Erkennung unsicher war
    unsicher: list[str] = field(default_factory=list)
    verfuegbare_spalten: list[str] = field(default_factory=list)

    @property
    def artikelnummer_spalte(self) -> str | None:
        return self.zuordnung.get(FELD_ARTIKELNUMMER)


def erkenne_spalten(df: pd.DataFrame) -> Spaltenzuordnung:
    """Spalten heuristisch den Zielfeldern zuordnen."""
    spalten = [str(s) for s in df.columns]
    normiert = {s: normiere_header(s) for s in spalten}

    # Alle plausiblen Paare bewerten und dann bestbewertet zuweisen.
    bewertungen: list[tuple[float, str, str]] = []
    for feld, varianten in SYNONYME.items():
        for rang, variante in enumerate(varianten):
            for spalte in spalten:
                kopf = normiert[spalte]
                if not kopf:
                    continue
                if kopf == variante:
                    punkte = 1000 - rang
                elif len(variante) >= 4 and variante in kopf:
                    # Längere Übereinstimmung = spezifischer = besser.
                    punkte = 500 - rang + len(variante)
                else:
                    continue
                bewertungen.append((punkte, feld, spalte))

    bewertungen.sort(key=lambda b: -b[0])
    zuordnung: dict[str, str] = {}
    belegt: set[str] = set()
    for _, feld, spalte in bewertungen:
        if feld in zuordnung or spalte in belegt:
            continue
        zuordnung[feld] = spalte
        belegt.add(spalte)

    unsicher: list[str] = []

    # Fallback: keine erkannte Artikelnummer-Spalte -> die nummernartigste nehmen.
    if FELD_ARTIKELNUMMER not in zuordnung:
        offen = [s for s in spalten if s not in belegt] or spalten
        punkte = {s: _nummern_punkte(df[s]) for s in offen}
        bester = max(punkte, key=punkte.get) if punkte else None
        if bester is not None and punkte[bester] > 0.3:
            zuordnung[FELD_ARTIKELNUMMER] = bester
            belegt.add(bester)
            unsicher.append(FELD_ARTIKELNUMMER)
        elif spalten:
            zuordnung[FELD_ARTIKELNUMMER] = spalten[0]
            belegt.add(spalten[0])
            unsicher.append(FELD_ARTIKELNUMMER)

    return Spaltenzuordnung(
        zuordnung=zuordnung, unsicher=unsicher, verfuegbare_spalten=spalten
    )


def baue_kundenliste(df: pd.DataFrame, zuordnung: dict[str, str]) -> pd.DataFrame:
    """Kundendatei anhand der Zuordnung in die Arbeitsform bringen und bereinigen."""
    if FELD_ARTIKELNUMMER not in zuordnung:
        raise ValueError("Es wurde keine Spalte mit Artikelnummern festgelegt.")

    daten: dict[str, list] = {}
    for feld, spalte in zuordnung.items():
        if not spalte or spalte not in df.columns:
            continue
        roh = df[spalte]
        if feld in _BEZEICHNUNGSFELDER:
            werte = [bereinige_bezeichnung(w) for w in roh]
        else:
            # Nummern- und Mengenfelder: nur kaputte Notation verwerfen,
            # eine "0" kann hier ein gültiger Wert sein (z. B. Lager Min).
            werte = [bereinige_nummer(w) for w in roh]
        daten[feld] = werte

    ergebnis = pd.DataFrame(daten)
    # Leere Zeichenketten zu NaN, damit "kein Wert" überall gleich aussieht.
    ergebnis = ergebnis.replace({"": None})
    ergebnis = ergebnis[ergebnis[FELD_ARTIKELNUMMER].notna()].reset_index(drop=True)
    return ergebnis
