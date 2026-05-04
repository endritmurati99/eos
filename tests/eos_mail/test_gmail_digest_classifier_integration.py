from __future__ import annotations

import src.eos_mail.digest as digest
from src.eos_mail.digest import bucket_messages, digest_payload
from src.eos_mail.gmail_client import MailSummary


def summary(
    *,
    message_id: str,
    sender: str,
    subject: str,
    snippet: str = "",
    headers_subset: dict[str, str] | None = None,
    has_attachments: bool = False,
) -> MailSummary:
    return MailSummary(
        message_id=message_id,
        thread_id=f"thread-{message_id}",
        sender=sender,
        to="user@example.test",
        subject=subject,
        date="Mon, 04 May 2026 10:00:00 +0000",
        snippet=snippet,
        headers_subset=headers_subset or {"From": sender, "Subject": subject},
        has_attachments=has_attachments,
        label_ids=("INBOX",),
    )


def test_finance_mail_summary_lands_in_finance_and_review() -> None:
    message = summary(
        message_id="finance",
        sender="statements@example-bank.test",
        subject="Monthly bank statement",
        snippet="Your monthly bank statement is ready.",
    )

    buckets = bucket_messages([message])

    assert buckets["finance"] == [message]
    assert buckets["review_needed"] == [message]


def test_security_mail_summary_lands_in_critical_security_and_review() -> None:
    message = summary(
        message_id="security",
        sender="security@example.test",
        subject="Login alert",
        snippet="New login from a new device.",
    )

    buckets = bucket_messages([message])

    assert buckets["critical"] == [message]
    assert buckets["security"] == [message]
    assert buckets["review_needed"] == [message]


def test_newsletter_mail_summary_lands_in_newsletter_bucket() -> None:
    message = summary(
        message_id="newsletter",
        sender="research@example.test",
        subject="Weekly research brief",
        snippet="Curated research and policy digest.",
        headers_subset={
            "From": "research@example.test",
            "Subject": "Weekly research brief",
            "List-Unsubscribe": "<mailto:unsubscribe@example.test>",
        },
    )

    buckets = bucket_messages([message])

    assert buckets["newsletter_high_signal"] == [message]


def test_action_required_mail_summary_lands_in_action_required() -> None:
    message = summary(
        message_id="action",
        sender="person@example.test",
        subject="Please reply by Friday",
        snippet="Can you confirm the deadline?",
    )

    buckets = bucket_messages([message])

    assert buckets["action_required"] == [message]


def test_unknown_mail_summary_lands_in_unknown_and_review() -> None:
    message = summary(
        message_id="unknown",
        sender="hello@new-sender.example",
        subject="Quick note",
        snippet="A vague update without deterministic context.",
    )

    buckets = bucket_messages([message])

    assert buckets["unknown"] == [message]
    assert buckets["review_needed"] == [message]


def test_digest_adapter_never_requires_or_persists_full_body() -> None:
    message = summary(
        message_id="metadata-only",
        sender="billing@example.test",
        subject="Invoice available",
        snippet="Your invoice and amount due are ready.",
    )

    mail_input = digest._mail_input_from_summary(message)
    payload = digest_payload([message])

    assert mail_input.body_excerpt is None
    assert "body" not in message.to_dict()
    assert "body_excerpt" not in payload["groups"]["finance"][0]


def test_digest_falls_back_to_metadata_only_when_classifier_unavailable(monkeypatch) -> None:
    message = summary(
        message_id="fallback-finance",
        sender="billing@example.test",
        subject="Invoice available",
        snippet="Payment due this week.",
    )
    monkeypatch.setattr(digest, "_classify_mail", None)

    payload = digest_payload([message])

    assert payload["status"] == "partial"
    assert payload["issue"] == "classifier_unavailable"
    assert payload["issues"] == ["classifier_unavailable"]
    assert payload["classifier_enabled"] is False
    assert payload["counts"]["finance"] == 1
