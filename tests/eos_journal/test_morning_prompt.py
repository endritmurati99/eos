from __future__ import annotations

import json
from pathlib import Path

from src.eos_journal.morning_prompt import generate_morning_prompt
from src.eos_journal.types import DailySignalInput

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "journal"
FORBIDDEN_LANGUAGE = ("schuld", "streak", "bestraf", "therapie", "diagnose", "medizin")


def load_signal(name: str) -> DailySignalInput:
    return DailySignalInput.from_dict(json.loads((FIXTURE_ROOT / f"{name}.json").read_text(encoding="utf-8")))


def test_morning_prompt_is_short_and_structured() -> None:
    output = generate_morning_prompt(load_signal("normal_workday"))

    assert output.status == "stable"
    assert len(output.message) <= 260
    assert "Fokus:" in output.message
    assert "Minimum:" in output.message
    assert "Risiko:" in output.message
    assert output.notification_allowed is True
    assert output.minimum_day_actions[0] == "1 Deep Work Block"


def test_morning_prompt_avoids_guilt_streak_and_medical_language() -> None:
    output = generate_morning_prompt(load_signal("sick_day"))
    rendered = f"{output.headline} {output.message}".lower()

    for forbidden in FORBIDDEN_LANGUAGE:
        assert forbidden not in rendered
    assert output.status == "recovery_needed"
    assert output.minimum_day_actions == [
        "20 Minuten Bewegung",
        "1 kleiner Fokusblock",
        "Abend Shutdown",
    ]


def test_morning_prompt_uses_unattributed_placeholder_quote() -> None:
    output = generate_morning_prompt(load_signal("stable_day"))

    assert "Zitat:" in output.message
    assert "Marcus" not in output.message
    assert "Seneca" not in output.message
