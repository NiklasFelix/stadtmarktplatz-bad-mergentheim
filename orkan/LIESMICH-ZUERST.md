# OrKan Artikel-Matching-Tool — Übergabepaket

**Fang mit `UEBERGABE.md` an.** Dort steht der ganze Ablauf.

## Was hier liegt

- `UEBERGABE.md` — **Hier anfangen**
- `CLAUDE.md` — Datenregeln – liest der Code-Chat automatisch
- `README.md` — Betrieb und Installation
- `EXPORT-ANFORDERUNGEN.md` — Referenz für den Datenpool-Chat
- `PROMPT-NEUE-DATEN-EINARBEITEN.md` — Aufgabe: neue Datenquelle
- `PROMPT-BILDNAMEN-ERGAENZEN.md` — Aufgabe: Bildnamen
- `PROMPT-FUER-DATENPOOL-CHAT.md` — Aufgabe: geprüfte Neuaufnahmen
- `requirements.txt` — Abhängigkeiten
- `pytest.ini` — Testkonfiguration
- `requirements-dev.txt` — Abhängigkeiten für die Tests
- `desktop.py` — Einstiegspunkt der Desktop-Fassung
- `orkan.spec` — Bauanleitung für die .exe
- `.gitignore` — was nicht in die Versionsverwaltung gehört
- `.dockerignore` — was nicht ins Docker-Abbild gehört
- `Dockerfile` — Server-Betrieb
- `docker-compose.yml` — Server-Betrieb
- `start.bat` — Einzelplatzstart unter Windows
- `daten/Datenpool_bereinigt.csv` — Der Datenpool – die eine Wahrheit
- `.claude/launch.json` — Startkonfiguration für den Entwicklungsserver

- `app/` — Die Anwendung
- `tests/` — Die Testsuite
- `werkzeuge/` — Prüf- und Packskripte
- `referenz/` — Originalskript und Formatvorlage – nicht ändern

## Erster Schritt

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m pytest -q
```

Alle Tests müssen grün sein. Danach `UEBERGABE.md` lesen.

## Was bewusst fehlt

- die virtuelle Umgebung (`.venv`) — wird oben neu angelegt
- die gebaute `.exe` (rund 62 MB) — wird mit einem Befehl erzeugt,
  siehe `UEBERGABE.md`, Schritt 5
- Sicherungskopien des Pools, alte Chat-Exporte, Aufzeichnungen
- die Prüf-Queue (`daten/neuaufnahmen_queue.csv`) — sie enthält
  Kundendaten und gehört nicht in eine Übergabe
- der Ordner `EXPORT CHAT INFOS` — er enthält nur eine zweite Kopie
  des Pools und entsteht mit einem Befehl:

  ```bash
  .venv/Scripts/python werkzeuge/chat_infos_packen.py
  ```
