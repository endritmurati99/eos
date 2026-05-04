"""Redaction helpers for runtime output and smoke-test logs."""

from __future__ import annotations

from .secret_patterns import SENSITIVE_PATTERNS


def scan_for_sensitive_patterns(value: str) -> dict:
    """Return pattern counts without exposing matched secret or PII values."""

    text = "" if value is None else str(value)
    counts: dict[str, int] = {}
    classes: set[str] = set()

    for sensitive_pattern in SENSITIVE_PATTERNS:
        matches = sensitive_pattern.pattern.findall(text)
        if matches:
            counts[sensitive_pattern.label] = len(matches)
            classes.add(sensitive_pattern.data_class)

    return {
        "has_sensitive": bool(counts),
        "counts": counts,
        "data_classes": sorted(classes),
    }


def redact_text(value: str) -> str:
    """Mask known secrets and PII in a string."""

    text = "" if value is None else str(value)
    redacted = text

    for sensitive_pattern in SENSITIVE_PATTERNS:
        redacted = sensitive_pattern.pattern.sub(f"[REDACTED:{sensitive_pattern.label}]", redacted)

    return redacted
