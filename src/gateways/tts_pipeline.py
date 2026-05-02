from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.gateways.tts_local import synthesize_with_piper
from src.gateways.tts_provider import failure_result

TTSProvider = Callable[..., dict[str, Any]]


def synthesize_briefing_audio(
    text: str,
    *,
    target: str = "telegram",
    voice: str | None = None,
    prefer_local: bool = True,
    provider: TTSProvider | None = None,
) -> dict[str, Any]:
    if not text.strip():
        return failure_result(
            status="input_empty",
            provider="tts_pipeline",
            error="No briefing text was provided for audio generation.",
        )

    if provider is not None:
        return provider(text=text, target=target, voice=voice)

    if prefer_local:
        return synthesize_with_piper(text, target=target, voice=voice)

    return failure_result(
        status="config_missing",
        provider="tts_pipeline",
        error="No TTS provider is configured.",
    )
