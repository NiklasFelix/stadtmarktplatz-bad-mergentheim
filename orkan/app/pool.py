"""Laden und Indizieren des Artikel-Datenpools.

Der Pool bleibt ausschließlich serverseitig. Dieses Modul gibt nie den ganzen
Datenbestand heraus, sondern nur einzelne Treffer zu konkreten Artikelnummern.
"""
from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from . import config
from .text import tokens

SCHLUESSELSPALTE = "ArtikelNrLieferant"


@dataclass
class Datenpool:
    """Pool plus vorberechnete Indizes für schnelles Matching."""

    df: pd.DataFrame
    #: normierte Artikelnummer -> Zeilenposition (erster Treffer bei Dubletten)
    lookup: dict[str, int]
    #: Zeilenpositionen der Artikel mit gefülltem LagerMin (MinMax-Kandidaten)
    kandidaten: np.ndarray
    kand_min: np.ndarray
    kand_max: np.ndarray
    #: Artikelgruppe (klein geschrieben) -> Indizes in die Kandidaten-Arrays
    gruppen_index: dict[str, np.ndarray] = field(default_factory=dict)
    #: Bezeichnungs-Token -> Indizes in die Kandidaten-Arrays
    token_index: dict[str, np.ndarray] = field(default_factory=dict)
    quelle: Path | None = None

    def __len__(self) -> int:
        return len(self.df)

    def finde(self, artikelnummer_normiert: str) -> pd.Series | None:
        """Einzelnen Pool-Artikel holen, sonst None. Kein Zugriff auf den Rest."""
        pos = self.lookup.get(artikelnummer_normiert)
        return None if pos is None else self.df.iloc[pos]

    @property
    def spalten(self) -> list[str]:
        return list(self.df.columns)


def _als_zahl(reihe: pd.Series) -> np.ndarray:
    return pd.to_numeric(reihe, errors="coerce").to_numpy(dtype=float)


def laden(pfad: Path | None = None) -> Datenpool:
    """Pool von der Platte lesen und die Suchindizes aufbauen."""
    pfad = Path(pfad or config.POOL_PFAD)
    if not pfad.exists():
        raise FileNotFoundError(f"Datenpool nicht gefunden: {pfad}")

    df = pd.read_csv(
        pfad,
        sep=config.CSV_TRENNZEICHEN,
        dtype=str,
        encoding=config.CSV_KODIERUNG,
        keep_default_na=True,
    )
    if SCHLUESSELSPALTE not in df.columns:
        raise ValueError(
            f"Spalte '{SCHLUESSELSPALTE}' fehlt im Datenpool {pfad}. "
            f"Gefunden: {', '.join(df.columns[:5])} …"
        )

    schluessel = df[SCHLUESSELSPALTE].fillna("").str.strip().str.upper()
    lookup: dict[str, int] = {}
    for pos, wert in enumerate(schluessel):
        # Bei Dubletten gewinnt der erste Treffer (wie in der Referenzlogik).
        if wert and wert not in lookup:
            lookup[wert] = pos

    kandidaten = np.flatnonzero(df["LagerMin"].notna().to_numpy())
    kand_df = df.iloc[kandidaten]
    kand_min = _als_zahl(kand_df["LagerMin"])
    kand_max = _als_zahl(kand_df["LagerMax"])

    gruppen_roh: dict[str, list[int]] = defaultdict(list)
    for i, gruppe in enumerate(kand_df["BezArtikelGruppe"].to_numpy()):
        if isinstance(gruppe, str):
            schluessel_gruppe = gruppe.strip().lower()
            gruppen_roh[schluessel_gruppe].append(i)

    token_roh: dict[str, list[int]] = defaultdict(list)
    for i, bez in enumerate(kand_df["BezArtikel1"].fillna("").to_numpy()):
        for tok in tokens(bez):
            token_roh[tok].append(i)

    return Datenpool(
        df=df,
        lookup=lookup,
        kandidaten=kandidaten,
        kand_min=kand_min,
        kand_max=kand_max,
        gruppen_index={k: np.array(v, dtype=np.int64) for k, v in gruppen_roh.items()},
        token_index={k: np.array(v, dtype=np.int64) for k, v in token_roh.items()},
        quelle=pfad,
    )


# ---------------------------------------------------------------------------
# Prozessweiter Cache, damit der Pool nur einmal gelesen wird.
# ---------------------------------------------------------------------------
_cache: Datenpool | None = None
_sperre = threading.Lock()


def hole() -> Datenpool:
    global _cache
    if _cache is None:
        with _sperre:
            if _cache is None:
                _cache = laden()
    return _cache


def neu_laden() -> Datenpool:
    """Pool nach einem Dateiaustausch ohne Serverneustart neu einlesen."""
    global _cache
    with _sperre:
        _cache = laden()
    return _cache
