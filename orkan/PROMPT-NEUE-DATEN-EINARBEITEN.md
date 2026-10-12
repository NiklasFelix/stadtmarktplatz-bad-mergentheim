Ich setze das OrKan Artikel-Matching-Programm produktiv ein. Ich habe neue
Artikeldaten, die in den Datenpool eingearbeitet werden sollen.

Im Anhang:

- **die neuen Daten**
- **Datenpool_bereinigt.csv** — der aktuelle Stand, **Grundlage der Arbeit**
- **EXPORT-ANFORDERUNGEN.md** — verbindliche Vorgaben für jeden Export
- **pool_pruefen.py** — prüft, ob eine Pool-Datei in sich gültig ist
- **pool_vergleichen.py** — prüft, ob gegenüber dem alten Stand etwas
  verlorengegangen ist

**Bitte Abschnitt 4.0 der Anforderungen zuerst lesen: Grundlage ist die
beiliegende Pool-Datei, nicht eine eigene Kopie.**

**Weiter lesen**, besonders Abschnitt 1 (die Anwendung
ist fertig, kein Prompt für den Code-Chat), Abschnitt 4 (die drei
unumstößlichen Regeln) und Abschnitt 9 (was wie ein Fehler aussieht, aber
gewollt ist).

Ausgangslage: **94.610 Artikel, 28 Spalten**, 78.426 davon mit Bildname.

---

## Auftrag

Die neuen Daten in den Pool einarbeiten und den vollständigen Pool
zurückgeben.

**Beim Zusammenführen:**

- Kennt der Pool die Artikelnummer schon: Lücken füllen; vorhandene Werte nur
  ersetzen, wenn der neue Wert nachweislich besser ist — und das melden.
- Kennt der Pool sie nicht: neuer Artikel. **Ohne `BezArtikel1` wird kein
  Artikel angelegt.**
- Nicht anlegen: Nummern, die eine Bezeichnung sind (`Michael Seiler`), die ein
  Semikolon enthalten, oder die rein numerisch mit höchstens vier Ziffern sind.
- Neue Werte müssen den Feldregeln aus Abschnitt 5 genügen — besonders
  Einheiten (ausgeschrieben, keine Mengen im Feld), Satzart (`ST`), keine
  Platzhalterwörter, keine Steuerzeichen.

**Die drei Regeln, die nie gebrochen werden** (Abschnitt 4):

1. Kein Artikel darf verschwinden.
2. Kein gefülltes Feld darf leer werden.
3. Artikelnummern bleiben zeichengenau — beide Seiten mit `dtype=str` einlesen.

---

## Vor der Übergabe

```bash
python pool_pruefen.py Datenpool_bereinigt.csv
python pool_vergleichen.py alter_pool.csv Datenpool_bereinigt.csv
```

Beide müssen 0 liefern. Bleibt eine Meldung stehen, bitte begründen.

---

## Was ich zurück brauche

1. `Datenpool_bereinigt.csv` — der vollständige neue Pool
2. die Ausgabe beider Prüfskripte
3. eine kurze Änderungsübersicht: Zeilen vorher/nachher, davon neue Artikel,
   welche Quelle dazugekommen ist, wie viele Werte ersetzt wurden und warum,
   was **nicht** übernommen wurde und weshalb
4. falls das Programm etwas wissen muss: ein kurzer Absatz — kein Prompt
