from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]


def discover_openclaw_root(start: Path | None = None) -> Path:
    env_root = os.getenv("EOS_OPENCLAW_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    current = (start or WORKSPACE_ROOT).expanduser().resolve()
    if current.is_file():
        current = current.parent

    for candidate_root in (current, *current.parents):
        if candidate_root == candidate_root.parent:
            continue
        if (candidate_root / ".openclaw").exists():
            return candidate_root
        if (candidate_root / "data" / ".openclaw").exists():
            return candidate_root

    return WORKSPACE_ROOT


def _openclaw_state_root(openclaw_root: Path) -> Path:
    data_state = openclaw_root / "data" / ".openclaw"
    if data_state.exists():
        return data_state

    direct_state = openclaw_root / ".openclaw"
    if direct_state.exists():
        return direct_state

    return direct_state


OPENCLAW_ROOT = discover_openclaw_root()
OPENCLAW_STATE_ROOT = _openclaw_state_root(OPENCLAW_ROOT)
CRON_JOBS_PATH = OPENCLAW_STATE_ROOT / "cron" / "jobs.json"
CRON_RUNS_DIR = OPENCLAW_STATE_ROOT / "cron" / "runs"
AGENT_MODELS_PATH = OPENCLAW_STATE_ROOT / "agents" / "personal-assistant" / "agent" / "models.json"

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
