from __future__ import annotations

from src.eos_location_intelligence import (
    CalendarLocationEvent,
    extract_event_location,
    is_same_location,
    normalize_location,
)


def test_location_extractor_normalizes_synthetic_location_labels() -> None:
    event = CalendarLocationEvent(
        event_id="office",
        title="Office",
        start="2026-05-04T09:00:00",
        end="2026-05-04T09:30:00",
        location="  Office   Example  ",
        calendar_role="primary",
    )

    assert extract_event_location(event) == "Office Example"
    assert normalize_location("Home") == "Home"
    assert is_same_location("office example", "Office Example") is True


def test_missing_and_tbd_locations_return_none() -> None:
    event = CalendarLocationEvent(
        event_id="missing",
        title="Missing",
        start="2026-05-04T09:00:00",
        end="2026-05-04T09:30:00",
        location=None,
        calendar_role="primary",
    )

    assert extract_event_location(event) is None
    assert normalize_location("TBD") is None
    assert normalize_location("online") is None


def test_ambiguous_placeholder_is_kept_without_real_address() -> None:
    assert normalize_location("Ambiguous Example") == "Ambiguous Example"
