from __future__ import annotations

from pathlib import Path
from typing import Any


def success_result(
    *,
    provider: str,
    audio_path: str | Path,
    mime_type: str,
    duration_estimate: float | None,
) -> dict[str, Any]:
    return {
        "status": "success",
        "provider": provider,
        "audio_path": str(audio_path),
        "mime_type": mime_type,
        "duration_estimate": duration_estimate,
        "error": None,
    }


def failure_result(
    *,
    status: str,
    provider: str,
    error: str,
    audio_path: str | Path | None = None,
    mime_type: str | None = None,
    duration_estimate: float | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "provider": provider,
        "audio_path": str(audio_path) if audio_path else None,
        "mime_type": mime_type,
        "duration_estimate": duration_estimate,
        "error": error,
    }


def estimate_duration_seconds(text: str, *, words_per_minute: int = 150) -> float:
    words = [word for word in text.split() if word.strip()]
    if not words:
        return 0.0
    return round((len(words) / words_per_minute) * 60, 1)
