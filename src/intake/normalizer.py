from __future__ import annotations

import re
import unicodedata


_UMLAUT_FOLD = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "ß": "ss",
    "Ä": "ae",
    "Ö": "oe",
    "Ü": "ue",
}

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(raw: str) -> str:
    if not raw:
        return ""
    folded = "".join(_UMLAUT_FOLD.get(ch, ch) for ch in raw)
    decomposed = unicodedata.normalize("NFKD", folded)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    lowered = stripped.lower().strip()
    collapsed = _WHITESPACE_RE.sub(" ", lowered)
    return collapsed


def tokenize(normalized: str) -> list[str]:
    if not normalized:
        return []
    return [token for token in re.split(r"[^a-z0-9]+", normalized) if token]
