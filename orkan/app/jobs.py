"""Verwaltung der laufenden Aufträge und Aufräumen alter Dateien.

Ein Auftrag lebt in einem eigenen Unterverzeichnis. Die hochgeladene Datei wird
sofort nach dem Einlesen gelöscht; die Ergebnisdateien verschwinden nach Ablauf
der eingestellten Frist.
"""
from __future__ import annotations

import re
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from . import config

ROHDATEI = "kundenliste.pkl"


@dataclass
class Job:
    id: str
    verzeichnis: Path
    dateiname: str
    quelle: str
    hinweis: str = ""
    ki_genutzt: bool = False
    spalten: list[str] = field(default_factory=list)
    zuordnung: dict[str, str] = field(default_factory=dict)
    unsicher: list[str] = field(default_factory=list)
    zeilen: int = 0
    erstellt: float = field(default_factory=time.time)
    verarbeitet: bool = False
    ergebnis: dict = field(default_factory=dict)

    @property
    def rohdatei(self) -> Path:
        return self.verzeichnis / ROHDATEI


_jobs: dict[str, Job] = {}
_sperre = threading.Lock()

_SAUBER = re.compile(r"[^A-Za-z0-9_.\-]+")


def sichere_kennung(text: str, standard: str = "Kunde") -> str:
    """Kundenkennung auf einen dateisystemtauglichen Namen reduzieren."""
    sauber = _SAUBER.sub("_", (text or "").strip()).strip("._-")
    return sauber[:40] or standard


def anlegen(dateiname: str) -> Job:
    job_id = uuid.uuid4().hex[:12]
    verzeichnis = Path(config.ARBEITSVERZEICHNIS) / job_id
    verzeichnis.mkdir(parents=True, exist_ok=True)
    job = Job(id=job_id, verzeichnis=verzeichnis, dateiname=dateiname, quelle="")
    with _sperre:
        _jobs[job_id] = job
    return job


def hole(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def rohdaten_sichern(job: Job, df: pd.DataFrame) -> None:
    df.to_pickle(job.rohdatei)


def rohdaten_laden(job: Job) -> pd.DataFrame:
    if not job.rohdatei.exists():
        raise FileNotFoundError(
            "Die hochgeladene Liste ist nicht mehr verfügbar. "
            "Bitte laden Sie die Datei erneut hoch."
        )
    return pd.read_pickle(job.rohdatei)


def rohdaten_loeschen(job: Job) -> None:
    job.rohdatei.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Aufräumen
# ---------------------------------------------------------------------------
def aufraeumen() -> int:
    """Auftragsverzeichnisse löschen, die älter sind als die Aufbewahrungsfrist."""
    basis = Path(config.ARBEITSVERZEICHNIS)
    if not basis.exists():
        return 0

    grenze = time.time() - config.ERGEBNIS_TTL_STUNDEN * 3600
    entfernt = 0
    for eintrag in basis.iterdir():
        if not eintrag.is_dir():
            continue
        try:
            if eintrag.stat().st_mtime < grenze:
                shutil.rmtree(eintrag, ignore_errors=True)
                entfernt += 1
                with _sperre:
                    _jobs.pop(eintrag.name, None)
        except OSError:
            continue
    return entfernt


def aufraeumen_starten(intervall_sekunden: int = 3600) -> threading.Thread:
    """Hintergrundschleife, die regelmäßig aufräumt."""

    def schleife() -> None:
        while True:
            try:
                aufraeumen()
            except Exception:
                pass
            time.sleep(intervall_sekunden)

    t = threading.Thread(target=schleife, daemon=True, name="aufraeumen")
    t.start()
    return t
