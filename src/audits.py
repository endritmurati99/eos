from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.runtime import (
    AGENT_MODELS_PATH,
    CRON_JOBS_PATH,
    CRON_RUNS_DIR,
    MODEL_PROFILES,
    WORKSPACE_ROOT,
    load_json,
    public_job_summary,
)


FAILURE_SUMMARY_MARKERS = (
    "can't cd",
    "cd: can't cd",
    "workspace-pfad nicht erreichbar",
    "cli-befehl ist fehlgeschlagen",
    "calendar/tasks nicht success",
    "requires target <chatid>",
    "current quota",
    "usage limit",
    "hit your chatgpt usage limit",
    "approval required",
    "/approve ",
    "approval-timeout",
    "no module named 'jsonschema'",
    "modulenotfounderror: no module named 'jsonschema'",
    "fehlendes python-modul `jsonschema`",
    "provider_disabled",
    "auth_required",
)


def audit_cron(
    jobs_path: str | Path | None = None,
    runs_dir: str | Path | None = None,
) -> dict[str, Any]:
    path = Path(jobs_path) if jobs_path is not None else CRON_JOBS_PATH
    run_log_dir = Path(runs_dir) if runs_dir is not None else CRON_RUNS_DIR
    payload = load_json(path, {"jobs": []})
    jobs = payload.get("jobs", [])
    issues = []

    for job in jobs:
        delivery = job.get("delivery") or {}
        state = job.get("state") or {}
        payload_model = (job.get("payload") or {}).get("model") or job.get("model")
        payload_message = str((job.get("payload") or {}).get("message") or "")
        enabled = bool(job.get("enabled"))

        if enabled and delivery.get("mode") == "announce":
            if delivery.get("channel") != "telegram" or not str(delivery.get("to") or "").startswith("telegram:"):
                issues.append(_issue(job, "delivery_target_missing", "Enabled announce job has no Telegram target."))

        if enabled and state.get("consecutiveErrors", 0):
            issues.append(_issue(job, "last_run_error", str(state.get("lastError") or "Previous run failed.")))

        if enabled and payload_model and payload_model not in set(MODEL_PROFILES.values()):
            issues.append(_issue(job, "unexpected_model", f"Job uses non-profile model: {payload_model}"))

        if enabled and "/docker/openclaw-qt6t/" in payload_message:
            issues.append(_issue(job, "host_path_in_payload", "Cron payload uses host-only /docker path; use /data path inside OpenClaw runtime."))

        if enabled and job.get("sessionTarget") == "isolated":
            issues.append(_issue(job, "isolated_session", "Isolated cron session may miss runtime tools/config."))

        latest_run = _latest_run_entry(job.get("id"), run_log_dir)
        if enabled and latest_run:
            issues.extend(_latest_run_issues(job, latest_run))

    status = "success" if not issues else "warning"
    return {
        "status": status,
        "jobs_path": str(path),
        "runs_dir": str(run_log_dir),
        "job_count": len(jobs),
        "enabled_count": sum(1 for job in jobs if job.get("enabled")),
        "issues": issues,
        "jobs": [public_job_summary(job) for job in jobs],
    }


def audit_models(
    *,
    jobs_path: str | Path | None = None,
    models_path: str | Path | None = None,
) -> dict[str, Any]:
    job_payload = load_json(Path(jobs_path) if jobs_path is not None else CRON_JOBS_PATH, {"jobs": []})
    model_payload = load_json(Path(models_path) if models_path is not None else AGENT_MODELS_PATH, {"providers": {}})
    available_models = _available_models(model_payload)
    jobs = job_payload.get("jobs", [])
    issues = []

    for profile, model_id in MODEL_PROFILES.items():
        if model_id not in available_models:
            issues.append({
                "code": "profile_model_missing",
                "profile": profile,
                "model": model_id,
                "message": f"Model profile {profile} points to unavailable model {model_id}.",
            })

    for job in jobs:
        if not job.get("enabled"):
            continue
        model_id = (job.get("payload") or {}).get("model") or job.get("model")
        if model_id and model_id not in available_models and model_id not in set(MODEL_PROFILES.values()):
            issues.append(_issue(job, "job_model_missing", f"Cron job uses unavailable model {model_id}."))

    return {
        "status": "success" if not issues else "warning",
        "model_profiles": MODEL_PROFILES,
        "available_models": sorted(available_models),
        "issues": issues,
    }


def audit_vault(workspace_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(workspace_root) if workspace_root is not None else WORKSPACE_ROOT
    vault_root = root / "vault"
    required_dirs = (
        "10 Inbox",
        "11 Daily Notes",
        "12 Projects",
        "13 Areas",
        "14 Knowledge",
        "15 Ideas",
        "90 Archive",
    )
    missing = [folder for folder in required_dirs if not (vault_root / folder).is_dir()]
    return {
        "status": "success" if not missing else "config_missing",
        "vault_root": str(vault_root),
        "missing_dirs": missing,
    }


def _available_models(payload: dict[str, Any]) -> set[str]:
    models = set()
    for provider in payload.get("providers", {}).values():
        for model in provider.get("models", []):
            if model.get("id"):
                models.add(model["id"])
    return models


def _issue(job: dict[str, Any], code: str, message: str) -> dict[str, Any]:
    return {
        "job_id": job.get("id"),
        "job_name": job.get("name"),
        "code": code,
        "message": message,
    }


def _latest_run_entry(job_id: Any, runs_dir: Path) -> dict[str, Any] | None:
    if not job_id:
        return None
    path = runs_dir / f"{job_id}.jsonl"
    if not path.exists():
        return None

    latest: dict[str, Any] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(entry, dict):
            latest = entry
    return latest


def _latest_run_issues(job: dict[str, Any], run: dict[str, Any]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    status = str(run.get("status") or "").lower()
    summary = str(run.get("summary") or "")
    error = str(run.get("error") or "")
    combined = f"{summary}\n{error}".lower()

    if status == "error":
        issues.append(_issue(job, "latest_run_log_error", error or summary or "Latest cron run logged status=error."))
    elif any(marker in combined for marker in FAILURE_SUMMARY_MARKERS):
        issues.append(
            _issue(
                job,
                "latest_run_summary_error",
                "Latest cron run was marked ok/delivered but its summary contains a failure signal.",
            )
        )

    delivery_status = str(run.get("deliveryStatus") or "").lower()
    if (job.get("delivery") or {}).get("mode") == "announce" and delivery_status and delivery_status != "delivered":
        issues.append(_issue(job, "latest_delivery_not_delivered", f"Latest delivery status: {delivery_status}"))

    return issues
