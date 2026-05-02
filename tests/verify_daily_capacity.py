#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.jobs.daily_capacity import run_daily_capacity  # noqa: E402
import src.jobs.daily_capacity as daily_capacity  # noqa: E402


class OfflineTaskGateway:
    gog_bin = None
    account = None
    token_root = None

    def get_canonical_open_tasks(self, list_names=None):  # noqa: ANN001
        return {
            "provider": "gog_tasks",
            "task_read_status": "provider_disabled",
            "tasks_by_list": {list_name: [] for list_name in (list_names or ())},
            "failed_lists": [
                {
                    "list_name": list_name,
                    "status": "provider_disabled",
                    "error": "Google Tasks API disabled: accessNotConfigured",
                }
                for list_name in (list_names or ())
            ],
            "open_task_count": 0,
        }


def main() -> int:
    original_gateway = daily_capacity.TaskGateway
    daily_capacity.TaskGateway = OfflineTaskGateway
    try:
        live_default = run_daily_capacity(date(2026, 4, 23))
    finally:
        daily_capacity.TaskGateway = original_gateway

    assert live_default["calendar_source"] != "stub_file"
    assert live_default["calendar_read_status"] == "config_missing"
    assert live_default["task_source"] == "live_gog"
    assert live_default["task_read_status"] == "provider_disabled"
    assert live_default["ranked_tasks"] == []
    assert live_default["top_tasks"] == []
    assert "TASK BASIS WEAK" in live_default["recommendation"]

    result = run_daily_capacity(
        date(2026, 4, 23),
        allow_stub_calendar=True,
        allow_stub_tasks=True,
        prefer_live_calendar=False,
        prefer_live_tasks=False,
    )

    assert result["job"] == "daily_capacity"
    assert result["dry_run"] is True
    assert result["target_date_berlin"] == "2026-04-23"
    assert result["calendar_source"] == "stub_file"
    assert result["task_source"] == "google_tasks_stub"
    assert result["capacity"]["blocked_min"] == 555
    assert result["capacity"]["buffer_min"] == 192
    assert result["capacity"]["available_min"] == 213
    assert result["status"] == "yellow"
    assert result["triage_required"] is True
    assert result["top_tasks"] == []
    assert len(result["untriaged_tasks"]) >= 1

    morning = next(
        habit for habit in result["habit_versions"]
        if habit["habit_id"] == "habit-morning-routine"
    )
    assert morning["version"] == "minimum"

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
