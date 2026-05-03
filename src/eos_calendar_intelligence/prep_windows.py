from __future__ import annotations

from datetime import timedelta

from src.eos_calendar_intelligence.types import (
    CalendarEventInput,
    PrepWindowSuggestion,
    clamp_confidence,
    event_search_text,
    format_time_window,
    keyword_matches,
    parse_event_datetime,
)


IMPORTANT_KEYWORDS = ("deadline", "interview", "client", "arzt", "doctor", "exam", "klausur")
MEDIUM_KEYWORDS = ("review", "sync", "project", "projekt", "decision", "call")


def suggest_prep_windows(
    events: list[CalendarEventInput],
    busy_events: list[CalendarEventInput] | None = None,
) -> list[PrepWindowSuggestion]:
    busy = busy_events or events
    suggestions: list[PrepWindowSuggestion] = []
    for event in sorted(events, key=lambda item: parse_event_datetime(item.start)):
        duration = prep_duration_minutes(event)
        start = parse_event_datetime(event.start)
        window_end = start
        window_start = start - timedelta(minutes=duration)
        if _overlaps_any(window_start, window_end, busy, exclude_event_id=event.event_id):
            window_start = start - timedelta(minutes=duration + 15)
            window_end = start - timedelta(minutes=15)
        suggestions.append(
            PrepWindowSuggestion(
                event_id=event.event_id,
                title=event.title,
                duration_minutes=duration,
                window_start=window_start.isoformat(),
                window_end=window_end.isoformat(),
                reason=f"{duration} min prep suggested before {format_time_window(event)}",
                confidence=clamp_confidence(0.72 + (duration / 300)),
            )
        )
    return suggestions


def prep_duration_minutes(event: CalendarEventInput) -> int:
    text = event_search_text(event)
    if any(keyword_matches(text, keyword) for keyword in IMPORTANT_KEYWORDS):
        return 60
    if any(keyword_matches(text, keyword) for keyword in MEDIUM_KEYWORDS) or len(event.attendees) >= 3:
        return 30
    return 15


def _overlaps_any(
    start,
    end,
    busy_events: list[CalendarEventInput],
    *,
    exclude_event_id: str,
) -> bool:
    for event in busy_events:
        if event.event_id == exclude_event_id:
            continue
        busy_start = parse_event_datetime(event.start)
        busy_end = parse_event_datetime(event.end)
        if start < busy_end and end > busy_start:
            return True
    return False
