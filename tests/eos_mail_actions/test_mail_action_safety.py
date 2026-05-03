from __future__ import annotations

from src.eos_mail_actions import MailActionInput, build_task_proposals
from src.eos_mail_actions.safety import is_sensitive_category, redact_sensitive_text


def test_sensitive_categories_always_require_approval() -> None:
    sensitive_categories = [
        "_Money/Banking",
        "_Money/Credit Card",
        "_Security/Login Alert",
        "_Legal",
        "_Health",
    ]

    for category in sensitive_categories:
        mail = MailActionInput(
            message_id=f"message-{category}",
            thread_id="thread",
            sender="sender@example.test",
            subject="Please confirm tomorrow",
            snippet="Please confirm tomorrow.",
            body_excerpt="Please confirm tomorrow.",
            categories=[category],
            priority="critical",
            received_at="2026-05-04T09:00:00",
        )

        proposals = build_task_proposals(mail)
        assert is_sensitive_category([category]) is True
        assert proposals == [] or proposals[0].requires_approval is True


def test_normal_clear_reply_can_skip_approval() -> None:
    mail = MailActionInput(
        message_id="normal-reply",
        thread_id="thread-normal",
        sender="colleague@example.test",
        subject="Quick question",
        snippet="Please reply by Friday.",
        body_excerpt="Please reply by Friday with a yes or no.",
        categories=["_EOS/Action Required", "_Work"],
        priority="important",
        received_at="2026-05-04T09:00:00",
    )

    proposal = build_task_proposals(mail)[0]

    assert proposal.requires_approval is False
    assert proposal.list_name == "Inbox"


def test_notes_redact_codes_links_and_account_numbers() -> None:
    raw = (
        "Verification code is 123456. Reset at https://login.example.test/reset. "
        "IBAN DE12500105170648489890 and card 4111 1111 1111 1111."
    )

    redacted = redact_sensitive_text(raw)

    assert "123456" not in redacted
    assert "https://login.example.test/reset" not in redacted
    assert "DE12500105170648489890" not in redacted
    assert "4111 1111 1111 1111" not in redacted


def test_security_proposal_notes_do_not_include_sensitive_values() -> None:
    mail = MailActionInput(
        message_id="security-redaction",
        thread_id="thread-security",
        sender="security@example.test",
        subject="New login alert",
        snippet="New login detected.",
        body_excerpt="Login code is 123456. Reset at https://login.example.test/reset.",
        categories=["_Security/Login Alert"],
        priority="critical",
        received_at="2026-05-04T09:00:00",
    )

    proposal = build_task_proposals(mail)[0]

    assert proposal.requires_approval is True
    assert "123456" not in proposal.notes
    assert "https://login.example.test/reset" not in proposal.notes
    assert "[redacted-code]" in proposal.notes
    assert "[redacted-link]" in proposal.notes
