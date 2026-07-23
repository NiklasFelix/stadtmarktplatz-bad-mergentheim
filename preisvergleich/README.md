# Artikel- und Preisvergleich

Zentrale Datenbank zum Zusammenfuehren von Artikel- und Preisdaten aus mehreren
OrKan-Cloud-Kunden und Grosshaendler-Preislisten (Excel/PDF), mit Matching ueber
EAN bzw. semantischer Aehnlichkeit und einer API fuer den Preisvergleich.

Die API nutzt echte Benutzerkonten mit Rollen (`admin`, `einkauf`, `lager`,
`management`) statt eines geteilten API-Keys - OrKan-Cloud-Kunden haben
weiterhin keinen Zugriff, nur internes Personal meldet sich mit eigenem
Konto an.

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

## Benutzerkonten anlegen

```bash
docker compose --profile tools run --rm tools python scripts/seed_users.py
```

Legt vier Demo-Konten an (Benutzername = Rolle, Passwoerter danach aendern):
`admin` / `einkauf` / `lager` / `management` (Passwort jeweils `<benutzername>1234`).

## API

Alle Endpunkte (ausser `/health` und `/auth/login`) erfordern den Header
`Authorization: Bearer <token>` aus `POST /auth/login`. Schreibende Endpunkte
(anlegen/aendern/loeschen) sind auf die Rollen `admin`/`einkauf` beschraenkt.

- `POST /auth/login`, `GET /auth/me`, `PUT /auth/me/password`
- `GET/POST/PUT/DELETE /articles`, `/articles/{id}` - Artikel-CRUD, Suche/Filter
  (`q`, `warengruppe`, `kategorie`, `supplier_id`, `price_min/max`, `lieferzeit_max`)
- `POST/PUT/DELETE /articles/{id}/offers[/​{offer_id}]` - Lieferantenangebote pflegen
- `GET /articles/{id}/price-history` - Preisverlauf
- `GET/POST/PUT/DELETE /suppliers`, `/customers` - Lieferanten-/Kunden-CRUD
- `GET /reviews`, `POST /reviews/{id}/confirm|reject` - Dubletten aus dem Import pruefen
- `POST /import/upload` (multipart: `file`, `source_name`, `source_type`) - echter
  Excel/CSV-Import inkl. Validierung, Fehlerprotokoll (`import_errors`) und
  sofortigem Matching; `GET /import/history`
- `GET /export/articles.csv|xlsx|pdf`, `GET /export/preisvergleich/{id}.pdf` - echte Dateien
- `GET /ai/duplicates`, `GET /ai/data-quality`, `GET /ai/price-analysis`,
  `POST /ai/duplicates/merge`, `POST /ai/chat` - alles live aus der DB berechnet
  (Chat: deterministischer Intent-Router auf echten SQL-Abfragen, kein LLM ohne
  hinterlegten `OPENAI_API_KEY`)
- `GET /dashboard/kpis`, `GET /dashboard/activity` - Dashboard-Kennzahlen live

## Frontend

Das Frontend liegt ausserhalb dieses Verzeichnisses als eigenstaendige HTML-Datei
(Sprügel-Design) und spricht per `fetch()` mit dieser API (`API_BASE` am
Scriptanfang anpassen, falls die API nicht auf `http://localhost:8000` laeuft).

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
