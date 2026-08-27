from __future__ import annotations

from src.eos_calendar_intelligence import build_meeting_brief

from tests.eos_calendar_intelligence._helpers import load_event


def test_meeting_brief_fields_are_operational_and_bounded() -> None:
    event = load_event("project_sync")
    brief = build_meeting_brief(event)

    assert brief.event_id == "project_sync"
    assert brief.title == event.title
    assert brief.time_window == "2026-05-04 10:00-10:30"
    assert "Projekt Sync" in (brief.goal or "")
    assert brief.context_points
    assert brief.prep_actions
    assert brief.risks
    assert 0.0 <= brief.confidence <= 1.0
    assert len(brief.context_points) <= 4
    assert len(brief.prep_actions) <= 4


def test_meeting_brief_detects_required_meeting_types() -> None:
    expectations = {
        "doctor_appointment": "Arzttermin",
        "sport_event": "Sporttermin",
        "university_exam": "Uni-Termin",
        "deadline_review": "Deadline-Meeting",
        "weekly_review": "Review Meeting",
        "client_call": "Interview/Call",
        "admin_block": "Admin-Termin",
    }

    for fixture_name, expected_goal in expectations.items():
        brief = build_meeting_brief(load_event(fixture_name))
        assert expected_goal in (brief.goal or "")


def test_missing_description_is_called_out_as_risk() -> None:
    brief = build_meeting_brief(load_event("meeting_without_description"))

    assert any("Missing description" in risk for risk in brief.risks)
    assert brief.confidence < 0.9


def test_followups_are_included_in_meeting_brief() -> None:
    brief = build_meeting_brief(load_event("meeting_with_decision"))

    assert "Record decision and owner" in brief.followup_candidates
    assert "Clarify next steps" in brief.followup_candidates
    assert "Send or review the protocol" in brief.followup_candidates
