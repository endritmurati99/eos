from __future__ import annotations

from datetime import date

from src.eos_mail_actions import extract_deadline


REFERENCE_DATE = date(2026, 5, 4)


def test_extracts_relative_deadlines() -> None:
    assert extract_deadline("Please handle today", REFERENCE_DATE).due == "2026-05-04"
    assert extract_deadline("Bitte morgen bestaetigen", REFERENCE_DATE).due == "2026-05-05"
    assert extract_deadline("Please reply within 3 days", REFERENCE_DATE).due == "2026-05-07"


def test_extracts_weekday_deadlines() -> None:
    friday = extract_deadline("Please reply by Friday", REFERENCE_DATE)
    monday = extract_deadline("Please respond until Monday", date(2026, 5, 5))

    assert friday.due == "2026-05-08"
    assert friday.reason == "weekday_friday"
    assert monday.due == "2026-05-11"


def test_extracts_explicit_dates() -> None:
    assert extract_deadline("due on 2026-05-10", REFERENCE_DATE).due == "2026-05-10"
    assert extract_deadline("faellig am 10.05.2026", REFERENCE_DATE).due == "2026-05-10"


def test_extracts_end_of_week() -> None:
    result = extract_deadline("Bitte bis Ende der Woche erledigen", REFERENCE_DATE)

    assert result.due == "2026-05-08"
    assert result.reason == "end_of_week"


def test_uncertain_deadline_requires_approval() -> None:
    result = extract_deadline("Please reply soon; the deadline is moving", REFERENCE_DATE)

    assert result.due is None
    assert result.requires_approval is True
    assert "deadline_uncertain" in result.risk_flags
