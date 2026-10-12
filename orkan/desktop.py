"""Startet das Artikel-Matching-Tool als Desktop-Programm.

Dieses Modul ist der Einstiegspunkt für die eingepackte ``.exe``. Es startet
den Dienst nur auf diesem Rechner (127.0.0.1), öffnet den Standardbrowser und
zeigt ein Fenster mit dem Betriebszustand.

Bewusst nicht im Netz erreichbar: Die Desktop-Fassung ist ein Einzelplatz-
Werkzeug. Für den Mehrbenutzerbetrieb gibt es das Server-Setup.
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

STARTPORT = 8000
ANZAHL_VERSUCHE = 50


def _port_frei(port: int) -> bool:
    """Ist der Port wirklich frei?

    Geprüft wird gegen alle Netzwerkkarten *und* gegen die lokale Adresse.
    Windows lässt sonst zu, dass wir uns auf ``127.0.0.1:8000`` legen, obwohl
    schon ein anderer Dienst auf ``0.0.0.0:8000`` lauscht – dann laufen zwei
    Server auf demselben Port und der Nutzer landet je nach Adresse beim
    falschen.
    """
    for adresse in ("", "127.0.0.1"):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((adresse, port))
            except OSError:
                return False
    return True


def freier_port(start: int = STARTPORT) -> int:
    """Ersten wirklich freien Port ab ``start`` suchen."""
    for port in range(start, start + ANZAHL_VERSUCHE):
        if _port_frei(port):
            return port
    raise RuntimeError(
        f"Zwischen Port {start} und {start + ANZAHL_VERSUCHE} war keiner frei."
    )


def _banner(url: str, artikel: int, benutzerdaten: Path) -> str:
    linie = "=" * 58
    return f"""
 {linie}
  OrKan Artikel-Matching-Tool
 {linie}

  Das Programm ist gestartet. Im Browser öffnet sich gleich:

      {url}

  Artikel im Datenpool:  {artikel:,}
  Ihre Ergebnisdateien:  {benutzerdaten}

  Neue Artikel prüfen:   {url}/admin/neuaufnahmen

  Falls sich kein Browser öffnet, geben Sie die Adresse oben
  von Hand ein.

  ZUM BEENDEN dieses Fenster schließen (oder Strg + C).

 {linie}
""".replace(",", ".")


def main() -> int:
    # Muss vor dem Import der Anwendung stehen: legt die Pfade fest.
    from app import config

    try:
        port = freier_port()
    except RuntimeError as fehler:
        print(f"\n  FEHLER: {fehler}\n")
        input("  Zum Schließen die Eingabetaste drücken ... ")
        return 1

    url = f"http://127.0.0.1:{port}"

    try:
        from app import pool as pool_modul
        from app.main import app

        anzahl = len(pool_modul.hole())
    except FileNotFoundError:
        print(
            "\n  FEHLER: Der Artikel-Datenpool wurde nicht gefunden.\n"
            "  Das Programmpaket ist unvollständig – bitte erneut anfordern.\n"
        )
        input("  Zum Schließen die Eingabetaste drücken ... ")
        return 1
    except Exception as fehler:  # pragma: no cover - Notausgang mit Meldung
        print(f"\n  FEHLER beim Start: {fehler}\n")
        input("  Zum Schließen die Eingabetaste drücken ... ")
        return 1

    print(_banner(url, anzahl, Path(config.ARBEITSVERZEICHNIS).parent))

    def browser_oeffnen() -> None:
        """Erst öffnen, wenn der Dienst wirklich antwortet.

        Ein fester Wartewert reicht auf einem langsamen Rechner nicht: Der
        Browser zeigt dann eine Fehlerseite, oder die Seite lädt zwar, aber
        die erste Abfrage läuft ins Leere.
        """
        for _ in range(120):  # bis zu 60 Sekunden
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.4)
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.5)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=browser_oeffnen, daemon=True).start()

    import uvicorn

    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    except KeyboardInterrupt:
        pass

    print("\n  Das Programm wurde beendet.")
    return 0


if __name__ == "__main__":
    # Die Prüfliste ist auch hier erreichbar – ohne Anmeldung, weil der Dienst
    # nur auf diesem Rechner lauscht. Der Datenpool bleibt schreibgeschützt:
    # gepflegt wird er ausschließlich auf dem OrKan-Server.
    os.environ.pop("ADMIN_USER", None)
    os.environ.pop("ADMIN_PASSWORT", None)
    sys.exit(main())
