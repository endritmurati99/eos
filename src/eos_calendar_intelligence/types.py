from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
import unicodedata


@dataclass(frozen=True)
class CalendarEventInput:
    event_id: str
    title: str
    start: str
    end: str
    location: str | None
    description: str | None
    attendees: list[str]
    calendar_role: str | None


@dataclass(frozen=True)
class MeetingBrief:
    event_id: str
    title: str
    time_window: str
    goal: str | None
    context_points: list[str]
    prep_actions: list[str]
    risks: list[str]
    followup_candidates: list[str]
    confidence: float


@dataclass(frozen=True)
class CalendarConflictReport:
    risk_level: str
    issues: list[str]
    suggestions: list[str]


@dataclass(frozen=True)
class PrepWindowSuggestion:
    event_id: str
    title: str
    duration_minutes: int
    window_start: str
    window_end: str
    reason: str
    confidence: float


@dataclass(frozen=True)
class MeetingLookupCandidate:
    event_id: str
    title: str
    time_window: str
    evidence: list[str]
    confidence: float


@dataclass(frozen=True)
class MeetingLookupResult:
    answer: str
    evidence: list[str]
    uncertainty: str
    candidates: list[MeetingLookupCandidate]


def parse_event_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized)


def event_duration_minutes(event: CalendarEventInput) -> int:
    duration = parse_event_datetime(event.end) - parse_event_datetime(event.start)
    return max(0, int(duration.total_seconds() // 60))


def format_time_window(event: CalendarEventInput) -> str:
    start = parse_event_datetime(event.start)
    end = parse_event_datetime(event.end)
    if start.date() == end.date():
        return f"{start:%Y-%m-%d %H:%M}-{end:%H:%M}"
    return f"{start:%Y-%m-%d %H:%M} - {end:%Y-%m-%d %H:%M}"


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    lowered = (
        value.casefold()
        .replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
    )
    decomposed = unicodedata.normalize("NFKD", lowered)
    ascii_text = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", ascii_text).strip()


def event_search_text(event: CalendarEventInput) -> str:
    return normalize_text(
        " ".join(
            [
                event.title,
                event.description or "",
                event.location or "",
                event.calendar_role or "",
                " ".join(event.attendees),
            ]
        )
    )


def keyword_matches(text: str, keyword: str) -> bool:
    normalized_keyword = normalize_text(keyword)
    if not normalized_keyword:
        return False
    if " " in normalized_keyword:
        return normalized_keyword in text
    return normalized_keyword in set(text.split())


def clamp_confidence(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 2)
