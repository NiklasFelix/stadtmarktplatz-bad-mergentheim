"""Prüft eine Datenpool-CSV, bevor sie in die Anwendung übernommen wird.

Aufruf:

    python werkzeuge/pool_pruefen.py daten/Datenpool_bereinigt.csv

Zusätzlich lässt sich prüfen, ob die eingetragenen Bildnamen im Bildpool
tatsächlich als Datei liegen — sonst fehlen sie später im ZIP zur Importdatei:

    python werkzeuge/pool_pruefen.py neuer_pool.csv --bildordner D:/Bildpool

Der Rückgabewert ist 0, wenn die Datei einsetzbar ist, sonst 1. Fehler machen
die Datei unbrauchbar, Warnungen kosten nur Datenqualität.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import pandas as pd

#: Die 28 Spalten des Pools, in genau dieser Reihenfolge.
SPALTEN = [
    "ArtikelNrLieferant", "BezArtikel1", "BezArtikel2", "BezArtikel3",
    "BezArtikelLang", "KurzBezeichnung", "BezArtikelGruppe", "Lager",
    "Lagerort", "BezLagerort", "LagerMin", "LagerMax", "LagerEinheit",
    "VpeEinheit", "MengeProVPE", "AbwBestellmenge", "AbwBestelleinheit",
    "Werksnummer", "HerstellerNr", "EAN",
    "Bild", "Lieferanten_alle", "Anz_Lieferanten", "Vorkommen", "Quellen",
    "VermutlichTestdaten", "HatKonflikt", "KritischerKonflikt",
]

WISSENSCHAFTLICH = re.compile(r"^\s*[+-]?\d+(?:[.,]\d+)?[eE][+-]?\d+\s*$")
WORT = re.compile(r"^[A-Za-zÄÖÜäöüß]{3,}$")


def sieht_nach_text_aus(wert: str) -> bool:
    """Zwei oder mehr echte Wörter deuten auf eine Bezeichnung statt eine Nummer."""
    return len([t for t in wert.split() if WORT.match(t)]) >= 2


def pruefe(pfad: Path, bildordner: Path | None = None) -> tuple[list[str], list[str]]:
    fehler: list[str] = []
    warnungen: list[str] = []

    if not pfad.exists():
        return [f"Datei nicht gefunden: {pfad}"], []

    # --- Kodierung -----------------------------------------------------
    roh = pfad.open("rb").read(3)
    if roh != b"\xef\xbb\xbf":
        fehler.append(
            "Die Datei beginnt nicht mit dem UTF-8-BOM. Excel zeigt dann "
            "Umlaute falsch an. Beim Speichern 'UTF-8 mit BOM' wählen."
        )

    # --- Kopfzeile -----------------------------------------------------
    with pfad.open("r", encoding="utf-8-sig", newline="") as f:
        try:
            kopf = next(csv.reader(f, delimiter=";"))
        except StopIteration:
            return ["Die Datei ist leer."], []

    kopf = [s.strip() for s in kopf]
    if kopf != SPALTEN:
        fehlend = [s for s in SPALTEN if s not in kopf]
        zuviel = [s for s in kopf if s not in SPALTEN]
        teile = [f"{len(SPALTEN)} Spalten erwartet, {len(kopf)} gefunden"]
        if fehlend:
            teile.append("fehlend: " + ", ".join(fehlend))
        if zuviel:
            teile.append("unbekannt: " + ", ".join(zuviel))
        if not fehlend and not zuviel:
            teile.append("Reihenfolge weicht ab")
        fehler.append("Spaltenaufbau stimmt nicht — " + "; ".join(teile))
        return fehler, warnungen

    df = pd.read_csv(pfad, sep=";", dtype=str, encoding="utf-8-sig")
    nr = df["ArtikelNrLieferant"].fillna("")

    # --- Schlüsselspalte ------------------------------------------------
    leer = int((nr.str.strip() == "").sum())
    if leer:
        fehler.append(f"{leer} Zeilen ohne Artikelnummer.")

    dubletten = int(nr[nr != ""].duplicated().sum())
    if dubletten:
        fehler.append(
            f"{dubletten} doppelte Artikelnummern. Die Nummer muss eindeutig sein, "
            "sonst gewinnt beim Abgleich willkürlich der erste Treffer."
        )

    # --- Kaputte Zahlen -------------------------------------------------
    for spalte in ("ArtikelNrLieferant", "EAN", "Werksnummer", "HerstellerNr"):
        betroffen = df[spalte].fillna("").map(lambda v: bool(WISSENSCHAFTLICH.match(v)))
        if betroffen.any():
            beispiel = df.loc[betroffen, spalte].iloc[0]
            fehler.append(
                f"{int(betroffen.sum())} Werte in '{spalte}' stehen in "
                f"wissenschaftlicher Notation (z. B. {beispiel!r}). Die Ziffern "
                "sind damit unwiederbringlich verloren — Spalte vor dem Export "
                "als Text formatieren."
            )

    # --- Bezeichnung ins Nummernfeld gerutscht --------------------------
    kaputt = nr.map(lambda v: ";" in v or sieht_nach_text_aus(v))
    if kaputt.any():
        beispiele = df.loc[kaputt, "ArtikelNrLieferant"].head(3).tolist()
        warnungen.append(
            f"{int(kaputt.sum())} Artikelnummern sehen nach Bezeichnung oder Name "
            f"aus, z. B. {beispiele}. Solche Zeilen gehören nicht in den Pool."
        )

    # --- Bezeichnungen --------------------------------------------------
    ohne_bez = int(df["BezArtikel1"].isna().sum())
    if ohne_bez:
        warnungen.append(
            f"{ohne_bez} Artikel ohne Bezeichnung (BezArtikel1). Sie erscheinen "
            "beim Kunden als leere Zeile in der Importdatei."
        )

    # --- Bildnamen ------------------------------------------------------
    # Aus ihnen wird später das Bild-ZIP zur Importdatei gepackt; sie müssen
    # deshalb exakte Dateinamen sein.
    bild = df["Bild"].fillna("")
    gefuellt = bild[bild.str.strip() != ""]
    if len(gefuellt):
        mit_pfad = gefuellt[gefuellt.str.contains(r"[\\/]", regex=True)]
        if len(mit_pfad):
            fehler.append(
                f"{len(mit_pfad)} Bildnamen enthalten einen Pfadanteil "
                f"(z. B. {mit_pfad.iloc[0]!r}). Erwartet wird nur der Dateiname."
            )

        ohne_endung = gefuellt[~gefuellt.str.contains(r"\.[A-Za-z0-9]+$", regex=True)]
        if len(ohne_endung):
            warnungen.append(
                f"{len(ohne_endung)} Bildnamen ohne Dateiendung "
                f"(z. B. {ohne_endung.iloc[0]!r}). Diese Bilder lassen sich im "
                "Bildpool nicht finden und fehlen später im ZIP."
            )

        erlaubt = {"jpg", "jpeg", "png", "webp", "jfif", "gif", "bmp"}
        endungen = gefuellt.str.extract(r"\.([A-Za-z0-9]+)$", expand=False).str.lower()
        fremd = gefuellt[endungen.notna() & ~endungen.isin(erlaubt)]
        if len(fremd):
            warnungen.append(
                f"{len(fremd)} Bildnamen zeigen auf kein Bildformat "
                f"(z. B. {fremd.iloc[0]!r})."
            )

        if bildordner is not None:
            fehler_b, warnung_b = _pruefe_gegen_bildpool(gefuellt, bildordner)
            fehler.extend(fehler_b)
            warnungen.extend(warnung_b)

    # --- Feldregeln aus den Anforderungen, Abschnitt 5 ------------------
    # Diese Regeln sind im Pool umgesetzt. Taucht ein Verstoß wieder auf, ist es
    # fast immer ein Export, der auf einer veralteten Kopie aufsetzt.
    regel_fehler, regel_warnungen = _pruefe_feldregeln(df)
    fehler.extend(regel_fehler)
    warnungen.extend(regel_warnungen)

    # --- Lagerwerte -----------------------------------------------------
    mn = pd.to_numeric(df["LagerMin"], errors="coerce")
    mx = pd.to_numeric(df["LagerMax"], errors="coerce")
    verdreht = int((mn > mx).sum())
    if verdreht:
        warnungen.append(f"{verdreht} Artikel haben LagerMin größer als LagerMax.")

    ohne_min = int(mn.isna().sum())
    if ohne_min:
        warnungen.append(
            f"{ohne_min} Artikel ohne LagerMin. Das ist erlaubt, sie dienen aber "
            "nicht mehr als Vorlage für MinMax-Vorschläge bei Neuaufnahmen."
        )

    return fehler, warnungen


BILDENDUNGEN = {".jpg", ".jpeg", ".png", ".webp", ".jfif", ".gif", ".bmp"}

#: Einheitenfelder – dort gelten die Regeln aus Abschnitt 5.1.
EINHEITENFELDER = ("LagerEinheit", "VpeEinheit", "AbwBestelleinheit")

#: UN/ECE-Kennungen, die ausgeschrieben gehören.
EINHEITEN_CODES = {
    "PCE", "MTR", "PR", "LTR", "SET", "KGM", "MTK", "DZN", "MMT", "CMK",
    "CMQ", "TNE",
}

#: Wörter, die eindeutig statt einer leeren Zelle dastehen. Sie sind nie eine
#: Angabe und gelten deshalb als Fehler.
PLATZHALTER = {"leer", "n/a", "na", "null", "none"}

#: Grenzfälle: könnten auch bewusst so geschrieben sein („Lagerort: Unbekannt“).
#: Nur ein Hinweis – die Anwendung filtert sie ohnehin aus der Importdatei.
PLATZHALTER_WEICH = {"keine", "unbekannt"}


def _pruefe_feldregeln(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    """Die Regeln aus Abschnitt 5, die im Pool bereits umgesetzt sind.

    Ein Verstoß bedeutet in aller Regel: Der Export setzt auf einer veralteten
    Kopie auf. Genau so ist einmal eine Lieferung hereingekommen, die 1.988
    Platzhalter und 1.850 Nullen zurückgebracht hätte.
    """
    fehler: list[str] = []
    warnungen: list[str] = []

    hart = weich = 0
    for spalte in df.columns:
        klein = df[spalte].fillna("").str.strip().str.lower()
        hart += int(klein.isin(PLATZHALTER).sum())
        weich += int(klein.isin(PLATZHALTER_WEICH).sum())
    if hart:
        fehler.append(
            f"{hart} Zellen enthalten ein Platzhalterwort wie „leer“ statt "
            "einer leeren Zelle (Abschnitt 5.4)."
        )
    if weich:
        warnungen.append(
            f"{weich} Zellen enthalten „Unbekannt“ oder „keine“. Falls das keine "
            "Angabe sein soll, gehört die Zelle geleert (Abschnitt 5.4)."
        )

    codes = 0
    for spalte in EINHEITENFELDER:
        if spalte in df.columns:
            codes += int(df[spalte].fillna("").str.strip().isin(EINHEITEN_CODES).sum())
    if codes:
        fehler.append(
            f"{codes} Einheiten stehen als Kürzel statt ausgeschrieben "
            "(PCE, MTR, PR, LTR …) – siehe Abschnitt 5.1."
        )

    if "MengeProVPE" in df.columns:
        nullen = int(df["MengeProVPE"].fillna("").str.strip().isin(["0", "0.0", "0,0"]).sum())
        if nullen:
            fehler.append(
                f"{nullen} Artikel haben MengeProVPE = 0. Null Stück je Verpackung "
                "ergibt keinen Sinn; die Zelle bleibt leer (Abschnitt 5.2)."
            )

    if "KurzBezeichnung" in df.columns:
        werte = df["KurzBezeichnung"].fillna("").str.strip()
        abweichend = int((werte != "ST").sum())
        if abweichend:
            andere = sorted(set(werte[werte != "ST"]))[:4]
            fehler.append(
                f"{abweichend} Artikel haben eine andere Satzart als ST "
                f"(z. B. {', '.join(repr(a) for a in andere)}) – siehe Abschnitt 5.3."
            )

    if {"AbwBestellmenge", "AbwBestelleinheit"} <= set(df.columns):
        menge = df["AbwBestellmenge"].fillna("").str.strip() != ""
        einheit = df["AbwBestelleinheit"].fillna("").str.strip() != ""
        halb = int((menge ^ einheit).sum())
        if halb:
            fehler.append(
                f"{halb} Artikel haben nur eines der beiden Bestellfelder gefüllt. "
                "Beide gehören zusammen oder beide bleiben leer (Abschnitt 5.2)."
            )
        null = int(df["AbwBestellmenge"].fillna("").str.strip().isin(["0", "0.0"]).sum())
        if null:
            fehler.append(f"{null} Artikel haben AbwBestellmenge = 0 (Abschnitt 5.2).")

    return fehler, warnungen


def _pruefe_gegen_bildpool(namen, ordner: Path) -> tuple[list[str], list[str]]:
    """Liegt zu jedem eingetragenen Bildnamen auch eine Datei im Bildpool?

    Der Vergleich läuft ohne Groß-/Kleinschreibung und über alle Unterordner —
    genauso, wie ``app/bildpool.py`` die Dateien später sucht.
    """
    if not ordner.is_dir():
        return [f"Bildordner nicht gefunden: {ordner}"], []

    vorhanden = {
        d.name.lower()
        for d in ordner.rglob("*")
        if d.is_file() and d.suffix.lower() in BILDENDUNGEN
    }
    eindeutig = {n.strip().lower() for n in namen if n.strip()}
    fehlend = sorted(eindeutig - vorhanden)

    hinweis = [
        f"Bildpool: {len(vorhanden):,} Dateien, im Pool verwendet: "
        f"{len(eindeutig):,} verschiedene Namen.".replace(",", ".")
    ]
    if not fehlend:
        return [], hinweis

    beispiele = ", ".join(repr(n) for n in fehlend[:3])
    anteil = len(fehlend) / len(eindeutig) * 100
    meldung = (
        f"{len(fehlend):,} von {len(eindeutig):,} Bildnamen ({anteil:.1f} %) liegen "
        f"nicht im Bildordner (z. B. {beispiele}). Diese Bilder fehlen später im "
        "ZIP zur Importdatei.".replace(",", ".")
    )
    # Vereinzelte Lücken sind Alltag; reißt es die Mehrheit, stimmt die
    # Zuordnung nicht und die Datei sollte so nicht übernommen werden.
    return ([meldung], hinweis) if anteil > 50 else ([], hinweis + [meldung])


def main(argumente: list[str]) -> int:
    bildordner = None
    if "--bildordner" in argumente:
        i = argumente.index("--bildordner")
        if i + 1 >= len(argumente):
            print("FEHLER: --bildordner braucht einen Pfad.")
            return 1
        bildordner = Path(argumente[i + 1])
        argumente = argumente[:i] + argumente[i + 2:]

    pfad = Path(argumente[0]) if argumente else Path("daten/Datenpool_bereinigt.csv")
    fehler, warnungen = pruefe(pfad, bildordner)

    print(f"Geprüft: {pfad}")
    try:
        anzahl = len(pd.read_csv(pfad, sep=";", dtype=str, encoding="utf-8-sig"))
        print(f"Zeilen : {anzahl:,}".replace(",", "."))
    except Exception:
        pass
    print()

    if fehler:
        print(f"FEHLER ({len(fehler)}) — die Datei ist so nicht einsetzbar:")
        for f in fehler:
            print(f"  • {f}")
        print()
    if warnungen:
        print(f"WARNUNGEN ({len(warnungen)}) — nutzbar, aber Datenqualität leidet:")
        for w in warnungen:
            print(f"  • {w}")
        print()
    if not fehler and not warnungen:
        print("Alles in Ordnung.")
    elif not fehler:
        print("Keine harten Fehler — die Datei ist einsetzbar.")

    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
