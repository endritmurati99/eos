from __future__ import annotations

from collections import defaultdict
from datetime import time

from src.eos_calendar_intelligence.prep_windows import prep_duration_minutes
from src.eos_calendar_intelligence.types import (
    CalendarConflictReport,
    CalendarEventInput,
    event_duration_minutes,
    event_search_text,
    format_time_window,
    keyword_matches,
    parse_event_datetime,
)


def detect_calendar_conflicts(events: list[CalendarEventInput]) -> CalendarConflictReport:
    sorted_events = sorted(events, key=lambda event: parse_event_datetime(event.start))
    issues: list[str] = []
    suggestions: list[str] = []

    overlap_issues, overlap_suggestions = _overlap_issues(sorted_events)
    issues.extend(overlap_issues)
    suggestions.extend(overlap_suggestions)
    issues.extend(_back_to_back_issues(sorted_events))

    by_day: dict[str, list[CalendarEventInput]] = defaultdict(list)
    for event in sorted_events:
        by_day[parse_event_datetime(event.start).date().isoformat()].append(event)

    for day, day_events in by_day.items():
        total_minutes = sum(event_duration_minutes(event) for event in day_events)
        if total_minutes > 240:
            issues.append(f"{day}: more than 4 hours of meetings ({total_minutes} min).")
            suggestions.append(f"{day}: protect recovery buffers and reduce optional meetings.")
        if not _has_deep_work_window(day_events):
            issues.append(f"{day}: no 90 min deep-work window detected.")
            suggestions.append(f"{day}: keep at least one uninterrupted deep-work block.")
        if _has_evening_overload(day_events):
            issues.append(f"{day}: evening overload after 18:00.")
            suggestions.append(f"{day}: move low-priority evening items or lower expectations.")
        if _sport_blocked(day_events):
            issues.append(f"{day}: sport block is overlapped or squeezed by another event.")
            suggestions.append(f"{day}: preserve sport buffer or move the conflicting item.")
        for event in day_events:
            if prep_duration_minutes(event) >= 30 and not _has_prep_window(event, day_events):
                issues.append(f"{event.title}: meeting has no clear prep window.")
                suggestions.append(f"{event.title}: schedule read-only prep before the event.")

    risk_level = _risk_level(issues)
    if not suggestions and not issues:
        suggestions.append("No calendar conflict detected from synthetic event data.")

    return CalendarConflictReport(
        risk_level=risk_level,
        issues=_unique(issues),
        suggestions=_unique(suggestions),
    )


def _overlap_issues(events: list[CalendarEventInput]) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    suggestions: list[str] = []
    for previous, current in zip(events, events[1:]):
        previous_end = parse_event_datetime(previous.end)
        current_start = parse_event_datetime(current.start)
        if previous_end > current_start:
            issues.append(
                f"Overlap: {previous.title} conflicts with {current.title} ({format_time_window(current)})."
            )
            suggestions.append(f"Resolve overlap between {previous.title} and {current.title}.")
    return issues, suggestions


def _back_to_back_issues(events: list[CalendarEventInput]) -> list[str]:
    issues: list[str] = []
    for previous, current in zip(events, events[1:]):
        previous_end = parse_event_datetime(previous.end)
        current_start = parse_event_datetime(current.start)
        if previous_end.date() != current_start.date() or previous_end > current_start:
            continue
        gap = int((current_start - previous_end).total_seconds() // 60)
        if gap < 10:
            issues.append(f"No break: {previous.title} into {current.title} has only {gap} min buffer.")
    return issues


def _has_deep_work_window(events: list[CalendarEventInput]) -> bool:
    day_start = parse_event_datetime(events[0].start).replace(hour=8, minute=0, second=0, microsecond=0)
    day_end = parse_event_datetime(events[0].start).replace(hour=18, minute=0, second=0, microsecond=0)
    cursor = day_start
    for event in sorted(events, key=lambda item: parse_event_datetime(item.start)):
        start = parse_event_datetime(event.start)
        end = parse_event_datetime(event.end)
        if start > cursor and int((start - cursor).total_seconds() // 60) >= 90:
            return True
        if end > cursor:
            cursor = end
    return day_end > cursor and int((day_end - cursor).total_seconds() // 60) >= 90


def _has_evening_overload(events: list[CalendarEventInput]) -> bool:
    evening_minutes = 0
    evening_count = 0
    for event in events:
        start = parse_event_datetime(event.start)
        if start.time() >= time(18, 0):
            evening_count += 1
            evening_minutes += event_duration_minutes(event)
    return evening_count >= 2 or evening_minutes >= 120


def _sport_blocked(events: list[CalendarEventInput]) -> bool:
    sport_events = [event for event in events if _looks_like_sport(event)]
    if not sport_events:
        return False
    for sport in sport_events:
        sport_start = parse_event_datetime(sport.start)
        sport_end = parse_event_datetime(sport.end)
        for event in events:
            if event.event_id == sport.event_id:
                continue
            start = parse_event_datetime(event.start)
            end = parse_event_datetime(event.end)
            if start < sport_end and end > sport_start:
                return True
            gap_before = int((sport_start - end).total_seconds() // 60)
            gap_after = int((start - sport_end).total_seconds() // 60)
            if 0 <= gap_before < 15 or 0 <= gap_after < 15:
                return True
    return False


def _has_prep_window(event: CalendarEventInput, events: list[CalendarEventInput]) -> bool:
    required = prep_duration_minutes(event)
    start = parse_event_datetime(event.start)
    latest_busy_end = None
    for other in events:
        if other.event_id == event.event_id:
            continue
        other_end = parse_event_datetime(other.end)
        if other_end <= start and (latest_busy_end is None or other_end > latest_busy_end):
            latest_busy_end = other_end
    if latest_busy_end is None:
        day_start = start.replace(hour=8, minute=0, second=0, microsecond=0)
        available = int((start - day_start).total_seconds() // 60)
    else:
        available = int((start - latest_busy_end).total_seconds() // 60)
    return available >= required


def _looks_like_sport(event: CalendarEventInput) -> bool:
    text = event_search_text(event)
    return any(keyword_matches(text, keyword) for keyword in ("sport", "gym", "kickbox", "training", "bjj", "workout"))


def _risk_level(issues: list[str]) -> str:
    if any(issue.startswith("Overlap") for issue in issues) or len(issues) >= 5:
        return "high"
    if issues:
        return "medium"
    return "low"


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
