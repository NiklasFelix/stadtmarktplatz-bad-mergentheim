-- Zentrale Artikel- und Preisvergleichs-Datenbank
-- Schema-Aufbau: staging (Rohdaten unveraendert) -> canonical_articles (kanonisches Modell)
-- -> article_matches (Zuordnung staging -> canonical) -> supplier_offers (Preis-Zeitverlauf)

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto; -- fuer gen_random_uuid()

-- ============================================================
-- Quellen: einzelne OrKan-Cloud-Kunden ODER Grosshaendler/Lieferanten-Preislisten
-- ============================================================
CREATE TABLE sources (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('customer', 'supplier')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Ein Import-Lauf (eine Datei) je Quelle
CREATE TABLE import_batches (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES sources(id),
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('excel', 'pdf')),
    row_count INTEGER NOT NULL DEFAULT 0,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- STAGING: Rohdaten aus Import, unveraendert (raw_row = komplette Originalzeile)
-- ============================================================
CREATE TABLE staging_items (
    id BIGSERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES import_batches(id),
    source_id INTEGER NOT NULL REFERENCES sources(id),
    row_number INTEGER,
    raw_row JSONB NOT NULL,
    -- vom Importer erkannte Felder, dienen nur als Eingabe fuers Matching,
    -- die Originalwerte bleiben unangetastet in raw_row erhalten
    description TEXT,
    supplier_name_raw TEXT,
    article_number_raw TEXT,
    ean TEXT,
    price NUMERIC(12, 4),
    currency TEXT NOT NULL DEFAULT 'EUR',
    unit TEXT,
    valid_from DATE,
    imported_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_staging_items_ean ON staging_items(ean) WHERE ean IS NOT NULL;
CREATE INDEX idx_staging_items_batch ON staging_items(batch_id);

-- ============================================================
-- KANONISCHES ARTIKELMODELL: ein Datensatz pro real existierendem Artikel
-- ============================================================
CREATE TABLE canonical_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ean TEXT UNIQUE,
    canonical_name TEXT NOT NULL,
    description TEXT,
    -- text-embedding-3-small hat 1536 Dimensionen
    embedding VECTOR(1536),
    review_status TEXT NOT NULL DEFAULT 'auto' CHECK (review_status IN ('auto', 'confirmed', 'needs_review')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_canonical_articles_embedding ON canonical_articles
    USING hnsw (embedding vector_cosine_ops);

-- ============================================================
-- MAPPING: staging_item -> canonical_article, mit Nachweis wie/wie sicher gematcht wurde
-- ============================================================
CREATE TABLE article_matches (
    id BIGSERIAL PRIMARY KEY,
    staging_item_id BIGINT NOT NULL UNIQUE REFERENCES staging_items(id),
    canonical_article_id UUID NOT NULL REFERENCES canonical_articles(id),
    match_method TEXT NOT NULL CHECK (match_method IN ('ean_exact', 'semantic', 'new_article')),
    similarity_score NUMERIC(6, 5),
    -- needs_review: unsichere semantische Zuordnung, muss manuell bestaetigt werden
    status TEXT NOT NULL CHECK (status IN ('auto_accepted', 'needs_review', 'confirmed', 'rejected')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT
);

CREATE INDEX idx_article_matches_status ON article_matches(status);
CREATE INDEX idx_article_matches_canonical ON article_matches(canonical_article_id);

-- ============================================================
-- LIEFERANTEN (normalisiert, da dieselbe Firma in Quellen unterschiedlich benannt wird)
-- ============================================================
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE supplier_aliases (
    id SERIAL PRIMARY KEY,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    alias_name TEXT NOT NULL UNIQUE
);

-- ============================================================
-- ANGEBOTE: Preis-Zeitverlauf je Artikel + Lieferant
-- ============================================================
CREATE TABLE supplier_offers (
    id BIGSERIAL PRIMARY KEY,
    canonical_article_id UUID NOT NULL REFERENCES canonical_articles(id),
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    source_id INTEGER NOT NULL REFERENCES sources(id),
    staging_item_id BIGINT NOT NULL REFERENCES staging_items(id),
    article_number_at_supplier TEXT,
    -- nullable: manche Preislisten fuehren Artikel "auf Anfrage" ohne Preis
    price NUMERIC(12, 4),
    currency TEXT NOT NULL DEFAULT 'EUR',
    unit TEXT,
    valid_from DATE NOT NULL,
    valid_to DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_supplier_offers_article_current
    ON supplier_offers(canonical_article_id, supplier_id, valid_from DESC);

-- ============================================================
-- MVP-Erweiterung: Nutzer/Rollen, Kunden-Stammdaten, PIM-Felder,
-- Angebotsdetails (Lieferzeit/Verfuegbarkeit/Bewertung/Staffelpreise),
-- Importfehlerprotokoll
-- ============================================================

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'einkauf', 'lager', 'management')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    customer_number TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    branche TEXT,
    standorte INTEGER NOT NULL DEFAULT 1,
    ansprechpartner TEXT,
    email TEXT,
    telefon TEXT,
    einkaufsvolumen NUMERIC(14, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE SEQUENCE article_number_seq START 100001;

ALTER TABLE canonical_articles
    ADD COLUMN artikelnummer TEXT UNIQUE DEFAULT ('ART-' || nextval('article_number_seq')),
    ADD COLUMN herstellernummer TEXT,
    ADD COLUMN hersteller TEXT,
    ADD COLUMN warengruppe TEXT,
    ADD COLUMN kategorie TEXT,
    ADD COLUMN masse TEXT,
    ADD COLUMN gewicht TEXT,
    ADD COLUMN verpackungseinheit TEXT,
    ADD COLUMN mindestbestellmenge TEXT,
    ADD COLUMN technische_daten JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN dokumente JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN zertifikate JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN bilder JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN active BOOLEAN NOT NULL DEFAULT true;

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_canonical_articles_warengruppe ON canonical_articles(warengruppe);
CREATE INDEX idx_canonical_articles_name_trgm ON canonical_articles USING gin (canonical_name gin_trgm_ops);

ALTER TABLE suppliers
    ADD COLUMN ansprechpartner TEXT,
    ADD COLUMN email TEXT,
    ADD COLUMN telefon TEXT,
    ADD COLUMN adresse TEXT,
    ADD COLUMN lieferbedingungen TEXT,
    ADD COLUMN lieferzeit_standard TEXT,
    ADD COLUMN zahlungsbedingungen TEXT,
    ADD COLUMN liefertreue_pct NUMERIC(5, 2),
    ADD COLUMN active BOOLEAN NOT NULL DEFAULT true;

ALTER TABLE supplier_offers
    ADD COLUMN lieferzeit_tage NUMERIC(5, 1),
    ADD COLUMN verfuegbarkeit TEXT,
    ADD COLUMN bewertung NUMERIC(2, 1),
    ADD COLUMN rabatt_pct NUMERIC(5, 2) NOT NULL DEFAULT 0,
    ADD COLUMN staffelpreise JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE import_errors (
    id BIGSERIAL PRIMARY KEY,
    batch_id INTEGER NOT NULL REFERENCES import_batches(id),
    row_number INTEGER,
    message TEXT NOT NULL,
    raw_row JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- generischer Trigger, damit updated_at bei jedem UPDATE automatisch mitgeht
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_canonical_articles_updated_at
    BEFORE UPDATE ON canonical_articles
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Guenstigster aktueller Preis je Artikel: pro (Artikel, Lieferant) der neueste Eintrag,
-- davon ueber alle Lieferanten das Minimum
CREATE VIEW current_offers AS
SELECT DISTINCT ON (canonical_article_id, supplier_id)
    id AS offer_id,
    canonical_article_id,
    supplier_id,
    source_id,
    article_number_at_supplier,
    price,
    currency,
    unit,
    valid_from,
    lieferzeit_tage,
    verfuegbarkeit,
    bewertung,
    rabatt_pct,
    staffelpreise
FROM supplier_offers
WHERE valid_to IS NULL OR valid_to >= CURRENT_DATE
ORDER BY canonical_article_id, supplier_id, valid_from DESC;
