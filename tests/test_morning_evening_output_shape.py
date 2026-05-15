from __future__ import annotations

from src.jobs.evening_reset import _render_evening_reset
from src.jobs.runner import _render_daily_morning


def test_evening_reset_output_is_compact_deduped_and_has_water_check() -> None:
    output = _render_evening_reset(
        target_date_berlin=__import__("datetime").date(2026, 5, 16),
        calendar_result={
            "source": "live_gog",
            "hard_events": [
                {"title": "Abendroutine", "start_display": "21:30", "end_display": "22:00"},
                {"title": "Abendroutine", "start_display": "21:30", "end_display": "22:00"},
                {"title": "Deep Work", "start_display": "09:00", "end_display": "10:30"},
            ],
        },
        task_bundle={"task_read_status": "provider_error", "tasks_by_list": {}},
        evaluation={
            "priorities": [],
            "prep_items": [],
            "assessment": "Status: YELLOW.",
            "recommendation": "Top-1 halten.",
            "warning": "Tasks fehlen.",
        },
    )

    assert output.count("21:30-22:00 Abendroutine") == 1
    assert "Morgenkalender: 2 feste Termine" in output
    assert "Wasser: Flasche sichtbar" in output


def test_daily_morning_output_includes_calendar_shape_and_water_check() -> None:
    output = _render_daily_morning(
        {
            "calendar_read_status": "success",
            "task_read_status": "success",
            "calendar_blocks": [
                {"title": "Deep Work", "start": "09:00", "end": "10:30"},
                {"title": "Microneedling Reminder", "start": "20:00", "end": "20:20"},
            ],
            "recommendation": "Ein Fokusblock reicht.",
            "top_tasks": [],
            "habit_status": {"habits": []},
        }
    )

    assert "## Heute steht an" in output
    assert "Kalender: 2 feste Termine" in output
    assert "Wasser: Flasche sichtbar" in output
