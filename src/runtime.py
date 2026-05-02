from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
CRON_JOBS_PATH = WORKSPACE_ROOT.parents[2] / ".openclaw" / "cron" / "jobs.json"
CRON_RUNS_DIR = WORKSPACE_ROOT.parents[2] / ".openclaw" / "cron" / "runs"
AGENT_MODELS_PATH = WORKSPACE_ROOT.parents[2] / ".openclaw" / "agents" / "personal-assistant" / "agent" / "models.json"

MODEL_PROFILES = {
    "fast": "gpt-5.4-mini",
    "standard": "gpt-5.4-mini",
    "deep": "gpt-5.4",
}


def load_env_file(start: Path | None = None) -> Path | None:
    current = (start or WORKSPACE_ROOT).resolve()
    for candidate_root in (current, *current.parents):
        env_path = candidate_root / ".env"
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
        return env_path
    return None


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def public_job_summary(job: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") or {}
    delivery = job.get("delivery") or {}
    state = job.get("state") or {}
    return {
        "id": job.get("id"),
        "name": job.get("name"),
        "enabled": bool(job.get("enabled")),
        "schedule": job.get("schedule"),
        "session_target": job.get("sessionTarget"),
        "delivery_mode": delivery.get("mode"),
        "delivery_channel": delivery.get("channel"),
        "delivery_to": delivery.get("to"),
        "model": payload.get("model") or job.get("model"),
        "light_context": payload.get("lightContext"),
        "timeout_seconds": payload.get("timeoutSeconds"),
        "last_status": state.get("lastStatus") or state.get("lastRunStatus"),
        "last_delivery_status": state.get("lastDeliveryStatus"),
        "consecutive_errors": state.get("consecutiveErrors", 0),
        "last_error": state.get("lastError"),
        "next_run_at_ms": state.get("nextRunAtMs"),
    }
