# Übergabe: OrKan Artikel-Matching-Tool

Für die Person, die das Projekt weiterführt. Lies **nur dieses Dokument** zuerst —
danach weißt du, was du wo tust.

---

## Was das ist

SHK-Handwerksbetriebe laden ihre Artikelliste hoch (Excel, CSV, PDF). Die
Anwendung gleicht sie gegen einen zentralen Artikel-Datenpool ab und liefert
eine fertige Importdatei für die OrKan-Cloud, dazu einen Abgleich-Report und ein
ZIP mit den benötigten Artikelbildern.

Die Anwendung ist **fertig und im Einsatz**. Sie wird nicht neu gebaut. Was
regelmäßig passiert, ist etwas anderes: **Der Datenpool wächst.**

---

## Der Kreislauf — zwei Chats, klare Rollen

```
   ┌─────────────────────┐        Pool + Regeln + Aufgabe        ┌──────────────────┐
   │   DATENPOOL-CHAT    │  ◄────────────────────────────────────│   CODE-CHAT      │
   │   (claude.ai)       │                                       │   (Claude Code)  │
   │                     │        neuer Pool + Prüfausgaben      │                  │
   │ pflegt die Daten    │  ─────────────────────────────────────►  prüft, übernimmt│
   └─────────────────────┘                                       │  baut die .exe   │
                                                                  └──────────────────┘
```

**Datenpool-Chat** (ein normaler Chat auf claude.ai): Dort werden neue
Artikeldaten in den Pool eingearbeitet. Er kennt den Code nicht und soll ihn
nicht anfassen.

**Code-Chat** (Claude Code in diesem Ordner): Prüft jede Lieferung, übernimmt
sie, baut die `.exe`. Er ändert die Daten nur, wenn etwas nachweislich falsch
ist.

> **Die wichtigste Regel:** Der Datenpool-Chat arbeitet **immer** auf der
> Pool-Datei, die man ihm mitschickt — nie auf seiner eigenen alten Kopie. Das
> ist einmal schiefgegangen: Zurück kam ein Export, der 1.988 Platzhalter,
> 1.850 Nullen und 685 Einheiten-Codes wieder enthielt, alles längst korrigiert.

---

## Einmalig: Code-Chat einrichten

1. Ordner in Claude Code öffnen.
2. `CLAUDE.md` wird automatisch gelesen — dort stehen alle verbindlichen
   Datenregeln. Nichts weiter tun.
3. Umgebung herstellen:

   ```bash
   python -m venv .venv
   .venv/Scripts/pip install -r requirements.txt
   .venv/Scripts/python -m pytest -q
   ```

   Es müssen **alle** Tests grün sein. Ist das nicht so, stimmt etwas mit der
   Umgebung nicht — nicht weiterarbeiten.

---

## Einmalig: Datenpool-Chat einrichten

Neuen Chat auf claude.ai anlegen. Nichts weiter — der Chat bekommt bei jeder
Aufgabe alles Nötige mitgeschickt (siehe unten). Er braucht **kein**
Projektwissen und **keine** Vorgeschichte.

---

## Der wiederkehrende Ablauf

### Schritt 1 — Paket für den Datenpool-Chat erzeugen

```bash
.venv/Scripts/python werkzeuge/chat_infos_packen.py
```

Das füllt den Ordner `EXPORT CHAT INFOS` neu und meldet, wenn Zahlen in den
Anweisungen nicht mehr zum eingesetzten Pool passen. Rückgabewert 0 = in Ordnung.

### Schritt 2 — An den Datenpool-Chat schicken

Aus `EXPORT CHAT INFOS` **immer** diese vier:

| Datei | wofür |
|---|---|
| `Datenpool_bereinigt.csv` | die Arbeitsgrundlage |
| `EXPORT-ANFORDERUNGEN.md` | alle verbindlichen Regeln |
| `pool_pruefen.py` | ist die Datei in sich gültig? |
| `pool_vergleichen.py` | ist etwas verlorengegangen? |

Dazu **genau eine** Aufgaben-Nachricht, je nach Anlass:

| Anlass | Datei |
|---|---|
| Neue Artikeldaten einarbeiten | `PROMPT-NEUE-DATEN-EINARBEITEN.md` |
| Bildnamen nachtragen | `PROMPT-BILDNAMEN-ERGAENZEN.md` |
| Geprüfte Neuaufnahmen übernehmen | `PROMPT-FUER-DATENPOOL-CHAT.md` |

Den Text der Aufgaben-Nachricht in den Chat kopieren, die vier Dateien anhängen,
dazu die neuen Daten.

> **Gibst du eine Vorgabe-Datei mit** (etwa eine Excel mit gepflegten Bildnamen
> oder Einheiten), dann schreibe ausdrücklich dazu, dass **deren** Datenqualität
> gilt. Der Code-Chat hält sich sonst an die allgemeinen Regeln und meldet einen
> richtigen Export als falsch. Siehe Abschnitt 5.0 der Anforderungen.

### Schritt 3 — Lieferung prüfen (im Code-Chat)

Kommentarlos möglich — ein Befehl:

```bash
.venv/Scripts/python werkzeuge/pool_bericht.py NEUE_DATEI.csv --gegen daten/Datenpool_bereinigt.csv
```

Das zeigt in ~16 Zeilen: Aufbau, Nummernformate, Bilder, Einheiten, Mengen,
Satzart, Qualität — und was sich gegenüber dem Einsatzstand geändert hat.

Dann die beiden Prüfskripte:

```bash
.venv/Scripts/python werkzeuge/pool_pruefen.py NEUE_DATEI.csv
.venv/Scripts/python werkzeuge/pool_vergleichen.py daten/Datenpool_bereinigt.csv NEUE_DATEI.csv
```

**Beide müssen 0 liefern.** `pool_pruefen.py` erkennt auch einen Export, der auf
einer veralteten Kopie aufsetzt.

Optional, wenn neue Bildnamen dabei sind:

```bash
.venv/Scripts/python werkzeuge/pool_pruefen.py NEUE_DATEI.csv --bildordner PFAD\ZUM\BILDPOOL
```

### Schritt 4 — Übernehmen

```bash
cp daten/Datenpool_bereinigt.csv daten/Datenpool_bereinigt.backup-JJJJMMTT.csv
cp NEUE_DATEI.csv daten/Datenpool_bereinigt.csv
.venv/Scripts/python -m pytest -q
```

### Schritt 5 — `.exe` bauen

```bash
.venv/Scripts/python -m PyInstaller orkan.spec --noconfirm --clean
```

Ergebnis: `dist/OrKan-Artikel-Matching.exe`, rund 62 MB. Danach starten und
prüfen, dass die Artikelzahl stimmt.

Der erste Start dauert 10–15 Sekunden (Paket entpacken, Pool laden). Das Fenster
zeigt nach jedem Durchlauf eine Zeitmessung — praktisch bei Rückfragen aus dem
Betrieb.

---

## Was nie passieren darf

- **Der Pool verlässt den Server nie.** Kunden dürfen ihn weder herunterladen
  noch durchsuchen. Keine Route gibt ihn ganz oder in Teilen heraus.
- **Die `.exe` enthält den kompletten Artikelbestand** — unverschlüsselt. Nur
  für OrKan-Mitarbeiter, **nie für Kunden**. Für Kunden gibt es das Server-Setup.
- **Ungeprüfte Kundendaten ändern den Pool nicht.** Nicht gefundene Artikel
  gehen in eine Prüf-Queue und werden erst nach menschlicher Prüfung übernommen.
- **Artikelnummern bleiben zeichengenau.** `72 011 23` bleibt `72 011 23`. Wird
  das „vereinheitlicht", findet der Kunde seine Artikel nicht mehr.

Alle Datenregeln stehen vollständig in `CLAUDE.md` und werden vom Code-Chat
automatisch gelesen.

---

## Werkzeuge

| Werkzeug | Zweck |
|---|---|
| `werkzeuge/pool_bericht.py` | alle Kennzahlen in einem Aufruf, wahlweise mit Vergleich |
| `werkzeuge/pool_pruefen.py` | ist eine Pool-Datei in sich gültig? |
| `werkzeuge/pool_vergleichen.py` | ist gegenüber dem alten Stand etwas verlorengegangen? |
| `werkzeuge/chat_infos_packen.py` | Paket für den Datenpool-Chat erzeugen |

---

## Betriebsarten

| | Pool liegt | für wen |
|---|---|---|
| **Desktop-`.exe`** | fest im Paket | OrKan-Mitarbeiter |
| **Server / Docker** | als Volume, austauschbar ohne Rebuild | Kundenbetrieb |

Beim Server reicht `POST /admin/pool/neuladen` (Basic Auth), um einen neuen Pool
ohne Neustart einzulesen. Details in `README.md`.

---

## Wo was steht

| Datei | Inhalt |
|---|---|
| `CLAUDE.md` | Datenregeln, Aufbau, Umgebungsvariablen — liest der Code-Chat automatisch |
| `README.md` | Betrieb, Installation, Prüf-Ablauf der Neuaufnahmen |
| `EXPORT-ANFORDERUNGEN.md` | die Referenz für den Datenpool-Chat |
| `UEBERGABE.md` | dieses Dokument |
| `referenz/abgleich_referenz.py` | das produktiv erprobte Originalskript — **nicht ändern** |
| `referenz/Importformat_39_Spalten_Vorlage.csv` | das verbindliche Ausgabeformat — **nicht ändern** |
