#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.audits import audit_cron, audit_models


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        jobs_path = tmp_path / "jobs.json"
        models_path = tmp_path / "models.json"
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()

        jobs_path.write_text(
            json.dumps(
                {
                    "jobs": [
                        {
                            "id": "missing-delivery",
                            "name": "Daily without Telegram",
                            "enabled": True,
                            "delivery": {"mode": "announce"},
                            "state": {},
                            "payload": {"model": "gpt-5.4-mini"},
                        },
                        {
                            "id": "bad-model",
                            "name": "Weekly bad model",
                            "enabled": True,
                            "delivery": {
                                "mode": "announce",
                                "channel": "telegram",
                                "to": "telegram:123",
                            },
                            "state": {"consecutiveErrors": 1, "lastError": "previous failure"},
                            "payload": {"model": "openai/gpt-5-mini"},
                        },
                        {
                            "id": "host-path",
                            "name": "Host path payload",
                            "enabled": True,
                            "delivery": {
                                "mode": "announce",
                                "channel": "telegram",
                                "to": "telegram:123",
                            },
                            "state": {},
                            "payload": {
                                "model": "gpt-5.4-mini",
                                "message": "cd /docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant && python3 -m src.eos_cli health",
                            },
                        },
                        {
                            "id": "green-but-bad",
                            "name": "Delivered failure summary",
                            "enabled": True,
                            "delivery": {
                                "mode": "announce",
                                "channel": "telegram",
                                "to": "telegram:123",
                            },
                            "state": {},
                            "payload": {"model": "gpt-5.4-mini"},
                        },
                        {
                            "id": "approval-loop",
                            "name": "Delivered approval prompt",
                            "enabled": True,
                            "delivery": {
                                "mode": "announce",
                                "channel": "telegram",
                                "to": "telegram:123",
                            },
                            "state": {},
                            "payload": {"model": "gpt-5.4-mini"},
                        },
                    ]
                }
            ),
            encoding="utf-8",
        )
        (runs_dir / "green-but-bad.jsonl").write_text(
            json.dumps(
                {
                    "status": "ok",
                    "summary": "Calendar/Tasks nicht success, der CLI-Befehl ist fehlgeschlagen: cd: can't cd to /docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant",
                    "deliveryStatus": "delivered",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (runs_dir / "approval-loop.jsonl").write_text(
            json.dumps(
                {
                    "status": "ok",
                    "summary": "/approve a442be71 allow-once",
                    "deliveryStatus": "delivered",
                }
            )
            + "\n",
            encoding="utf-8",
        )
        models_path.write_text(
            json.dumps(
                {
                    "providers": {
                        "codex": {
                            "models": [
                                {"id": "gpt-5.4-mini"},
                                {"id": "gpt-5.4"},
                            ]
                        }
                    }
                }
            ),
            encoding="utf-8",
        )

        cron = audit_cron(jobs_path, runs_dir=runs_dir)
        model = audit_models(jobs_path=jobs_path, models_path=models_path)

    cron_codes = {issue["code"] for issue in cron["issues"]}
    model_codes = {issue["code"] for issue in model["issues"]}

    assert cron["status"] == "warning"
    assert "delivery_target_missing" in cron_codes
    assert "last_run_error" in cron_codes
    assert "unexpected_model" in cron_codes
    assert "host_path_in_payload" in cron_codes
    assert "latest_run_summary_error" in cron_codes
    assert model["status"] == "warning"
    assert "job_model_missing" in model_codes
    print("verify_cron_audit: ok")


if __name__ == "__main__":
    main()
