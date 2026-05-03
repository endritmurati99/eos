from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.eos_mail_actions import MailActionInput, extract_actions

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "mail_actions"


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "fixture_name",
    [
        "reply_by_friday",
        "confirm_appointment",
        "send_document",
        "invoice_due_date",
        "bank_alert_review",
        "credit_card_charge_review",
        "security_login_alert_review",
        "legal_notice_review",
        "health_appointment_confirm",
        "meeting_prepare",
        "meeting_followup",
        "waiting_for_reply",
        "ambiguous_deadline_review",
    ],
)
def test_extracts_expected_action_types(fixture_name: str) -> None:
    fixture = _load_fixture(fixture_name)
    mail = MailActionInput(**fixture["mail"])  # type: ignore[arg-type]
    expected = fixture["expected"]  # type: ignore[assignment]

    actions = extract_actions(mail)

    assert len(actions) == expected["proposal_count"]
    assert actions[0].action_type == expected["action_type"]
    assert actions[0].due == expected["due"]
    assert actions[0].requires_approval is expected["requires_approval"]
    assert actions[0].confidence >= 0.84
    if "risk_flag" in expected:
        assert expected["risk_flag"] in actions[0].risk_flags


@pytest.mark.parametrize(
    "fixture_name",
    [
        "receipt_no_action",
        "password_reset_no_task",
        "newsletter_no_task",
        "spam_no_task",
        "phishing_no_task",
    ],
)
def test_suppressed_categories_produce_no_actions(fixture_name: str) -> None:
    fixture = _load_fixture(fixture_name)
    mail = MailActionInput(**fixture["mail"])  # type: ignore[arg-type]

    assert extract_actions(mail) == []
