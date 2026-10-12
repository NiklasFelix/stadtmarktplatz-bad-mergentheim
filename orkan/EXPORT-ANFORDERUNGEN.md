# Datenpool — Anforderungen an jeden Export

**Dieses Dokument gehört bei jeder Pool-Aufgabe in den Datenpool-Chat.**

Es beschreibt, was ein Export erfüllen muss, damit die Anwendung ihn ohne
Nacharbeit übernehmen kann. Alle Zahlen stammen aus dem eingesetzten Pool
(Stand 27.08.2026) und alle Regeln aus Fehlern, die tatsächlich aufgetreten
sind.

Dazu gehören zwei Prüfskripte: `werkzeuge/pool_pruefen.py` und
`werkzeuge/pool_vergleichen.py`. Beide bitte mitschicken.

---

## 1. Wichtig vorab: Die Anwendung ist fertig

Sie läuft produktiv und ist durch **456 automatische Tests** abgesichert.

> **Bitte keinen Prompt für den Code-Chat schreiben.** Das ist einmal passiert:
> Zurück kam ein Auftrag, vier bereits gebaute Funktionen erneut zu
> programmieren. Wenn sich am Pool etwas ändert, das das Programm wissen muss,
> genügt ein **kurzer Absatz** in der Änderungsübersicht — keine
> Auftragsbeschreibung, kein Prompt.

**Was die Anwendung heute kann**, damit es nicht neu erfunden wird:

- Upload von Excel, CSV und PDF (bis 20 MB, bis 20.000 Zeilen); Trennzeichen,
  Zeichensatz und Spalten werden erkannt, der Kunde bestätigt die Zuordnung.
- **25 Zielspalten zuordenbar.** Kundenangaben haben Vorrang, der Pool füllt
  nur Lücken; je Feld umstellbar. Der Report weist die Herkunft je Feld aus.
- Abgleich gegen den Pool nach der Logik aus `abgleich_referenz.py`. 1.000
  Zeilen brauchen unter einer Sekunde.
- Ausgabe: Importdatei als `.xlsx` und `.csv` im geprüften 39-Spalten-Format,
  dazu ein Abgleich-Report und ein ZIP mit genau den benötigten Bildern.
- Nicht gefundene Artikel gehen in eine Prüf-Queue, nie automatisch in den Pool.
- Betrieb per Docker oder als eigenständige Windows-`.exe`.

---

## 2. Aktueller Stand des Pools

| | |
|---|---|
| Zeilen | **94.610** (Stand 27.08.) |
| Spalten | **28** |
| mit Bildname | 78.426 (83 %) — 33.165 verschiedene Dateien |
| ohne Bildname | 16.184 |
| Artikel ohne `BezArtikel1` | 0 |
| `LagerMin` > `LagerMax` | 0 |
| Dubletten in der Artikelnummer | 0, auch case-insensitiv |
| verschiedene Quellkennungen | 410 |

---

## 3. Format der Datei (hart — sonst startet die Anwendung nicht)

| Eigenschaft | Vorgabe |
|---|---|
| Dateiname | `Datenpool_bereinigt.csv` |
| Kodierung | **UTF-8 mit BOM** |
| Trennzeichen | Semikolon `;` |
| Textbegrenzer | Anführungszeichen `"` — **zwingend**, siehe 3.2 |
| Zeilenende | CRLF oder LF |
| Spaltenzahl | **28** |
| Schlüsselspalte | `ArtikelNrLieferant`, eindeutig, nie leer |

### 3.1 Die 28 Spalten in exakt dieser Reihenfolge

```
ArtikelNrLieferant;BezArtikel1;BezArtikel2;BezArtikel3;BezArtikelLang;
KurzBezeichnung;BezArtikelGruppe;Lager;Lagerort;BezLagerort;LagerMin;LagerMax;
LagerEinheit;VpeEinheit;MengeProVPE;AbwBestellmenge;AbwBestelleinheit;
Werksnummer;HerstellerNr;EAN;Bild;Lieferanten_alle;Anz_Lieferanten;Vorkommen;
Quellen;VermutlichTestdaten;HatKonflikt;KritischerKonflikt
```

(im Export in einer Zeile). Zusätzliche Spalten sind nicht erlaubt — Ausnahme:
`NeuAusKundenliste` darf als 29. am Ende stehen.

### 3.2 Semikolons stehen **in** den Werten — Quoting ist Pflicht

Ohne korrektes CSV-Quoting verrutschen dort alle Folgespalten:

| Spalte | betroffene Werte |
|---|---|
| `Quellen` | 71.550 |
| `Lieferanten_alle` | 13.345 |
| `BezArtikelLang` | 40 |
| `BezArtikel2` | 35 |
| `BezArtikel3` | 8 |
| `BezArtikel1` | 6 |

Export mit einer echten CSV-Bibliothek erzeugen (`pandas.to_csv`,
`csv.writer`) — nie durch Zusammenkleben von Strings.

### 3.3 Alle Nummernfelder als Text

Der folgenschwerste Exportfehler: Sobald eine Tabellenkalkulation eine lange
Nummer als Zahl behandelt, ist sie zerstört.

- `4,04478E+12` statt `4004478000123` — die Ziffern sind unwiederbringlich weg
- `100951687` statt `0000100951687` — führende Nullen fallen weg

Betroffene Spalten: **`ArtikelNrLieferant`**, `EAN`, `Werksnummer`,
`HerstellerNr`, `Bild`, `KurzBezeichnung`. Beim Einlesen immer `dtype=str`.

---

## 4. Die drei unumstößlichen Regeln

### 4.0 Grundlage ist immer die mitgeschickte Datei

**Bitte nie auf einer eigenen, älteren Kopie des Pools aufsetzen.** Der Pool
wird auch außerhalb dieses Chats gepflegt: Fehler werden korrigiert, Zeichen
repariert, Karteileichen entfernt. Eine Kopie von vor zwei Tagen kennt das
alles nicht.

Der Ausgangspunkt ist **ausschließlich** die `Datenpool_bereinigt.csv`, die
dieser Aufgabe beiliegt. Ist keine dabei, bitte danach fragen statt eine
vorhandene zu verwenden.

> Das ist einmal schiefgegangen: Zurück kam ein Export, der 1.988 Platzhalter,
> 1.850 Nullen, 685 Einheiten-Codes und 222 kaputte Steuerzeichen wieder
> enthielt — alles längst korrigiert. Erkennbar war es nur daran, dass
> `pool_vergleichen.py` gegen den eingesetzten Stand Verluste meldete.

**Selbsttest vor dem Beginn:** Enthält die vorliegende Datei irgendwo das Wort
`leer` als Wert, den Wert `0` in `MengeProVPE`, Einheiten-Kürzel wie `PR` oder
`LTR`, oder in `KurzBezeichnung` etwas anderes als `ST`? Dann ist es eine alte
Fassung — bitte melden statt damit zu arbeiten.

### 4.1 Kein Artikel darf verschwinden

Was heute im Pool steht, steht auch morgen darin. Ein Kunde, dessen
Artikelnummer plötzlich fehlt, bekommt sie als Neuaufnahme zurück statt als
Treffer.

*Ausnahme:* Dubletten, die sich nur in Groß-/Kleinschreibung unterscheiden
(`130S25` = `130s25`), dürfen zusammengeführt werden.

### 4.2 Kein gefülltes Feld darf leer werden

Ein vorhandener Wert darf durch einen besseren ersetzt werden — aber nie durch
nichts. Gilt für alle Felder, besonders Bezeichnungen, Bildnamen, Lieferanten.

*Ausnahmen:* Text, der bei der 25-Zeichen-Aufteilung in ein anderes
Bezeichnungsfeld desselben Artikels wandert; und die in Abschnitt 5 benannten
Platzhalterwerte.

### 4.3 Artikelnummern bleiben zeichengenau

Kein Entfernen von Leerzeichen, kein Auffüllen, kein „Vereinheitlichen":

| Schreibweise | Beispiel | im Pool |
|---|---|---|
| mit Leerzeichen als Gruppierung | `72 011 23` | 6.149 |
| führende Null | `0000100951687` | 5.695 |
| ganz ohne Ziffern (Lieferantenkürzel) | `QBSHNS` | 1.259 |
| lange reine Zahl (≥ 12 Stellen) | `387500140020` | 18.817 |
| mit Punkten | `01.001.90` | — |

Ein Export, der aus `72 011 23` ein `7201123` macht, zerstört die Zuordnung:
Der Kunde findet seinen Artikel nicht mehr wieder. `tests/test_nummernformate.py`
sichert das in der Anwendung ab.

Weicht eine neue Datenquelle in der Schreibweise ab, bitte **melden statt
automatisch angleichen**.

---

## 5. Feldregeln

### 5.0 Führende Quelle schlägt diese Regeln

Wird zu einer Aufgabe eine **Vorgabe-Datei** mitgeschickt — etwa eine Excel mit
gepflegten Bildnamen, Lagereinheiten und Mengen —, dann **gilt deren
Datenqualität**, nicht die Schreibweise-Regeln aus diesem Abschnitt. Die
Vorgabe wird in der Aufgabenstellung ausdrücklich benannt.

Am 27.08. war das so: Eine Excel gab `Bildname`, `LagerEinheit`, `MengeProVPE`
und `VpeEinheit` vor. Dadurch haben sich frühere Festlegungen geändert —
Box-Artikel führen wieder ihren Packungsinhalt statt `1`, und in zwei Feldern
steht `qm` statt `m²`. Das ist gewollt.

**Ohne** eine solche Vorgabe gelten weiterhin die Regeln unten.

### 5.1 Einheiten — `LagerEinheit`, `VpeEinheit`, `AbwBestelleinheit`

**Ausgeschrieben, nicht als Code.** Die früher enthaltenen Kürzel waren
Einheitenkennungen nach UN/ECE Recommendation 20:

| Code | UN/ECE | ausgeschrieben |
|---|---|---|
| `PCE` | piece | `Stück` |
| `MTR` | metre | `meter` |
| `PR` | pair | `Paar` |
| `LTR` | litre | `liter` |
| `SET` | set | `Set` |
| `KGM` | kilogram | `kilo` |
| `MTK` | square metre | `m²` |
| `DZN` | dozen | `Dutzend` |
| `MMT` | millimetre | `mm` |
| `CMK` | square centimetre | `cm²` |
| `CMQ` | cubic centimetre | `cm³` |
| `TNE` | tonne | `Tonne` |

**`VPE` bleibt `VPE`** — kein UN-Code, sondern die hausübliche Abkürzung für
Verpackungseinheit.

**Eine Schreibweise je Einheit.** Substantive groß: `Pack`, `Karton`, `Rolle`,
`Kanister`, `Stück`, `Dose`, `Stange`, `Flasche`. Singular, nicht Plural.

> **Offen:** Quadratmeter steht seit dem 27.08. uneinheitlich im Pool — `m²` in
> `LagerEinheit` (24×), `qm` in `VpeEinheit` und `AbwBestelleinheit` (je 30×).
> Das kam mit der Vorgabe-Excel (Abschnitt 5.0). Bitte beim nächsten Mal auf
> **eine** Schreibweise festlegen und durchziehen.

**Keine Mengen im Einheitenfeld.** `Box25` → `Box`, `Pack 12` → `Pack`. Die
Zahl gehört in `MengeProVPE`. Nur bei echten Gebindewörtern streichen (Box,
Pack, Stück, Rolle, Set, Köcher, Karton, Kanister) — sonst würde aus der
Flächeneinheit `m2` ein `m`.

**Auch Längenangaben gehören nicht ins Einheitenfeld** (seit 27.08.):
`Stange a. 5m` → `Stange`, `Rolle 5m` → `Rolle`, `m/Rolle` → `Rolle`. Das
Gebindewort steht allein; die Länge gehört in die Bezeichnung.

`LagerEinheit` hat dadurch **42** verschiedene Werte (früher 111).

### 5.2 Mengen — `MengeProVPE` und `AbwBestellmenge`

| Gebinde | `MengeProVPE` | `AbwBestellmenge` |
|---|---|---|
| **Pack** und alle übrigen | Packungsinhalt, z. B. `200` | **gleich dem Inhalt**, `200` Stück |
| **Box** | `1` | `1` Stück |

> Der Pack-Fall ist **so gewollt**: Bestellt wird kaufmännisch in Stück, wegen
> der IDS-Übertragung an die Onlineshops. `AbwBestellmenge` ist deshalb bei
> 12.831 von 12.847 Artikeln absichtlich gleich `MengeProVPE`. **Das ist keine
> Dublette und darf nicht „aufgeräumt" werden.**

- **`MengeProVPE` ist nie `0`.** Null Stück je Verpackung ergibt keinen Sinn;
  die Zelle bleibt dann leer.
- **`AbwBestellmenge` ist nie `0`.**
- **Bestellmenge und Bestelleinheit gehören zusammen** — beide gefüllt oder
  beide leer.

### 5.3 Satzart — `KurzBezeichnung`

Diese Spalte enthält die Satzart und geht in die Importspalte `Matchcode`.

**Pauschal immer `ST`, in jeder Zeile.** Früher standen dort auch `SF`, `KO`,
`EX` und leere Zellen; alles ist jetzt `ST` (94.610 ×).

### 5.4 Platzhalter statt leerer Zellen — verboten

Eine leere Angabe ist eine **leere Zelle**. Das Wort `leer` ist keine Einheit.
Ebenso wenig `n/a`, `null`, `keine`, `unbekannt`.

> Die Anwendung filtert diese Wörter zwar zusätzlich heraus
> (`matching.POOL_PLATZHALTER`), aber sie gehören gar nicht erst in den Pool.

### 5.5 Zeichensatz — keine Steuerzeichen

Der Pool enthielt 213 Zellen mit Steuerzeichen aus einer misslungenen
Zeichensatz-Wandlung. In Excel erscheinen sie als leeres Kästchen. **Es sind
keine Anführungszeichen** — U+0093 ist nicht `"`, das wäre U+201C.

| gefunden | war gemeint |
|---|---|
| `U+0081` neben oder anstelle von `ü` | `ü` |
| `U+009D` vor einer Zahl | `Ø` (Durchmesser) |
| `U+009D` doppelt, `U+0093`, `U+0094` | `"` (Zollzeichen, gerade U+0022) |

So schreiben es die gepflegten Artikel: `Red. Muffe 1/2" x 3/8"`,
`Ø 63 mm, DN 32`. Bitte auch die **Quelle** prüfen, damit die Zeichen beim
nächsten Import nicht erneut entstehen.

### 5.6 Bezeichnungen

- `BezArtikel1` ist nie leer — sonst erscheint beim Kunden eine leere Zeile.
- `BezArtikel1–3` sind auf 25 Zeichen begrenzt (Cloud-Vorgabe).
- Keine Bezeichnung im Nummernfeld (`Michael Seiler` als Artikelnummer).
- Keine Artikelnummer als Bezeichnung.

### 5.7 Bildnamen

Reiner Dateiname **mit Endung**, kein Pfadanteil. Erlaubt: `.jpg`, `.jpeg`,
`.png`, `.webp`, `.jfif`, `.gif`, `.bmp`.

> **Bildnamen dürfen nie aus der Artikelnummer abgeleitet werden.** Nur 4,5 %
> passen zur Nummer; der Normalfall ist eine Artikelfamilie mit einem
> gemeinsamen Bild:
> `590801404, 590801405, 590801407 → 590800404_Detail.jpg`

### 5.8 MinMax

`LagerMin` nie größer als `LagerMax`. Wo keine Quelle Werte lieferte, gilt
pauschal `1 / 2` mit Einheit `Stück` — dieselbe Regel wendet die Anwendung an.

---

## 6. Prüfung vor der Übergabe — beide Skripte

```bash
python pool_pruefen.py Datenpool_bereinigt.csv
python pool_vergleichen.py alter_pool.csv Datenpool_bereinigt.csv
```

**Beide müssen Rückgabewert 0 liefern.**

`pool_pruefen.py` beantwortet „ist die Datei in sich gültig?" — BOM,
Spaltenaufbau, Dubletten, zerstörte Nummern, Bildnamen, Lagerwerte. **Es prüft
seit dem 21.08. auch die Feldregeln aus Abschnitt 5** und erkennt damit einen
Export, der auf einer veralteten Kopie aufsetzt: Platzhalterwörter,
Einheiten-Kürzel, `MengeProVPE = 0`, eine andere Satzart als `ST` und halb
gefüllte Bestellangaben sind harte Fehler.

`pool_vergleichen.py` beantwortet die andere Frage: **ist gegenüber dem alten
Stand etwas verlorengegangen?** Es meldet verschwundene Artikel und geleerte
Felder — genau die zwei Fehler, die man in einer Datei dieser Größe sonst
nicht bemerkt. Die erlaubten Ausnahmen kennt es (Dubletten-Zusammenführung,
Umverteilung zwischen den Bezeichnungsfeldern) und schlägt dort nicht an.

> Es fand einmal sieben Artikel, die ihre `BezArtikel3` verloren hatten — die
> Prüfung von Hand hatte nur `BezArtikel1` angesehen.

Bleibt eine Meldung stehen, bitte **begründen statt übergehen**.

---

## 7. Die drei wiederkehrenden Aufgaben

Für jede gibt es eine fertige Einfüge-Nachricht:

| Aufgabe | Datei |
|---|---|
| Neue Datenquelle einarbeiten | `PROMPT-NEUE-DATEN-EINARBEITEN.md` |
| Bildnamen nachtragen | `PROMPT-BILDNAMEN-ERGAENZEN.md` |
| Geprüfte Neuaufnahmen aus Kundenlisten übernehmen | `PROMPT-FUER-DATENPOOL-CHAT.md` |

### Warum Neuaufnahmen hier eingepflegt werden

Der Pool hat zwei mögliche Schreiber: die Anwendung („In Pool übernehmen") und
den Datenpool-Chat (kompletter Neuexport). **Der Neuexport ersetzt die ganze
Datei** — alles, was zwischenzeitlich in der Anwendung hinzugefügt wurde, wäre
verloren. Deshalb: sammeln und prüfen in der Anwendung, **einpflegen im Chat**.

---

## 8. Was zurückkommen muss

1. `Datenpool_bereinigt.csv` — der vollständige neue Pool
2. die Ausgabe **beider** Prüfskripte
3. eine kurze Änderungsübersicht:
   - Zeilen vorher / nachher, davon neue Artikel
   - welche Quelle dazugekommen ist
   - wie viele vorhandene Werte ersetzt wurden und warum
   - was **nicht** übernommen wurde, mit Grund
4. falls sich etwas geändert hat, das das Programm wissen muss: **ein kurzer
   Absatz** — kein Prompt

---

## 9. Bewusste Entscheidungen — bitte nicht „korrigieren"

Diese Punkte sehen wie Fehler aus, sind aber so gewollt:

| | |
|---|---|
| **`AbwBestellmenge` = `MengeProVPE`** bei 12.831 Artikeln | IDS-Übertragung, siehe 5.2 |
| **Lieferant `Mustermann`** bei 1.134 Artikeln | Kunden geben den Lieferanten immer selbst mit; ihre Angabe hat Vorrang, der Platzhalter erreicht sie nie |
| **1.151 Artikel mit `VermutlichTestdaten = Ja`** | die Markierung kommt vom Platzhalter-Lieferanten, nicht vom Artikel — die Artikel selbst sind echt (`Geka-Kupplung starr`, `Straßenbesen 40cm`) |
| **Zwei gelöschte Artikel** — `lökläklökl`/`klkjkljkl` und `15487`/`15487` | Datenmüll, dürfen nicht zurückkommen. Die einzige Ausnahme von Regel 4.1 |
| **`Bild` bleibt bei Neuaufnahmen leer** | ungeprüfte Kundenbildnamen gehören nicht in den Pool |

---

## 10. Fehler, die schon passiert sind

Kurzliste zum Gegenlesen des eigenen Exports:

1. **27 statt 26 Spalten** angegeben — die Spaltenzahl muss exakt stimmen.
2. **Regex für wissenschaftliche Notation** aus dem Referenzskript zitiert, die
   es dort nie gab. Sie lautet: `^\s*[+-]?\d+(?:[.,]\d+)?[eE][+-]?\d+\s*$`
3. **Modell „claude-sonnet"** genannt — der korrekte Bezeichner ist
   `claude-sonnet-5`.
4. **Semikolon-Angabe unvollständig** — es sind sechs Spalten, nicht eine.
5. **123 Einträge ohne Bezeichnung** gelangten einmal in den Pool. Seither
   verhindert eine Qualitätsprüfung das.
6. **Artikelnummern „vereinheitlicht"** — 6.149 Nummern mit Leerzeichen wären
   dadurch unauffindbar geworden.
7. **Ein Prompt für den Code-Chat** geschrieben, der vier fertige Funktionen
   erneut beauftragte.

---

## 11. Offen — an der Quelle zu prüfen

Kein Auftrag, nur Hinweise für den nächsten Export:

- **64 Artikel, deren Bezeichnung mit der Artikelnummer identisch ist**
  (`PPT181215`, `10238`). Darunter mehrere mit Lieferant `Dummy`, bei denen die
  Bezeichnung in der Nummernspalte steht: `NYM-J 5x 2,5 Eca Ri.50`.
- **Zehn Artikel mit Unsinn in der Bezeichnung** (`Satzart Test SF`, `Test`).
- **Zwei Artikel mit der Bezeichnung `schwarz`**, einer davon mit der
  Artikelnummer `Prüfen 20`.
- `Dispenser a 10Klinge`, `Pack VPE 2` als Lagereinheit — vermutlich
  Restbestände aus einer Quelle mit freiem Textfeld.

---

## 12. Umgebung (betrifft nicht den Export, aber den Start)

| Variable | Standard | Zweck |
|---|---|---|
| `POOL_PFAD` | `daten/Datenpool_bereinigt.csv` | Pfad zum Pool |
| `ANTHROPIC_MODELL` | `claude-sonnet-5` | Modell für die PDF-Extraktion |
| `MAX_ZEILEN` | `20000` | maximale Zeilen je Upload |
| `BILDPOOL_PFAD` | — | Verzeichnis mit den Artikelbildern |

Pool austauschen: Datei ersetzen, dann `POST /admin/pool/neuladen` — oder
Server neu starten. Im Docker-Setup ist die Datei als Volume gemountet, ein
Rebuild ist nicht nötig. Die Desktop-`.exe` enthält den Pool fest eingebaut und
muss nach jeder Pooländerung neu gebaut werden.
