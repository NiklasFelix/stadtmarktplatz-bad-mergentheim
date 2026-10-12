"""Neuaufnahme-Queue: sammeln, bearbeiten, prüfen, übernehmen.

Nicht gefundene Artikel landen hier – **nicht** im Produktivpool. Der Ablauf für
den OrKan-Mitarbeiter ist dreistufig:

1. **Export** der offenen Einträge als Excel-Datei.
2. **Bearbeiten** in Excel: Bezeichnungen ergänzen, Gruppen korrigieren,
   unbrauchbare Zeilen einfach löschen.
3. **Re-Import** der Datei, danach **Übernahme** in den Pool.

Vor der Übernahme prüft :func:`pruefe_eintrag` jede Zeile. Was offensichtlich
kein Artikel ist (fehlende Bezeichnung, Name statt Nummer), wird abgelehnt –
sonst wandern Kundendaten ungeprüft in den zentralen Pool.
"""
from __future__ import annotations

import re
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import config, pool as pool_modul

ZUSATZSPALTEN = ["QueueId", "Zeitstempel", "Kundenkennung", "QueueStatus"]
STATUS_OFFEN = "offen"
STATUS_UEBERNOMMEN = "uebernommen"
STATUS_VERWORFEN = "verworfen"

#: Aufbau der Export-/Importdatei: (Spalte in der Queue, Überschrift in Excel)
EXPORT_SPALTEN: list[tuple[str, str]] = [
    ("QueueId", "Kennung"),
    ("ArtikelNrLieferant", "Artikelnummer"),
    ("BezArtikel1", "Bezeichnung 1"),
    ("BezArtikel2", "Bezeichnung 2"),
    ("BezArtikel3", "Bezeichnung 3"),
    ("BezArtikelLang", "Bezeichnung lang"),
    ("BezArtikelGruppe", "Artikelgruppe"),
    ("Lagerort", "Lagerort"),
    ("BezLagerort", "Lagerortbezeichnung"),
    ("LagerMin", "Lager Min"),
    ("LagerMax", "Lager Max"),
    ("LagerEinheit", "Einheit"),
    ("Werksnummer", "Werksnummer"),
    ("HerstellerNr", "Herstellernummer"),
    ("EAN", "EAN"),
    ("Lieferanten_alle", "Lieferant"),
    ("Kundenkennung", "Von Kunde"),
    ("Zeitstempel", "Eingegangen"),
]

#: Diese Felder identifizieren den Eintrag und werden beim Re-Import ignoriert.
NICHT_AENDERBAR = {"QueueId", "ArtikelNrLieferant", "Kundenkennung", "Zeitstempel"}

#: Zusätzliche Spalte im Export – reine Lesehilfe, kommt nicht zurück.
HINWEISSPALTE = "Zu klaeren"

_UEBERSCHRIFT_ZU_SPALTE = {ueber: spalte for spalte, ueber in EXPORT_SPALTEN}
_SPALTE_ZU_UEBERSCHRIFT = dict(EXPORT_SPALTEN)

_NUR_ZIFFERN_KURZ = re.compile(r"^\d{1,4}$")
#: Ein Wort aus mindestens drei Buchstaben – zwei davon sprechen für Fließtext.
_WORT = re.compile(r"^[A-Za-zÄÖÜäöüß]{3,}$")


def _sieht_nach_text_aus(nummer: str) -> bool:
    """Zwei oder mehr echte Wörter deuten auf einen Namen statt eine Nummer.

    Wichtig: Leerzeichen allein sind kein Grund – im Pool stehen über 5.000
    gültige Nummern der Form ``72 011 23``.
    """
    woerter = [t for t in nummer.split() if _WORT.match(t)]
    return len(woerter) >= 2

_sperre = threading.Lock()


def _pfad() -> Path:
    return Path(config.QUEUE_PFAD)


def _lesen_roh() -> pd.DataFrame:
    pfad = _pfad()
    if not pfad.exists():
        return pd.DataFrame()
    return pd.read_csv(
        pfad, sep=config.CSV_TRENNZEICHEN, dtype=str, encoding=config.CSV_KODIERUNG
    )


def _schreiben_roh(df: pd.DataFrame) -> None:
    pfad = _pfad()
    pfad.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(
        pfad, sep=config.CSV_TRENNZEICHEN, index=False,
        encoding=config.CSV_KODIERUNG, na_rep="",
    )


def _text(wert) -> str:
    if wert is None or (isinstance(wert, float) and pd.isna(wert)):
        return ""
    return str(wert).strip()


# ---------------------------------------------------------------------------
# Sammeln
# ---------------------------------------------------------------------------
def anhaengen(neuaufnahmen: list[dict], kundenkennung: str, job_id: str) -> int:
    """Neuaufnahmen mit Zeitstempel und Kundenkennung in die Queue schreiben."""
    if not neuaufnahmen:
        return 0

    jetzt = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    zeilen = []
    for i, eintrag in enumerate(neuaufnahmen, start=1):
        zeile = dict(eintrag)
        zeile["QueueId"] = f"{job_id}-{i:04d}"
        zeile["Zeitstempel"] = jetzt
        zeile["Kundenkennung"] = kundenkennung
        zeile["QueueStatus"] = STATUS_OFFEN
        zeilen.append(zeile)

    neu = pd.DataFrame(zeilen).astype(str).replace({"nan": None, "None": None, "": None})
    with _sperre:
        vorhanden = _lesen_roh()
        gesamt = pd.concat([vorhanden, neu], ignore_index=True) if len(vorhanden) else neu
        # Zusatzspalten hinten anstellen, damit die Pool-Spalten vorn stehen.
        spalten = [s for s in gesamt.columns if s not in ZUSATZSPALTEN] + [
            s for s in ZUSATZSPALTEN if s in gesamt.columns
        ]
        _schreiben_roh(gesamt[spalten])
    return len(zeilen)


def lesen(nur_offen: bool = False) -> pd.DataFrame:
    df = _lesen_roh()
    if len(df) and nur_offen and "QueueStatus" in df.columns:
        df = df[df["QueueStatus"].fillna(STATUS_OFFEN) == STATUS_OFFEN]
    return df


def zaehle_offen() -> int:
    return len(lesen(nur_offen=True))


# ---------------------------------------------------------------------------
# Qualitätsprüfung
# ---------------------------------------------------------------------------
def pruefe_eintrag(zeile) -> list[str]:
    """Was spricht dagegen, diese Zeile in den Pool zu übernehmen?

    Gibt eine (ggf. leere) Liste verständlicher Gründe zurück.
    """
    gruende: list[str] = []

    nummer = _text(zeile.get("ArtikelNrLieferant"))
    if not nummer:
        gruende.append("keine Artikelnummer")
    elif ";" in nummer:
        # Ein Semikolon heißt fast immer: hier ist eine Bezeichnung ins
        # Nummernfeld gerutscht.
        gruende.append("Semikolon in der Artikelnummer")
    elif _sieht_nach_text_aus(nummer):
        gruende.append("sieht nach Text aus, nicht nach Artikelnummer")
    elif _NUR_ZIFFERN_KURZ.match(nummer):
        gruende.append("rein numerisch mit hoechstens vier Ziffern")

    if not _text(zeile.get("BezArtikel1")):
        gruende.append("keine Bezeichnung")

    mn, mx = _text(zeile.get("LagerMin")), _text(zeile.get("LagerMax"))
    try:
        if mn and mx and float(mn.replace(",", ".")) > float(mx.replace(",", ".")):
            gruende.append("Lager Min ist groesser als Lager Max")
    except ValueError:
        gruende.append("Lager Min/Max ist keine Zahl")

    return gruende


def pruefbericht(queue_ids: list[str] | None = None) -> dict[str, list[str]]:
    """Prüfergebnis je QueueId für die offenen (bzw. gewählten) Einträge."""
    df = lesen(nur_offen=True)
    if not len(df):
        return {}
    if queue_ids is not None:
        df = df[df["QueueId"].isin({str(i) for i in queue_ids})]
    bericht = {}
    for _, zeile in df.iterrows():
        gruende = pruefe_eintrag(zeile)
        if gruende:
            bericht[str(zeile["QueueId"])] = gruende
    return bericht


# ---------------------------------------------------------------------------
# Export und Re-Import
# ---------------------------------------------------------------------------
def export_tabelle(nur_offen: bool = True) -> pd.DataFrame:
    """Bearbeitbare Sicht auf die Queue, für den Excel-Export."""
    spalten = [s for s, _ in EXPORT_SPALTEN]
    ueberschriften = [_SPALTE_ZU_UEBERSCHRIFT[s] for s in spalten]

    df = lesen(nur_offen=nur_offen)
    if not len(df):
        return pd.DataFrame(columns=ueberschriften + [HINWEISSPALTE])

    auszug = df.reindex(columns=spalten)
    auszug.columns = ueberschriften
    # Lesehilfe: was an dieser Zeile noch fehlt.
    auszug[HINWEISSPALTE] = [", ".join(pruefe_eintrag(z)) for _, z in df.iterrows()]
    return auszug


def import_tabelle(df: pd.DataFrame) -> dict:
    """Bearbeitete Datei zurück in die Queue einspielen.

    Abgeglichen wird über die Spalte ``Kennung``. Offene Einträge, die in der
    Datei fehlen, gelten als aussortiert und werden verworfen.
    """
    if df is None or not len(df):
        raise ValueError("Die hochgeladene Datei enthaelt keine Zeilen.")

    df = df.rename(columns=lambda s: str(s).strip())
    if "Kennung" not in df.columns:
        raise ValueError(
            "In der Datei fehlt die Spalte 'Kennung'. Bitte die Datei verwenden, "
            "die ueber 'Liste als Excel herunterladen' erzeugt wurde."
        )

    aenderbar = [
        (_UEBERSCHRIFT_ZU_SPALTE[u], u)
        for _, u in EXPORT_SPALTEN
        if _UEBERSCHRIFT_ZU_SPALTE[u] not in NICHT_AENDERBAR and u in df.columns
    ]

    with _sperre:
        queue = _lesen_roh()
        if not len(queue) or "QueueId" not in queue.columns:
            raise ValueError("Es liegen keine Eintraege zur Pruefung vor.")

        queue["QueueStatus"] = queue["QueueStatus"].fillna(STATUS_OFFEN)
        offen = set(queue.loc[queue["QueueStatus"] == STATUS_OFFEN, "QueueId"])

        aus_datei = {_text(k) for k in df["Kennung"] if _text(k)}
        unbekannt = sorted(aus_datei - set(queue["QueueId"]))

        aktualisiert = 0
        for _, zeile in df.iterrows():
            kennung = _text(zeile.get("Kennung"))
            if kennung not in offen:
                continue
            maske = queue["QueueId"] == kennung
            for spalte, ueberschrift in aenderbar:
                wert = _text(zeile.get(ueberschrift))
                queue.loc[maske, spalte] = wert or None
            aktualisiert += 1

        # Was der Prüfer aus der Datei gelöscht hat, gilt als aussortiert.
        entfernt = sorted(offen - aus_datei)
        if entfernt:
            queue.loc[queue["QueueId"].isin(entfernt), "QueueStatus"] = STATUS_VERWORFEN

        _schreiben_roh(queue)

    return {
        "aktualisiert": aktualisiert,
        "verworfen": len(entfernt),
        "unbekannt": unbekannt,
    }


# ---------------------------------------------------------------------------
# Verwerfen und Übernehmen
# ---------------------------------------------------------------------------
def _status_setzen(df: pd.DataFrame, ids: set[str], status: str) -> pd.DataFrame:
    df.loc[df["QueueId"].isin(ids), "QueueStatus"] = status
    return df


def verwerfen(queue_ids: list[str]) -> int:
    """Einträge als geprüft-und-verworfen markieren, ohne den Pool anzufassen."""
    ids = {str(i) for i in queue_ids}
    with _sperre:
        df = _lesen_roh()
        if not len(df) or "QueueId" not in df.columns:
            return 0
        betroffen = df["QueueId"].isin(ids) & (
            df["QueueStatus"].fillna(STATUS_OFFEN) == STATUS_OFFEN
        )
        anzahl = int(betroffen.sum())
        if anzahl:
            _schreiben_roh(_status_setzen(df, ids, STATUS_VERWORFEN))
        return anzahl


def in_pool_uebernehmen(queue_ids: list[str]) -> int:
    """Geprüfte Einträge an den Pool anhängen und in der Queue abhaken.

    Zuvor läuft die Qualitätsprüfung: Zeilen ohne Bezeichnung oder mit
    unplausibler Artikelnummer werden abgelehnt, damit kein Unsinn in den
    zentralen Pool wandert. Vom Pool wird vorher eine Sicherungskopie angelegt.
    """
    if not config.pool_schreibbar():
        raise ValueError(
            "In der Desktop-Fassung kann der Datenpool nicht veraendert werden. "
            "Das Uebernehmen geprueffter Neuaufnahmen erfolgt auf dem OrKan-Server."
        )

    ids = {str(i) for i in queue_ids}
    if not ids:
        return 0

    with _sperre:
        queue = _lesen_roh()
        if not len(queue) or "QueueId" not in queue.columns:
            return 0

        offen = queue["QueueStatus"].fillna(STATUS_OFFEN) == STATUS_OFFEN
        auswahl = queue[queue["QueueId"].isin(ids) & offen]
        if not len(auswahl):
            return 0

        # --- Qualitätsprüfung vor dem Schreiben ---
        maengel = []
        for _, zeile in auswahl.iterrows():
            gruende = pruefe_eintrag(zeile)
            if gruende:
                nummer = _text(zeile.get("ArtikelNrLieferant")) or "(ohne Nummer)"
                maengel.append(f"{nummer}: " + ", ".join(gruende))
        if maengel:
            gezeigt = maengel[:10]
            rest = len(maengel) - len(gezeigt)
            raise ValueError(
                f"{len(maengel)} von {len(auswahl)} Eintraegen sind noch nicht "
                "vollstaendig und wurden deshalb nicht uebernommen:\n• "
                + "\n• ".join(gezeigt)
                + (f"\n... und {rest} weitere." if rest else "")
                + "\n\nBitte die Liste herunterladen, ergaenzen und wieder "
                "einspielen – oder die betroffenen Zeilen verwerfen."
            )

        pool_pfad = Path(config.POOL_PFAD)
        pool_df = pd.read_csv(
            pool_pfad, sep=config.CSV_TRENNZEICHEN, dtype=str,
            encoding=config.CSV_KODIERUNG,
        )
        if "NeuAusKundenliste" not in pool_df.columns:
            pool_df["NeuAusKundenliste"] = "Nein"

        neu = auswahl.drop(columns=[s for s in ZUSATZSPALTEN if s in auswahl.columns])
        neu = neu.reindex(columns=pool_df.columns)

        sicherung = pool_pfad.with_suffix(
            f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"
        )
        shutil.copy2(pool_pfad, sicherung)

        erweitert = pd.concat([pool_df, neu], ignore_index=True)
        erweitert.to_csv(
            pool_pfad, sep=config.CSV_TRENNZEICHEN, index=False,
            encoding=config.CSV_KODIERUNG, na_rep="",
        )

        _schreiben_roh(_status_setzen(queue, ids, STATUS_UEBERNOMMEN))

    pool_modul.neu_laden()
    return len(auswahl)
