"""Desktop-Fassung: Pfadauflösung, Schreibschutz des Pools, Portsuche."""
from __future__ import annotations

import socket

import pytest

import desktop
from app import config, queue_store


def test_portsuche_findet_freien_port():
    port = desktop.freier_port(8000)
    assert 8000 <= port < 8050
    # Der gemeldete Port muss tatsächlich belegbar sein.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", port))


def test_portsuche_weicht_auf_naechsten_port_aus():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as belegt:
        belegt.bind(("127.0.0.1", 0))
        belegt.listen(1)
        genommen = belegt.getsockname()[1]
        assert desktop.freier_port(genommen) != genommen


def test_portsuche_meidet_port_der_auf_allen_karten_belegt_ist():
    """Windows erlaubt sonst 127.0.0.1:P neben 0.0.0.0:P – zwei Server, ein Port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as wildcard:
        wildcard.bind(("", 0))
        wildcard.listen(1)
        belegt = wildcard.getsockname()[1]

        assert not desktop._port_frei(belegt)
        assert desktop.freier_port(belegt) > belegt


def test_portsuche_meldet_klaren_fehler_wenn_alles_belegt(monkeypatch):
    monkeypatch.setattr(desktop, "ANZAHL_VERSUCHE", 0)
    with pytest.raises(RuntimeError, match="keiner frei"):
        desktop.freier_port(8000)


def test_im_normalbetrieb_ist_der_pool_beschreibbar():
    assert not config.gebuendelt()
    assert config.pool_schreibbar()


def test_gebuendelt_erkennt_pyinstaller(monkeypatch):
    monkeypatch.setattr(config.sys, "frozen", True, raising=False)
    monkeypatch.setattr(config.sys, "_MEIPASS", "C:/irgendwo", raising=False)
    assert config.gebuendelt()
    assert not config.pool_schreibbar()


def test_desktop_verweigert_das_aendern_des_pools(monkeypatch):
    """Im Paket liegt der Pool schreibgeschützt – das muss klar gemeldet werden."""
    monkeypatch.setattr(config, "pool_schreibbar", lambda: False)
    with pytest.raises(ValueError, match="OrKan-Server"):
        queue_store.in_pool_uebernehmen(["irgendeine-id"])


def test_verwerfen_bleibt_im_desktop_moeglich(monkeypatch):
    """Verwerfen fasst den Pool nicht an und muss weiter funktionieren."""
    monkeypatch.setattr(config, "pool_schreibbar", lambda: False)
    assert queue_store.verwerfen(["gibtesnicht"]) == 0
