"""Abgleich der Kundenliste gegen den Datenpool.

Portiert aus ``referenz/abgleich_referenz.py``. Die fachlichen Entscheidungen
(Lagerort-Regeln, MinMax-Vorschlag, Feldbelegung der Importdatei) sind
unverändert übernommen. Abweichungen zur Referenz:

* Neue Artikel werden **nicht** in den Pool geschrieben, sondern nur in die
  Neuaufnahme-Queue gestellt (siehe ``queue_store.py``).
* Rein numerische Artikelnummern mit höchstens vier Ziffern gelten als ungültig
  und werden weder gematcht noch aufgenommen.
* ``minmax_von_aehnlichen`` liefert dasselbe Ergebnis wie die Referenz, arbeitet
  aber über vorberechnete Indizes statt über einen Vollscan je Artikel.
* **Kundenangaben haben Vorrang.** Früher kam bei einem gefundenen Artikel alles
  aus dem Pool (einzige Ausnahme: Lieferant). Jetzt entscheidet je Feld die
  :class:`Anreicherung`, wer gewinnt – und der Report weist die Herkunft aus.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import felder
from .pool import Datenpool
from .text import tokens

# ---------------------------------------------------------------------------
# Status-Werte für den Abgleich-Report
# ---------------------------------------------------------------------------
STATUS_GEFUNDEN = "GEFUNDEN"
STATUS_LIEFERANT_WAEHLEN = "GEFUNDEN – Lieferant wählen"
STATUS_NEU = "NEU AUFGENOMMEN – Prüfung nötig"
STATUS_UNGUELTIG = "UNGÜLTIGE NUMMER"

# ---------------------------------------------------------------------------
# Anreicherung: wer gewinnt bei einem Konflikt?
# ---------------------------------------------------------------------------
MODUS_ERGAENZEN = "ergaenzen"      # Standard: Kunde gilt, Pool füllt nur Lücken
MODUS_POOL = "pool"                # wo der Pool etwas hat, gewinnt der Pool
MODUS_NUR_KUNDE = "nur_kunde"      # für dieses Feld nie etwas aus dem Pool
MODI = (MODUS_ERGAENZEN, MODUS_POOL, MODUS_NUR_KUNDE)

HERKUNFT_KUNDE = "Kundenliste"
HERKUNFT_POOL = "Datenpool"
HERKUNFT_VORSCHLAG = "Vorschlag"   # aus ähnlichen Artikeln abgeleitet


@dataclass
class Anreicherung:
    """Einstellung für einen Durchlauf – wird nicht gespeichert."""

    #: Globaler Schalter „Fehlende Angaben aus dem Datenpool ergänzen".
    aktiv: bool = True
    #: Abweichender Modus je Feld; ohne Eintrag gilt ``MODUS_ERGAENZEN``.
    je_feld: dict[str, str] = field(default_factory=dict)

    def modus(self, feldname: str) -> str:
        if not self.aktiv:
            # Schalter aus: der Pool wird gar nicht herangezogen.
            return MODUS_NUR_KUNDE
        gewaehlt = self.je_feld.get(feldname, MODUS_ERGAENZEN)
        return gewaehlt if gewaehlt in MODI else MODUS_ERGAENZEN


#: Spalten der Importdatei mit fest vorgegebenem Inhalt.
FESTE_SPALTEN: dict[str, object] = {
    "Artikelnr.": np.nan,          # interne Nummer vergibt die Cloud
    "Lager/Gebäude": "Standard Lager",
    "EK-Preis": np.nan,
    "Abw. EK-Preis": np.nan,
    "Gewicht (Tara) in kg": np.nan,
    "Höhe": np.nan,
    "Breite": np.nan,
    "Länge": np.nan,
    "Wert in €": np.nan,
    "Satzart": "ST",
    "Bestellfähig": "True",
    "Bestand": "0",
    "Erstellt am": np.nan,
    "Geändert am": np.nan,
}

#: Pauschalwerte, wenn weder Kunde noch Pool eine Bestandsangabe liefern.
PAUSCHAL_MIN, PAUSCHAL_MAX, PAUSCHAL_EINHEIT = 1, 2, "Stück"

#: Rein numerische Nummern mit höchstens vier Ziffern sind keine Artikelnummern.
_UNGUELTIG = re.compile(r"^\d{1,4}$")


def normiere_artikelnummer(wert) -> str:
    """Trimmen und Großschreibung – die Normalisierung aus der Referenz."""
    if wert is None or (isinstance(wert, float) and pd.isna(wert)):
        return ""
    return str(wert).strip().upper()


def ist_ungueltige_nummer(artikelnummer_normiert: str) -> bool:
    return bool(_UNGUELTIG.match(artikelnummer_normiert))


# ---------------------------------------------------------------------------
# Lagerort-Regeln (1:1 aus der Referenz)
# ---------------------------------------------------------------------------
def lagerort(bez, gruppe) -> str:
    txt = f"{bez} {gruppe}".lower()
    if "press" in txt and "kupfer" in txt:
        return "Kupferpress"
    if ("löt" in txt or "loet" in txt) and "kupfer" in txt:
        return "Kupferloet"
    if "press" in txt and "edelstahl" in txt:
        return "Edelstahlpress"
    if "press" in txt and "c-stahl" in txt:
        return "C-Stahl-Press"
    if "mepla" in txt:
        return "Mepla"
    if "mapress" in txt:
        return "Mapress"
    if "gewindestange" in txt:
        return "Gewindestangen"
    if pd.notna(gruppe) and str(gruppe).strip():
        return str(gruppe).strip()[:24]
    return "Allgemein"


# ---------------------------------------------------------------------------
# MinMax-Vorschlag
# ---------------------------------------------------------------------------
def minmax_von_aehnlichen(pool: Datenpool, bez1, gruppe) -> tuple[int, int]:
    """Median ähnlicher Artikel: gleiche Artikelgruppe, sonst Bezeichnungs-Token.

    Ergebnisgleich zur Referenz, aber über den invertierten Token-Index des
    Pools statt über einen Vollscan.
    """
    anzahl = len(pool.kand_min)
    auswahl = np.arange(anzahl, dtype=np.int64)

    if pd.notna(gruppe):
        treffer = pool.gruppen_index.get(str(gruppe).strip().lower())
        if treffer is not None and len(treffer) >= 3:
            auswahl = treffer

    tok = tokens(bez1)
    if tok:
        ueberschneidung = np.zeros(anzahl, dtype=np.int32)
        for t in tok:
            positionen = pool.token_index.get(t)
            if positionen is not None:
                ueberschneidung[positionen] += 1
        aehnlichkeit = ueberschneidung[auswahl]
        if aehnlichkeit.size and aehnlichkeit.max() > 0:
            beste = auswahl[aehnlichkeit >= aehnlichkeit.max()]
            if len(beste) >= 3:
                auswahl = beste

    if auswahl.size:
        mn = np.nanmedian(pool.kand_min[auswahl])
        mx = np.nanmedian(pool.kand_max[auswahl])
    else:
        mn = mx = np.nan

    if pd.isna(mn):
        mn, mx = 1.0, 2.0
    hoch = max(mx, mn + 1) if pd.notna(mx) else mn * 2
    return int(round(mn)), int(round(hoch))


# ---------------------------------------------------------------------------
# Ergebnisstrukturen
# ---------------------------------------------------------------------------
@dataclass
class AbgleichErgebnis:
    importzeilen: list[dict] = field(default_factory=list)
    reportzeilen: list[dict] = field(default_factory=list)
    neuaufnahmen: list[dict] = field(default_factory=list)
    anzahl_gesamt: int = 0
    anzahl_gefunden: int = 0
    anzahl_neu: int = 0
    anzahl_ungueltig: int = 0
    #: Wie oft ein Feld aus welcher Quelle kam – für die Zusammenfassung.
    herkunft_zaehler: dict[str, int] = field(
        default_factory=lambda: {HERKUNFT_KUNDE: 0, HERKUNFT_POOL: 0, HERKUNFT_VORSCHLAG: 0}
    )

    @property
    def trefferquote(self) -> float:
        """Anteil der Nummern, die direkt im Pool gefunden wurden."""
        if not self.anzahl_gesamt:
            return 0.0
        return self.anzahl_gefunden / self.anzahl_gesamt

    @property
    def anzahl_verwertbar(self) -> int:
        """Zeilen, die in der Importdatei landen."""
        return self.anzahl_gefunden + self.anzahl_neu


#: Wörter, die im Pool anstelle einer leeren Zelle stehen. Sie bedeuten
#: „keine Angabe" und werden wie eine leere Zelle behandelt – sonst erschiene
#: bei 1.988 Artikeln die Einheit „leer" in der Importdatei des Kunden.
#: Bewusst nur Wörter: Zahlen wie ``0`` sind bei LagerMin gültige Werte.
POOL_PLATZHALTER = {"leer", "n/a", "na", "null", "keine", "none", "unbekannt"}


def _leer(wert) -> bool:
    if wert is None:
        return True
    if isinstance(wert, float) and pd.isna(wert):
        return True
    return not str(wert).strip()


def _wert(row, spalte, standard=np.nan):
    """Optionalen Wert aus der Kundenzeile holen; Leerwerte werden zu NaN."""
    wert = row.get(spalte, standard) if hasattr(row, "get") else standard
    return standard if _leer(wert) else wert


def _waehle(kundenwert, poolwert, modus: str, pool_herkunft: str):
    """Entscheidet je Feld, welcher Wert in die Importdatei kommt.

    Gibt ``(wert, herkunft)`` zurück; ``herkunft`` ist leer, wenn das Feld
    leer bleibt.
    """
    hat_kunde = not _leer(kundenwert)
    hat_pool = not _leer(poolwert)

    if modus == MODUS_NUR_KUNDE:
        return (kundenwert, HERKUNFT_KUNDE) if hat_kunde else (np.nan, "")
    if modus == MODUS_POOL:
        if hat_pool:
            return poolwert, pool_herkunft
        return (kundenwert, HERKUNFT_KUNDE) if hat_kunde else (np.nan, "")
    # MODUS_ERGAENZEN: Kundenangabe gilt, der Pool füllt nur Lücken.
    if hat_kunde:
        return kundenwert, HERKUNFT_KUNDE
    return (poolwert, pool_herkunft) if hat_pool else (np.nan, "")


def _poolwert(p, feld: felder.Feld):
    """Wert aus dem Pool-Datensatz für dieses Feld."""
    if not feld.poolspalte:
        return np.nan
    wert = p.get(feld.poolspalte)
    if not _leer(wert) and str(wert).strip().lower() in POOL_PLATZHALTER:
        # Das Wort steht im Pool anstelle einer leeren Zelle. Es ist keine
        # Angabe und darf nicht als Einheit beim Kunden landen.
        return np.nan
    if feld.name == "Lieferant" and not _leer(wert):
        # Im Pool steht eine Liste; der erste Eintrag gilt.
        return str(wert).split(";")[0].strip()
    return wert


def _neuaufnahme_bauen(pool: Datenpool, row, quelle: str) -> dict:
    """Nicht gefundenen Artikel aus Kundendaten befüllen (Feldbelegung der Referenz)."""
    bez1 = _wert(row, "Bezeichnung1")
    gruppe = _wert(row, "Artikelgruppe")
    mn, mx = minmax_von_aehnlichen(pool, bez1, gruppe)
    bez2 = _wert(row, "Bezeichnung2")
    ort = lagerort(f"{bez1} {'' if pd.isna(bez2) else bez2}", gruppe)
    lieferant = _wert(row, "Lieferant")

    # Kundenangaben zu Bestand und Lagerort haben Vorrang vor dem Vorschlag.
    kunde_min, kunde_max = _wert(row, "LagerMin"), _wert(row, "LagerMax")
    kunde_ort = _wert(row, "Lagerort")

    return {
        "ArtikelNrLieferant": str(row["Artikelnummer"]).strip(),
        "BezArtikel1": bez1,
        "BezArtikel2": bez2,
        "BezArtikel3": _wert(row, "Bezeichnung3"),
        "BezArtikelLang": _wert(row, "BezeichnungLang"),
        "KurzBezeichnung": _wert(row, "Matchcode"),
        "BezArtikelGruppe": gruppe,
        "Lager": "Standard Lager",
        "Lagerort": kunde_ort if not _leer(kunde_ort) else ort,
        "BezLagerort": _wert(row, "Lagerortbezeichnung", gruppe if pd.notna(gruppe) else ort),
        "LagerMin": kunde_min if not _leer(kunde_min) else mn,
        "LagerMax": kunde_max if not _leer(kunde_max) else mx,
        "LagerEinheit": _wert(row, "Einheit", PAUSCHAL_EINHEIT),
        "VpeEinheit": _wert(row, "MengeneinheitVPE"),
        "MengeProVPE": _wert(row, "Menge"),
        "Werksnummer": _wert(row, "Werksnummer"),
        "HerstellerNr": _wert(row, "Herstellernummer"),
        "EAN": _wert(row, "EAN"),
        # Bild bleibt bei Neuaufnahmen in den Pool immer leer – ein vom Kunden
        # gelieferter Bildname geht trotzdem in seine Importdatei.
        "Bild": np.nan,
        "Lieferanten_alle": lieferant,
        "Anz_Lieferanten": 1 if pd.notna(lieferant) else 0,
        "Vorkommen": 1,
        "Quellen": f"Kundenliste-{quelle}",
        "VermutlichTestdaten": "Nein",
        "HatKonflikt": "Nein",
        "KritischerKonflikt": "Nein",
        "NeuAusKundenliste": "Ja",
    }


def _importzeile_bauen(row, p, anreicherung: Anreicherung, ist_neu: bool):
    """Eine Zeile im 39-Spalten-Format, plus Herkunft je Feld."""
    zeile: dict = dict(FESTE_SPALTEN)
    herkunft: dict[str, str] = {}
    pool_herkunft = HERKUNFT_VORSCHLAG if ist_neu else HERKUNFT_POOL

    for f in felder.FELDER:
        kundenwert = _wert(row, f.name)
        wert, woher = _waehle(
            kundenwert, _poolwert(p, f), anreicherung.modus(f.name), pool_herkunft
        )
        zeile[f.importspalte] = wert
        if woher:
            herkunft[f.name] = woher

    # Die Artikelnummer ist der Schlüssel und kommt immer aus der Kundenliste.
    zeile["Artikelnummer des Lieferanten"] = str(row["Artikelnummer"]).strip()
    herkunft["Artikelnummer"] = HERKUNFT_KUNDE

    # Min und Max können aus verschiedenen Quellen stammen (etwa Min vom Kunden,
    # Max aus dem Pool) und dann nicht zusammenpassen. Ein Bestellvorschlag mit
    # Min über Max wäre unsinnig.
    _min, _max = pd.to_numeric(zeile["Lager Min"], errors="coerce"), pd.to_numeric(
        zeile["Lager Max"], errors="coerce"
    )
    if pd.notna(_min) and pd.notna(_max) and _min > _max:
        zeile["Lager Max"] = int(_min) + 1
        herkunft["LagerMax"] = HERKUNFT_VORSCHLAG

    # Pauschalwerte, falls weder Kunde noch Pool eine Bestandsangabe liefern.
    if _leer(zeile["Lager Min"]) and _leer(zeile["Lager Max"]):
        zeile["Lager Min"], zeile["Lager Max"] = PAUSCHAL_MIN, PAUSCHAL_MAX
        herkunft["LagerMin"] = herkunft["LagerMax"] = HERKUNFT_VORSCHLAG
        if _leer(zeile["Lagereinheit"]):
            zeile["Lagereinheit"] = PAUSCHAL_EINHEIT
            herkunft["Einheit"] = HERKUNFT_VORSCHLAG

    return zeile, herkunft


def _mehrere_lieferanten(p) -> bool:
    roh = p.get("Anz_Lieferanten")
    if roh is None or pd.isna(roh):
        return False
    try:
        return float(roh) > 1
    except (TypeError, ValueError):
        return False


#: So viele Feldnamen werden im Report ausgeschrieben, danach nur noch gezählt.
HERKUNFT_MAX_NAMEN = 6


def _herkunft_text(herkunft: dict[str, str], *gesucht: str) -> str:
    """Feldbeschriftungen einer Herkunft, für den Report – gekürzt lesbar."""
    namen = [
        felder.NACH_NAME[n].beschriftung.replace(" (nötig)", "")
        for n, wo in herkunft.items()
        if wo in gesucht and n in felder.NACH_NAME
    ]
    if len(namen) <= HERKUNFT_MAX_NAMEN:
        return ", ".join(namen)
    rest = len(namen) - HERKUNFT_MAX_NAMEN
    return ", ".join(namen[:HERKUNFT_MAX_NAMEN]) + f" und {rest} weitere"


def abgleich(
    kundenliste: pd.DataFrame,
    pool: Datenpool,
    kunde: str = "Kunde",
    anreicherung: Anreicherung | None = None,
) -> AbgleichErgebnis:
    """Kundenliste gegen den Pool abgleichen.

    ``kundenliste`` braucht die Spalte ``Artikelnummer``; alle weiteren Felder
    aus :mod:`app.felder` werden verwertet, wenn sie zugeordnet wurden.
    """
    if "Artikelnummer" not in kundenliste.columns:
        raise ValueError("Spalte 'Artikelnummer' fehlt in der Kundenliste.")

    anreicherung = anreicherung or Anreicherung()
    ergebnis = AbgleichErgebnis()

    for _, row in kundenliste.iterrows():
        anr = normiere_artikelnummer(row.get("Artikelnummer"))
        if not anr:
            continue  # Zeilen ohne Artikelnummer werden übergangen.
        ergebnis.anzahl_gesamt += 1
        anzeige = str(row.get("Artikelnummer")).strip()

        if ist_ungueltige_nummer(anr):
            ergebnis.anzahl_ungueltig += 1
            ergebnis.reportzeilen.append({
                "Artikelnummer": anzeige,
                "Status": STATUS_UNGUELTIG,
                "Bezeichnung": np.nan,
                "Lieferanten_im_Pool": np.nan,
                "MinMax": np.nan,
                "Bild_vorhanden": "Nein",
                "Von Ihnen": "",
                "Aus dem Datenpool": "",
            })
            continue

        treffer = pool.finde(anr)
        ist_neu = treffer is None
        if not ist_neu:
            p = treffer
            status = STATUS_LIEFERANT_WAEHLEN if _mehrere_lieferanten(p) else STATUS_GEFUNDEN
            ergebnis.anzahl_gefunden += 1
        else:
            p = pd.Series(_neuaufnahme_bauen(pool, row, kunde))
            ergebnis.neuaufnahmen.append(p.to_dict())
            status = STATUS_NEU
            ergebnis.anzahl_neu += 1

        zeile, herkunft = _importzeile_bauen(row, p, anreicherung, ist_neu)
        ergebnis.importzeilen.append(zeile)
        for wo in herkunft.values():
            ergebnis.herkunft_zaehler[wo] = ergebnis.herkunft_zaehler.get(wo, 0) + 1

        ergebnis.reportzeilen.append({
            "Artikelnummer": anzeige,
            "Status": status,
            "Bezeichnung": zeile["Bezeichnung1"],
            "Lieferanten_im_Pool": p.get("Lieferanten_alle"),
            "MinMax": f"{zeile['Lager Min']}/{zeile['Lager Max']}",
            "Bild_vorhanden": "Ja" if not _leer(zeile["Artikelbild"]) else "Nein",
            "Von Ihnen": _herkunft_text(herkunft, HERKUNFT_KUNDE),
            "Aus dem Datenpool": _herkunft_text(
                herkunft, HERKUNFT_POOL, HERKUNFT_VORSCHLAG
            ),
        })

    return ergebnis
