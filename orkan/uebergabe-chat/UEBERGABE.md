# Übergabe: OrKan Artikel-Datenpool & Matching-Programm

Diese Anleitung beschreibt, wie das Projekt an eine Person außerhalb der
Organisation übergeben wird, sodass dort **ohne Rückfragen** weitergearbeitet
werden kann: neue Daten in den Pool einlesen (Chat) und das Programm
aktualisieren (Claude Code).

---

## 0. Was NICHT mitwandert — und deshalb in Dateien stehen muss

| Geht nicht mit | Ersatz |
|---|---|
| Der Claude-Chatverlauf | die Prompt-Dateien und EXPORT-ANFORDERUNGEN.md |
| Das Claude-Projekt selbst (Projekte lassen sich nur innerhalb derselben Organisation teilen) | Empfänger legt ein eigenes Projekt an, Anweisungen aus `PROJEKTANWEISUNG-DATENPOOL-CHAT.md` |
| Die Projekt-Anweisungen und gespeicherte Erinnerungen | dieselbe Datei |
| Der Bildpool (ca. 33.000 Dateien) | separat übergeben: Festplatte, Cloud-Ordner oder Freigabe |
| Zugangsdaten (Admin-Login, `BILDPOOL_PFAD`, evtl. API-Schlüssel) | nicht in die Übergabe packen — neu setzen lassen |

Alles, was heute nur „im Chat besprochen" wurde, ist bereits in den
Anforderungen und Prompts festgehalten. Prüfe vor dem Versand eine Sache: Wenn
dir beim Durchlesen der Anforderungen etwas fehlt, was du im Chat mündlich
geklärt hast, ergänze es dort — der Empfänger hat keinen Verlauf.

---

## 1. Zwei Pakete schnüren

### Paket A — Datenpool-Chat

Erzeugt `werkzeuge/chat_infos_packen.py`. Inhalt:

```
Datenpool-Chat/
  LIESMICH.md
  Datenpool_bereinigt.csv            <- aktueller Pool, 94.610 Artikel, 28 Spalten
  EXPORT-ANFORDERUNGEN.md            <- alle verbindlichen Regeln
  pool_pruefen.py
  pool_vergleichen.py
  PROMPT-NEUE-DATEN-EINARBEITEN.md
  PROMPT-BILDNAMEN-ERGAENZEN.md
  PROMPT-FUER-DATENPOOL-CHAT.md
  PROJEKTANWEISUNG-DATENPOOL-CHAT.md <- neu, siehe beiliegende Datei
  Beispiel/                          <- neu, siehe Abschnitt 3
    Vorher_Datenpool_bereinigt.csv
    Beispielquelle.xlsx
    Erwartetes_Ergebnis.md
```

### Paket B — Programm

Der Export aus Claude Code: der komplette Projektordner mit `CLAUDE.md`,
Anwendung, Tests, `werkzeuge/`, `Dockerfile`, README.
Vor dem Versand entfernen: `.env`, Ergebnis- und Upload-Ordner,
`neuaufnahmen_queue.csv` (enthält Kundendaten), alles unter `daten/`, was nicht
der Pool ist.

> **Vor dem Versand klären:** Der Pool enthält Artikeldaten aus Kundenlisten und
> ist zugleich das Betriebskapital hinter dem Produkt. Die Weitergabe an eine
> Person außerhalb der Organisation sollte vertraglich abgesichert sein
> (Geheimhaltung, Nutzungszweck) und mit der Geschäftsführung abgestimmt werden.

---

## 2. Was der Empfänger einrichtet

1. **Claude-Projekt anlegen** (eigene Organisation).
2. Den Inhalt von `PROJEKTANWEISUNG-DATENPOOL-CHAT.md` in die
   Projekt-Anweisungen kopieren.
3. Als Projektwissen hochladen: `EXPORT-ANFORDERUNGEN.md`, `pool_pruefen.py`,
   `pool_vergleichen.py`, die drei Prompt-Dateien.
   **Die Pool-CSV NICHT ins Projektwissen legen** — sie ändert sich bei jedem
   Durchlauf und wird pro Chat frisch mitgeschickt.
4. **Claude Code**: Paket B entpacken, Claude Code im Ordner starten. Die
   `CLAUDE.md` im Repo erklärt den Rest. `BILDPOOL_PFAD` auf den eigenen
   Bildordner setzen, Tests einmal laufen lassen.

---

## 3. Der Beispieldurchlauf — damit der Ablauf vergleichbar wird

Das ist das Stück, das den Unterschied macht: Der Empfänger muss einmal
**denselben Durchlauf mit demselben Ergebnis** hinbekommen, bevor er mit echten
Daten arbeitet. Lege dem Paket A einen Ordner `Beispiel/` bei:

- `Vorher_Datenpool_bereinigt.csv` — der Poolstand **vor** der letzten
  Einarbeitung
- `Beispielquelle.xlsx` — die Datei, die zuletzt eingearbeitet wurde
- `Erwartetes_Ergebnis.md` — die Zahlen, die dabei herauskamen:

```
Zeilen vorher / nachher    94.610 -> 94.610
Neue Artikel               0
Geänderte Felder           LagerEinheit 17, VpeEinheit 31, MengeProVPE 118,
                           AbwBestellmenge 118, AbwBestelleinheit 31
Nicht übernommen           283 Einheiten mit Menge im Feld (Box25 -> Box),
                           1 Bildname .tif, 6 widersprüchliche Doppelnummern,
                           3.922 Nummern ohne Bezeichnung
pool_pruefen.py            RC 0, eine Warnung (42 Zellen „Unbekannt"/„keine")
pool_vergleichen.py        RC 0, kein Datenverlust
```

Anleitung für den Empfänger: neuen Chat im Projekt öffnen,
`Vorher_Datenpool_bereinigt.csv` + `Beispielquelle.xlsx` + die vier
Standarddateien anhängen, `PROMPT-NEUE-DATEN-EINARBEITEN.md` als Nachricht
absenden. Kommen dieselben Zahlen heraus, ist der Ablauf reproduziert. Weichen
sie ab, fehlt eine Regel in den Anforderungen — dann dort nachtragen, nicht im
Chat mündlich klären.

---

## 4. Der laufende Ablauf nach der Übergabe

```
neue Daten
   |
   v
[Chat]  4 Standarddateien + neue Daten + passender Prompt
   |    -> neue Datenpool_bereinigt.csv + Ausgabe beider Prüfskripte
   v
[Code]  Pool-Datei in daten/ ersetzen, Anwendung neu starten
   |    -> pool_pruefen.py, optional --bildordner, Tests laufen lassen
   v
produktiv
```

Zwei Regeln, die den Ablauf stabil halten:

- **Der Pool aus dem letzten Chat ist die Grundlage des nächsten.** Nie eine
  ältere Kopie anhängen, nie „den Pool aus dem Gedächtnis" rekonstruieren
  lassen. Abschnitt 4.0 der Anforderungen sagt dasselbe.
- **Pro Chat genau eine Aufgabe.** Neue Datenquelle, Bildnamen oder geprüfte
  Neuaufnahmen — nicht mischen. Dafür gibt es die drei getrennten Prompts.

Wenn sich am Pool etwas ändert, das das Programm wissen muss (neue Spalte,
geänderte Schreibweisen), kommt aus dem Chat ein kurzer Absatz dazu. Der geht in
den Code-Chat — kein neuer Bauauftrag, die Anwendung ist fertig.

---

## 5. Übergabe-Checkliste

- [ ] Paket A erzeugt (`chat_infos_packen.py`), Beispiel-Ordner ergänzt
- [ ] `PROJEKTANWEISUNG-DATENPOOL-CHAT.md` beigelegt
- [ ] Poolstand in `LIESMICH.md` und in den Prompts auf den aktuellen Stand
      gebracht (Artikelzahl, Spaltenzahl, Bildabdeckung)
- [ ] Paket B bereinigt: keine `.env`, keine Kundendaten, keine Queue
- [ ] Bildpool separat übergeben, Pfad im Zielsystem gesetzt
- [ ] Beispieldurchlauf beim Empfänger einmal erfolgreich
- [ ] Ein gemeinsames Gespräch zur Übergabe: eine halbe Stunde entlang dieser
      Anleitung erspart zehn Rückfragen
- [ ] Geheimhaltung/Nutzungszweck geklärt
