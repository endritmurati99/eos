from __future__ import annotations

import json
from pathlib import Path

from src.eos_journal.habit_trends import summarize_habit_trends
from src.eos_journal.types import DailySignalInput

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "journal"


def load_week(name: str) -> list[DailySignalInput]:
    payload = json.loads((FIXTURE_ROOT / f"{name}.json").read_text(encoding="utf-8"))
    return [DailySignalInput.from_dict(day) for day in payload["days"]]


def test_habit_trends_detect_repeated_missed_training() -> None:
    output = summarize_habit_trends(load_week("missed_training_week"))

    assert "training_repeatedly_missed" in output.risk_flags
    assert any("Training" in item for item in output.trend_summary)


def test_habit_trends_detect_stable_deep_work() -> None:
    output = summarize_habit_trends(load_week("deep_work_stable_week"))

    assert any("Deep Work war stabil" in item for item in output.trend_summary)
    assert "Deep Work Block beibehalten." in output.recommendations


def test_habit_trends_detect_sleep_and_mood_and_overload_risk() -> None:
    days = load_week("mood_decline_week") + load_week("bad_evening_shutdown_week")
    output = summarize_habit_trends(days)

    assert "sleep_unstable" in output.risk_flags
    assert "mood_declining" in output.risk_flags

    overloaded_days = [
        DailySignalInput(
            date=f"2026-05-{day:02d}",
            sleep_quality=6,
            energy_level=6,
            mood_level=6,
            stress_level=5,
            deep_work_done=True,
            training_done=True,
            evening_shutdown_done=True,
            open_task_count=14 if day >= 11 else 5,
            calendar_load_score=0.9 if day >= 11 else 0.4,
        )
        for day in range(7, 14)
    ]
    overload_output = summarize_habit_trends(overloaded_days)
    assert "overload_risk_rising" in overload_output.risk_flags
