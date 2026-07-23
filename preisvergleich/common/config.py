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

# JWT-Login fuer Nutzer (admin/einkauf/lager/management)
JWT_SECRET = os.environ.get("JWT_SECRET", "changeme-local-dev-jwt-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_MINUTES = int(os.environ.get("JWT_EXPIRES_MINUTES", "480"))

UPLOAD_DIR = os.environ.get("UPLOAD_DIR", "/app/uploads")
