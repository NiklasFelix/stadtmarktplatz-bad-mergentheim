"""Textbausteine, die von Pool- und Matching-Modul gemeinsam genutzt werden."""
from __future__ import annotations

import re

_NICHT_WORT = re.compile(r"[^a-z0-9äöüß ]")


def tokens(wert) -> set[str]:
    """Bezeichnung in Vergleichs-Token zerlegen (1:1 aus der Referenzlogik)."""
    return set(_NICHT_WORT.sub(" ", str(wert).lower()).split())
