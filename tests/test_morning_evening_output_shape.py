from __future__ import annotations

from src.jobs.evening_reset import _render_evening_reset
from src.jobs.runner import _render_daily_morning, _render_habit_checkin


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

    assert "🌙 Abendbriefing" in output
    assert "Abendroutine" not in output
    assert "Morgenkalender: 1 feste Termine" in output
    assert "Wasser: Flasche sichtbar" in output
    assert "Was ist heute passiert?" in output


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

    assert "☀️ Morgenbriefing" in output
    assert "📌 Fix" in output
    assert "Kalender: 2 feste Termine" in output
    assert "Wasser: Flasche sichtbar" in output


def test_habit_checkin_many_habits_uses_time_appropriate_compaction() -> None:
    habits = [
        {"pending": True, "target_time": "20:00", "name": f"Habit {index:02d}"}
        for index in range(8)
    ]
    base = {"business_date_berlin": "2026-05-15", "habits": habits}

    evening = _render_habit_checkin("habit_checkin_evening", base)
    morning = _render_habit_checkin("habit_checkin_morning", base)

    assert "Habit 00" in evening
    assert "Habit 07" not in evening
    assert "+ 3 weitere" in evening
    assert "Abendbriefing" in evening
    assert "Was ist heute passiert?" in evening

    assert "Abendbriefing" not in morning
    assert "Minimum-Version" in morning
