"""Erzeugt Embeddings fuer Artikelbezeichnungen. Zwei Provider:
- "openai": echte Embeddings ueber die OpenAI API (fuer Produktivbetrieb, per
  Nutzerentscheidung der Standard).
- "mock": deterministische lokale Vektoren ueber Hashing von Zeichen-Trigrammen
  (klassischer "Hashing-Trick"), nur zum Testen der Pipeline ohne API-Key/Netzwerk.
  Erkennt Aehnlichkeit ueber gemeinsame Zeichenfolgen, ist aber kein echtes
  semantisches Modell - fuer Produktivdaten OPENAI_API_KEY setzen.
"""
import hashlib
import re

import numpy as np

from common.config import EMBEDDING_PROVIDER, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL

EMBEDDING_DIM = 1536
_NGRAM_SIZE = 3

_openai_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI

        _openai_client = OpenAI(api_key=OPENAI_API_KEY)
    return _openai_client


def _stable_hash(s: str) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)


def _char_ngrams(text: str, n: int = _NGRAM_SIZE) -> list:
    padded = f"  {text}  "
    return [padded[i : i + n] for i in range(len(padded) - n + 1)]


def _mock_embedding(text: str) -> list:
    normalized = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", text.lower())).strip()
    vec = np.zeros(EMBEDDING_DIM)
    if not normalized:
        return vec.tolist()
    for ngram in _char_ngrams(normalized):
        h = _stable_hash(ngram)
        idx = h % EMBEDDING_DIM
        sign = 1.0 if (h // EMBEDDING_DIM) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = np.linalg.norm(vec)
    return (vec / norm).tolist() if norm else vec.tolist()


def get_embedding(text: str) -> list:
    if EMBEDDING_PROVIDER == "mock":
        return _mock_embedding(text)
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "EMBEDDING_PROVIDER=openai erfordert OPENAI_API_KEY. "
            "Fuer lokales Testen ohne Key EMBEDDING_PROVIDER=mock setzen."
        )
    client = _get_openai_client()
    response = client.embeddings.create(model=OPENAI_EMBEDDING_MODEL, input=text)
    return response.data[0].embedding
