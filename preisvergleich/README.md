# Artikel- und Preisvergleich

Zentrale Datenbank zum Zusammenfuehren von Artikel- und Preisdaten aus mehreren
OrKan-Cloud-Kunden und Grosshaendler-Preislisten (Excel/PDF), mit Matching ueber
EAN bzw. semantischer Aehnlichkeit und einer API fuer den Preisvergleich.

Diese API ist ausschliesslich fuer den internen Gebrauch gedacht (ein API-Key,
kein Mandantenkonzept) - OrKan-Cloud-Kunden haben keinen Zugriff darauf.

## Architektur

```
staging_items (Rohdaten, unveraendert)
      |
      v  Matching: EAN exakt -> sonst Embeddings + Schwellenwert
      v
article_matches (Zuordnung + Status: auto_accepted / needs_review / confirmed / rejected)
      |
      v
canonical_articles (ein Datensatz pro echtem Artikel, inkl. Embedding)
      |
      v
supplier_offers (Preis-Zeitverlauf je Artikel + Lieferant)
```

- **sources / import_batches / staging_items**: jede importierte Datei landet
  unveraendert (als `raw_row` JSON) in `staging_items`.
- **canonical_articles**: kanonisches Artikelmodell inkl. `embedding` (pgvector)
  fuer semantisches Matching.
- **article_matches**: Mapping `staging_item -> canonical_article` mit
  `match_method` (`ean_exact` / `semantic` / `new_article`) und `status`.
  Unsichere semantische Treffer bekommen `needs_review` und werden **nicht**
  automatisch als Angebot uebernommen.
- **suppliers / supplier_offers**: normalisierte Lieferanten + Preis-Zeitverlauf
  je Artikel/Lieferant. `current_offers`-View liefert die jeweils aktuellsten
  Preise, `GET /articles/{id}/cheapest` sortiert danach.

Schwellenwerte (in `common/config.py`, per Env ueberschreibbar):
- `SEMANTIC_AUTO_ACCEPT_THRESHOLD` (Default 0.92): automatisch uebernehmen
- `SEMANTIC_REVIEW_THRESHOLD` (Default 0.80): manuell pruefen
- darunter: neuer eigenstaendiger Artikel

## Lokal starten (Docker)

```bash
cd preisvergleich
cp .env.example .env   # API_KEY, EMBEDDING_PROVIDER, OPENAI_API_KEY anpassen
docker compose up -d db
docker compose up -d api
```

Kompletten Testlauf mit generierten Beispieldaten (Import + Matching + Abfragen):

```bash
./scripts/run_e2e_test.sh
```

Einzelne Schritte manuell (`--profile tools` aktiviert den Werkzeug-Service):

```bash
docker compose --profile tools run --rm tools python scripts/generate_sample_data.py sample_data
docker compose --profile tools run --rm tools python import/import_excel.py sample_data/datei.xlsx --source-name "Lieferant X" --source-type supplier
docker compose --profile tools run --rm tools python import/import_pdf.py sample_data/liste.pdf --source-name "Lieferant Y" --source-type supplier
docker compose --profile tools run --rm tools python matching/run_matching.py
```

## API

Alle Endpunkte (ausser `/health`) erfordern den Header `X-API-Key: <API_KEY>`.

- `GET /articles?q=suchbegriff` - Artikel suchen
- `GET /articles/{id}/offers` - alle aktuellen Angebote, guenstigstes zuerst
- `GET /articles/{id}/cheapest` - guenstigstes aktuelles Angebot
- `GET /reviews` - offene, manuell zu pruefende Zuordnungen
- `POST /reviews/{match_id}/confirm` `{"reviewed_by": "name"}` - Zuordnung bestaetigen, legt Angebot an
- `POST /reviews/{match_id}/reject` `{"reviewed_by": "name"}` - Zuordnung ablehnen, legt stattdessen neuen Artikel an

## Embeddings: mock vs. openai

`EMBEDDING_PROVIDER=openai` (Standard) nutzt echte OpenAI-Embeddings und
erfordert `OPENAI_API_KEY`. `EMBEDDING_PROVIDER=mock` nutzt lokale, deterministische
Vektoren auf Basis von Zeichen-Trigrammen (Hashing-Trick) - funktioniert offline,
erkennt aber nur textliche Aehnlichkeit, kein echtes semantisches Verstaendnis.
Nur zum Testen der Pipeline ohne API-Key gedacht.

## Bekannte Grenzen / naechste Schritte

- PDF-Import geht von einer konsistenten Kopfzeile ueber alle Tabellen der Datei
  aus; bei sehr unterschiedlichen Lieferanten-Layouts ggf. pro Lieferant anpassen.
- `valid_to` in `supplier_offers` wird aktuell nicht automatisch gesetzt; "aktuell"
  bedeutet der jeweils neueste `valid_from` je Artikel/Lieferant.
- Spalten-Erkennung (`import/column_mapping.py`) deckt gaengige deutsche
  Bezeichnungen ab: bei exotischen Preislisten-Formaten muss `ALIASES` erweitert
  werden.
