Ich setze das OrKan Artikel-Matching-Programm produktiv ein. Ich habe eine
Liste mit Bildnamen, die in den Datenpool sollen.

Im Anhang:

- **die Bildnamen-Liste**
- **Datenpool_bereinigt.csv** — der aktuelle Stand, **Grundlage der Arbeit**
- **EXPORT-ANFORDERUNGEN.md** — verbindliche Vorgaben für jeden Export
- **pool_pruefen.py** und **pool_vergleichen.py** — die beiden Prüfskripte

Bitte Abschnitt 5.7 (Bildnamen) und Abschnitt 4 (die drei unumstößlichen
Regeln) der Anforderungen lesen.

## Ausgangslage

| | |
|---|---|
| Artikel gesamt | 94.610 |
| davon **mit** Bildname | 78.426 (83 %) |
| davon **ohne** Bildname | **16.184** |
| verschiedene Bilddateien | 33.165 |

`Bild` ist Spalte 21 der 28.

---

## Auftrag

**Nur die Spalte `Bild` verändern.** Die anderen 27 Spalten bleiben Zeichen für
Zeichen, wie sie sind; keine Zeile kommt dazu, fällt weg oder wechselt die
Reihenfolge.

### 1. Zuordnung ausschließlich über `ArtikelNrLieferant`

Die Liste muss eine echte Zuordnung Artikelnummer → Bildname enthalten. Falls
nicht: **nachfragen statt raten.**

> **Bildnamen dürfen NICHT aus der Artikelnummer abgeleitet werden.** Nur 4,5 %
> der vorhandenen Bildnamen passen zur Nummer. Der Normalfall ist eine
> Artikelfamilie mit einem gemeinsamen Bild:
>
> ```
> 590801404, 590801405, 590801407, 590810405  ->  590800404_Detail.jpg
> ```
>
> Eine Regel wie „Artikelnummer + `_Detail.jpg`" erzeugt zehntausende Namen,
> zu denen keine Datei existiert.

### 2. Artikelnummern zeichengenau verbinden

Beide Tabellen als **Text** einlesen (`dtype=str`). Sonst wird aus
`0000100951687` ein `100951687` und aus `387500140020` ein `3,875E+11` — der
Abgleich bricht dann still zusammen. Siehe Abschnitt 4.3.

Weicht die Liste in der Schreibweise ab (`72011 23` statt `72 011 23`), bitte
**melden statt angleichen**.

### 3. Vorhandene Bildnamen bleiben stehen

**Nur leere Zellen füllen.** Steht schon ein Name und die Liste liefert einen
anderen, gilt der bestehende Eintrag. Bitte trotzdem zählen und melden, wie oft
das vorkam.

### 4. Form der Bildnamen

Reiner Dateiname **mit Endung**, kein Pfadanteil. Erlaubt: `.jpg`, `.jpeg`,
`.png`, `.webp`, `.jfif`, `.gif`, `.bmp`. Groß-/Kleinschreibung wie in der
Liste. Namen ohne oder mit anderer Endung nicht eintragen, sondern auflisten.

### 5. Unbekannte Artikelnummern

**Nicht anlegen.** Aus einer Bildnamen-Liste lässt sich kein Artikel bauen — es
fehlt die Bezeichnung. Diese Nummern als eigene Liste zurückgeben.

---

## Vor der Übergabe

```bash
python pool_pruefen.py Datenpool_bereinigt.csv
python pool_vergleichen.py alter_pool.csv Datenpool_bereinigt.csv
```

Beide müssen 0 liefern. `pool_vergleichen.py` darf **nur** bei `Bild`
Änderungen melden — jede andere geänderte Spalte ist ein Fehler.

---

## Was ich zurück brauche

1. `Datenpool_bereinigt.csv` — der vollständige neue Pool (weiterhin 94.610 Zeilen)
2. die Ausgabe beider Prüfskripte
3. Zeilen mit Bildname vorher / nachher
4. wie viele Bildnamen aus der Liste **nicht** zugeordnet werden konnten
5. die Artikelnummern aus der Liste, die es im Pool nicht gibt
6. die Bildnamen mit unbrauchbarer Form
7. in wie vielen Fällen bereits ein anderer Bildname im Pool stand

Ich prüfe hier anschließend gegen den echten Bildbestand, ob zu den neuen Namen
auch Dateien existieren.
