from __future__ import annotations

import re
import unicodedata


CANONICAL_TRIGGERS = (
    "muede",
    "stress",
    "langeweile",
    "aufschieben",
    "handy_im_bett",
    "sozialer_druck",
    "hunger",
    "frustration",
    "unbekannt",
)

_TRIGGER_ALIASES: dict[str, tuple[str, ...]] = {
    "muede": ("muede", "muedigkeit", "erschoepft", "schlapp", "tired"),
    "stress": ("stress", "ueberlastung", "druck", "anspannung"),
    "langeweile": ("langeweile", "boredom", "nichts zu tun"),
    "aufschieben": ("aufschieben", "prokrastination", "vermeidung", "procrastination"),
    "handy_im_bett": ("handy im bett", "phone in bed", "handy bett"),
    "sozialer_druck": ("sozialer druck", "fomo", "social"),
    "hunger": ("hunger", "hungrig", "appetit"),
    "frustration": ("frustration", "frustriert", "wut", "aerger"),
}


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    folded = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    folded = (
        folded.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .replace("Ä", "ae")
        .replace("Ö", "oe")
        .replace("Ü", "ue")
    )
    return re.sub(r"\s+", " ", folded.lower()).strip()


def classify_trigger(raw: str | None) -> str:
    if not raw:
        return "unbekannt"
    normalized = _normalize(raw)
    if not normalized:
        return "unbekannt"
    for canonical, aliases in _TRIGGER_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                return canonical
    return "unbekannt"


def normalize_replacement(raw: str | None) -> str | None:
    if raw is None:
        return None
    cleaned = _normalize(raw)
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")
    return cleaned or None


__all__ = [
    "CANONICAL_TRIGGERS",
    "classify_trigger",
    "normalize_replacement",
]
