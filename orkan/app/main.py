"""FastAPI-Anwendung: Upload, Abgleich, Downloads, Admin-Bereich."""
from __future__ import annotations

import html
import io
import secrets
import time
import shutil
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

from . import (
    bildpool, config, export, felder, jobs, matching, parsing,
    pool as pool_modul, queue_store,
)

STATIC = Path(config.STATIC_PFAD)

#: Maximale Anzahl Reportzeilen, die an die Oberfläche gehen.
REPORT_ANZEIGE = 500


@asynccontextmanager
async def lebenszyklus(app: FastAPI):
    Path(config.ARBEITSVERZEICHNIS).mkdir(parents=True, exist_ok=True)
    jobs.aufraeumen()
    jobs.aufraeumen_starten()
    pool_modul.hole()  # Pool einmal vorladen, damit der erste Upload schnell ist.
    yield


# Kein /docs, /redoc und kein /openapi.json: die Anwendung soll von außen
# nichts über ihre Datenstruktur verraten.
app = FastAPI(
    title="OrKan Artikel-Matching",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lebenszyklus,
)


@app.exception_handler(ValueError)
def wert_fehler(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"fehler": str(exc)})


@app.exception_handler(FileNotFoundError)
def datei_fehler(request: Request, exc: FileNotFoundError) -> JSONResponse:
    """Hochgeladene Datei ist weg – etwa weil die Aufräumung dazwischenkam.

    ``FileNotFoundError`` ist kein ``ValueError``, fiel also bis dahin durch und
    endete als nackter Serverfehler. Die Meldungen sind aber bereits für den
    Anwender formuliert („Bitte laden Sie die Datei erneut hoch") und sollen
    ihn auch erreichen.
    """
    return JSONResponse(status_code=410, content={"fehler": str(exc)})


# ---------------------------------------------------------------------------
# Oberfläche
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def startseite() -> HTMLResponse:
    return HTMLResponse((STATIC / "index.html").read_text(encoding="utf-8"))


#: Erlaubte Logo-Dateien in app/static – die erste gefundene wird verwendet.
LOGO_DATEIEN = (
    ("logo.svg", "image/svg+xml"),
    ("logo.png", "image/png"),
    ("logo.webp", "image/webp"),
    ("logo.jpg", "image/jpeg"),
    ("logo.jpeg", "image/jpeg"),
)


def _logo() -> tuple[Path, str] | None:
    """Firmenlogo aus dem Static-Verzeichnis, falls hinterlegt.

    Fester Dateiname, kein Pfad aus einer Anfrage – damit ist hier kein
    Ausbruch aus dem Verzeichnis möglich.
    """
    for name, typ in LOGO_DATEIEN:
        datei = STATIC / name
        if datei.is_file():
            return datei, typ
    return None


def _logo_adresse() -> str:
    """Adresse des Logos mit Änderungszeitpunkt als Fassung, sonst leer."""
    gefunden = _logo()
    if gefunden is None:
        return ""
    datei, _ = gefunden
    return f"/logo?v={int(datei.stat().st_mtime)}"


@app.get("/logo")
def logo() -> FileResponse:
    """Das Firmenlogo ausliefern – wird auch als Symbol im Browsertab genutzt."""
    gefunden = _logo()
    if gefunden is None:
        raise HTTPException(status_code=404, detail="Kein Logo hinterlegt.")
    datei, typ = gefunden
    # Ein Logo ändert sich selten; einen Tag zwischenspeichern lassen.
    return FileResponse(datei, media_type=typ, headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/status")
def status() -> dict:
    return {
        "artikel_im_pool": len(pool_modul.hole()),
        # Adresse samt Fassung: Wird das Logo ausgetauscht, ändert sich die
        # Adresse mit – sonst zeigt der Browser bis zu einen Tag lang das alte.
        "logo": _logo_adresse(),
        "pruefliste": {
            "erreichbar": config.gebuendelt() or config.admin_aktiv(),
            "offen": queue_store.zaehle_offen(),
            "pool_beschreibbar": config.pool_schreibbar(),
        },
        "pdf_ki_aktiv": config.ki_pdf_aktiv(),
        "max_mb": config.MAX_UPLOAD_MB,
        "max_zeilen": config.MAX_ZEILEN,
        "felder": [
            {
                "name": f.name,
                "beschriftung": f.beschriftung,
                "aus_pool": bool(f.poolspalte),
            }
            for f in felder.FELDER
        ],
        "modi": list(matching.MODI),
        "bildpool": {
            "eingerichtet": bildpool.eingerichtet(),
            "aenderbar": bildpool.darf_gesetzt_werden(),
            "pfad": str(bildpool.pfad() or ""),
            "anzahl_bilder": bildpool.anzahl_bilder(),
        },
    }


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
@app.post("/api/upload")
async def hochladen(datei: UploadFile = File(...)) -> dict:
    name = Path(datei.filename or "liste").name
    endung = Path(name).suffix.lower()
    if endung not in (".xlsx", ".xlsm", ".xls", ".csv", ".pdf", ".txt", ".tsv"):
        raise ValueError(
            "Dieses Dateiformat können wir nicht lesen. "
            "Bitte laden Sie eine Excel-, CSV- oder PDF-Datei hoch."
        )

    job = jobs.anlegen(name)
    ziel = job.verzeichnis / f"upload{endung}"
    groesse = 0
    try:
        with ziel.open("wb") as f:
            while brocken := await datei.read(1024 * 1024):
                groesse += len(brocken)
                if groesse > config.MAX_UPLOAD_BYTES:
                    raise ValueError(
                        f"Die Datei ist größer als {config.MAX_UPLOAD_MB} MB. "
                        "Bitte teilen Sie die Liste auf."
                    )
                f.write(brocken)

        if groesse == 0:
            raise ValueError("Die hochgeladene Datei ist leer.")

        roh = parsing.lies_datei(ziel)
    except Exception:
        shutil.rmtree(job.verzeichnis, ignore_errors=True)
        raise
    finally:
        # Die hochgeladene Datei wird nach dem Einlesen sofort gelöscht.
        ziel.unlink(missing_ok=True)

    if roh.df.empty:
        shutil.rmtree(job.verzeichnis, ignore_errors=True)
        raise ValueError("In der Datei wurden keine Zeilen gefunden.")
    if len(roh.df) > config.MAX_ZEILEN:
        shutil.rmtree(job.verzeichnis, ignore_errors=True)
        raise ValueError(
            f"Die Liste hat {len(roh.df):,} Zeilen. Wir verarbeiten höchstens "
            f"{config.MAX_ZEILEN:,} Zeilen auf einmal.".replace(",", ".")
        )

    erkannt = parsing.erkenne_spalten(roh.df)
    jobs.rohdaten_sichern(job, roh.df)

    job.quelle = roh.quelle
    job.hinweis = roh.hinweis
    job.ki_genutzt = roh.ki_genutzt
    job.spalten = erkannt.verfuegbare_spalten
    job.zuordnung = erkannt.zuordnung
    job.unsicher = erkannt.unsicher
    job.zeilen = len(roh.df)

    vorschau = roh.df.head(5).astype(object).where(pd.notna(roh.df.head(5)), "")
    return {
        "job_id": job.id,
        "dateiname": job.dateiname,
        "quelle": job.quelle,
        "hinweis": job.hinweis,
        "ki_genutzt": job.ki_genutzt,
        "zeilen": job.zeilen,
        "spalten": job.spalten,
        "zuordnung": job.zuordnung,
        "unsicher": job.unsicher,
        "felder": parsing.ZIELFELDER,
        "vorschau": vorschau.astype(str).to_dict(orient="records"),
    }


# ---------------------------------------------------------------------------
# Verarbeitung
# ---------------------------------------------------------------------------
class VerarbeitenAnfrage(BaseModel):
    job_id: str
    zuordnung: dict[str, str] = Field(default_factory=dict)
    kundenkennung: str = ""
    #: Globaler Schalter „Fehlende Angaben aus dem Datenpool ergänzen".
    anreichern: bool = True
    #: Abweichender Modus je Feld: ergaenzen | pool | nur_kunde
    anreicherung_je_feld: dict[str, str] = Field(default_factory=dict)


@app.post("/api/verarbeiten")
def verarbeiten(anfrage: VerarbeitenAnfrage) -> dict:
    job = jobs.hole(anfrage.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Auftrag nicht gefunden.")

    zuordnung = {
        feld: spalte
        for feld, spalte in (anfrage.zuordnung or job.zuordnung).items()
        if spalte and spalte in job.spalten
    }
    if parsing.FELD_ARTIKELNUMMER not in zuordnung:
        raise ValueError(
            "Bitte wählen Sie die Spalte aus, in der die Artikelnummern stehen."
        )

    roh = jobs.rohdaten_laden(job)
    kundenliste = parsing.baue_kundenliste(roh, zuordnung)
    if kundenliste.empty:
        raise ValueError("In der gewählten Spalte stehen keine Artikelnummern.")

    kunde = jobs.sichere_kennung(anfrage.kundenkennung)
    pool = pool_modul.hole()
    anreicherung = matching.Anreicherung(
        aktiv=anfrage.anreichern,
        je_feld={
            feldname: modus
            for feldname, modus in (anfrage.anreicherung_je_feld or {}).items()
            if feldname in felder.NACH_NAME and modus in matching.MODI
        },
    )
    _t = time.perf_counter()
    ergebnis = matching.abgleich(kundenliste, pool, kunde=kunde, anreicherung=anreicherung)
    dauer_abgleich = time.perf_counter() - _t

    importtabelle = export.importtabelle_bauen(ergebnis.importzeilen)
    report = pd.DataFrame(
        ergebnis.reportzeilen,
        columns=[
            "Artikelnummer", "Status", "Bezeichnung", "Lieferanten_im_Pool",
            "MinMax", "Bild_vorhanden", "Von Ihnen", "Aus dem Datenpool",
        ],
    )

    _t = time.perf_counter()
    dateien = export.schreibe_importdatei(importtabelle, job.verzeichnis, kunde)
    dateien["report"] = export.schreibe_report(report, job.verzeichnis, kunde)
    dauer_dateien = time.perf_counter() - _t

    # Bilder, die in der Importdatei vorkommen, als ZIP dazulegen.
    _t = time.perf_counter()
    bilder = bildpool.packe(
        ergebnis.importzeilen, job.verzeichnis / f"Bilder_{kunde}.zip"
    )
    dauer_bilder = time.perf_counter() - _t
    if bilder.pfad is not None:
        dateien["bilder"] = bilder.pfad

    # Im Fenster der Desktop-Fassung sichtbar. Bei einer Rückfrage aus dem
    # Betrieb steht damit sofort fest, welcher Schritt die Zeit gekostet hat –
    # einmal dauerte ein Durchlauf drei Minuten statt einer halben Sekunde.
    print(
        f"  Abgleich {len(kundenliste)} Zeilen: {dauer_abgleich:.1f}s | "
        f"Dateien: {dauer_dateien:.1f}s | "
        f"Bilder ({bilder.anzahl}): {dauer_bilder:.1f}s",
        flush=True,
    )

    in_queue = queue_store.anhaengen(ergebnis.neuaufnahmen, kunde, job.id)

    # Die eingelesene Kundenliste wird nach der Verarbeitung nicht mehr gebraucht.
    jobs.rohdaten_loeschen(job)
    job.verarbeitet = True
    job.zuordnung = zuordnung
    job.ergebnis = {n: p.name for n, p in dateien.items()}

    anzeige = report.head(REPORT_ANZEIGE).astype(object)
    anzeige = anzeige.where(pd.notna(anzeige), "")

    return {
        "job_id": job.id,
        "zusammenfassung": {
            "gesamt": ergebnis.anzahl_gesamt,
            "gefunden": ergebnis.anzahl_gefunden,
            "neu": ergebnis.anzahl_neu,
            "ungueltig": ergebnis.anzahl_ungueltig,
            "in_importdatei": ergebnis.anzahl_verwertbar,
            "trefferquote": round(ergebnis.trefferquote * 100),
            "zur_pruefung": in_queue,
            "herkunft": ergebnis.herkunft_zaehler,
        },
        "report": anzeige.astype(str).to_dict(orient="records"),
        "report_gekuerzt": len(report) > REPORT_ANZEIGE,
        "downloads": {
            art: f"/api/download/{job.id}/{art}" for art in job.ergebnis
        },
        "bilder": {
            "eingerichtet": bildpool.eingerichtet(),
            "gepackt": bilder.anzahl,
            "fehlend": bilder.fehlend[:50],
            "fehlend_gesamt": len(bilder.fehlend),
            "groesse_mb": bilder.groesse_mb,
            "hinweis": bilder.abgebrochen,
        },
    }


class BildordnerAnfrage(BaseModel):
    pfad: str = ""


@app.post("/api/bildordner")
def bildordner_setzen(anfrage: BildordnerAnfrage) -> dict:
    """Bildordner festlegen und gleich zurückmelden, was darin liegt."""
    gesetzt = bildpool.setze_pfad(anfrage.pfad)
    return {
        "pfad": str(gesetzt or ""),
        "eingerichtet": bildpool.eingerichtet(),
        "anzahl_bilder": bildpool.anzahl_bilder(),
    }


@app.get("/api/download/{job_id}/{art}")
def herunterladen(job_id: str, art: str) -> FileResponse:
    job = jobs.hole(job_id)
    if job is None or not job.verarbeitet:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden.")
    name = job.ergebnis.get(art)
    if not name:
        raise HTTPException(status_code=404, detail="Datei nicht gefunden.")
    pfad = job.verzeichnis / name
    if not pfad.exists():
        raise HTTPException(
            status_code=410,
            detail="Die Datei wurde inzwischen gelöscht. Bitte laden Sie die Liste erneut hoch.",
        )
    typ = {
        ".csv": "text/csv; charset=utf-8",
        ".zip": "application/zip",
    }.get(
        pfad.suffix,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    return FileResponse(pfad, media_type=typ, filename=pfad.name)


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------
basic = HTTPBasic(auto_error=False)


def admin(anmeldung: HTTPBasicCredentials | None = Depends(basic)) -> str:
    # Desktop-Fassung: Der Dienst lauscht nur auf 127.0.0.1, es kommt also
    # ohnehin nur heran, wer am Rechner sitzt. Eine Anmeldung brächte hier
    # keinen Schutz – der Datenpool bleibt trotzdem schreibgeschützt.
    if config.gebuendelt():
        return "desktop"
    if not config.admin_aktiv():
        raise HTTPException(
            status_code=503,
            detail="Der Admin-Bereich ist nicht eingerichtet (ADMIN_USER/ADMIN_PASSWORT fehlen).",
        )
    kopf = {"WWW-Authenticate": "Basic"}
    if anmeldung is None:
        raise HTTPException(status_code=401, detail="Anmeldung nötig.", headers=kopf)
    passt = secrets.compare_digest(
        anmeldung.username, config.ADMIN_USER
    ) & secrets.compare_digest(anmeldung.password, config.ADMIN_PASSWORT)
    if not passt:
        raise HTTPException(status_code=401, detail="Anmeldung fehlgeschlagen.", headers=kopf)
    return anmeldung.username


@app.get("/admin/neuaufnahmen", response_class=HTMLResponse)
def admin_neuaufnahmen(nur_offen: bool = True, _: str = Depends(admin)) -> HTMLResponse:
    df = queue_store.lesen(nur_offen=nur_offen)
    return HTMLResponse(_queue_seite(df, nur_offen))


class QueueAktion(BaseModel):
    queue_ids: list[str]


@app.post("/admin/neuaufnahmen/uebernehmen")
def admin_uebernehmen(aktion: QueueAktion, _: str = Depends(admin)) -> dict:
    anzahl = queue_store.in_pool_uebernehmen(aktion.queue_ids)
    return {"uebernommen": anzahl, "artikel_im_pool": len(pool_modul.hole())}


@app.post("/admin/neuaufnahmen/verwerfen")
def admin_verwerfen(aktion: QueueAktion, _: str = Depends(admin)) -> dict:
    return {"verworfen": queue_store.verwerfen(aktion.queue_ids)}


@app.get("/admin/neuaufnahmen/export")
def admin_export(nur_offen: bool = True, _: str = Depends(admin)) -> FileResponse:
    """Offene Einträge als Excel-Datei zum Bearbeiten herunterladen."""
    tabelle = queue_store.export_tabelle(nur_offen=nur_offen)
    verzeichnis = Path(config.ARBEITSVERZEICHNIS) / "_export"
    verzeichnis.mkdir(parents=True, exist_ok=True)
    name = f"Neuaufnahmen_{datetime.now().strftime('%Y%m%d-%H%M')}.xlsx"
    pfad = export.schreibe_xlsx(tabelle, verzeichnis / name, "Neuaufnahmen")
    return FileResponse(
        pfad,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=name,
    )


@app.post("/admin/neuaufnahmen/import")
async def admin_import(datei: UploadFile = File(...), _: str = Depends(admin)) -> dict:
    """Bearbeitete Datei einspielen; fehlende Zeilen gelten als aussortiert."""
    name = Path(datei.filename or "liste.xlsx").name
    endung = Path(name).suffix.lower()
    if endung not in (".xlsx", ".xlsm", ".csv"):
        raise ValueError("Bitte die bearbeitete Excel- oder CSV-Datei hochladen.")

    inhalt = await datei.read()
    if not inhalt:
        raise ValueError("Die hochgeladene Datei ist leer.")

    puffer = io.BytesIO(inhalt)
    if endung == ".csv":
        tabelle = pd.read_csv(
            puffer, sep=config.CSV_TRENNZEICHEN, dtype=str,
            encoding=config.CSV_KODIERUNG,
        )
    else:
        tabelle = pd.read_excel(puffer, dtype=object)

    ergebnis = queue_store.import_tabelle(tabelle)
    ergebnis["offen"] = queue_store.zaehle_offen()
    ergebnis["unvollstaendig"] = len(queue_store.pruefbericht())
    return ergebnis


@app.post("/admin/pool/neuladen")
def admin_pool_neuladen(_: str = Depends(admin)) -> dict:
    return {"artikel_im_pool": len(pool_modul.neu_laden())}




_QUEUE_SPALTEN = [
    ("QueueId", "Kennung"),
    ("ArtikelNrLieferant", "Artikelnummer"),
    ("BezArtikel1", "Bezeichnung"),
    ("BezArtikelGruppe", "Artikelgruppe"),
    ("Lagerort", "Lagerort"),
    ("LagerMin", "Min"),
    ("LagerMax", "Max"),
    ("Lieferanten_alle", "Lieferant"),
    ("Kundenkennung", "Von Kunde"),
    ("Zeitstempel", "Eingegangen"),
    ("QueueStatus", "Status"),
]


#: Text für Schritt 3, je nachdem ob der Pool hier beschreibbar ist.
SCHRITT3_SERVER = """  <button onclick="alle(true)" class="zweit">Alle auswählen</button>
  <button onclick="alle(false)" class="zweit">Auswahl aufheben</button>
  <button onclick="senden('uebernehmen')">In Pool übernehmen</button>
  <button onclick="senden('verwerfen')" class="zweit">Verwerfen</button>"""

SCHRITT3_DESKTOP = """  <p class="hinweis" style="margin:0">
    In dieser Fassung lässt sich der Datenpool nicht ändern – er ist fest im
    Programm hinterlegt. Laden Sie die geprüfte Liste herunter und schicken Sie
    sie an OrKan; dort wird sie in den zentralen Datenpool übernommen.</p>
  <div style="margin-top:.8rem">
    <button onclick="alle(true)" class="zweit">Alle auswählen</button>
    <button onclick="alle(false)" class="zweit">Auswahl aufheben</button>
    <button onclick="senden('verwerfen')" class="zweit">Verwerfen</button>
  </div>"""


def _queue_seite(df: pd.DataFrame, nur_offen: bool) -> str:
    spaltenzahl = len(_QUEUE_SPALTEN) + 2  # Auswahlkästchen + Hinweisspalte
    offen_gesamt = 0
    unvollstaendig = 0

    if not len(df):
        zeilen = (
            f'<tr><td colspan="{spaltenzahl}" class="leer">'
            "Aktuell liegen keine Neuaufnahmen zur Prüfung vor.</td></tr>"
        )
    else:
        teile = []
        for _, zeile in df.iterrows():
            qid = html.escape(str(zeile.get("QueueId", "")))
            offen = str(zeile.get("QueueStatus", queue_store.STATUS_OFFEN)) == queue_store.STATUS_OFFEN
            gruende = queue_store.pruefe_eintrag(zeile) if offen else []
            if offen:
                offen_gesamt += 1
                if gruende:
                    unvollstaendig += 1

            zellen = "".join(
                "<td>{}</td>".format(
                    html.escape(
                        "" if pd.isna(zeile.get(s)) else str(zeile.get(s, ""))
                    )
                )
                for s, _ in _QUEUE_SPALTEN
            )
            box = (
                f'<input type="checkbox" class="auswahl" value="{qid}">' if offen else "–"
            )
            hinweis = (
                f'<td class="mangel">{html.escape(", ".join(gruende))}</td>'
                if gruende
                else '<td class="ok">vollständig</td>'
            )
            klasse = ' class="unvollstaendig"' if gruende else ""
            teile.append(f"<tr{klasse}><td>{box}</td>{zellen}{hinweis}</tr>")
        zeilen = "".join(teile)

    kopf = "".join(f"<th>{html.escape(t)}</th>" for _, t in _QUEUE_SPALTEN)
    beschreibbar = config.pool_schreibbar()
    schritt3_titel = (
        "Geprüfte Artikel in den Pool übernehmen" if beschreibbar
        else "Geprüfte Liste an OrKan übergeben"
    )
    schritt3_inhalt = SCHRITT3_SERVER if beschreibbar else SCHRITT3_DESKTOP
    umschalten = "false" if nur_offen else "true"
    umschalttext = "Alle anzeigen" if nur_offen else "Nur offene anzeigen"
    filtertext = "Nur offene Einträge." if nur_offen else "Alle Einträge."

    warnung = ""
    if unvollstaendig:
        warnung = (
            f'<div class="warnung"><strong>{unvollstaendig} von {offen_gesamt} '
            "offenen Einträgen sind noch unvollständig</strong> – meist fehlt die "
            "Bezeichnung, weil sie in der Kundenliste nicht enthalten war. "
            "Solche Zeilen werden bei der Übernahme abgelehnt. Laden Sie die Liste "
            "herunter, ergänzen Sie sie in Excel und spielen Sie sie wieder ein.</div>"
        )

    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Neuaufnahmen prüfen</title>
<style>
 :root{{--rand:#dcdfe3;--leise:#5b636d;--akzent:#0b6bcb;--warn:#9a6200;--gut:#137a4c}}
 *{{box-sizing:border-box}}
 body{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;
       padding:1.5rem;color:#16191d;background:#f5f6f7;line-height:1.5}}
 h1{{font-size:1.3rem;margin:0 0 .4rem}}
 .hinweis{{color:var(--leise);font-size:.88rem;margin:0 0 1rem}}
 .karte{{background:#fff;border:1px solid var(--rand);border-radius:10px;
         padding:1.1rem 1.25rem;margin-bottom:1rem}}
 .karte h2{{font-size:1rem;margin:0 0 .6rem}}
 .schritt{{display:inline-block;width:1.4rem;height:1.4rem;border-radius:50%;
           background:var(--akzent);color:#fff;text-align:center;line-height:1.4rem;
           font-size:.8rem;font-weight:700;margin-right:.45rem}}
 table{{border-collapse:collapse;width:100%;font-size:.82rem;background:#fff}}
 th,td{{border:1px solid var(--rand);padding:.35rem .5rem;text-align:left;
        vertical-align:top;white-space:nowrap}}
 th{{background:#f4f4f5;position:sticky;top:0;z-index:1}}
 .rollbar{{max-height:32rem;overflow:auto;border:1px solid var(--rand);border-radius:8px}}
 tr.unvollstaendig{{background:#fffaf0}}
 td.mangel{{color:var(--warn);white-space:normal;min-width:14rem}}
 td.ok{{color:var(--gut)}}
 td.leer{{text-align:center;color:var(--leise);padding:1.5rem}}
 button,.knopf{{font:inherit;border:0;border-radius:7px;padding:.5rem 1rem;
        cursor:pointer;background:var(--akzent);color:#fff;font-weight:600;
        text-decoration:none;display:inline-block}}
 button.zweit,.knopf.zweit{{background:#f0f1f3;color:#16191d;border:1px solid var(--rand);
        font-weight:500}}
 button:hover,.knopf:hover{{filter:brightness(.94)}}
 .warnung{{background:#fdf1dc;border:1px solid #f0d9a8;color:var(--warn);
           padding:.7rem 1rem;border-radius:8px;margin-bottom:1rem;font-size:.9rem}}
 .meldung{{padding:.7rem 1rem;border-radius:8px;margin-bottom:1rem;font-size:.9rem;
           white-space:pre-line;display:none}}
 .meldung.gut{{background:#e4f4ec;border:1px solid #b9e0cb;color:var(--gut)}}
 .meldung.schlecht{{background:#fbe9e9;border:1px solid #f0c4c4;color:#a92f2f}}
 input[type=file]{{font:inherit;font-size:.9rem}}
</style></head><body>

<h1>Neuaufnahmen prüfen</h1>
<p class="hinweis">Diese Artikel stammen aus Kundenlisten und sind
<strong>noch nicht</strong> im Datenpool. {filtertext}
<a href="/admin/neuaufnahmen?nur_offen={umschalten}">{umschalttext}</a></p>

<div id="meldung" class="meldung"></div>
{warnung}

<div class="karte">
  <h2><span class="schritt">1</span>Liste herunterladen und in Excel ergänzen</h2>
  <a class="knopf" href="/admin/neuaufnahmen/export">Als Excel herunterladen</a>
  <p class="hinweis" style="margin:.6rem 0 0">
    Ergänzen Sie fehlende Bezeichnungen und Gruppen. <strong>Zeilen, die kein
    echter Artikel sind, einfach löschen</strong> – sie gelten dann als verworfen.
    Die Spalten „Kennung" und „Artikelnummer" bitte unverändert lassen.</p>
</div>

<div class="karte">
  <h2><span class="schritt">2</span>Bearbeitete Datei wieder einspielen</h2>
  <input type="file" id="datei" accept=".xlsx,.xlsm,.csv">
  <button onclick="einspielen()">Einspielen</button>
</div>

<div class="karte">
  <h2><span class="schritt">3</span>{schritt3_titel}</h2>
  {schritt3_inhalt}
</div>

<div class="rollbar">
  <table><thead><tr><th></th>{kopf}<th>Prüfung</th></tr></thead>
  <tbody>{zeilen}</tbody></table>
</div>

<script>
function ids(){{return [...document.querySelectorAll('.auswahl:checked')].map(e=>e.value)}}
function alle(an){{document.querySelectorAll('.auswahl').forEach(e=>e.checked=an)}}

function zeige(text, gut){{
  const m = document.getElementById('meldung');
  m.textContent = text;
  m.className = 'meldung ' + (gut ? 'gut' : 'schlecht');
  m.style.display = 'block';
  window.scrollTo({{top:0, behavior:'smooth'}});
}}

async function senden(aktion){{
  const auswahl = ids();
  if(!auswahl.length){{zeige('Bitte zuerst Einträge auswählen.', false); return}}
  if(aktion === 'uebernehmen' &&
     !confirm(auswahl.length + ' Artikel in den Datenpool übernehmen?')) return;
  const r = await fetch('/admin/neuaufnahmen/' + aktion, {{
    method:'POST', headers:{{'Content-Type':'application/json'}},
    body: JSON.stringify({{queue_ids: auswahl}})}});
  const d = await r.json().catch(()=>({{}}));
  if(!r.ok){{zeige(d.fehler || d.detail || ('Fehler ' + r.status), false); return}}
  location.reload();
}}

async function einspielen(){{
  const f = document.getElementById('datei').files[0];
  if(!f){{zeige('Bitte zuerst die bearbeitete Datei auswählen.', false); return}}
  const formular = new FormData();
  formular.append('datei', f);
  const r = await fetch('/admin/neuaufnahmen/import', {{method:'POST', body: formular}});
  const d = await r.json().catch(()=>({{}}));
  if(!r.ok){{zeige(d.fehler || d.detail || ('Fehler ' + r.status), false); return}}
  let text = d.aktualisiert + ' Einträge übernommen';
  if(d.verworfen) text += ', ' + d.verworfen + ' gelöschte Zeilen verworfen';
  text += '. Noch offen: ' + d.offen;
  if(d.unvollstaendig) text += ' (davon ' + d.unvollstaendig + ' unvollständig)';
  if(d.unbekannt && d.unbekannt.length)
    text += '\\nUnbekannte Kennungen übersprungen: ' + d.unbekannt.length;
  sessionStorage.setItem('meldung', text);
  location.reload();
}}

window.addEventListener('DOMContentLoaded', () => {{
  const m = sessionStorage.getItem('meldung');
  if(m){{sessionStorage.removeItem('meldung'); zeige(m, true)}}
}});
</script>
</body></html>"""
