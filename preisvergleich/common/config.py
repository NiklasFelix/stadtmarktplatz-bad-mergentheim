import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://preisvergleich:preisvergleich@db:5432/preisvergleich"
)

# "openai" fuer echte Embeddings, "mock" fuer deterministische Test-Embeddings ohne API-Key
EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "openai")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Schwellenwerte fuer semantisches Matching (Kosinus-Aehnlichkeit, 1.0 = identisch)
SEMANTIC_AUTO_ACCEPT_THRESHOLD = float(os.environ.get("SEMANTIC_AUTO_ACCEPT_THRESHOLD", "0.92"))
SEMANTIC_REVIEW_THRESHOLD = float(os.environ.get("SEMANTIC_REVIEW_THRESHOLD", "0.80"))

# Interner API-Key fuer die Preisvergleichs-API (kein Mandanten-/Kundenzugriff)
API_KEY = os.environ.get("API_KEY", "changeme-local-dev-key")
