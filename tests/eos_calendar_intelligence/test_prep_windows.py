from __future__ import annotations

from datetime import datetime

from src.eos_calendar_intelligence import suggest_prep_windows

from tests.eos_calendar_intelligence._helpers import load_event


def test_prep_window_duration_by_importance() -> None:
    suggestions = suggest_prep_windows(
        [
            load_event("low_priority_event"),
            load_event("project_sync"),
            load_event("prep_needed_meeting"),
        ]
    )
    durations = {suggestion.event_id: suggestion.duration_minutes for suggestion in suggestions}

    assert durations["low_priority_event"] == 15
    assert durations["project_sync"] == 30
    assert durations["prep_needed_meeting"] == 60


def test_prep_window_is_before_event_and_read_only() -> None:
    event = load_event("deadline_review")
    suggestion = suggest_prep_windows([event])[0]

    assert suggestion.event_id == event.event_id
    assert datetime.fromisoformat(suggestion.window_start) < datetime.fromisoformat(event.start)
    assert datetime.fromisoformat(suggestion.window_end) <= datetime.fromisoformat(event.start)
    assert suggestion.duration_minutes == 60
    assert 0.0 <= suggestion.confidence <= 1.0
    assert not hasattr(suggestion, "write_status")


def test_prep_window_moves_earlier_when_busy_slot_overlaps() -> None:
    event = load_event("deadline_review")
    busy = event.__class__(
        event_id="busy-before",
        title="Busy before deadline",
        start="2026-05-08T10:15:00",
        end="2026-05-08T10:45:00",
        location=None,
        description="Busy block.",
        attendees=[],
        calendar_role="primary",
    )
    suggestion = suggest_prep_windows([event], busy_events=[event, busy])[0]

    assert suggestion.window_end == "2026-05-08T10:45:00"
