from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class CalendarBriefingContext:
    """Small, privacy-preserving calendar summary for journal prompts.

    The booklet layer should know the shape of the day without needing raw calendar
    payloads. Titles are optional and intentionally capped by callers/tests.
    """

    fixed_event_count: int = 0
    deep_session_count: int = 0
    reminder_count: int = 0
    first_event: str | None = None
    last_event: str | None = None
    load_label: str | None = None
    carry_items: tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "CalendarBriefingContext | None":
        if not payload:
            return None
        carry_items = payload.get("carry_items") or ()
        return cls(
            fixed_event_count=_safe_int(payload.get("fixed_event_count")),
            deep_session_count=_safe_int(payload.get("deep_session_count")),
            reminder_count=_safe_int(payload.get("reminder_count")),
            first_event=_optional_str(payload.get("first_event")),
            last_event=_optional_str(payload.get("last_event")),
            load_label=_optional_str(payload.get("load_label")),
            carry_items=tuple(str(item) for item in carry_items if str(item).strip())[:4],
        )


def summarize_calendar_context(context: CalendarBriefingContext | None) -> list[str]:
    if context is None:
        return []

    event_phrase = "fester Termin" if context.fixed_event_count == 1 else "feste Termine"
    deep_word = "Deep-Session" if context.deep_session_count == 1 else "Deep-Sessions"
    reminder_word = "Erinnerung" if context.reminder_count == 1 else "Erinnerungen"
    load = f", Last: {context.load_label}" if context.load_label else ""

    lines = [
        (
            f"Kalender: {context.fixed_event_count} {event_phrase}, "
            f"{context.deep_session_count} {deep_word}, "
            f"{context.reminder_count} {reminder_word}{load}."
        )
    ]

    if context.first_event or context.last_event:
        if context.first_event and context.last_event and context.first_event != context.last_event:
            lines.append(f"Rahmen: Start mit {context.first_event}; Ende mit {context.last_event}.")
        else:
            lines.append(f"Rahmen: {context.first_event or context.last_event}.")

    if context.carry_items:
        lines.append("Mitnehmen: " + ", ".join(context.carry_items) + ".")

    return lines[:3]


def _safe_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
