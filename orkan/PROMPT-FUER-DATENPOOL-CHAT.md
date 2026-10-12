Ich setze das OrKan Artikel-Matching-Programm produktiv ein. Aus dem Betrieb
kommen **geprüfte Neuaufnahmen** zurück, die in den Datenpool sollen.

Im Anhang:

- **Neuaufnahmen_geprueft.xlsx** — die Liste, um die es geht
- **Datenpool_bereinigt.csv** — der aktuelle Stand, **Grundlage der Arbeit**
- **EXPORT-ANFORDERUNGEN.md** — verbindliche Vorgaben für jeden Export
- **pool_pruefen.py** und **pool_vergleichen.py** — die beiden Prüfskripte

Bitte Abschnitt 7 der Anforderungen lesen. Kurz: Ein Voll-Export von dort
ersetzt die ganze Pool-Datei — alles, was zwischenzeitlich in der Anwendung
hinzugefügt wurde, wäre sonst weg. Deshalb wird hier eingepflegt.

Ausgangslage: **94.610 Artikel, 28 Spalten**.

---

## Auftrag — die geprüften Neuaufnahmen einpflegen

### 1. Spalten zuordnen

| Spalte in der Excel-Datei | Zielspalte im Pool |
|---|---|
| Kennung | **nicht in den Pool** |
| Artikelnummer | `ArtikelNrLieferant` — Schlüssel, unverändert |
| Bezeichnung 1 | `BezArtikel1` |
| Bezeichnung 2 | `BezArtikel2` |
| Bezeichnung 3 | `BezArtikel3` |
| Bezeichnung lang | `BezArtikelLang` |
| Artikelgruppe | `BezArtikelGruppe` |
| Lagerort | `Lagerort` |
| Lagerortbezeichnung | `BezLagerort` |
| Lager Min | `LagerMin` |
| Lager Max | `LagerMax` |
| Einheit | `LagerEinheit` |
| Werksnummer | `Werksnummer` |
| Herstellernummer | `HerstellerNr` |
| EAN | `EAN` |
| Lieferant | `Lieferanten_alle` |
| Von Kunde | **nicht in den Pool** (nur für `Quellen`) |
| Eingegangen | **nicht in den Pool** |
| Zu klaeren | Lesehilfe der Anwendung, entfällt |

### 2. Die übrigen Poolspalten belegen

```
Lager                = Standard Lager
KurzBezeichnung      = ST
VpeEinheit           = leere Zelle
MengeProVPE          = leere Zelle
AbwBestellmenge      = leere Zelle
AbwBestelleinheit    = leere Zelle
Bild                 = LEER (siehe unten)
Anz_Lieferanten      = 1, wenn ein Lieferant genannt ist, sonst 0
Vorkommen            = 1
Quellen              = Kundenliste-<Von Kunde>
VermutlichTestdaten  = Nein
HatKonflikt          = Nein
KritischerKonflikt   = Nein
```

**`Bild` bleibt bei Neuaufnahmen immer leer.** Ein vom Kunden gelieferter
Bildname gehört in dessen Importdatei, aber nicht ungeprüft in den Pool — die
Datei müsste erst im Bildpool liegen.

Einheiten nach Abschnitt 5.1 schreiben (ausgeschrieben, keine Mengen im Feld).

### 3. Vor dem Einfügen prüfen

Zeilen, die dagegen verstoßen, gehören **nicht** in den Pool:

| Regel | Beispiel |
|---|---|
| keine Bezeichnung (`BezArtikel1` leer) | Kundenliste enthielt nur Nummern |
| Semikolon in der Artikelnummer | `Evoflex Gr. 8; Bund Orange` |
| zwei echte Wörter statt einer Nummer | `Michael Seiler` |
| rein numerisch mit höchstens vier Ziffern | `123` |
| `LagerMin` größer als `LagerMax` | `9 / 3` |
| Artikelnummer schon im Pool | Dublette — zusammenführen statt anhängen |

Gültig und **nicht** zu beanstanden: Nummern mit Leerzeichen (`72 011 23`),
ohne jede Ziffer (`QBSHNS`), mit führenden Nullen. Siehe Abschnitt 4.3.

---

## Vor der Übergabe

```bash
python pool_pruefen.py Datenpool_bereinigt.csv
python pool_vergleichen.py alter_pool.csv Datenpool_bereinigt.csv
```

Beide müssen 0 liefern.

---

## Was ich zurück brauche

1. `Datenpool_bereinigt.csv` — der vollständige neue Pool
2. die Ausgabe beider Prüfskripte
3. **welche Artikelnummern aufgenommen wurden** und welche nicht, mit Grund.
   Ohne diese Liste lässt sich in der Anwendung nicht abhaken, was erledigt ist.
4. Zeilen vorher / nachher, Dubletten zusammengeführt
