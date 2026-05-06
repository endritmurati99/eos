from __future__ import annotations

from src.eos_calendar_intelligence import detect_calendar_conflicts

from tests.eos_calendar_intelligence._helpers import load_event, load_events


def test_overlap_is_high_risk_conflict() -> None:
    report = detect_calendar_conflicts(load_events("overlapping_meetings"))

    assert report.risk_level == "high"
    assert any("Overlap" in issue for issue in report.issues)
    assert report.suggestions


def test_back_to_back_and_no_break_day_are_detected() -> None:
    report = detect_calendar_conflicts(load_events("no_break_day"))

    assert any("No break" in issue for issue in report.issues)
    assert any("more than 4 hours" in issue for issue in report.issues)
    assert report.risk_level in {"medium", "high"}


def test_evening_overload_is_detected() -> None:
    report = detect_calendar_conflicts(load_events("evening_overload"))

    assert any("evening overload" in issue for issue in report.issues)


def test_sport_blocked_by_adjacent_event_is_detected() -> None:
    events = [
        load_event("project_sync").__class__(
            event_id="before_sport",
            title="Admin Call",
            start="2026-05-05T17:30:00",
            end="2026-05-05T18:00:00",
            location="Phone",
            description="Admin call before training.",
            attendees=["admin@example.test"],
            calendar_role="primary",
        ),
        load_event("sport_event"),
    ]

    report = detect_calendar_conflicts(events)

    assert any("sport block" in issue for issue in report.issues)


def test_meeting_without_prep_window_is_detected() -> None:
    events = [
        load_event("prep_needed_meeting"),
        load_event("low_priority_event"),
    ]
    report = detect_calendar_conflicts(events)

    assert any("no clear prep window" in issue for issue in report.issues)


def test_low_risk_day_reports_no_conflict() -> None:
    events = [load_event("project_sync"), load_event("low_priority_event")]
    report = detect_calendar_conflicts(events)

    assert report.risk_level == "low"
    assert report.issues == []
