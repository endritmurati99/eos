from __future__ import annotations

from pathlib import Path

from src.eos_calendar_intelligence import detect_followup_candidates

from tests.eos_calendar_intelligence._helpers import load_event


def test_followup_candidates_detect_english_and_german_signals() -> None:
    candidates = detect_followup_candidates(load_event("meeting_with_followup"))
    decision_candidates = detect_followup_candidates(load_event("meeting_with_decision"))

    assert "Follow up after the meeting" in candidates
    assert "Capture and review action items" in candidates
    assert "Send requested material afterwards" in candidates
    assert "Record decision and owner" in decision_candidates
    assert "Send or review the protocol" in decision_candidates


def test_followup_detection_creates_only_candidates() -> None:
    candidates = detect_followup_candidates(load_event("meeting_with_followup"))

    assert candidates
    assert all("create task" not in candidate.lower() for candidate in candidates)


def test_calendar_intelligence_has_no_provider_or_write_dependencies() -> None:
    package_root = Path(__file__).resolve().parents[2] / "src" / "eos_calendar_intelligence"
    combined_source = "\n".join(path.read_text(encoding="utf-8") for path in package_root.glob("*.py"))

    forbidden = (
        "src.gateways",
        "src.eos_mail",
        "gmail",
        "subprocess",
        "requests",
        "google calendar api",
        "events.insert",
        "events.update",
        "events.delete",
    )
    for needle in forbidden:
        assert needle not in combined_source.lower()
