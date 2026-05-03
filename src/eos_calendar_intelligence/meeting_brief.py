from __future__ import annotations

from datetime import time

from src.eos_calendar_intelligence.followups import detect_followup_candidates
from src.eos_calendar_intelligence.types import (
    CalendarEventInput,
    MeetingBrief,
    clamp_confidence,
    event_search_text,
    format_time_window,
    keyword_matches,
    parse_event_datetime,
)


CATEGORY_RULES = (
    (
        "doctor",
        ("arzt", "doctor", "praxis", "clinic", "medical", "health", "termin beim arzt"),
        "Arzttermin",
        "Arrive prepared with symptoms, questions, and required documents.",
    ),
    (
        "sport",
        ("sport", "gym", "training", "kickbox", "bjj", "jiu jitsu", "workout"),
        "Sporttermin",
        "Protect the training block and prepare gear, travel, and recovery time.",
    ),
    (
        "university",
        ("uni", "university", "klausur", "exam", "seminar", "vorlesung"),
        "Uni-Termin",
        "Bring the right study context and clarify the academic outcome.",
    ),
    (
        "deadline",
        ("deadline", "due", "abgabe", "launch", "submission", "final review"),
        "Deadline-Meeting",
        "Clarify deadline status, blockers, final decisions, and owners.",
    ),
    (
        "project_sync",
        ("projekt", "project", "sync", "standup", "sprint", "weekly sync"),
        "Projekt Sync",
        "Align on status, blockers, ownership, and next milestones.",
    ),
    (
        "review",
        ("review", "retro", "weekly review", "monatsreview", "rueckblick"),
        "Review Meeting",
        "Review progress, decisions, open loops, and next actions.",
    ),
    (
        "call",
        ("interview", "call", "zoom", "phone", "telefon", "screening"),
        "Interview/Call",
        "Prepare the conversation agenda, questions, and follow-up path.",
    ),
    (
        "admin",
        ("admin", "rechnung", "invoice", "tax", "steuer", "bank", "vertrag", "form"),
        "Admin-Termin",
        "Resolve the administrative item with the required documents at hand.",
    ),
)


def build_meeting_brief(event: CalendarEventInput) -> MeetingBrief:
    category, goal = _classify_goal(event)
    context_points = _context_points(event, category)
    prep_actions = _prep_actions(event, category)
    risks = _risks(event, category)
    followups = detect_followup_candidates(event)

    confidence = 0.45
    if category:
        confidence += 0.25
    if event.description:
        confidence += 0.1
    if event.attendees:
        confidence += 0.07
    if event.location:
        confidence += 0.05
    if followups:
        confidence += 0.04

    return MeetingBrief(
        event_id=event.event_id,
        title=event.title,
        time_window=format_time_window(event),
        goal=goal,
        context_points=context_points[:4],
        prep_actions=prep_actions[:4],
        risks=risks[:4],
        followup_candidates=followups[:5],
        confidence=clamp_confidence(confidence),
    )


def _classify_goal(event: CalendarEventInput) -> tuple[str | None, str | None]:
    text = event_search_text(event)
    for category, keywords, label, goal in CATEGORY_RULES:
        if any(keyword_matches(text, keyword) for keyword in keywords):
            return category, f"{label}: {goal}"
    return None, "Clarify purpose, desired outcome, and next action."


def _context_points(event: CalendarEventInput, category: str | None) -> list[str]:
    points = [f"Time: {format_time_window(event)}"]
    if event.location:
        points.append(f"Location/channel: {event.location}")
    if event.attendees:
        points.append(f"Attendees: {', '.join(event.attendees[:4])}")
    if event.description:
        points.append("Description is available; use it as the primary context.")
    else:
        points.append("No description is available; infer carefully from title and attendees.")
    if category:
        points.append(f"Detected type: {category.replace('_', ' ')}")
    return points


def _prep_actions(event: CalendarEventInput, category: str | None) -> list[str]:
    actions = ["Write one target outcome before the meeting."]
    if category == "doctor":
        actions.append("List symptoms, medications, and questions.")
    elif category == "sport":
        actions.append("Prepare gear, hydration, and transit buffer.")
    elif category == "university":
        actions.append("Review syllabus, deadlines, and required materials.")
    elif category == "deadline":
        actions.append("Prepare blocker list, final status, and owner decisions.")
    elif category == "review":
        actions.append("Collect wins, misses, open loops, and metrics.")
    elif category == "project_sync":
        actions.append("Prepare status, blockers, and asks.")
    elif category == "call":
        actions.append("Prepare agenda, questions, and contact details.")
    elif category == "admin":
        actions.append("Gather documents, references, and account numbers.")
    else:
        actions.append("Check description, attendees, and location before joining.")
    if event.attendees:
        actions.append("Identify who needs a decision or update.")
    return actions


def _risks(event: CalendarEventInput, category: str | None) -> list[str]:
    risks: list[str] = []
    start = parse_event_datetime(event.start)
    if not event.description:
        risks.append("Missing description may hide purpose or prep requirements.")
    if not event.location and category in {"doctor", "sport", "university", "call"}:
        risks.append("Missing location/channel can cause late arrival.")
    if len(event.attendees) >= 6:
        risks.append("Large attendee list can dilute ownership.")
    if start.time() >= time(18, 0):
        risks.append("Evening timing may reduce energy and follow-through.")
    if category == "deadline":
        risks.append("Deadline context needs explicit owner and final decision.")
    return risks or ["No major risk detected from synthetic event fields."]
