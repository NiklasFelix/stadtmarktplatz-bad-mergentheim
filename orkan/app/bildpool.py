"""Artikelbilder aus dem Bildpool heraussuchen und als ZIP packen.

Die Importdatei nennt in der Spalte ``Artikelbild`` nur Dateinamen. Hier werden
genau diese Dateien im Bildpool gesucht und zu einem ZIP gepackt, das der Kunde
zusammen mit der Importdatei in die OrKan-Cloud einspielt.

Zwei Regeln bestimmen den Aufbau:

* **Nur die benötigten Bilder, jede Datei genau einmal.** Der Bildpool ist
  Betriebsvermögen und darf nie als Ganzes das Haus verlassen – dieselbe Logik
  wie beim Artikelpool. Mehrere Artikel teilen sich oft ein Bild.
* **Kein Ausbruch aus dem Bildpool.** Gesucht wird ausschließlich in einem
  Verzeichnisindex, der unterhalb des konfigurierten Ordners aufgebaut wurde.
  Ein Dateiname mit ``..`` oder Pfadanteil kann darin gar nicht vorkommen.
"""
from __future__ import annotations

import json
import os
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from . import config

#: Endungen, die im Datenpool tatsächlich vorkommen, plus die üblichen Nachbarn.
BILDENDUNGEN = {".jpg", ".jpeg", ".png", ".webp", ".jfif", ".gif", ".bmp"}

#: Im Desktop-Betrieb darf der Anwender den Pfad selbst setzen.
_EINSTELLUNGSDATEI = "einstellungen.json"
_ueberschreibung: str | None = None


# ---------------------------------------------------------------------------
# Wo liegt der Bildpool?
# ---------------------------------------------------------------------------
def _einstellungen_pfad() -> Path:
    return Path(config.BENUTZERDATEN) / _EINSTELLUNGSDATEI


def _gespeicherten_pfad_lesen() -> str:
    datei = _einstellungen_pfad()
    if not datei.exists():
        return ""
    try:
        return str(json.loads(datei.read_text(encoding="utf-8")).get("bildpool", ""))
    except (ValueError, OSError):
        return ""


def pfad() -> Path | None:
    """Konfigurierter Bildpool, oder ``None`` wenn keiner eingerichtet ist."""
    roh = _ueberschreibung
    if roh is None:
        roh = config.BILDPOOL_PFAD or (
            _gespeicherten_pfad_lesen() if darf_gesetzt_werden() else ""
        )
    roh = (roh or "").strip()
    return Path(roh) if roh else None


def darf_gesetzt_werden() -> bool:
    """Darf der Bildordner in der Oberfläche eingegeben werden?

    In der Desktop-Fassung immer – dort gehört der Rechner dem Anwender. Auf
    einem Server zeigt ein eingegebener Pfad dagegen auf den **Server**; wäre er
    frei wählbar, könnte man sich beliebige Verzeichnisse als ZIP herunterladen.
    Deshalb dort nur nach ausdrücklicher Freischaltung über ``BILDPOOL_EINGABE``.
    """
    return config.gebuendelt() or config.BILDPOOL_EINGABE


def anzahl_bilder(ordner: Path | None = None) -> int:
    """Wie viele Bilddateien liegen im Ordner? Für die Rückmeldung nach der Eingabe."""
    ordner = ordner or pfad()
    if not ordner or not ordner.is_dir():
        return 0
    return len(_index(ordner.resolve()))


def setze_pfad(wert: str) -> Path | None:
    """Bildpool-Verzeichnis setzen und für den nächsten Start merken."""
    global _ueberschreibung
    if not darf_gesetzt_werden():
        raise ValueError(
            "Der Bildordner ist hier fest eingestellt und lässt sich nicht ändern. "
            "Auf dem Server wird er über die Umgebungsvariable BILDPOOL_PFAD gesetzt; "
            "die Eingabe im Programm lässt sich mit BILDPOOL_EINGABE=1 freischalten."
        )

    wert = (wert or "").strip()
    if wert:
        ziel = Path(wert)
        if not ziel.exists() or not ziel.is_dir():
            raise ValueError(f"Der Ordner „{wert}“ wurde nicht gefunden.")
        wert = str(ziel.resolve())

    _ueberschreibung = wert
    index_vergessen()
    datei = _einstellungen_pfad()
    datei.parent.mkdir(parents=True, exist_ok=True)
    datei.write_text(json.dumps({"bildpool": wert}, ensure_ascii=False), encoding="utf-8")
    return Path(wert) if wert else None


def zuruecksetzen() -> None:
    """Nur für Tests: gemerkten Pfad und Verzeichnisindex vergessen."""
    global _ueberschreibung
    _ueberschreibung = None
    index_vergessen()


def eingerichtet() -> bool:
    p = pfad()
    return bool(p and p.is_dir())


# ---------------------------------------------------------------------------
# Suchen und packen
# ---------------------------------------------------------------------------
#: Gemerkte Verzeichnisse: Wurzel -> (Zeitpunkt, Index).
_index_speicher: dict[str, tuple[float, dict[str, Path]]] = {}

#: Wie lange ein gemerkter Index gilt. Ein Bildpool ändert sich selten; ein
#: neues Bild ist nach dieser Zeit von allein dabei.
INDEX_GUELTIG_S = 300


def _index_bauen(wurzel: Path) -> dict[str, Path]:
    """Dateiname (klein geschrieben) -> Datei, rekursiv unterhalb der Wurzel.

    Groß- und Kleinschreibung wird ignoriert, damit Windows und Linux dasselbe
    ZIP erzeugen. Bei gleichnamigen Dateien in mehreren Unterordnern gewinnt der
    alphabetisch erste Pfad – das hält das Ergebnis reproduzierbar.

    Bewusst ``os.walk`` statt ``rglob``: ``rglob`` fragt für jeden Eintrag beim
    Dateisystem nach, ob er eine Datei ist. Auf einem Netzlaufwerk ist das je
    Eintrag ein Netzwerk-Rundlauf – bei 20.000 Bildern der Unterschied zwischen
    Sekunden und Minuten.
    """
    treffer: list[tuple[str, Path]] = []
    for ordner, _unterordner, dateien in os.walk(wurzel):
        basis = Path(ordner)
        for name in dateien:
            if os.path.splitext(name)[1].lower() in BILDENDUNGEN:
                treffer.append((name.lower(), basis / name))

    gefunden: dict[str, Path] = {}
    for schluessel, datei in sorted(treffer, key=lambda t: str(t[1])):
        gefunden.setdefault(schluessel, datei)
    return gefunden


def _index(wurzel: Path) -> dict[str, Path]:
    """Verzeichnisindex, für kurze Zeit gemerkt.

    Ohne dieses Merken wurde der Bildordner bei jedem Statusaufruf **und** bei
    jedem Abgleich komplett neu durchsucht.
    """
    schluessel = str(wurzel)
    eintrag = _index_speicher.get(schluessel)
    if eintrag and (time.monotonic() - eintrag[0]) < INDEX_GUELTIG_S:
        return eintrag[1]

    gefunden = _index_bauen(wurzel)
    _index_speicher[schluessel] = (time.monotonic(), gefunden)
    return gefunden


def index_vergessen() -> None:
    """Gemerkte Verzeichnisse verwerfen (nach Pfadwechsel, und für Tests)."""
    _index_speicher.clear()


@dataclass
class ZipErgebnis:
    """Was beim Packen herausgekommen ist."""

    pfad: Path | None = None
    gepackt: list[str] = field(default_factory=list)
    fehlend: list[str] = field(default_factory=list)
    groesse: int = 0
    abgebrochen: str = ""

    @property
    def anzahl(self) -> int:
        return len(self.gepackt)

    @property
    def groesse_mb(self) -> float:
        return round(self.groesse / 1024 / 1024, 1)


def bildnamen_sammeln(importzeilen: list[dict]) -> list[str]:
    """Die verschiedenen Bildnamen einer Importdatei – jeder genau einmal.

    Bewusst über die Menge der Namen, nicht über die Artikelzeilen: Im Pool
    teilen sich tausende Artikel dieselbe Bilddatei.
    """
    gesehen: dict[str, str] = {}
    for zeile in importzeilen:
        wert = zeile.get("Artikelbild")
        if wert is None:
            continue
        name = str(wert).strip()
        if not name or name.lower() in ("nan", "none"):
            continue
        gesehen.setdefault(name.lower(), name)
    return [gesehen[k] for k in sorted(gesehen)]


def packe(importzeilen: list[dict], ziel: Path) -> ZipErgebnis:
    """Benötigte Bilder in ein ZIP packen.

    Liefert immer ein Ergebnis – auch wenn kein Bildpool eingerichtet ist oder
    keine Bilder gebraucht werden. Dann bleibt ``pfad`` leer.
    """
    namen = bildnamen_sammeln(importzeilen)
    ergebnis = ZipErgebnis()
    if not namen:
        return ergebnis

    wurzel = pfad()
    if not wurzel or not wurzel.is_dir():
        ergebnis.fehlend = namen
        ergebnis.abgebrochen = "kein Bildordner eingerichtet"
        return ergebnis

    wurzel = wurzel.resolve()
    verzeichnis = _index(wurzel)

    grenze = config.MAX_ZIP_MB * 1024 * 1024
    ziel.parent.mkdir(parents=True, exist_ok=True)
    summe = 0

    with zipfile.ZipFile(ziel, "w", zipfile.ZIP_DEFLATED) as archiv:
        for name in namen:
            datei = verzeichnis.get(name.lower())
            if datei is None:
                ergebnis.fehlend.append(name)
                continue
            # Doppelt genäht: Die Datei stammt aus dem Index unterhalb der
            # Wurzel, wird aber trotzdem noch einmal dagegen geprüft.
            if not datei.resolve().is_relative_to(wurzel):
                ergebnis.fehlend.append(name)
                continue

            groesse = datei.stat().st_size
            if summe + groesse > grenze:
                ergebnis.abgebrochen = (
                    f"Das Bildpaket würde {config.MAX_ZIP_MB} MB überschreiten. "
                    "Bitte teilen Sie die Liste auf."
                )
                break

            # Unter dem Namen aus der Importdatei ablegen, nicht unter dem
            # Namen auf der Platte – sonst passt die Schreibweise nicht.
            archiv.write(datei, arcname=name)
            ergebnis.gepackt.append(name)
            summe += groesse

    if not ergebnis.gepackt:
        ziel.unlink(missing_ok=True)
        return ergebnis

    ergebnis.pfad = ziel
    ergebnis.groesse = ziel.stat().st_size
    return ergebnis
