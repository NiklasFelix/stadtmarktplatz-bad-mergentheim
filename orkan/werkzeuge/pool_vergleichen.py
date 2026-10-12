"""Vergleicht einen neuen Datenpool-Export mit dem eingesetzten Pool.

`pool_pruefen.py` beantwortet „ist die Datei in sich gültig?". Dieses Werkzeug
beantwortet die andere Frage: **was hat sich gegenüber dem alten Stand
verändert — und ist dabei etwas verlorengegangen?**

    python werkzeuge/pool_vergleichen.py daten/Datenpool_bereinigt.csv neuer_pool.csv

Rückgabewert 0, wenn nichts verlorenging. 1, wenn Artikel verschwunden sind
oder gefüllte Felder geleert wurden — beides ist im laufenden Betrieb ein
Rückschritt und muss vor der Übernahme geklärt werden.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SCHLUESSEL = "ArtikelNrLieferant"

#: Bezeichnungsfelder. Der Pool verteilt Text zwischen ihnen um (25-Zeichen-
#: Grenze der Cloud), deshalb wird hier zusätzlich geprüft, ob ein
#: verschwundener Wert nur in ein Nachbarfeld gewandert ist.
BEZEICHNUNGEN = ("BezArtikel1", "BezArtikel2", "BezArtikel3", "BezArtikelLang")

#: Felder, deren Verlust ein Kunde unmittelbar merkt.
BEOBACHTET = [
    "BezArtikel1", "BezArtikel2", "BezArtikel3", "BezArtikelLang",
    "BezArtikelGruppe", "Lagerort", "BezLagerort", "LagerMin", "LagerMax",
    "LagerEinheit", "VpeEinheit", "MengeProVPE", "AbwBestellmenge",
    "AbwBestelleinheit", "Werksnummer", "HerstellerNr", "EAN", "Bild",
    "Lieferanten_alle",
]


def _lies(pfad: Path) -> pd.DataFrame:
    return pd.read_csv(
        pfad, sep=";", dtype=str, encoding="utf-8-sig", keep_default_na=False
    )


def _zahl(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def vergleiche(alt_pfad: Path, neu_pfad: Path) -> tuple[list[str], list[str], list[str]]:
    """Gibt ``(verluste, hinweise, bericht)`` zurück."""
    verluste: list[str] = []
    hinweise: list[str] = []
    bericht: list[str] = []

    for p in (alt_pfad, neu_pfad):
        if not p.exists():
            return [f"Datei nicht gefunden: {p}"], [], []

    alt, neu = _lies(alt_pfad), _lies(neu_pfad)

    # --- Aufbau ---------------------------------------------------------
    bericht.append(f"Zeilen   {_zahl(len(alt))}  ->  {_zahl(len(neu))}")
    if list(alt.columns) != list(neu.columns):
        dazu = [s for s in neu.columns if s not in alt.columns]
        weg = [s for s in alt.columns if s not in neu.columns]
        if weg:
            verluste.append(f"Spalten fehlen jetzt: {', '.join(weg)}")
        if dazu:
            hinweise.append(f"Neue Spalten: {', '.join(dazu)}")

    if SCHLUESSEL not in neu.columns:
        return [f"Spalte {SCHLUESSEL} fehlt."], hinweise, bericht

    # --- Bestand --------------------------------------------------------
    na = alt[SCHLUESSEL].str.strip()
    nn = neu[SCHLUESSEL].str.strip()
    sa, sn = set(na), set(nn)
    verschwunden = sa - sn
    # Groß-/Kleinschreibung ist kein Verlust: das Matching normalisiert ohnehin,
    # und der Pool führt solche Dubletten bewusst zusammen.
    sn_ci = {x.upper() for x in sn}
    echt_weg = sorted(x for x in verschwunden if x.upper() not in sn_ci)
    zusammengefuehrt = len(verschwunden) - len(echt_weg)

    bericht.append(f"Artikel  {_zahl(len(sa))}  ->  {_zahl(len(sn))}   "
                   f"(neu: {_zahl(len(sn - sa))})")
    if zusammengefuehrt:
        bericht.append(f"         {_zahl(zusammengefuehrt)} nur anders geschrieben "
                       "(Dublette zusammengeführt) — kein Verlust")
    if echt_weg:
        beispiele = ", ".join(repr(x) for x in echt_weg[:3])
        verluste.append(
            f"{_zahl(len(echt_weg))} Artikel sind ersatzlos verschwunden "
            f"(z. B. {beispiele}). Kunden finden diese Nummern nicht mehr."
        )

    # --- Feldinhalte der gemeinsamen Artikel ----------------------------
    gemeinsam = alt.merge(neu, on=SCHLUESSEL, suffixes=("_a", "_n"))
    bericht.append(f"in beiden Ständen: {_zahl(len(gemeinsam))}")
    bericht.append("")
    bericht.append(f"{'Feld':<18}{'geändert':>10}{'geleert':>10}{'neu gefüllt':>14}")

    for spalte in BEOBACHTET:
        if f"{spalte}_a" not in gemeinsam.columns:
            continue
        a = gemeinsam[f"{spalte}_a"].fillna("").str.strip()
        n = gemeinsam[f"{spalte}_n"].fillna("").str.strip()
        geaendert = int((a != n).sum())
        gefuellt = int(((a == "") & (n != "")).sum())

        leer_geworden = (a != "") & (n == "")
        verschoben = 0
        if spalte in BEZEICHNUNGEN and int(leer_geworden.sum()):
            # Steht der Text jetzt in einem anderen Bezeichnungsfeld desselben
            # Artikels, ist nichts verloren – er wurde nur umverteilt.
            andere = [
                f"{s}_n" for s in BEZEICHNUNGEN
                if s != spalte and f"{s}_n" in gemeinsam.columns
            ]
            rest = gemeinsam.loc[leer_geworden, andere].fillna("").agg(" ".join, axis=1)
            verschoben = int(
                [w in r for w, r in zip(a[leer_geworden], rest)].count(True)
            )
        geleert = int(leer_geworden.sum()) - verschoben
        if verschoben:
            hinweise.append(
                f"{spalte}: {_zahl(verschoben)} Werte sind in ein anderes "
                "Bezeichnungsfeld gewandert (Umverteilung, kein Verlust)."
            )
        if geaendert:
            bericht.append(
                f"{spalte:<18}{_zahl(geaendert):>10}{_zahl(geleert):>10}"
                f"{_zahl(gefuellt):>14}"
            )
        if geleert:
            verluste.append(
                f"{spalte}: {_zahl(geleert)} Artikel hatten einen Wert und haben "
                "jetzt keinen mehr."
            )
        # Überschreiben ist erlaubt, aber der Anwender soll es sehen.
        ersetzt = int(((a != "") & (n != "") & (a != n)).sum())
        if ersetzt:
            hinweise.append(
                f"{spalte}: {_zahl(ersetzt)} vorhandene Werte wurden durch andere "
                "ersetzt."
            )

    # --- Bildabdeckung ---------------------------------------------------
    if "Bild" in neu.columns:
        def bild(df):
            b = df["Bild"].fillna("").str.strip()
            g = b[b != ""]
            return len(g), g.str.lower().nunique()

        ga, va = bild(alt)
        gn, vn = bild(neu)
        bericht.append("")
        bericht.append(
            f"Bilder   {_zahl(ga)} ({ga/len(alt)*100:.0f} %)  ->  "
            f"{_zahl(gn)} ({gn/len(neu)*100:.0f} %)   "
            f"verschiedene Dateien: {_zahl(va)} -> {_zahl(vn)}"
        )

    return verluste, hinweise, bericht


def main(argumente: list[str]) -> int:
    if len(argumente) < 2:
        print(__doc__)
        return 1

    alt_pfad, neu_pfad = Path(argumente[0]), Path(argumente[1])
    verluste, hinweise, bericht = vergleiche(alt_pfad, neu_pfad)

    print(f"Alt: {alt_pfad}")
    print(f"Neu: {neu_pfad}")
    print()
    for zeile in bericht:
        print(zeile)
    print()

    if verluste:
        print(f"VERLUSTE ({len(verluste)}) — vor der Übernahme klären:")
        for v in verluste:
            print(f"  • {v}")
        print()
    if hinweise:
        print(f"HINWEISE ({len(hinweise)}):")
        for h in hinweise:
            print(f"  • {h}")
        print()
    if not verluste:
        print("Kein Datenverlust: kein Artikel und kein gefülltes Feld ist weggefallen.")

    return 1 if verluste else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
