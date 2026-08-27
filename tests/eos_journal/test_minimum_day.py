from __future__ import annotations

import json
from pathlib import Path

from src.eos_journal.minimum_day import recommend_minimum_day
from src.eos_journal.types import DailySignalInput

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "journal"


def load_signal(name: str) -> DailySignalInput:
    return DailySignalInput.from_dict(json.loads((FIXTURE_ROOT / f"{name}.json").read_text(encoding="utf-8")))


def test_minimum_day_for_normal_day() -> None:
    assert recommend_minimum_day(load_signal("stable_day")) == [
        "1 Deep Work Block",
        "Mailblock",
        "Sport/Routine",
    ]


def test_minimum_day_for_bad_day() -> None:
    assert recommend_minimum_day(load_signal("recovery_day")) == [
        "20 Minuten Bewegung",
        "1 kleiner Fokusblock",
        "Abend Shutdown",
    ]


def test_minimum_day_for_overloaded_day() -> None:
    assert recommend_minimum_day(load_signal("overloaded_calendar_day")) == [
        "Nur Pflichttermine",
        "1 wichtigste Aufgabe",
        "keine Zusatzbloecke",
    ]
