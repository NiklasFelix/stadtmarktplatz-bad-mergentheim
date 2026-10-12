# OrKan Artikel-Matching-Tool

## Zweck

Web-Anwendung für die OrKan-System GmbH. SHK-Handwerksbetriebe laden ihre Artikelliste
hoch (Excel, CSV oder PDF) und bekommen sofort eine fertige Importdatei für die
OrKan-Cloud zurück, angereichert aus dem zentralen Artikel-Datenpool.

Ablauf: Upload → Spaltenerkennung (vom Kunden bestätigt) → Abgleich gegen den Pool →
Importdatei (39 Spalten) + Abgleich-Report zum Download.

## Die eine Wahrheit: `daten/Datenpool_bereinigt.csv`

Der Pool ist die einzige Quelle für Artikelstammdaten. 94.610 Zeilen, 28 Spalten,
Semikolon-getrennt, UTF-8 mit BOM. Schlüsselspalte: `ArtikelNrLieferant`.

**Pool aktualisieren:** Datei ersetzen (neuen Stand aus dem Claude-Projekt "Datenpool"
exportieren), dann Server bzw. Container neu starten. Im Docker-Setup ist die Datei als
Volume gemountet, ein Rebuild ist also nicht nötig. Alternativ lässt sich der Pool über
`POST /admin/pool/neuladen` (Basic Auth) ohne Neustart neu einlesen.

Achtung beim Parsen: `Lieferanten_alle` enthält selbst Semikolons und ist deshalb
gequotet (`"Gerhard Sprügel GmbH; Test Lieferant"`). Immer mit einem echten CSV-Parser
lesen, nie per `split(';')` auf der Rohzeile.

## Datenregeln (verbindlich)

- **Der Pool verlässt den Server nie.** Kunden dürfen ihn weder herunterladen noch
  durchsuchen — sie reichern ausschließlich ihre eigenen Artikelnummern an. Keine Route
  gibt den Pool ganz oder in Teilen ohne konkrete Kundennummern heraus. Uploads sind auf
  `MAX_ZEILEN` Zeilen begrenzt, damit der Pool nicht durch Massen-Uploads abgeschöpft wird.
- **Kundenangaben haben Vorrang.** Liefert der Kunde für ein zugeordnetes Feld einen
  Wert, wird dieser übernommen; der Pool füllt nur Lücken. Je Feld lässt sich das über
  `matching.Anreicherung` umstellen (`ergaenzen` / `pool` / `nur_kunde`), dazu gibt es
  einen globalen Schalter. Der Report weist die Herkunft je Feld aus.
- **Keine Daten erfinden** – mit einer benannten Ausnahme: Bleibt MinMax nach
  Kundenangabe *und* Pool leer, gilt pauschal 1/2 mit Einheit „Stück". Diese Regel kommt
  aus dem Datenpool-Export, wo leere MinMax ebenso belegt wurden. Passen Min und Max aus
  verschiedenen Quellen nicht zusammen, wird Max auf Min+1 gehoben.
- **Wissenschaftliche Notation** (z. B. `4,04478E+12`) und der Füllwert `0` in
  Bezeichnungsfeldern werden aus Kundeneingaben entfernt (siehe `app/parsing.py`).
- **Ausgabe-Validierung vor jedem Download:** Spaltennamen und Reihenfolge werden exakt
  gegen `referenz/Importformat_39_Spalten_Vorlage.csv` geprüft. Bei Abweichung gibt es
  einen Fehler statt einer falschen Datei.
- **Neuaufnahmen ändern den Pool nicht automatisch.** Nicht gefundene Artikel landen in
  `daten/neuaufnahmen_queue.csv` und werden erst nach Prüfung durch einen
  OrKan-Mitarbeiter über `/admin/neuaufnahmen` in den Pool übernommen. Grund: ungeprüfte
  Kundendaten dürfen den zentralen Pool nicht verändern.
- **Prüfen heißt bearbeiten, nicht abnicken.** Die offenen Einträge lassen sich als
  Excel-Datei exportieren, ergänzen und wieder einspielen (`queue_store.export_tabelle`
  / `import_tabelle`). Gelöschte Zeilen gelten als verworfen.
- **Qualitätsbremse vor der Übernahme.** `queue_store.pruefe_eintrag` lehnt Zeilen ohne
  Bezeichnung, mit Semikolon in der Artikelnummer, mit zwei Wörtern statt einer Nummer
  (`Michael Seiler`), mit zu kurzer Zahlennummer und mit Min > Max ab. Ohne diese Prüfung
  sind einmal 123 Einträge ohne Bezeichnung im Pool gelandet.
  Die Regeln sind gegen den echten Pool kalibriert: Leerzeichen (`72 011 23`, 6.195 Stück)
  und Nummern ganz ohne Ziffern (`QBSHNS`, 1.260 Stück) sind **gültig**.
- **Bild bleibt bei Neuaufnahmen immer leer** – das betrifft den *Pool*. Ein vom Kunden
  gelieferter Bildname gehört sehr wohl in dessen Importdatei.
- **Der Bildpool verlässt den Server nie als Ganzes.** Das ZIP zur Importdatei enthält
  nur die dort referenzierten Dateien, jede genau einmal. Der Quellpfad steht auf dem
  Server in `BILDPOOL_PFAD` und ist im Kundenformular bewusst nicht eingebbar –
  in der Desktop-Fassung und mit `BILDPOOL_EINGABE=1` dagegen schon.
- **Rein numerische Artikelnummern mit ≤ 4 Ziffern sind ungültig.** Sie werden nicht
  gematcht, kommen nicht in die Importdatei und nicht in die Queue — sie erscheinen nur
  im Report mit Status `UNGÜLTIGE NUMMER`.
- **Alle Oberflächentexte auf Deutsch**, Zielgruppe Handwerksbetriebe: einfach und
  direkt, keine Fachbegriffe aus der Datenwelt.

## Matching-Logik

Portiert aus `referenz/abgleich_referenz.py` (produktiv erprobt, nicht neu erfinden):

- Normalisierung: trimmen + Großschreibung, Match gegen `ArtikelNrLieferant`.
- Gleiche Artikelnummer = gleicher Artikel, lieferantenübergreifend.
- Lieferant: aus der Kundenliste übernehmen, sonst erster Pool-Lieferant. Bei mehreren
  Pool-Lieferanten Hinweis im Report.
- `minmax_von_aehnlichen` und `_lagerort` sind bis aufs Ergebnis identisch übernommen.
  `minmax_von_aehnlichen` ist für den Web-Betrieb über einen invertierten Token-Index
  beschleunigt (`app/matching.py`); `tests/test_matching.py` prüft die Gleichheit zur
  Referenzimplementierung.

Ein wichtiger Unterschied zur Referenz: Das Referenzskript schreibt neue Artikel direkt
in den Pool (`pool_schreiben=True`). Diese Anwendung tut das **nicht** — sie schreibt in
die Queue.

## Aufbau

```
app/
  config.py       Einstellungen aus Umgebungsvariablen
  felder.py       Zentrale Feldtabelle: Zielfeld -> Importspalte -> Poolspalte
  bildpool.py     Bilder suchen und als ZIP packen
  pool.py         Pool laden, cachen, Lookup-Index, Token-Index
  matching.py     Kernlogik (aus der Referenz portiert)
  parsing.py      Datei-Parsing, Spaltenerkennung, Bereinigung
  pdf_extract.py  pdfplumber + optionaler Anthropic-Fallback
  export.py       39-Spalten-Importdatei, Report, Formatvalidierung
  queue_store.py  Queue lesen/schreiben, Export/Re-Import, Qualitätsprüfung
  jobs.py         Job-Zustand im Speicher, Aufräumen alter Dateien
  main.py         FastAPI-Routen
  static/index.html  Oberfläche (eine Seite)
  static/logo.*      Firmenlogo (svg/png/webp/jpg), optional
daten/            Pool + Queue (Volume im Docker-Setup)
referenz/         Originalskript + Formatvorlage (nicht ändern)
werkzeuge/        pool_pruefen.py – prüft neue Pool-Exporte vor der Übernahme
                  pool_vergleichen.py – findet Verluste gegenüber dem alten Stand
                  chat_infos_packen.py – sammelt die Chat-Dateien in einen Ordner
                  pool_bericht.py – alle Kennzahlen in einem Aufruf
                  uebergabe_packen.py – Projekt zur Übergabe packen
tests/            pytest
```

## Umgebungsvariablen

| Variable | Standard | Zweck |
|---|---|---|
| `POOL_PFAD` | `daten/Datenpool_bereinigt.csv` | Pfad zum Pool |
| `QUEUE_PFAD` | `daten/neuaufnahmen_queue.csv` | Pfad zur Neuaufnahme-Queue |
| `ARBEITSVERZEICHNIS` | `arbeitsdaten` | Uploads + Ergebnisdateien |
| `ADMIN_USER` / `ADMIN_PASSWORT` | — | Basic Auth für `/admin/*`; ohne beides ist der Admin-Bereich gesperrt |
| `ANTHROPIC_API_KEY` | — | Ohne Key ist die KI-PDF-Extraktion sauber deaktiviert |
| `ANTHROPIC_MODELL` | `claude-sonnet-5` | Modell für die PDF-Extraktion |
| `MAX_UPLOAD_MB` | `20` | Maximale Uploadgröße |
| `MAX_ZEILEN` | `20000` | Maximale Zeilen je Upload |
| `ERGEBNIS_TTL_STUNDEN` | `24` | Ergebnisdateien werden danach gelöscht |
| `BILDPOOL_PFAD` | — | Verzeichnis mit den Artikelbildern; ohne Angabe kein Bild-ZIP |
| `MAX_ZIP_MB` | `500` | Obergrenze für das Bild-ZIP |
| `BILDPOOL_EINGABE` | aus | `1` erlaubt die Pfadeingabe in der Oberfläche |

## Tests

```bash
pytest -q
```

463 Tests decken ab: Spaltenerkennung (mehrere Header-Varianten), Matching inkl.
Normalisierung, Ungültige-Nummern-Regel, MinMax-Ähnlichkeitslogik (Gleichheit zur
Referenz), Formatvalidierung der Ausgabe, den Prüf-Ablauf der Neuaufnahmen und den
Prüfer für neue Pool-Exporte, den Vorrang der Kundenangaben je Modus sowie das
Bild-ZIP samt Entdopplung und Pfadsicherheit.

**Vor jedem Datenpool-Export:**

```bash
python werkzeuge/chat_infos_packen.py
```

füllt den Ordner `EXPORT CHAT INFOS` mit dem aktuellen Stand aller Dateien für
den Datenpool-Chat und meldet, wenn die Zahlen in den Anweisungen nicht mehr
zum eingesetzten Pool passen. Mitzuschicken sind immer `EXPORT-ANFORDERUNGEN.md`
und beide Prüfskripte, dazu genau eine Aufgaben-Nachricht.

Die zurückgelieferte Datei danach mit `werkzeuge/pool_pruefen.py` **und**
`werkzeuge/pool_vergleichen.py` prüfen.
