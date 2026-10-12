"""Ein Blick auf den Pool – alle Kennzahlen in einem Aufruf.

    python werkzeuge/pool_bericht.py                       # eingesetzter Pool
    python werkzeuge/pool_bericht.py neue_lieferung.csv    # eine andere Datei
    python werkzeuge/pool_bericht.py neu.csv --gegen alt.csv

Ersetzt die Wegwerf-Skripte, mit denen dieselben Fragen sonst jedes Mal neu
beantwortet werden: Wie viele Artikel? Wie viele Bilder? Stimmen die
Schreibweisen? Ist etwas verlorengegangen?

Die Ausgabe ist bewusst knapp – sie soll in einen Blick passen und in einer
Unterhaltung wenig Platz kosten.
"""
from __future__ import annotations

import collections
import os
import sys
from pathlib import Path

import pandas as pd

PROJEKT = Path(__file__).resolve().parent.parent
STANDARD = PROJEKT / "daten" / "Datenpool_bereinigt.csv"

EINHEITENFELDER = ("LagerEinheit", "VpeEinheit", "AbwBestelleinheit")
CODES = {"PCE", "MTR", "PR", "LTR", "SET", "KGM", "MTK", "DZN", "MMT", "CMK", "CMQ", "TNE"}
PLATZHALTER = {"leer", "n/a", "na", "null", "none", "keine", "unbekannt"}


def z(n) -> str:
    return f"{n:,}".replace(",", ".")


def lies(pfad: Path) -> pd.DataFrame:
    return pd.read_csv(pfad, sep=";", dtype=str, encoding="utf-8-sig",
                       keep_default_na=False)


def _steuerzeichen(df: pd.DataFrame) -> int:
    return sum(
        1 for s in df.columns for x in df[s]
        if any(0x7f <= ord(c) < 0xa0 for c in x)
    )


def bericht(df: pd.DataFrame, pfad: Path) -> list[str]:
    nr = df["ArtikelNrLieferant"].str.strip()
    bild = df["Bild"].str.strip()
    mit_bild = bild[bild != ""]
    mn = pd.to_numeric(df["LagerMin"], errors="coerce")
    mx = pd.to_numeric(df["LagerMax"], errors="coerce")

    mit_bom = pfad.open("rb").read(3) == b"\xef\xbb\xbf"
    endungen = collections.Counter(os.path.splitext(x)[1].lower() for x in mit_bild)

    codes = sum(int(df[s].str.strip().isin(CODES).sum())
                for s in EINHEITENFELDER if s in df.columns)
    platz = sum(int(df[s].str.strip().str.lower().isin(PLATZHALTER).sum())
                for s in df.columns)
    menge = df["AbwBestellmenge"].str.strip() != ""
    einheit = df["AbwBestelleinheit"].str.strip() != ""
    satzarten = collections.Counter(df["KurzBezeichnung"].str.strip())

    return [
        f"AUFBAU     {z(len(df))} Zeilen, {len(df.columns)} Spalten, "
        f"BOM {'ja' if mit_bom else 'NEIN'}",
        f"NUMMERN    Dubletten {int(nr.duplicated().sum())} "
        f"(ohne Groß/klein {int(nr.str.upper().duplicated().sum())}) | "
        f"Leerzeichen {z(int(nr.str.contains(' ').sum()))} | "
        f"führende Null {z(int(nr.str.startswith('0').sum()))} | "
        f"ohne Ziffer {z(int((~nr.str.contains(r'[0-9]')).sum()))}",
        f"BILDER     {z(len(mit_bild))} von {z(len(df))} "
        f"({len(mit_bild)/len(df)*100:.0f} %), {z(mit_bild.str.lower().nunique())} verschiedene | "
        + ", ".join(f"{e or '(ohne)'} {z(n)}" for e, n in endungen.most_common(4)),
        f"EINHEITEN  {df['LagerEinheit'].str.strip().replace('', pd.NA).nunique()} verschiedene "
        f"in LagerEinheit | Codes {codes} | Platzhalterwörter {platz}",
        f"MENGEN     MengeProVPE=0 {z(int(df['MengeProVPE'].str.strip().isin(['0','0.0']).sum()))} | "
        f"Bestellangabe halb {int((menge ^ einheit).sum())} | "
        f"Bestellmenge=0 {int(df['AbwBestellmenge'].str.strip().isin(['0','0.0']).sum())}",
        "SATZART    " + ", ".join(f"{a or '(leer)'} {z(n)}" for a, n in satzarten.most_common(4)),
        f"QUALITÄT   ohne Bezeichnung {int((df['BezArtikel1'].str.strip()=='').sum())} | "
        f"Min>Max {int((mn > mx).sum())} | "
        f"Steuerzeichen {_steuerzeichen(df)} | "
        f"Testdaten {z(int((df['VermutlichTestdaten'].str.strip().str.lower()=='ja').sum()))}",
    ]


def vergleich(alt: pd.DataFrame, neu: pd.DataFrame) -> list[str]:
    sa = set(alt["ArtikelNrLieferant"].str.strip())
    sn = set(neu["ArtikelNrLieferant"].str.strip())
    sn_ci = {x.upper() for x in sn}
    weg = sorted(x for x in sa - sn if x.upper() not in sn_ci)
    dazu = sorted(sn - sa)

    zeilen = [
        "",
        f"VERGLEICH  {z(len(sa))} -> {z(len(sn))} Artikel | "
        f"neu {z(len(dazu))} | verschwunden {z(len(weg))}",
    ]
    if dazu:
        zeilen.append("  neu:          " + ", ".join(repr(x) for x in dazu[:5])
                      + (f" … (+{len(dazu)-5})" if len(dazu) > 5 else ""))
    if weg:
        zeilen.append("  verschwunden: " + ", ".join(repr(x) for x in weg[:5])
                      + (f" … (+{len(weg)-5})" if len(weg) > 5 else ""))

    gemeinsam = alt.merge(neu, on="ArtikelNrLieferant", suffixes=("_a", "_n"))
    geaendert = []
    for spalte in alt.columns:
        if spalte == "ArtikelNrLieferant" or f"{spalte}_a" not in gemeinsam.columns:
            continue
        a = gemeinsam[f"{spalte}_a"].str.strip()
        n = gemeinsam[f"{spalte}_n"].str.strip()
        anders = int((a != n).sum())
        if anders:
            geleert = int(((a != "") & (n == "")).sum())
            gefuellt = int(((a == "") & (n != "")).sum())
            geaendert.append(f"{spalte} {z(anders)}"
                             + (f" (-{z(geleert)}" if geleert else "")
                             + (f" +{z(gefuellt)})" if geleert and gefuellt
                                else ")" if geleert
                                else f" (+{z(gefuellt)})" if gefuellt else ""))
    zeilen.append("  Felder:       " + (", ".join(geaendert) if geaendert else "keine Änderung"))
    zeilen.append("                (-x geleert, +x neu gefüllt)")
    return zeilen


def main(argumente: list[str]) -> int:
    gegen = None
    if "--gegen" in argumente:
        i = argumente.index("--gegen")
        if i + 1 >= len(argumente):
            print("FEHLER: --gegen braucht eine Datei.")
            return 1
        gegen = Path(argumente[i + 1])
        argumente = argumente[:i] + argumente[i + 2:]

    pfad = Path(argumente[0]) if argumente else STANDARD
    if not pfad.exists():
        print(f"Datei nicht gefunden: {pfad}")
        return 1

    df = lies(pfad)
    print(f"### {pfad}")
    for zeile in bericht(df, pfad):
        print(zeile)

    if gegen is not None:
        if not gegen.exists():
            print(f"\nVergleichsdatei nicht gefunden: {gegen}")
            return 1
        for zeile in vergleich(lies(gegen), df):
            print(zeile)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
