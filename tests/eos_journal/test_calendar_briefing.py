from __future__ import annotations

from src.eos_journal.calendar_briefing import CalendarBriefingContext, summarize_calendar_context


def test_calendar_briefing_empty_context_is_silent() -> None:
    assert summarize_calendar_context(None) == []


def test_calendar_briefing_from_mapping_sanitizes_missing_values() -> None:
    context = CalendarBriefingContext.from_mapping(
        {
            "fixed_event_count": "2",
            "deep_session_count": None,
            "reminder_count": "bad",
            "first_event": " 09:00 Uni ",
            "last_event": "",
            "load_label": "mittel",
            "carry_items": ["Laptop", "", "Sporttasche"],
        }
    )

    assert context is not None
    assert context.fixed_event_count == 2
    assert context.deep_session_count == 0
    assert context.reminder_count == 0
    assert context.first_event == "09:00 Uni"
    assert context.last_event is None
    assert context.carry_items == ("Laptop", "Sporttasche")


def test_calendar_briefing_summary_is_compact_and_count_based() -> None:
    lines = summarize_calendar_context(
        CalendarBriefingContext(
            fixed_event_count=1,
            deep_session_count=1,
            reminder_count=1,
            first_event="Ganztags Klausurphase",
            last_event="20:00 Abendroutine",
            load_label="hoch",
            carry_items=("Wasser", "Notizbuch"),
        )
    )

    assert lines == [
        "Kalender: 1 fester Termin, 1 Deep-Session, 1 Erinnerung, Last: hoch.",
        "Rahmen: Start mit Ganztags Klausurphase; Ende mit 20:00 Abendroutine.",
        "Mitnehmen: Wasser, Notizbuch.",
    ]
