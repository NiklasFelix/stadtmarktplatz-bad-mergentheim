# OrKan Artikel-Matching-Tool

Web-Anwendung für die OrKan-System GmbH. Ein SHK-Handwerksbetrieb lädt seine
Artikelliste hoch (Excel, CSV oder PDF) und bekommt sofort eine fertige
Importdatei für die OrKan-Cloud zurück – angereichert aus dem zentralen
Artikel-Datenpool mit rund 87.000 Artikeln.

Der Datenpool bleibt dabei ausschließlich auf dem Server. Kunden reichern nur
ihre eigenen Artikelnummern an; über keine Route ist der Pool ganz oder in
Teilen abrufbar.

## Schnellstart (lokal)

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements-dev.txt
```

```bash
.venv/Scripts/python -m uvicorn app.main:app --reload
```

Danach http://127.0.0.1:8000 im Browser öffnen.

Unter Linux/macOS liegen die Skripte statt in `.venv/Scripts` in `.venv/bin`.

## Betrieb mit Docker

```bash
docker compose up -d --build
```

Der Pool wird als Volume gemountet (`./daten`), das Image muss beim Austausch
also nicht neu gebaut werden.

Zugangsdaten und API-Key kommen aus der Umgebung – am einfachsten über eine
`.env`-Datei neben der `docker-compose.yml`:

```
ADMIN_USER=pruefer
ADMIN_PASSWORT=bitte-aendern
ANTHROPIC_API_KEY=sk-ant-...
```

> Die Anwendung bringt kein TLS mit. Auf dem OrKan-Server bitte hinter einen
> Reverse Proxy (nginx, Caddy, Traefik) mit HTTPS stellen.

## Datenpool aktualisieren

1. Neuen Stand aus dem Claude-Projekt „Datenpool" exportieren.
   `EXPORT-ANFORDERUNGEN.md` beschreibt, was der Export erfüllen muss – diesen
   Text vor dem Export in den Datenpool-Chat kopieren.
2. Neue Datei prüfen, **bevor** sie die alte ersetzt:

   ```bash
   .venv/Scripts/python werkzeuge/pool_pruefen.py neuer_pool.csv
   ```

   Rückgabewert 0 heißt einsetzbar. Geprüft werden BOM, Spaltenaufbau,
   Dubletten, zerstörte Nummern und Datenqualität.

   Enthält der Export neue Bildnamen, zusätzlich gegen den Bildbestand prüfen:

   ```bash
   .venv/Scripts/python werkzeuge/pool_pruefen.py neuer_pool.csv --bildordner D:/Bildpool
   ```

   Einzelne fehlende Bilder sind eine Warnung; fehlt die Mehrheit, stimmt die
   Zuordnung nicht und der Pool sollte so nicht übernommen werden.

   Und immer auch gegen den bisherigen Stand vergleichen — das findet
   verschwundene Artikel und geleerte Felder:

   ```bash
   .venv/Scripts/python werkzeuge/pool_vergleichen.py daten/Datenpool_bereinigt.csv neuer_pool.csv
   ```

   Rückgabewert 0 heißt: nichts verloren. Dubletten-Zusammenführung und die
   Umverteilung zwischen den Bezeichnungsfeldern kennt das Skript und meldet
   sie nur als Hinweis.

5. Für den schnellen Überblick – alle Kennzahlen in einem Aufruf, wahlweise mit
   Vergleich:

   ```bash
   .venv/Scripts/python werkzeuge/pool_bericht.py neuer_pool.csv --gegen daten/Datenpool_bereinigt.csv
   ```
3. `daten/Datenpool_bereinigt.csv` ersetzen.
4. Server bzw. Container neu starten – oder ohne Neustart:

```bash
curl -u "$ADMIN_USER:$ADMIN_PASSWORT" -X POST http://localhost:8000/admin/pool/neuladen
```

## Neuaufnahmen prüfen und ergänzen

Artikelnummern, die nicht im Pool stehen, erscheinen in der Importdatei des
Kunden **und** landen in `daten/neuaufnahmen_queue.csv` – mit Zeitstempel und
Kundenkennung. Sie werden **nicht** automatisch in den Pool geschrieben.

Der Ablauf unter `/admin/neuaufnahmen` (Basic Auth) ist dreistufig:

**1. Liste herunterladen.** „Als Excel herunterladen" liefert alle offenen
Einträge. Die Spalte **„Zu klaeren"** sagt je Zeile, was noch fehlt.

**2. In Excel ergänzen.** Bezeichnungen nachtragen, Artikelgruppe und Lagerort
korrigieren, Min/Max anpassen. **Zeilen, die kein echter Artikel sind, einfach
löschen** – sie gelten beim Einspielen als verworfen. Die Spalten „Kennung" und
„Artikelnummer" identifizieren den Eintrag und werden beim Einspielen ignoriert.

**3. Einspielen und übernehmen.** Die bearbeitete Datei hochladen, dann die
gewünschten Zeilen auswählen und „In Pool übernehmen".

### Die Qualitätsbremse

Vor dem Schreiben in den Pool prüft die Anwendung jede Zeile und lehnt ab, was
offensichtlich kein Artikel ist:

| Regel | Beispiel |
|---|---|
| keine Bezeichnung | Kundenliste enthielt nur Nummern |
| Semikolon in der Artikelnummer | `Evoflex Gr. 8; Bund Orange` |
| sieht nach Text aus (zwei Wörter) | `Michael Seiler` |
| rein numerisch, höchstens vier Ziffern | `123` |
| Lager Min größer als Lager Max | `9 / 3` |

Die Regeln sind gegen den echten Pool kalibriert: Nummern mit Leerzeichen
(`72 011 23`, 6.195 Stück) und ohne jede Ziffer (`QBSHNS`, 1.260 Stück) sind
gültig und werden **nicht** abgelehnt.

Die Meldung nennt die betroffenen Zeilen samt Grund; der Pool bleibt in diesem
Fall unverändert. Beim erfolgreichen Übernehmen wird vorher automatisch eine
Sicherungskopie angelegt (`Datenpool_bereinigt.backup-<Zeitstempel>.csv`).

> Diese Prüfung gibt es, weil ohne sie 123 Einträge ohne jede Bezeichnung in den
> Pool gelangt sind – darunter ein Personenname als Artikelnummer.

### Wo die Aufnahme in den Pool stattfinden sollte

Der Pool hat zwei mögliche Schreiber: diese Anwendung und den Datenpool-Chat,
aus dem der Pool exportiert wird. **Ein Neuexport ersetzt die ganze Datei** –
alles, was zwischenzeitlich hier übernommen wurde, wäre damit weg.

Deshalb die empfohlene Arbeitsteilung:

| Schritt | Wo |
|---|---|
| Sammeln | automatisch in dieser Anwendung |
| Prüfen und ergänzen | hier, in Excel (Schritt 1 und 2 oben) |
| **In den Pool aufnehmen** | **im Datenpool-Chat** |
| Neuen Pool einsetzen | Datei ersetzen, `POST /admin/pool/neuladen` |

Die fertige Anweisung dafür steht in `PROMPT-FUER-DATENPOOL-CHAT.md`; die
Spaltenzuordnung und die festen Werte stehen darin.

„In Pool übernehmen" in der Anwendung bleibt für den dringenden Einzelfall
nutzbar. Dann muss dieselbe Liste trotzdem in den Datenpool-Chat, sonst
verschwinden die Artikel beim nächsten Export.

## Was der Kunde ausfüllen kann

Im Bestätigungsschritt lassen sich **25 Zielspalten** zuordnen – neben
Artikelnummer, Lieferant und Bezeichnungen auch Bildname, Lagerort, Lagerplatz,
Lager Min/Max, Matchcode, Verwendungszweck, HTN-Code sowie die abweichende
Bestellmenge und -einheit.

**Kundenangaben haben Vorrang.** Was der Kunde mitliefert, steht in seiner
Importdatei; der Pool füllt nur die Lücken. Unter „Erweiterte Einstellungen"
lässt sich das je Feld umstellen:

| Auswahl | Bedeutung |
|---|---|
| **Meine Angabe gilt** (Standard) | Kundenwert gewinnt, Pool füllt Lücken |
| OrKan-Angabe bevorzugen | wo der Pool etwas hat, gewinnt der Pool |
| Nur meine Daten | für dieses Feld nie etwas aus dem Pool |

Dazu ein Schalter „Fehlende Angaben aus dem OrKan-Datenbestand ergänzen"
(standardmäßig an). Die Einstellung gilt nur für den einzelnen Durchlauf.

Der Abgleich-Report weist je Zeile aus, welche Felder vom Kunden kamen und
welche ergänzt wurden.

Bleibt MinMax nach Kundenangabe und Pool leer, gilt pauschal 1/2 mit Einheit
„Stück". Passen Min und Max aus verschiedenen Quellen nicht zusammen, wird Max
auf Min+1 gehoben.

## Bilder als ZIP

Zusätzlich zur Importdatei entsteht ein ZIP mit genau den Bildern, die dort in
der Spalte `Artikelbild` vorkommen – **jede Datei genau einmal**, auch wenn
mehrere Artikel dasselbe Bild nutzen. Bei einer Liste mit 400 Bildverweisen
waren das 165 Dateien, rund 2 % des Gesamtbestands.

### Wo der Bildordner herkommt

| Betriebsart | Bildordner |
|---|---|
| **Desktop-`.exe`** | im Programm eingebbar, wird gemerkt |
| **Einzelplatz (`start.bat`)** | im Programm eingebbar (`BILDPOOL_EINGABE=1` ist dort gesetzt) |
| **Server / Docker** | fest über `BILDPOOL_PFAD`, Eingabe gesperrt |

Ist die Eingabe frei, erscheint im Zuordnungsschritt der Bereich **„Bildordner"**:
Pfad einfügen, „Ordner übernehmen" – die Anwendung meldet zurück, wie viele
Bilder darin liegen, und merkt sich den Pfad für den nächsten Start.

> **Warum auf dem Server gesperrt:** Ein dort eingetippter Pfad zeigt auf den
> **Server**, nicht auf den Rechner des Kunden. Wäre er frei wählbar, könnte
> jemand `C:\Windows` eintragen und den Inhalt als ZIP herunterladen. Mit
> `BILDPOOL_EINGABE=1` lässt sich die Eingabe bewusst freischalten – nur tun,
> wenn niemand Fremdes an die Oberfläche kommt.

Nicht gefundene Bilder werden benannt, Anzahl und Größe vor dem Download
angezeigt. Ohne eingerichteten Bildordner entfällt der ZIP-Download.

## Firmenlogo

Die Logo-Datei liegt in `app/static/` und heißt `logo.svg`, `logo.png`,
`logo.webp` oder `logo.jpg` – die erste gefundene aus dieser Reihenfolge wird
verwendet. Sie erscheint links neben der Überschrift und dient zugleich als
Symbol im Browsertab.

Zum Austauschen: Datei ersetzen, Server neu starten. Der Browser bekommt
automatisch die neue Fassung, weil die Adresse den Änderungszeitpunkt trägt
(`/logo?v=…`). Für die Desktop-Fassung danach neu bauen.

> **Nur eine Logo-Datei behalten.** Liegt noch ein altes `logo.svg` neben einem
> neuen `logo.png`, gewinnt das SVG – das kostet sonst Suchzeit.

Ohne Logo-Datei bleibt die Überschrift wie bisher; es fehlt nichts.
Details stehen in `app/static/LIESMICH-logo.txt`.

## Umgebungsvariablen

| Variable | Standard | Zweck |
|---|---|---|
| `POOL_PFAD` | `daten/Datenpool_bereinigt.csv` | Pfad zum Datenpool |
| `QUEUE_PFAD` | `daten/neuaufnahmen_queue.csv` | Pfad zur Neuaufnahme-Queue |
| `ARBEITSVERZEICHNIS` | `arbeitsdaten` | Uploads und Ergebnisdateien |
| `ADMIN_USER` / `ADMIN_PASSWORT` | — | Basic Auth für `/admin/*`; ohne beides ist der Admin-Bereich gesperrt |
| `ANTHROPIC_API_KEY` | — | Ohne Key ist die KI-Auswertung von Scan-PDFs sauber deaktiviert |
| `ANTHROPIC_MODELL` | `claude-sonnet-5` | Modell für die PDF-Auswertung |
| `MAX_UPLOAD_MB` | `20` | Maximale Uploadgröße |
| `MAX_ZEILEN` | `20000` | Maximale Zeilen je Upload |
| `ERGEBNIS_TTL_STUNDEN` | `24` | Danach werden Ergebnisdateien gelöscht |
| `BILDPOOL_PFAD` | — | Verzeichnis mit den Artikelbildern; ohne Angabe kein Bild-ZIP |
| `MAX_ZIP_MB` | `500` | Obergrenze für das Bild-ZIP |
| `BILDPOOL_EINGABE` | aus | `1` erlaubt die Pfadeingabe in der Oberfläche |

## Datenschutz und Aufbewahrung

- Die hochgeladene Datei wird direkt nach dem Einlesen gelöscht.
- Die eingelesene Liste wird nach dem Abgleich gelöscht.
- Ergebnisdateien werden nach `ERGEBNIS_TTL_STUNDEN` (Standard 24 h) entfernt;
  ein Hintergrundprozess räumt stündlich auf.
- In der Queue bleiben nur die Neuaufnahme-Kandidaten samt Kundenkennung stehen.

## Tests

```bash
.venv/Scripts/python -m pytest -q
```

456 Tests decken ab: Spaltenerkennung (13 Header-Varianten plus Fallback-Heuristik),
Trennzeichen- und Encoding-Erkennung, Matching inklusive Normalisierung, die
Ungültige-Nummern-Regel, die MinMax-Ähnlichkeitslogik (Gleichheit zur
Referenzimplementierung, auch stichprobenartig gegen den echten Pool), die
Lagerort-Regeln, die Formatvalidierung der Ausgabe, Excel-Sicherheit bei langen
Nummern und führenden Nullen, das Einlesen von Tabellen-PDFs, den Admin-Bereich
den Prüf-Ablauf der Neuaufnahmen (Export, Re-Import, Qualitätsbremse), den
Prüfer für neue Pool-Exporte sowie alle fünf Abnahmekriterien.

`requirements-dev.txt` enthält die Testabhängigkeiten (u. a. `reportlab`, mit dem
die Test-PDFs erzeugt werden). Das Docker-Image installiert nur
`requirements.txt`.

## Aufbau

```
app/           Anwendung (siehe CLAUDE.md für die Modulübersicht)
daten/         Datenpool + Neuaufnahme-Queue (Volume im Docker-Setup)
referenz/      Originales Abgleichskript + verbindliche 39-Spalten-Vorlage
tests/         pytest
```

`CLAUDE.md` beschreibt Zweck, Datenregeln und die Matching-Logik im Detail.

## Das Programm einem Kollegen zur Verfügung stellen

**Der Datenpool darf nicht mitgehen.** Er ist deshalb in `.gitignore` ausgeschlossen
und wird nie Teil einer Weitergabe. Der Kollege bekommt entweder Zugriff auf eine
laufende Instanz oder den Quellcode ohne Daten.

### Variante 1 – gemeinsam testen (gleiches Netz)

`start.bat` doppelklicken. Die Anwendung lauscht dann im ganzen lokalen Netz;
das Fenster zeigt die Adresse an, die der Kollege im Browser öffnet
(z. B. `http://192.168.178.34:8000`). Beim ersten Start fragt die
Windows-Firewall einmalig nach – „Zugriff zulassen" für private Netzwerke.

Voraussetzung: beide im selben Netz (Büro-LAN, WLAN oder VPN).
Solange das Fenster offen bleibt, läuft der Dienst.

### Variante 2 – dauerhaft auf einem OrKan-Server (empfohlen)

```bash
docker compose up -d --build
```

Den Pool nach `daten/` legen, `.env` mit `ADMIN_USER` und `ADMIN_PASSWORT`
füllen, davor einen Reverse Proxy mit HTTPS. Danach erreichen alle Kollegen
die Anwendung dauerhaft unter einer festen Adresse – unabhängig davon, ob Ihr
Rechner läuft.

> Ohne Reverse Proxy läuft die Anwendung unverschlüsselt und **ohne Login**.
> Im internen Netz für einen Test vertretbar, im offenen Internet nicht.

### Variante 3 – Quellcode an einen Entwickler

```bash
git init && git add . && git commit -m "OrKan Artikel-Matching-Tool"
```

`.gitignore` hält Datenpool, Queue, Arbeitsdateien und die virtuelle Umgebung
heraus. Der Kollege legt seinen eigenen Pool nach `daten/` (siehe
`daten/LIESMICH.txt`) und startet mit:

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements-dev.txt
```

Ohne Datenpool laufen die Tests weiterhin durch – nur der Stichprobenvergleich
gegen den echten Pool wird übersprungen.

## Desktop-Fassung (eine .exe zum Verschicken)

Für Kollegen ohne Python-Installation lässt sich die Anwendung zu einer einzelnen
`.exe` packen: doppelklicken, der Browser öffnet sich, fertig.

```bash
.venv/Scripts/python -m PyInstaller orkan.spec --noconfirm
```

Das Ergebnis liegt danach unter `dist/OrKan-Artikel-Matching.exe`.

> ⚠️ **Nur für OrKan-Mitarbeiter.** Die `.exe` enthält den vollständigen
> Artikel-Datenpool. Solche Pakete lassen sich mit wenig Aufwand wieder
> auspacken — wer die Datei bekommt, hat den Artikelstamm. **Nicht an Kunden
> weitergeben.** Für Kunden bleibt der Browser-Zugriff auf eine zentrale
> Instanz der richtige Weg.

### Was der Empfänger braucht

**Nur die Datei `OrKan-Artikel-Matching.exe`** – sonst nichts. Kein Python, keine
Installation, nicht der Projektordner. Programmcode, alle Bibliotheken, der
Datenpool, die Formatvorlage und die Oberfläche stecken in der Datei.

Sie läuft aus jedem beliebigen Ordner (Desktop, Downloads, USB-Stick) und legt
neben sich nichts ab. Ergebnisse und Queue landen unter
`%LOCALAPPDATA%\OrKan-Matching\`.

Beim ersten Start meldet sich Windows SmartScreen („Der Computer wurde durch
Windows geschützt"), weil die Datei nicht signiert ist – über *Weitere
Informationen → Trotzdem ausführen* geht es weiter. Den Empfänger vorher darauf
hinweisen, sonst löscht er die Datei.

### Unterschiede zur Server-Fassung

| | Server / Docker | Desktop-`.exe` |
|---|---|---|
| Erreichbar für | alle im Netz | nur den eigenen Rechner (`127.0.0.1`) |
| Port | fest `8000` | erster freier ab `8000` |
| Datenpool | austauschbare Datei | fest eingebaut, schreibgeschützt |
| Neuaufnahmen | Queue + Übernahme in den Pool | Queue ja, Übernahme gesperrt |
| Admin-Bereich | vorhanden | deaktiviert |

Die Pflege des Datenpools bleibt bewusst dem Server vorbehalten. Änderungen an
einem eingebauten Pool wären beim Schließen des Programms ohnehin verloren.

### Wo die Dateien landen

Im Paket kann nicht geschrieben werden, deshalb liegen Ergebnisse und Queue im
Benutzerprofil:

```
%LOCALAPPDATA%\OrKan-Matching\arbeitsdaten\        Import- und Reportdateien
%LOCALAPPDATA%\OrKan-Matching\daten\neuaufnahmen_queue.csv
```

Die Ergebnisdateien werden auch hier nach 24 Stunden aufgeräumt.

### Neuen Datenpool einbauen

Der Pool steckt fest in der `.exe`. Für einen neuen Stand:
`daten/Datenpool_bereinigt.csv` ersetzen und neu bauen.

## Weitere Ideen für später

- **Nutzerkonten und Mandantentrennung.** V1 hat kein Login; jeder mit Zugriff
  auf die URL kann Listen hochladen. Für den Betrieb im offenen Netz nötig.
- **Lieferanten-Auswahl-UI.** Artikel mit mehreren Pool-Lieferanten werden im
  Report nur als „Lieferant wählen" markiert. V2: Auswahl direkt in der
  Oberfläche, bevor die Importdatei erzeugt wird.
- **Direkte Anbindung an die OrKan-Cloud-API.** Statt Download und manuellem
  Import die Artikel direkt in die Cloud schreiben.
- **Rückmeldung an den Pool.** Auswertung, welche Neuaufnahmen häufig auftreten,
  um den Pool gezielt zu ergänzen.
- **Dublettenprüfung über Bezeichnungen.** Aktuell wird nur über die
  Artikelnummer gematcht. Eine unscharfe Suche über Bezeichnung und EAN würde
  die Trefferquote weiter erhöhen.
- **Historie je Kunde.** Frühere Abgleiche einsehen und erneut herunterladen.
- **Ratenbegrenzung pro IP** als zusätzlicher Schutz gegen Massen-Uploads
  (heute greift nur das Zeilenlimit je Upload).
