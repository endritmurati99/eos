from __future__ import annotations

import re

from src.eos_location_intelligence.types import CalendarLocationEvent


def extract_event_location(event: CalendarLocationEvent) -> str | None:
    return normalize_location(event.location)


def normalize_location(location: str | None) -> str | None:
    if location is None:
        return None
    normalized = re.sub(r"\s+", " ", location).strip()
    if not normalized:
        return None
    if normalized.casefold() in {"tbd", "unknown", "none", "online"}:
        return None
    return normalized


def is_same_location(left: str | None, right: str | None) -> bool:
    normalized_left = normalize_location(left)
    normalized_right = normalize_location(right)
    if not normalized_left or not normalized_right:
        return False
    return normalized_left.casefold() == normalized_right.casefold()
