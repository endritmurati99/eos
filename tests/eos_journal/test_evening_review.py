from __future__ import annotations

import json
from pathlib import Path

from src.eos_journal.evening_review import generate_evening_review
from src.eos_journal.types import DailySignalInput

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "journal"
FORBIDDEN_LANGUAGE = ("schuld", "versagt", "streak", "bestraf", "therapie", "diagnose", "medizin")


def load_signal(name: str) -> DailySignalInput:
    return DailySignalInput.from_dict(json.loads((FIXTURE_ROOT / f"{name}.json").read_text(encoding="utf-8")))


def test_evening_review_has_required_sections() -> None:
    output = generate_evening_review(load_signal("overloaded_calendar_day"))

    assert "Stabil:" in output.message
    assert "Offen:" in output.message
    assert "Energieverlust:" in output.message
    assert "Morgen:" in output.message
    assert output.status == "overloaded"
    assert output.notification_allowed is True


def test_evening_review_has_no_guilt_or_therapy_language() -> None:
    output = generate_evening_review(load_signal("recovery_day"))
    rendered = f"{output.headline} {output.message}".lower()

    for forbidden in FORBIDDEN_LANGUAGE:
        assert forbidden not in rendered
    assert "Abend Review" in output.headline
