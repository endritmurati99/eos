from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from src.gateways.tts_provider import (
    estimate_duration_seconds,
    failure_result,
    success_result,
)

PROVIDER_NAME = "piper_local"
SHARED_WORKSPACE_ROOT = Path("/data/.openclaw/workspace")
DEFAULT_VENDOR_PATH = SHARED_WORKSPACE_ROOT / "vendor" / "piper"
DEFAULT_PIPER_BIN = DEFAULT_VENDOR_PATH / "bin" / "piper"
DEFAULT_MODEL_PATH = SHARED_WORKSPACE_ROOT / "tts" / "piper" / "de_DE-eva_k-x_low.onnx"
DEFAULT_CONFIG_PATH = SHARED_WORKSPACE_ROOT / "tts" / "piper" / "de_DE-eva_k-x_low.onnx.json"


def synthesize_with_piper(
    text: str,
    *,
    target: str = "telegram",
    voice: str | None = None,
    output_dir: str | Path | None = None,
    piper_bin: str | Path | None = None,
    model_path: str | Path | None = None,
    config_path: str | Path | None = None,
    vendor_path: str | Path | None = None,
    python_bin: str | Path | None = None,
) -> dict[str, Any]:
    del voice
    if not text.strip():
        return failure_result(
            status="input_empty",
            provider=PROVIDER_NAME,
            error="No text was provided for speech synthesis.",
        )

    resolved_bin = _resolve_piper_bin(piper_bin)
    resolved_model = Path(
        model_path
        or os.getenv("EOS_TTS_PIPER_MODEL_PATH")
        or DEFAULT_MODEL_PATH
    ).expanduser()
    resolved_config = Path(
        config_path
        or os.getenv("EOS_TTS_PIPER_CONFIG_PATH")
        or DEFAULT_CONFIG_PATH
    ).expanduser()
    resolved_vendor = Path(
        vendor_path
        or os.getenv("EOS_TTS_PIPER_VENDOR_PATH")
        or DEFAULT_VENDOR_PATH
    ).expanduser()

    missing = [
        str(path)
        for path in (resolved_bin, resolved_model, resolved_config)
        if not path.exists()
    ]
    if missing:
        return failure_result(
            status="config_missing",
            provider=PROVIDER_NAME,
            error="Missing Piper runtime assets: " + ", ".join(missing),
        )

    target_dir = Path(
        output_dir
        or os.getenv("EOS_TTS_OUTPUT_DIR")
        or Path(__file__).resolve().parents[2] / "var" / "tts"
    ).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / _output_filename(text, target)

    env = os.environ.copy()
    if resolved_vendor.exists():
        current_pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = (
            f"{resolved_vendor}{os.pathsep}{current_pythonpath}"
            if current_pythonpath
            else str(resolved_vendor)
        )

    command = _build_piper_command(
        resolved_bin,
        python_bin=python_bin or os.getenv("EOS_TTS_PIPER_PYTHON"),
    ) + [
        "--model",
        str(resolved_model),
        "--config",
        str(resolved_config),
        "--output_file",
        str(output_path),
    ]
    completed = subprocess.run(
        command,
        input=text,
        capture_output=True,
        text=True,
        env=env,
    )
    if completed.returncode != 0:
        return failure_result(
            status="provider_error",
            provider=PROVIDER_NAME,
            error=_best_process_error(completed),
            audio_path=output_path,
            mime_type="audio/wav",
            duration_estimate=estimate_duration_seconds(text),
        )

    if not output_path.exists():
        return failure_result(
            status="provider_error",
            provider=PROVIDER_NAME,
            error="Piper finished without creating an audio file.",
            audio_path=output_path,
            mime_type="audio/wav",
            duration_estimate=estimate_duration_seconds(text),
        )

    return success_result(
        provider=PROVIDER_NAME,
        audio_path=output_path,
        mime_type="audio/wav",
        duration_estimate=estimate_duration_seconds(text),
    )


def _resolve_piper_bin(piper_bin: str | Path | None) -> Path:
    configured = piper_bin or os.getenv("EOS_TTS_PIPER_BIN")
    if configured:
        return Path(configured).expanduser()
    discovered = shutil.which("piper")
    if discovered:
        return Path(discovered)
    return DEFAULT_PIPER_BIN


def _output_filename(text: str, target: str) -> str:
    digest = hashlib.sha256(f"{target}\n{text}".encode("utf-8")).hexdigest()[:16]
    safe_target = "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in target)
    return f"{safe_target}-{digest}.wav"


def _build_piper_command(piper_bin: Path, *, python_bin: str | Path | None) -> list[str]:
    if python_bin:
        return [str(Path(python_bin).expanduser()), str(piper_bin)]
    return [str(piper_bin)]


def _best_process_error(completed: subprocess.CompletedProcess[str]) -> str:
    for value in (completed.stderr, completed.stdout):
        if value and value.strip():
            return value.strip()
    return f"Piper exited with code {completed.returncode}."
