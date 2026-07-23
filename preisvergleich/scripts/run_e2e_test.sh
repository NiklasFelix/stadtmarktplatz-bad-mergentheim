#!/usr/bin/env bash
# Kompletter lokaler Testlauf: DB hochfahren, Beispieldaten erzeugen, importieren,
# matchen, API starten und ein paar Abfragen zeigen.
set -euo pipefail
cd "$(dirname "$0")/.."

COMPOSE="docker compose --profile tools"

echo "== 1/6 Datenbank hochfahren =="
$COMPOSE up -d db
$COMPOSE run --rm tools python -c "
import time, psycopg2, os
for _ in range(30):
    try:
        psycopg2.connect(os.environ['DATABASE_URL']).close()
        break
    except Exception:
        time.sleep(1)
"

echo "== 2/6 Beispieldaten erzeugen =="
$COMPOSE run --rm tools python scripts/generate_sample_data.py sample_data

echo "== 3/6 Import (Excel + PDF) =="
$COMPOSE run --rm tools python import/import_excel.py sample_data/grosshandel_nord.xlsx --source-name "Grosshandel Nord" --source-type supplier
$COMPOSE run --rm tools python import/import_excel.py sample_data/grosshandel_sued.xlsx --source-name "Grosshandel Sued" --source-type supplier
$COMPOSE run --rm tools python import/import_pdf.py sample_data/frischehof_preisliste.pdf --source-name "Frischehof" --source-type supplier
$COMPOSE run --rm tools python import/import_excel.py sample_data/customer_muster_gmbh.xlsx --source-name "Muster GmbH" --source-type customer
$COMPOSE run --rm tools python import/import_excel.py sample_data/customer_beispiel_handel.xlsx --source-name "Beispiel Handel" --source-type customer

echo "== 4/6 Matching ausfuehren =="
$COMPOSE run --rm tools python matching/run_matching.py

echo "== 5/6 Benutzer anlegen & API starten =="
$COMPOSE run --rm tools python scripts/seed_users.py
$COMPOSE up -d api
sleep 3

echo "== 6/6 Beispielabfragen =="
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login -H "Content-Type: application/json" \
  -d '{"email":"admin@spruegel.de","password":"admin1234"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

echo "-- Suche nach 'Apfel' --"
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/articles?q=Apfel" | tee /tmp/apfel.json
ARTICLE_ID=$(python3 -c "import json;print(json.load(open('/tmp/apfel.json'))[0]['id'])")

echo -e "\n-- Alle Angebote fuer Apfel-Artikel --"
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/articles/$ARTICLE_ID/offers"

echo -e "\n-- Guenstigster Preis --"
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/articles/$ARTICLE_ID/cheapest"

echo -e "\n-- Offene manuelle Reviews (unsichere semantische Zuordnungen) --"
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8000/reviews"
echo
