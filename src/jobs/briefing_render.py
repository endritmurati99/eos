from __future__ import annotations

from typing import Any, Mapping


DEFAULT_EVENT_LIMIT = 6


def compact_event_lines(events: list[Mapping[str, Any]], *, limit: int = DEFAULT_EVENT_LIMIT) -> list[str]:
    unique = _unique_events(events)
    ordered = sorted(unique, key=_event_sort_key)
    rendered = [_format_event_line(event) for event in ordered[:limit]]
    remaining = len(ordered) - len(rendered)
    if remaining > 0:
        rendered.append(f"+ {remaining} weitere feste Termine im Kalender.")
    return rendered


def calendar_shape_line(events: list[Mapping[str, Any]], *, prefix: str = "Kalender") -> str:
    unique = _unique_events(events)
    fixed_count = len(unique)
    deep_count = sum(1 for event in unique if _looks_like_deep_session(event))
    reminder_count = sum(1 for event in unique if _looks_like_reminder(event))
    load = _load_label(fixed_count)
    return (
        f"{prefix}: {fixed_count} feste Termine, "
        f"{deep_count} Deep-Sessions, {reminder_count} Erinnerungen, Last: {load}."
    )


def hydration_check_line() -> str:
    return "Wasser: Flasche sichtbar hinstellen und vor dem ersten Fokusblock trinken."


def _unique_events(events: list[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    seen: set[tuple[str, str, str]] = set()
    unique: list[Mapping[str, Any]] = []
    for event in events:
        key = (
            str(event.get("start_display") or event.get("start") or ""),
            str(event.get("end_display") or event.get("end") or ""),
            _normalize_title(str(event.get("title") or "(ohne Titel)")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(event)
    return unique


def _format_event_line(event: Mapping[str, Any]) -> str:
    start = str(event.get("start_display") or event.get("start") or "").strip()
    end = str(event.get("end_display") or event.get("end") or "").strip()
    title = str(event.get("title") or "(ohne Titel)").strip()
    if start and end:
        return f"{start}-{end} {title}"
    if start:
        return f"{start} {title}"
    return title


def _event_sort_key(event: Mapping[str, Any]) -> tuple[int, str, str]:
    start = str(event.get("start_display") or event.get("start") or "")
    if start.lower() == "ganztags":
        return (0, "00:00", str(event.get("title") or ""))
    if len(start) >= 5 and start[2:3] == ":":
        return (1, start[:5], str(event.get("title") or ""))
    return (2, start, str(event.get("title") or ""))


def _looks_like_deep_session(event: Mapping[str, Any]) -> bool:
    title = _normalize_title(str(event.get("title") or ""))
    return any(token in title for token in ("deep", "fokus", "focus", "lernen", "coding", "arbeit"))


def _looks_like_reminder(event: Mapping[str, Any]) -> bool:
    title = _normalize_title(str(event.get("title") or ""))
    return any(token in title for token in ("reminder", "erinner", "microneedling", "routine", "wasser", "pack"))


def _load_label(fixed_count: int) -> str:
    if fixed_count >= 7:
        return "hoch"
    if fixed_count >= 4:
        return "mittel"
    return "ruhig"


def _normalize_title(title: str) -> str:
    return " ".join(title.casefold().split())
