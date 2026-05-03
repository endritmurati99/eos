from __future__ import annotations

from datetime import date

from src.eos_calendar_intelligence import lookup_meeting

from tests.eos_calendar_intelligence._helpers import load_event


def test_lookup_ranks_attendee_and_german_yesterday_query() -> None:
    max_event = load_event("project_sync").__class__(
        event_id="max_meeting",
        title="Project Update",
        start="2026-05-02T10:00:00",
        end="2026-05-02T10:30:00",
        location="Zoom",
        description="Update about Gmail integration.",
        attendees=["max@example.test"],
        calendar_role="primary",
    )
    other_event = load_event("client_call")

    result = lookup_meeting(
        "Meeting gestern mit Max",
        [other_event, max_event],
        reference_date=date(2026, 5, 3),
    )

    assert result.candidates[0].event_id == "max_meeting"
    assert "max" in " ".join(result.candidates[0].evidence).lower()
    assert result.uncertainty in {"low", "medium"}


def test_lookup_finds_context_query_about_invoice() -> None:
    result = lookup_meeting(
        "Termin wegen Rechnung",
        [load_event("admin_block"), load_event("sport_event"), load_event("ambiguous_meeting")],
        reference_date=date(2026, 5, 9),
    )

    assert result.candidates[0].event_id == "admin_block"
    assert "Rechnung" in result.candidates[0].title


def test_lookup_returns_top_three_candidates() -> None:
    result = lookup_meeting(
        "Call review decision",
        [
            load_event("client_call"),
            load_event("weekly_review"),
            load_event("meeting_with_decision"),
            load_event("sport_event"),
        ],
    )

    assert 1 <= len(result.candidates) <= 3
    assert result.candidates[0].confidence >= result.candidates[-1].confidence
    assert result.answer
    assert result.evidence


def test_lookup_reports_uncertainty_when_nothing_matches() -> None:
    result = lookup_meeting("Meeting mit Niemand", [load_event("sport_event")])

    assert result.candidates == []
    assert result.uncertainty == "high"
    assert "No matching" in result.answer
