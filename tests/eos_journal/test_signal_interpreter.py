from __future__ import annotations

import json
from pathlib import Path

from src.eos_journal.signal_interpreter import interpret_daily_signals
from src.eos_journal.types import DailySignalInput

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "journal"


def load_signal(name: str) -> DailySignalInput:
    return DailySignalInput.from_dict(json.loads((FIXTURE_ROOT / f"{name}.json").read_text(encoding="utf-8")))


def test_status_recognition_across_day_modes() -> None:
    assert interpret_daily_signals(load_signal("stable_day")).status == "stable"
    assert interpret_daily_signals(load_signal("low_sleep_day")).status == "tight"
    assert interpret_daily_signals(load_signal("overloaded_calendar_day")).status == "overloaded"
    assert interpret_daily_signals(load_signal("recovery_day")).status == "recovery_needed"


def test_signal_interpreter_adds_expected_risk_flags() -> None:
    high_stress = interpret_daily_signals(load_signal("high_stress_day"))
    overloaded = interpret_daily_signals(load_signal("overloaded_calendar_day"))

    assert "high_stress" in high_stress.risk_flags
    assert "missed_training" in high_stress.risk_flags
    assert "high_calendar_load" in overloaded.risk_flags
    assert "too_many_open_tasks" in overloaded.risk_flags
    assert "no_deep_work" in overloaded.risk_flags
