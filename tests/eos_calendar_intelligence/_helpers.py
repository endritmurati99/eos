from __future__ import annotations

import json
from pathlib import Path

from src.eos_calendar_intelligence import CalendarEventInput


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "calendar_intelligence"


def load_event(name: str) -> CalendarEventInput:
    payload = json.loads((FIXTURE_ROOT / f"{name}.json").read_text(encoding="utf-8"))
    if "events" in payload:
        raise ValueError(f"{name} contains multiple events")
    return CalendarEventInput(**payload)


def load_events(name: str) -> list[CalendarEventInput]:
    payload = json.loads((FIXTURE_ROOT / f"{name}.json").read_text(encoding="utf-8"))
    if "events" not in payload:
        return [CalendarEventInput(**payload)]
    return [CalendarEventInput(**event) for event in payload["events"]]
