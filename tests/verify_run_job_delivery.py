#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src import eos_cli  # noqa: E402
import src.jobs.runner as runner  # noqa: E402


def fake_calendar_events(*, target_date_berlin, **_kwargs):  # noqa: ANN001
    assert target_date_berlin == date(2026, 5, 1)
    return {
        "status": "success",
        "calendar_read_status": "success",
        "source": "fake",
        "hard_events": [],
        "error": None,
    }


def main() -> None:
    send_reject = eos_cli.command_run_job(
        type(
            "Args",
            (),
            {
                "job": "daily_hang_reminder",
                "date": None,
                "week_start": None,
                "dry_run": True,
                "send": True,
            },
        )()
    )
    assert send_reject["status"] == "failed"
    assert "--send cannot be used" in send_reject["error"]

    original_calendar = runner._load_calendar_events
    try:
        runner._load_calendar_events = fake_calendar_events
        skipped = runner.run_eos_job(
            "sport_prep_reminder",
            target_date=date(2026, 5, 1),
            dry_run=False,
            workspace_root=WORKSPACE_ROOT,
        )
    finally:
        runner._load_calendar_events = original_calendar

    assert skipped["status"] == "skipped"
    assert skipped["delivery_status"] == "skipped"
    assert skipped["sport_event_count"] == 0
    assert skipped["skip_reason"] == "no_sport_event"

    hang = runner.run_eos_job("daily_hang_reminder", target_date=date(2026, 5, 1), dry_run=True)
    assert hang["status"] == "success"
    assert "Klimmzugstangen-Check" in hang["output_markdown"]

    print("verify_run_job_delivery: ok")


if __name__ == "__main__":
    main()
