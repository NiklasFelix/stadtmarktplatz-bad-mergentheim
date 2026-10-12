"""Bilder heraussuchen und als ZIP packen.

Kernpunkte: nur die benötigten Dateien, jede genau einmal, kein Ausbruch aus
dem konfigurierten Verzeichnis, gleiches Ergebnis auf Windows und Linux.
"""
from __future__ import annotations

from pathlib import Path
import io
import zipfile

import pandas as pd
import pytest

from app import bildpool, config, matching


@pytest.fixture(autouse=True)
def sauberer_bildpool():
    bildpool.zuruecksetzen()
    yield
    bildpool.zuruecksetzen()


@pytest.fixture
def bildordner(tmp_path, monkeypatch):
    """Ein Bildpool mit ein paar Dateien, davon eine in einem Unterordner."""
    ordner = tmp_path / "bildpool"
    (ordner / "unterordner").mkdir(parents=True)
    for name, inhalt in [
        ("rohr.jpg", b"jpg-inhalt"),
        ("Winkel 45 RG.jpeg", b"jpeg-mit-leerzeichen"),
        ("GROSS.PNG", b"png-inhalt"),
        ("datenblatt.pdf", b"kein-bild"),
    ]:
        (ordner / name).write_bytes(inhalt)
    (ordner / "unterordner" / "tief.jpg").write_bytes(b"aus-unterordner")

    monkeypatch.setattr(config, "BILDPOOL_PFAD", str(ordner))
    return ordner


def _zeilen(*bildnamen):
    return [{"Artikelbild": n} for n in bildnamen]


def _inhalt(pfad):
    with zipfile.ZipFile(pfad) as z:
        return sorted(z.namelist())


# ---------------------------------------------------------------------------
# Bildnamen sammeln
# ---------------------------------------------------------------------------
def test_jede_datei_nur_einmal():
    """Im Pool teilen sich tausende Artikel dieselbe Bilddatei."""
    zeilen = _zeilen("a.jpg", "b.jpg", "a.jpg", "a.jpg", "b.jpg")
    assert bildpool.bildnamen_sammeln(zeilen) == ["a.jpg", "b.jpg"]


def test_gleicher_name_in_anderer_schreibweise_zaehlt_einmal():
    assert bildpool.bildnamen_sammeln(_zeilen("Rohr.jpg", "rohr.JPG")) == ["Rohr.jpg"]


@pytest.mark.parametrize("leer", [None, "", "   ", "nan", "None"])
def test_leere_bildnamen_werden_uebergangen(leer):
    assert bildpool.bildnamen_sammeln(_zeilen(leer, "echt.jpg")) == ["echt.jpg"]


def test_ohne_bilder_kein_zip(tmp_path):
    ergebnis = bildpool.packe(_zeilen(None, ""), tmp_path / "b.zip")
    assert ergebnis.pfad is None and ergebnis.anzahl == 0
    assert not (tmp_path / "b.zip").exists()


# ---------------------------------------------------------------------------
# Packen
# ---------------------------------------------------------------------------
def test_nur_die_benoetigten_bilder_landen_im_zip(bildordner, tmp_path):
    ergebnis = bildpool.packe(_zeilen("rohr.jpg", "rohr.jpg"), tmp_path / "b.zip")

    assert ergebnis.anzahl == 1
    assert _inhalt(ergebnis.pfad) == ["rohr.jpg"]
    assert ergebnis.fehlend == []
    assert ergebnis.groesse > 0


def test_bildnamen_mit_leerzeichen_funktionieren(bildordner, tmp_path):
    ergebnis = bildpool.packe(_zeilen("Winkel 45 RG.jpeg"), tmp_path / "b.zip")
    assert _inhalt(ergebnis.pfad) == ["Winkel 45 RG.jpeg"]


def test_suche_ignoriert_gross_und_kleinschreibung(bildordner, tmp_path):
    """Sonst entstünden auf Windows und Linux verschiedene ZIPs."""
    ergebnis = bildpool.packe(_zeilen("gross.png"), tmp_path / "b.zip")

    assert ergebnis.anzahl == 1
    # abgelegt unter dem Namen aus der Importdatei
    assert _inhalt(ergebnis.pfad) == ["gross.png"]


def test_unterordner_werden_durchsucht(bildordner, tmp_path):
    ergebnis = bildpool.packe(_zeilen("tief.jpg"), tmp_path / "b.zip")
    assert _inhalt(ergebnis.pfad) == ["tief.jpg"]


def test_fehlende_bilder_werden_gemeldet(bildordner, tmp_path):
    ergebnis = bildpool.packe(
        _zeilen("rohr.jpg", "gibtesnicht.jpg", "auchnicht.png"), tmp_path / "b.zip"
    )
    assert ergebnis.gepackt == ["rohr.jpg"]
    assert sorted(ergebnis.fehlend) == ["auchnicht.png", "gibtesnicht.jpg"]


def test_nichtbilder_werden_nicht_gefunden(bildordner, tmp_path):
    """Eine PDF im Bildordner ist kein Artikelbild."""
    ergebnis = bildpool.packe(_zeilen("datenblatt.pdf"), tmp_path / "b.zip")
    assert ergebnis.fehlend == ["datenblatt.pdf"]
    assert ergebnis.pfad is None


def test_ohne_eingerichteten_bildordner_gibt_es_eine_meldung(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "BILDPOOL_PFAD", "")
    ergebnis = bildpool.packe(_zeilen("rohr.jpg"), tmp_path / "b.zip")

    assert ergebnis.pfad is None
    assert ergebnis.fehlend == ["rohr.jpg"]
    assert "Bildordner" in ergebnis.abgebrochen


def test_groessengrenze_bricht_sauber_ab(bildordner, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "MAX_ZIP_MB", 0)
    ergebnis = bildpool.packe(_zeilen("rohr.jpg"), tmp_path / "b.zip")
    assert "MB" in ergebnis.abgebrochen


# ---------------------------------------------------------------------------
# Sicherheit: kein Ausbruch aus dem Bildordner
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "boesartig",
    [
        "../geheim.jpg",
        "..\\geheim.jpg",
        "../../windows/system32/config.jpg",
        "/etc/passwd.jpg",
        "C:\\Windows\\win.ini.jpg",
        "unterordner/../../geheim.jpg",
    ],
)
def test_kein_ausbruch_aus_dem_bildordner(bildordner, tmp_path, boesartig):
    # Eine Datei außerhalb des Bildpools, die nicht ins ZIP darf
    (bildordner.parent / "geheim.jpg").write_bytes(b"streng geheim")

    ergebnis = bildpool.packe(_zeilen(boesartig), tmp_path / "b.zip")

    assert ergebnis.gepackt == [], f"{boesartig} wurde gepackt"
    assert ergebnis.fehlend == [boesartig]
    assert ergebnis.pfad is None


def test_datei_ausserhalb_ist_auch_ueber_den_namen_nicht_erreichbar(bildordner, tmp_path):
    (bildordner.parent / "geheim.jpg").write_bytes(b"streng geheim")
    ergebnis = bildpool.packe(_zeilen("geheim.jpg"), tmp_path / "b.zip")
    assert ergebnis.gepackt == [] and ergebnis.fehlend == ["geheim.jpg"]


# ---------------------------------------------------------------------------
# Pfad setzen: nur in der Desktop-Fassung
# ---------------------------------------------------------------------------
def test_auf_dem_server_laesst_sich_der_pfad_nicht_setzen(tmp_path):
    assert not bildpool.darf_gesetzt_werden()
    with pytest.raises(ValueError, match="BILDPOOL_PFAD"):
        bildpool.setze_pfad(str(tmp_path))


def test_in_der_desktop_fassung_laesst_sich_der_pfad_setzen(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "gebuendelt", lambda: True)
    monkeypatch.setattr(config, "BENUTZERDATEN", tmp_path / "benutzer")

    ordner = tmp_path / "meine_bilder"
    ordner.mkdir()
    gesetzt = bildpool.setze_pfad(str(ordner))

    assert gesetzt == ordner.resolve()
    assert bildpool.eingerichtet()
    # und er wird für den nächsten Start gemerkt
    assert (tmp_path / "benutzer" / "einstellungen.json").exists()


def test_unbekannter_ordner_wird_abgelehnt(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "gebuendelt", lambda: True)
    monkeypatch.setattr(config, "BENUTZERDATEN", tmp_path / "benutzer")

    with pytest.raises(ValueError, match="nicht gefunden"):
        bildpool.setze_pfad(str(tmp_path / "gibtesnicht"))


# ---------------------------------------------------------------------------
# Zusammenspiel mit dem Abgleich
# ---------------------------------------------------------------------------
def test_zip_entsteht_aus_den_bildern_der_importdatei(pool, bildordner, tmp_path):
    liste = pd.DataFrame({
        "Artikelnummer": ["NEU-BILD-1", "NEU-BILD-2", "NEU-BILD-3"],
        "Bezeichnung1": ["Rohr", "Winkel", "Ohne Bild"],
        "Artikelbild": ["rohr.jpg", "Winkel 45 RG.jpeg", ""],
    })
    ergebnis = matching.abgleich(liste, pool)
    zip_ergebnis = bildpool.packe(ergebnis.importzeilen, tmp_path / "b.zip")

    assert sorted(zip_ergebnis.gepackt) == ["Winkel 45 RG.jpeg", "rohr.jpg"]
    assert zip_ergebnis.fehlend == []


def test_mehrere_artikel_mit_demselben_bild_ergeben_eine_datei(pool, bildordner, tmp_path):
    liste = pd.DataFrame({
        "Artikelnummer": [f"NEU-DOPP-{i}" for i in range(5)],
        "Bezeichnung1": ["Rohr"] * 5,
        "Artikelbild": ["rohr.jpg"] * 5,
    })
    ergebnis = matching.abgleich(liste, pool)
    zip_ergebnis = bildpool.packe(ergebnis.importzeilen, tmp_path / "b.zip")

    assert zip_ergebnis.anzahl == 1
    assert _inhalt(zip_ergebnis.pfad) == ["rohr.jpg"]


# ---------------------------------------------------------------------------
# Weg über die Weboberfläche
# ---------------------------------------------------------------------------
def test_zip_steht_zum_download_bereit(klient, bildordner):
    inhalt = (
        "Artikelnummer;Bezeichnung;Bildname\n"
        "NEU-WEB-1;Rohr;rohr.jpg\n"
        "NEU-WEB-2;Winkel;Winkel 45 RG.jpeg\n"
        "NEU-WEB-3;Fehlt;gibtesnicht.jpg\n"
    )
    hoch = klient.post(
        "/api/upload", files={"datei": ("l.csv", io.BytesIO(inhalt.encode()), "text/csv")}
    )
    job = hoch.json()
    antwort = klient.post("/api/verarbeiten", json={
        "job_id": job["job_id"], "zuordnung": job["zuordnung"], "kundenkennung": "Bildtest",
    })
    assert antwort.status_code == 200, antwort.text
    ergebnis = antwort.json()

    assert ergebnis["bilder"]["gepackt"] == 2
    assert ergebnis["bilder"]["fehlend"] == ["gibtesnicht.jpg"]
    assert ergebnis["bilder"]["groesse_mb"] >= 0
    assert "bilder" in ergebnis["downloads"]

    datei = klient.get(ergebnis["downloads"]["bilder"])
    assert datei.status_code == 200
    assert datei.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(datei.content)) as z:
        assert sorted(z.namelist()) == ["Winkel 45 RG.jpeg", "rohr.jpg"]


def test_ohne_bildordner_gibt_es_keinen_zip_download(klient, monkeypatch):
    monkeypatch.setattr(config, "BILDPOOL_PFAD", "")
    inhalt = "Artikelnummer;Bezeichnung;Bildname\nNEU-OHNE-1;Rohr;rohr.jpg\n"
    hoch = klient.post(
        "/api/upload", files={"datei": ("l.csv", io.BytesIO(inhalt.encode()), "text/csv")}
    )
    job = hoch.json()
    ergebnis = klient.post("/api/verarbeiten", json={
        "job_id": job["job_id"], "zuordnung": job["zuordnung"],
    }).json()

    assert "bilder" not in ergebnis["downloads"]
    assert ergebnis["bilder"]["eingerichtet"] is False
    assert ergebnis["bilder"]["fehlend"] == ["rohr.jpg"]


def test_bildordner_setzen_wird_auf_dem_server_abgelehnt(klient):
    antwort = klient.post("/api/bildordner", json={"pfad": "C:/Windows"})
    assert antwort.status_code == 400
    assert "BILDPOOL_PFAD" in antwort.json()["fehler"]


def test_status_meldet_den_bildpool(klient, bildordner):
    daten = klient.get("/api/status").json()["bildpool"]
    assert daten["eingerichtet"] is True
    assert daten["aenderbar"] is False


# ---------------------------------------------------------------------------
# Freischaltung der Pfadeingabe (BILDPOOL_EINGABE)
# ---------------------------------------------------------------------------
def test_ohne_freischaltung_ist_die_eingabe_gesperrt(monkeypatch):
    monkeypatch.setattr(config, "BILDPOOL_EINGABE", False)
    monkeypatch.setattr(config, "gebuendelt", lambda: False)
    assert not bildpool.darf_gesetzt_werden()


def test_freischaltung_erlaubt_die_eingabe(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "BILDPOOL_EINGABE", True)
    monkeypatch.setattr(config, "BENUTZERDATEN", tmp_path / "benutzer")
    assert bildpool.darf_gesetzt_werden()

    ordner = tmp_path / "bilder"
    ordner.mkdir()
    (ordner / "eins.jpg").write_bytes(b"x")
    assert bildpool.setze_pfad(str(ordner)) == ordner.resolve()
    assert bildpool.eingerichtet()


def test_desktop_fassung_braucht_keine_freischaltung(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "BILDPOOL_EINGABE", False)
    monkeypatch.setattr(config, "gebuendelt", lambda: True)
    assert bildpool.darf_gesetzt_werden()


# ---------------------------------------------------------------------------
# Bilder zählen
# ---------------------------------------------------------------------------
def test_bilder_werden_gezaehlt(bildordner):
    # rohr.jpg, Winkel 45 RG.jpeg, GROSS.PNG, unterordner/tief.jpg – die PDF nicht
    assert bildpool.anzahl_bilder() == 4


def test_ohne_ordner_werden_null_bilder_gemeldet(monkeypatch):
    monkeypatch.setattr(config, "BILDPOOL_PFAD", "")
    assert bildpool.anzahl_bilder() == 0


def test_endpunkt_meldet_die_bildzahl(klient, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "BILDPOOL_EINGABE", True)
    monkeypatch.setattr(config, "BENUTZERDATEN", tmp_path / "benutzer")
    ordner = tmp_path / "meine_bilder"
    ordner.mkdir()
    for n in ("a.jpg", "b.png", "c.txt"):
        (ordner / n).write_bytes(b"x")

    antwort = klient.post("/api/bildordner", json={"pfad": str(ordner)})
    assert antwort.status_code == 200, antwort.text
    daten = antwort.json()
    assert daten["anzahl_bilder"] == 2      # die .txt zählt nicht
    assert daten["eingerichtet"] is True
    assert daten["pfad"] == str(ordner.resolve())


def test_leerer_pfad_entfernt_den_ordner(klient, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "BILDPOOL_EINGABE", True)
    monkeypatch.setattr(config, "BENUTZERDATEN", tmp_path / "benutzer")
    ordner = tmp_path / "bilder"
    ordner.mkdir()
    klient.post("/api/bildordner", json={"pfad": str(ordner)})

    antwort = klient.post("/api/bildordner", json={"pfad": ""})
    assert antwort.json() == {"pfad": "", "eingerichtet": False, "anzahl_bilder": 0}


def test_status_meldet_die_bildzahl(klient, bildordner):
    daten = klient.get("/api/status").json()["bildpool"]
    assert daten["anzahl_bilder"] == 4
    assert daten["pfad"]


# ---------------------------------------------------------------------------
# Verzeichnisindex merken
# ---------------------------------------------------------------------------
# Aus der Praxis: Beim Kollegen dauerte ein Durchlauf drei Minuten statt einer
# halben Sekunde. Ursache war der Bildordner – er wurde bei jedem Statusaufruf
# und bei jedem Abgleich komplett neu durchsucht. Auf einem Netzlaufwerk ist
# jeder einzelne Dateizugriff ein Netzwerk-Rundlauf.
def test_der_ordner_wird_nicht_zweimal_durchsucht(tmp_path):
    ordner = tmp_path / "bilder"
    ordner.mkdir()
    (ordner / "rohr.jpg").write_bytes(b"x")
    bildpool.index_vergessen()

    assert bildpool.anzahl_bilder(ordner) == 1

    # Neue Datei – der gemerkte Index kennt sie noch nicht.
    (ordner / "bogen.jpg").write_bytes(b"x")
    assert bildpool.anzahl_bilder(ordner) == 1, "Der Index wurde neu aufgebaut"

    bildpool.index_vergessen()
    assert bildpool.anzahl_bilder(ordner) == 2


def test_ein_neuer_pfad_verwirft_den_gemerkten_index(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "BILDPOOL_EINGABE", True)
    erst = tmp_path / "erst"; erst.mkdir(); (erst / "a.jpg").write_bytes(b"x")
    zweit = tmp_path / "zweit"; zweit.mkdir()
    for i in range(3):
        (zweit / f"b{i}.jpg").write_bytes(b"x")

    bildpool.setze_pfad(str(erst))
    assert bildpool.anzahl_bilder() == 1

    bildpool.setze_pfad(str(zweit))
    assert bildpool.anzahl_bilder() == 3, "Der alte Index galt weiter"


def test_der_index_laeuft_nach_der_frist_ab(tmp_path, monkeypatch):
    ordner = tmp_path / "bilder"; ordner.mkdir()
    (ordner / "rohr.jpg").write_bytes(b"x")
    bildpool.index_vergessen()
    assert bildpool.anzahl_bilder(ordner) == 1

    (ordner / "bogen.jpg").write_bytes(b"x")
    monkeypatch.setattr(bildpool, "INDEX_GUELTIG_S", 0)
    assert bildpool.anzahl_bilder(ordner) == 2


def test_unterordner_und_grossschreibung_bleiben_wie_bisher(tmp_path):
    """Der schnellere Aufbau darf am Ergebnis nichts ändern."""
    ordner = tmp_path / "bilder"
    (ordner / "tief" / "tiefer").mkdir(parents=True)
    (ordner / "OBEN.JPG").write_bytes(b"x")
    (ordner / "tief" / "mitte.jpeg").write_bytes(b"x")
    (ordner / "tief" / "tiefer" / "unten.PNG").write_bytes(b"x")
    (ordner / "keinbild.txt").write_bytes(b"x")
    bildpool.index_vergessen()

    index = bildpool._index(ordner)
    assert set(index) == {"oben.jpg", "mitte.jpeg", "unten.png"}


def test_bei_gleichem_namen_gewinnt_weiterhin_der_erste_pfad(tmp_path):
    ordner = tmp_path / "bilder"
    (ordner / "a").mkdir(parents=True)
    (ordner / "b").mkdir(parents=True)
    (ordner / "a" / "rohr.jpg").write_bytes(b"aaa")
    (ordner / "b" / "rohr.jpg").write_bytes(b"bbb")
    bildpool.index_vergessen()

    assert bildpool._index(ordner)["rohr.jpg"].read_bytes() == b"aaa"


# ---------------------------------------------------------------------------
# Tests dürfen die echte Einstellung nicht anfassen
# ---------------------------------------------------------------------------
# Aus der Praxis: Ein Test rief setze_pfad() auf und schrieb damit in die
# Einstellungsdatei des Projekts. Danach zeigte der Bildordner des
# Entwicklungsservers auf ein pytest-Temp-Verzeichnis, das es nicht mehr gab –
# und das Bild-ZIP blieb leer.
def test_setze_pfad_schreibt_nicht_ins_projekt(tmp_path, monkeypatch):
    from app import config

    monkeypatch.setattr(config, "BILDPOOL_EINGABE", True)

    projektdatei = Path(__file__).resolve().parent.parent / "einstellungen.json"
    vorher = projektdatei.read_text(encoding="utf-8") if projektdatei.exists() else None

    ordner = tmp_path / "bilder"
    ordner.mkdir()
    bildpool.setze_pfad(str(ordner))

    nachher = projektdatei.read_text(encoding="utf-8") if projektdatei.exists() else None
    assert nachher == vorher, "Der Test hat die echte Einstellungsdatei verändert"
    # Geschrieben wurde stattdessen ins abgeschottete Verzeichnis.
    assert (Path(config.BENUTZERDATEN) / "einstellungen.json").exists()
