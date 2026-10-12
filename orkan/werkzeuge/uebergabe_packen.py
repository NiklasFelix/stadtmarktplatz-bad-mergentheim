"""Packt das Projekt zur Übergabe an eine andere Person.

    python werkzeuge/uebergabe_packen.py

Erzeugt den Ordner ``UEBERGABE`` mit allem, was die übernehmende Person
braucht — und **ohne** alles, was sie nicht braucht: Sicherungskopien des Pools,
alte Chat-Exporte, Bildschirmaufzeichnungen, die virtuelle Umgebung, gebaute
Pakete. Aus 740 MB werden so rund 30 MB.

Rückgabewert 0, wenn das Paket vollständig ist.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJEKT = Path(__file__).resolve().parent.parent
ZIEL = PROJEKT / "UEBERGABE"

#: Ganze Verzeichnisse, die mitkommen.
ORDNER = [
    ("app", "Die Anwendung"),
    ("tests", "Die Testsuite"),
    ("werkzeuge", "Prüf- und Packskripte"),
    ("referenz", "Originalskript und Formatvorlage – nicht ändern"),
]
# „EXPORT CHAT INFOS" kommt bewusst nicht mit: Der Ordner enthält eine zweite
# Kopie des 24-MB-Pools und wird mit einem Befehl neu erzeugt.

#: Einzelne Dateien.
DATEIEN = [
    ("UEBERGABE.md", "**Hier anfangen**"),
    ("CLAUDE.md", "Datenregeln – liest der Code-Chat automatisch"),
    ("README.md", "Betrieb und Installation"),
    ("EXPORT-ANFORDERUNGEN.md", "Referenz für den Datenpool-Chat"),
    ("PROMPT-NEUE-DATEN-EINARBEITEN.md", "Aufgabe: neue Datenquelle"),
    ("PROMPT-BILDNAMEN-ERGAENZEN.md", "Aufgabe: Bildnamen"),
    ("PROMPT-FUER-DATENPOOL-CHAT.md", "Aufgabe: geprüfte Neuaufnahmen"),
    ("requirements.txt", "Abhängigkeiten"),
    ("pytest.ini", "Testkonfiguration"),
    ("requirements-dev.txt", "Abhängigkeiten für die Tests"),
    # desktop.py ist der Einstiegspunkt der .exe – ohne sie kein Build und
    # keine lauffähige Testsuite.
    ("desktop.py", "Einstiegspunkt der Desktop-Fassung"),
    ("orkan.spec", "Bauanleitung für die .exe"),
    (".gitignore", "was nicht in die Versionsverwaltung gehört"),
    (".dockerignore", "was nicht ins Docker-Abbild gehört"),
    ("Dockerfile", "Server-Betrieb"),
    ("docker-compose.yml", "Server-Betrieb"),
    ("start.bat", "Einzelplatzstart unter Windows"),
    ("daten/Datenpool_bereinigt.csv", "Der Datenpool – die eine Wahrheit"),
    (".claude/launch.json", "Startkonfiguration für den Entwicklungsserver"),
]

#: Diese Namen fliegen aus mitgenommenen Ordnern raus.
NICHT_MIT = {"__pycache__", ".pytest_cache", ".venv", "node_modules"}


def _kopiere_ordner(name: str) -> tuple[int, int]:
    quelle = PROJEKT / name
    if not quelle.is_dir():
        return 0, 0
    dateien = groesse = 0
    for datei in quelle.rglob("*"):
        if not datei.is_file():
            continue
        if any(teil in NICHT_MIT for teil in datei.parts):
            continue
        ziel = ZIEL / datei.relative_to(PROJEKT)
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(datei, ziel)
        dateien += 1
        groesse += datei.stat().st_size
    return dateien, groesse


def _mb(bytes_: int) -> str:
    return f"{bytes_ / 1048576:.1f} MB"


def liesmich() -> str:
    zeilen = [
        "# OrKan Artikel-Matching-Tool — Übergabepaket",
        "",
        "**Fang mit `UEBERGABE.md` an.** Dort steht der ganze Ablauf.",
        "",
        "## Was hier liegt",
        "",
    ]
    for name, zweck in DATEIEN:
        zeilen.append(f"- `{name}` — {zweck}")
    zeilen.append("")
    for name, zweck in ORDNER:
        zeilen.append(f"- `{name}/` — {zweck}")
    zeilen += [
        "",
        "## Erster Schritt",
        "",
        "```bash",
        "python -m venv .venv",
        ".venv/Scripts/pip install -r requirements.txt",
        ".venv/Scripts/python -m pytest -q",
        "```",
        "",
        "Alle Tests müssen grün sein. Danach `UEBERGABE.md` lesen.",
        "",
        "## Was bewusst fehlt",
        "",
        "- die virtuelle Umgebung (`.venv`) — wird oben neu angelegt",
        "- die gebaute `.exe` (rund 62 MB) — wird mit einem Befehl erzeugt,",
        "  siehe `UEBERGABE.md`, Schritt 5",
        "- Sicherungskopien des Pools, alte Chat-Exporte, Aufzeichnungen",
        "- die Prüf-Queue (`daten/neuaufnahmen_queue.csv`) — sie enthält",
        "  Kundendaten und gehört nicht in eine Übergabe",
        "- der Ordner `EXPORT CHAT INFOS` — er enthält nur eine zweite Kopie",
        "  des Pools und entsteht mit einem Befehl:",
        "",
        "  ```bash",
        "  .venv/Scripts/python werkzeuge/chat_infos_packen.py",
        "  ```",
        "",
    ]
    return "\n".join(zeilen)


def main() -> int:
    if ZIEL.exists():
        shutil.rmtree(ZIEL)
    ZIEL.mkdir(parents=True)

    fehlend: list[str] = []
    gesamt_dateien = gesamt_groesse = 0

    for name, _ in DATEIEN:
        quelle = PROJEKT / name
        if not quelle.is_file():
            fehlend.append(name)
            continue
        ziel = ZIEL / name
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(quelle, ziel)
        gesamt_dateien += 1
        gesamt_groesse += quelle.stat().st_size
        print(f"  {name}")

    for name, _ in ORDNER:
        anzahl, groesse = _kopiere_ordner(name)
        if not anzahl:
            fehlend.append(name + "/")
            continue
        gesamt_dateien += anzahl
        gesamt_groesse += groesse
        print(f"  {name}/  ({anzahl} Dateien, {_mb(groesse)})")

    (ZIEL / "LIESMICH-ZUERST.md").write_text(liesmich(), encoding="utf-8")
    print("  LIESMICH-ZUERST.md")

    print(f"\nOrdner: {ZIEL}")
    print(f"Umfang: {gesamt_dateien} Dateien, {_mb(gesamt_groesse)}")

    if fehlend:
        print("\nFEHLT — das Paket ist unvollständig:")
        for f in fehlend:
            print(f"  • {f}")
        return 1

    # Die Queue enthält Kundendaten und darf nicht mitgehen.
    queue = ZIEL / "daten" / "neuaufnahmen_queue.csv"
    if queue.exists():
        queue.unlink()
        print("\nHinweis: Prüf-Queue entfernt (enthält Kundendaten).")

    print("\nDas Paket ist vollständig.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
