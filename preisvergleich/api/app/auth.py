from fastapi import Header, HTTPException, status

from common.config import API_KEY


def require_api_key(x_api_key: str = Header(default=None)):
    """Ein einziger interner API-Key - diese API ist nicht fuer OrKan-Cloud-Kunden gedacht,
    sondern nur fuer den internen Preisvergleich."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungueltiger oder fehlender X-API-Key")
