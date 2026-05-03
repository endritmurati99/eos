from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.eos_mail_actions import MailActionInput, build_task_proposals

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
def test_builds_expected_task_proposals(fixture_name: str) -> None:
    fixture = _load_fixture(fixture_name)
    mail = MailActionInput(**fixture["mail"])  # type: ignore[arg-type]
    expected = fixture["expected"]  # type: ignore[assignment]

    proposals = build_task_proposals(mail)

    assert len(proposals) == expected["proposal_count"]
    proposal = proposals[0]
    assert proposal.source == "mail"
    assert proposal.source_message_id == mail.message_id
    assert proposal.title.startswith(expected["title_prefix"])
    assert proposal.due == expected["due"]
    assert proposal.list_name == expected["list_name"]
    assert proposal.requires_approval is expected["requires_approval"]
    assert proposal.confidence >= 0.84


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
def test_no_task_fixtures_build_no_proposals(fixture_name: str) -> None:
    fixture = _load_fixture(fixture_name)
    mail = MailActionInput(**fixture["mail"])  # type: ignore[arg-type]

    assert build_task_proposals(mail) == []
