from __future__ import annotations

from datetime import date, timedelta

from src.eos_calendar_intelligence.types import (
    CalendarEventInput,
    MeetingLookupCandidate,
    MeetingLookupResult,
    clamp_confidence,
    event_search_text,
    format_time_window,
    normalize_text,
    parse_event_datetime,
)


STOPWORDS = {
    "was",
    "war",
    "nochmal",
    "das",
    "der",
    "die",
    "mit",
    "meeting",
    "termin",
    "call",
    "ueber",
    "uber",
    "wegen",
    "gestern",
    "heute",
    "morgen",
    "what",
    "was",
    "that",
    "about",
    "with",
}


def lookup_meeting(
    query: str,
    events: list[CalendarEventInput],
    reference_date: date | None = None,
) -> MeetingLookupResult:
    normalized_query = normalize_text(query)
    tokens = [token for token in normalized_query.split() if token not in STOPWORDS and len(token) >= 2]
    target_date = _target_date(normalized_query, reference_date)

    candidates = []
    for event in events:
        score, evidence = _score_event(event, tokens, target_date)
        if score <= 0:
            continue
        candidates.append(
            MeetingLookupCandidate(
                event_id=event.event_id,
                title=event.title,
                time_window=format_time_window(event),
                evidence=evidence[:4],
                confidence=clamp_confidence(score),
            )
        )

    candidates = sorted(candidates, key=lambda item: item.confidence, reverse=True)[:3]
    if not candidates:
        return MeetingLookupResult(
            answer="No matching meeting found in the provided synthetic calendar events.",
            evidence=[],
            uncertainty="high",
            candidates=[],
        )

    top = candidates[0]
    uncertainty = "low" if top.confidence >= 0.75 and (len(candidates) == 1 or top.confidence - candidates[1].confidence >= 0.15) else "medium"
    answer = f"Likely match: {top.title} at {top.time_window}."
    if len(candidates) > 1:
        answer = f"Top match: {top.title} at {top.time_window}. {len(candidates)} candidates found."

    return MeetingLookupResult(
        answer=answer,
        evidence=top.evidence,
        uncertainty=uncertainty,
        candidates=candidates,
    )


def _score_event(
    event: CalendarEventInput,
    tokens: list[str],
    target_date: date | None,
) -> tuple[float, list[str]]:
    text = event_search_text(event)
    title_text = normalize_text(event.title)
    attendee_text = normalize_text(" ".join(event.attendees))
    event_date = parse_event_datetime(event.start).date()
    evidence: list[str] = []
    score = 0.0

    if target_date and event_date == target_date:
        score += 0.3
        evidence.append(f"date matches {target_date.isoformat()}")
    elif target_date:
        score -= 0.2

    for token in tokens:
        if token in title_text:
            score += 0.22
            evidence.append(f"title matches '{token}'")
        elif token in attendee_text:
            score += 0.2
            evidence.append(f"attendee matches '{token}'")
        elif token in text:
            score += 0.14
            evidence.append(f"context matches '{token}'")

    if not tokens and target_date and event_date == target_date:
        score += 0.25
    if not evidence:
        return 0.0, []
    if event.description:
        score += 0.04
    if event.attendees:
        score += 0.04

    return clamp_confidence(score), evidence


def _target_date(normalized_query: str, reference_date: date | None) -> date | None:
    if not reference_date:
        return None
    if "gestern" in normalized_query or "yesterday" in normalized_query:
        return reference_date - timedelta(days=1)
    if "heute" in normalized_query or "today" in normalized_query:
        return reference_date
    if "morgen" in normalized_query or "tomorrow" in normalized_query:
        return reference_date + timedelta(days=1)
    return None
