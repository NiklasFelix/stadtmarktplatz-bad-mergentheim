"""Firmenlogo: wird ausgeliefert, wenn eines hinterlegt ist – sonst stört es nicht."""
from __future__ import annotations

import pytest

from app import main

# Ein winziges gültiges PNG (1x1 Pixel, transparent)
MINI_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)
MINI_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'


@pytest.fixture
def static_ordner(tmp_path, monkeypatch):
    """Ein eigenes Static-Verzeichnis mit der echten Oberfläche darin."""
    ziel = tmp_path / "static"
    ziel.mkdir()
    (ziel / "index.html").write_text(
        (main.STATIC / "index.html").read_text(encoding="utf-8"), encoding="utf-8"
    )
    monkeypatch.setattr(main, "STATIC", ziel)
    return ziel


# ---------------------------------------------------------------------------
# Ohne Logo
# ---------------------------------------------------------------------------
def test_ohne_logo_meldet_der_status_nichts(klient, static_ordner):
    assert klient.get("/api/status").json()["logo"] == ""


def test_ohne_logo_gibt_die_route_404(klient, static_ordner):
    assert klient.get("/logo").status_code == 404


def test_die_seite_laedt_auch_ohne_logo(klient, static_ordner):
    antwort = klient.get("/")
    assert antwort.status_code == 200
    assert "Artikelliste vervollständigen" in antwort.text


# ---------------------------------------------------------------------------
# Mit Logo
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "dateiname,inhalt,typ",
    [
        ("logo.svg", MINI_SVG, "image/svg+xml"),
        ("logo.png", MINI_PNG, "image/png"),
        ("logo.webp", b"RIFF0000WEBP", "image/webp"),
        ("logo.jpg", b"\xff\xd8\xff", "image/jpeg"),
    ],
)
def test_hinterlegtes_logo_wird_ausgeliefert(klient, static_ordner, dateiname, inhalt, typ):
    (static_ordner / dateiname).write_bytes(inhalt)

    adresse = klient.get("/api/status").json()["logo"]
    assert adresse.startswith("/logo?v=")
    antwort = klient.get("/logo")
    assert antwort.status_code == 200
    assert antwort.headers["content-type"].startswith(typ)
    assert antwort.content == inhalt


def test_svg_hat_vorrang_vor_png(klient, static_ordner):
    """Bei mehreren Dateien gewinnt das skalierbare Format."""
    (static_ordner / "logo.png").write_bytes(MINI_PNG)
    (static_ordner / "logo.svg").write_bytes(MINI_SVG)

    antwort = klient.get("/logo")
    assert antwort.headers["content-type"].startswith("image/svg+xml")
    assert antwort.content == MINI_SVG


def test_logo_darf_zwischengespeichert_werden(klient, static_ordner):
    (static_ordner / "logo.svg").write_bytes(MINI_SVG)
    assert "max-age" in klient.get("/logo").headers.get("cache-control", "")


def test_andere_dateien_im_static_ordner_sind_nicht_abrufbar(klient, static_ordner):
    """Die Route liefert nur die feste Logo-Datei, nichts sonst."""
    (static_ordner / "geheim.txt").write_text("nicht fuer die Oeffentlichkeit")

    assert klient.get("/logo").status_code == 404
    for pfad in ("/static/geheim.txt", "/geheim.txt", "/logo.svg"):
        assert klient.get(pfad).status_code >= 400, pfad


def test_oberflaeche_bindet_das_logo_ein(klient, static_ordner):
    """Die Seite enthält den Platzhalter, blendet ihn aber nur bei Bedarf ein."""
    seite = klient.get("/").text
    assert 'id="logo"' in seite
    assert "verborgen" in seite
    # Ohne festes src – die Adresse kommt mit Fassungsnummer aus /api/status.
    assert 'src="/logo"' not in seite


def test_ausgetauschtes_logo_bekommt_eine_neue_adresse(klient, static_ordner):
    """Sonst zeigt der Browser bis zu einen Tag lang das alte Logo."""
    import os, time

    datei = static_ordner / "logo.png"
    datei.write_bytes(MINI_PNG)
    vorher = klient.get("/api/status").json()["logo"]

    # Logo austauschen (mit deutlich anderem Zeitstempel)
    datei.write_bytes(MINI_PNG + MINI_PNG)
    os.utime(datei, (time.time() + 60, time.time() + 60))
    nachher = klient.get("/api/status").json()["logo"]

    assert vorher != nachher, "Die Adresse muss sich mit dem Logo ändern"


def test_svg_platzhalter_verdraengt_kein_echtes_png(klient, static_ordner):
    """Stolperstein aus der Praxis: ein liegengebliebenes logo.svg gewinnt."""
    (static_ordner / "logo.png").write_bytes(MINI_PNG)
    (static_ordner / "logo.svg").write_bytes(MINI_SVG)
    assert klient.get("/logo").content == MINI_SVG

    (static_ordner / "logo.svg").unlink()
    assert klient.get("/logo").content == MINI_PNG
