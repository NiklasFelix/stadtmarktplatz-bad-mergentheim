"""Sammelt alle Dateien für den Datenpool-Chat in einem Ordner.

    python werkzeuge/chat_infos_packen.py

Der Ordner ``EXPORT CHAT INFOS`` wird dabei komplett neu befüllt, damit dort
nie eine alte Fassung liegenbleibt. Zusätzlich wird geprüft, ob die Zahlen in
den Anweisungen noch zum eingesetzten Pool passen — genau daran ist es in der
Vergangenheit gescheitert: Der Chat bekam Vorgaben mit einem Poolstand von
vorgestern und lieferte entsprechend daneben.

Rückgabewert 0, wenn alles zusammenpasst; 1 bei veralteten Angaben.
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import pandas as pd

PROJEKT = Path(__file__).resolve().parent.parent
ZIEL = PROJEKT / "EXPORT CHAT INFOS"
POOL = PROJEKT / "daten" / "Datenpool_bereinigt.csv"

#: Diese Dateien gehören bei **jeder** Aufgabe mit.
IMMER = [
    # Der Pool zuerst: Er ist die Arbeitsgrundlage. Fehlt er, setzt der Chat auf
    # seiner eigenen, veralteten Kopie auf – genau so kam einmal ein Export
    # zurück, der alle Korrekturen rückgängig gemacht hätte.
    ("daten/Datenpool_bereinigt.csv", "Der aktuelle Pool — **Grundlage der Arbeit**"),
    ("EXPORT-ANFORDERUNGEN.md", "Die Referenz — alle verbindlichen Regeln"),
    ("werkzeuge/pool_pruefen.py", "Prüft, ob eine Pool-Datei in sich gültig ist"),
    ("werkzeuge/pool_vergleichen.py", "Prüft, ob etwas verlorengegangen ist"),
]

#: Davon je nach Anlass genau eine.
AUFGABEN = [
    ("PROMPT-NEUE-DATEN-EINARBEITEN.md", "Neue Datenquelle einarbeiten"),
    ("PROMPT-BILDNAMEN-ERGAENZEN.md", "Bildnamen nachtragen"),
    ("PROMPT-FUER-DATENPOOL-CHAT.md", "Geprüfte Neuaufnahmen übernehmen"),
]


def _zahl(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def pool_kennzahlen() -> dict[str, int] | None:
    """Zeilen, Spalten und Bildabdeckung des eingesetzten Pools."""
    if not POOL.exists():
        return None
    df = pd.read_csv(POOL, sep=";", dtype=str, encoding="utf-8-sig",
                     keep_default_na=False)
    bild = df["Bild"].str.strip()
    return {
        "zeilen": len(df),
        "spalten": len(df.columns),
        "mit_bild": int((bild != "").sum()),
    }


def pruefe_aktualitaet(kennzahlen: dict[str, int]) -> list[str]:
    """Stehen in den Anweisungen noch die Zahlen von gestern?

    Gesucht wird nach Zahlen im Format ``94.610`` – findet der Text eine
    Zeilenzahl, die nicht zum Pool passt, ist die Datei veraltet.
    """
    warnungen: list[str] = []
    erwartet = {_zahl(kennzahlen["zeilen"]), _zahl(kennzahlen["mit_bild"])}
    muster = re.compile(r"\b\d{2,3}\.\d{3}\b")

    for name, _ in IMMER + AUFGABEN:
        pfad = PROJEKT / name
        if not pfad.exists() or pfad.suffix != ".md":
            continue
        text = pfad.read_text(encoding="utf-8")
        verdaechtig = set()
        for treffer in muster.finditer(text):
            zahl = treffer.group(0)
            if zahl in erwartet:
                continue
            if not 50_000 <= int(zahl.replace(".", "")) <= 200_000:
                continue
            # Nur wenn die Zahl auch als Artikel- oder Zeilenzahl auftritt –
            # sonst schlägt die Prüfung bei jeder anderen Kennzahl an, etwa
            # der Zahl der Semikolons in einer Spalte.
            umfeld = text[max(0, treffer.start() - 40):treffer.end() + 40].lower()
            if "artikel" in umfeld or "zeilen" in umfeld:
                verdaechtig.add(zahl)
        if verdaechtig:
            warnungen.append(
                f"{name}: nennt {', '.join(sorted(verdaechtig))} — "
                f"der Pool hat {_zahl(kennzahlen['zeilen'])} Zeilen "
                f"und {_zahl(kennzahlen['mit_bild'])} Bildnamen"
            )
    return warnungen


def liesmich(kennzahlen: dict[str, int] | None) -> str:
    stand = ""
    if kennzahlen:
        stand = (
            f"\nPoolstand: **{_zahl(kennzahlen['zeilen'])} Artikel**, "
            f"{kennzahlen['spalten']} Spalten, "
            f"{_zahl(kennzahlen['mit_bild'])} mit Bildname.\n"
        )
    zeilen = [
        "# Dateien für den Datenpool-Chat",
        "",
        "Dieser Ordner wird von `werkzeuge/chat_infos_packen.py` erzeugt.",
        "**Nichts hier von Hand ändern** — bearbeitet wird immer das Original",
        "im Projektordner, danach das Skript erneut laufen lassen.",
        stand,
        "## Immer mitschicken",
        "",
    ]
    for name, zweck in IMMER:
        zeilen.append(f"- **{Path(name).name}** — {zweck}")
    zeilen += ["", "## Dazu genau eine Aufgabe", ""]
    for name, zweck in AUFGABEN:
        zeilen.append(f"- **{Path(name).name}** — {zweck}")
    zeilen += [
        "",
        "## Was zurückkommen muss",
        "",
        "Der vollständige neue Pool, die Ausgabe **beider** Prüfskripte und eine",
        "kurze Änderungsübersicht. Kein Prompt für den Code-Chat — die Anwendung",
        "ist fertig (siehe Abschnitt 1 der Anforderungen).",
        "",
    ]
    return "\n".join(zeilen)


def main() -> int:
    kennzahlen = pool_kennzahlen()

    if ZIEL.exists():
        shutil.rmtree(ZIEL)
    ZIEL.mkdir(parents=True)

    fehlend: list[str] = []
    for name, _ in IMMER + AUFGABEN:
        quelle = PROJEKT / name
        if not quelle.exists():
            fehlend.append(name)
            continue
        shutil.copy2(quelle, ZIEL / quelle.name)
        print(f"  kopiert: {quelle.name}")

    (ZIEL / "LIESMICH.md").write_text(liesmich(kennzahlen), encoding="utf-8")
    print("  erzeugt: LIESMICH.md")
    print(f"\nOrdner: {ZIEL}")

    if fehlend:
        print("\nFEHLER — diese Dateien gibt es nicht:")
        for f in fehlend:
            print(f"  • {f}")
        return 1

    if kennzahlen is None:
        print("\nHinweis: Kein Pool gefunden, Aktualität nicht geprüft.")
        return 0

    print(f"\nPool: {_zahl(kennzahlen['zeilen'])} Zeilen, "
          f"{kennzahlen['spalten']} Spalten, "
          f"{_zahl(kennzahlen['mit_bild'])} mit Bildname")

    warnungen = pruefe_aktualitaet(kennzahlen)
    if warnungen:
        print("\nVERALTETE ANGABEN — bitte im Original korrigieren:")
        for w in warnungen:
            print(f"  • {w}")
        return 1

    print("Die Angaben in den Anweisungen passen zum eingesetzten Pool.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
