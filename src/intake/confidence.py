from __future__ import annotations

CONFIDENCE_HIGH = 0.85
CONFIDENCE_MEDIUM = 0.60


def confidence_band(confidence: float) -> str:
    if confidence >= CONFIDENCE_HIGH:
        return "high"
    if confidence >= CONFIDENCE_MEDIUM:
        return "medium"
    return "low"


def requires_confirmation(confidence: float, *, has_ambiguity: bool = False) -> bool:
    if has_ambiguity:
        return True
    return confidence < CONFIDENCE_HIGH
