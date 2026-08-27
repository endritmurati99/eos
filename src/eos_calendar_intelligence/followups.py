from __future__ import annotations

from src.eos_calendar_intelligence.types import CalendarEventInput, event_search_text, keyword_matches


FOLLOWUP_PATTERNS = (
    ("follow up", "Follow up after the meeting"),
    ("action items", "Capture and review action items"),
    ("send afterwards", "Send requested material afterwards"),
    ("review", "Review outcomes and open questions"),
    ("decision", "Record decision and owner"),
    ("next steps", "Clarify next steps"),
    ("protokoll", "Send or review the protocol"),
    ("unterlagen schicken", "Send requested documents"),
)


def detect_followup_candidates(event: CalendarEventInput) -> list[str]:
    text = event_search_text(event)
    candidates: list[str] = []
    for raw_pattern, candidate in FOLLOWUP_PATTERNS:
        if keyword_matches(text, raw_pattern) and candidate not in candidates:
            candidates.append(candidate)
    return candidates
