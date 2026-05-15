from __future__ import annotations

from src.jobs.briefing_render import calendar_shape_line, compact_event_lines, hydration_check_line


def test_compact_event_lines_dedupes_sorts_and_limits() -> None:
    events = [
        {"title": "Abendroutine", "start_display": "21:30", "end_display": "22:00"},
        {"title": "Deep Work Solara", "start_display": "09:00", "end_display": "10:30"},
        {"title": "Abendroutine", "start_display": "21:30", "end_display": "22:00"},
        {"title": "Microneedling Reminder", "start_display": "20:00", "end_display": "20:20"},
        {"title": "Uni", "start_display": "06:45", "end_display": "12:00"},
    ]

    assert compact_event_lines(events, limit=3) == [
        "06:45-12:00 Uni",
        "09:00-10:30 Deep Work Solara",
        "20:00-20:20 Microneedling Reminder",
        "+ 1 weitere feste Termine im Kalender.",
    ]


def test_calendar_shape_line_counts_deep_sessions_and_reminders() -> None:
    events = [
        {"title": "Deep Work Solara", "start_display": "09:00", "end_display": "10:30"},
        {"title": "Microneedling Erinnerung", "start_display": "20:00", "end_display": "20:20"},
        {"title": "BJJ", "start_display": "18:00", "end_display": "19:30"},
        {"title": "BJJ", "start_display": "18:00", "end_display": "19:30"},
    ]

    assert calendar_shape_line(events, prefix="Morgenkalender") == "Morgenkalender: 3 feste Termine, 1 Deep-Sessions, 1 Erinnerungen, Last: ruhig."


def test_hydration_check_line_is_short() -> None:
    assert hydration_check_line() == "Wasser: Flasche sichtbar hinstellen und vor dem ersten Fokusblock trinken."
