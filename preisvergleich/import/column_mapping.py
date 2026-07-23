"""Erkennt gaengige deutsche Spaltenkoepfe aus Kunden-/Lieferanten-Preislisten
und wandelt Zeilen in staging_items-Datensaetze um, ohne die Rohwerte zu veraendern.
"""
import json
import math
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

ALIASES = {
    "description": ["bezeichnung", "artikel", "artikelbezeichnung", "name", "produktname", "beschreibung", "artikeltext"],
    "supplier_name": ["lieferant", "hersteller", "grosshaendler", "grosshändler", "supplier"],
    "article_number": ["artikelnummer", "art nr", "artnr", "art_nr", "bestellnummer", "artikel nr", "artikel-nr"],
    "ean": ["ean", "gtin", "ean code", "ean13"],
    "price": ["einkaufspreis", "ek preis", "ekpreis", "preis", "listenpreis", "nettopreis", "ek", "vk preis"],
    "unit": ["einheit", "vpe", "verpackungseinheit"],
    "valid_from": ["gueltig ab", "gültig ab", "preis gueltig ab", "stand"],
}

_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def normalize_header(header) -> str:
    h = str(header).strip().lower().translate(_UMLAUTE)
    h = re.sub(r"[^a-z0-9]+", " ", h).strip()
    return h


def map_headers(headers: list) -> dict:
    """Gibt {original_header: canonical_field_or_None} zurueck."""
    lookup = {}
    for field, aliases in ALIASES.items():
        for alias in aliases:
            lookup[alias] = field

    result = {}
    for header in headers:
        normalized = normalize_header(header)
        result[header] = lookup.get(normalized)
    return result


def _is_missing(value) -> bool:
    """None, leerer String oder NaN (leere Excel-Zellen werden von pandas als float('nan') gelesen)."""
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def parse_price(value) -> Decimal | None:
    if _is_missing(value):
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"[^\d,.\-]", "", text)
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def parse_ean(value) -> str | None:
    if _is_missing(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text or None


def parse_date(value) -> date | None:
    if _is_missing(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d.%m.%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _json_safe(value):
    if _is_missing(value):
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def build_staging_record(row: dict, header_map: dict, default_supplier_name: str | None, default_valid_from: date) -> dict:
    """row: {original_header: raw_value} fuer eine Zeile. Rohwerte bleiben unveraendert in raw_row erhalten."""
    raw_row = {str(k): _json_safe(v) for k, v in row.items()}

    fields = {"description": None, "supplier_name_raw": None, "article_number_raw": None, "ean": None, "price": None, "unit": None, "valid_from": None}
    for header, value in row.items():
        canonical = header_map.get(header)
        if canonical == "description":
            fields["description"] = None if _is_missing(value) else str(value).strip()
        elif canonical == "supplier_name":
            fields["supplier_name_raw"] = None if _is_missing(value) else str(value).strip()
        elif canonical == "article_number":
            fields["article_number_raw"] = None if _is_missing(value) else str(value).strip()
        elif canonical == "ean":
            fields["ean"] = parse_ean(value)
        elif canonical == "price":
            fields["price"] = fields["price"] or parse_price(value)
        elif canonical == "unit":
            fields["unit"] = None if _is_missing(value) else str(value).strip()
        elif canonical == "valid_from":
            fields["valid_from"] = parse_date(value)

    if not fields["supplier_name_raw"]:
        fields["supplier_name_raw"] = default_supplier_name
    if not fields["valid_from"]:
        fields["valid_from"] = default_valid_from

    return {"raw_row": raw_row, **fields}
