#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
import os
from pathlib import Path
import sys
import tempfile

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.gateways.google_tasks import CANONICAL_LISTS
import src.jobs.weekly_plan as weekly_plan


class FakeGateway:
    def readOpenTasks(self, list_names=None):  # noqa: N802
        names = tuple(list_names or CANONICAL_LISTS)
        return {
            "provider": "fake",
            "task_read_status": "success",
            "tasks_by_list": {
                name: (
                    [
                        {
                            "id": "task-1",
                            "title": "Weekly Test Task",
                            "due": "2026-05-05T00:00:00.000Z",
                        }
                    ]
                    if name == "Inbox"
                    else []
                )
                for name in names
            },
            "failed_lists": [],
            "open_task_count": 1,
        }


def fake_calendar_events(*, target_date_berlin, **_kwargs):
    events = []
    if target_date_berlin == date(2026, 5, 5):
        events = [
            {"title": "Arbeit", "start_display": "09:00", "end_display": "17:00"},
            {"title": "Gym", "start_display": "18:00", "end_display": "19:00"},
            {"title": "BJJ", "start_display": "20:00", "end_display": "21:30"},
        ]
    return {
        "calendar_read_status": "success",
        "source": "fake",
        "hard_events": events,
        "error": None,
    }


def main() -> None:
    original_gateway = weekly_plan.TaskGateway
    original_calendar = weekly_plan._load_calendar_events
    original_db_path = os.environ.get("EOS_DB_PATH")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["EOS_DB_PATH"] = str(Path(tmp) / "eos.db")
            weekly_plan.TaskGateway = FakeGateway
            weekly_plan._load_calendar_events = fake_calendar_events
            result = weekly_plan.run_weekly_plan(date(2026, 5, 4), dry_run=True)
    finally:
        weekly_plan.TaskGateway = original_gateway
        weekly_plan._load_calendar_events = original_calendar
        if original_db_path is None:
            os.environ.pop("EOS_DB_PATH", None)
        else:
            os.environ["EOS_DB_PATH"] = original_db_path

    assert result["status"] == "success"
    assert result["dry_run"] is True
    assert result["week_start_berlin"] == "2026-05-04"
    assert result["task_read_status"] == "success"
    assert result["open_task_count"] == 1
    assert result["habit_report"]["status"] == "success"
    assert result["evaluation"]["stacked_days"] == ["2026-05-05"]
    assert "Weekly Test Task" in result["output_markdown"]
    assert "🔁 Gewohnheiten" in result["output_markdown"]
    print("verify_weekly_plan_dry_run: ok")


if __name__ == "__main__":
    main()
