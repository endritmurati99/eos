from __future__ import annotations

from src.eos_mail.digest import bucket_messages, digest_payload, render_shadow_digest
from src.eos_mail.gmail_client import MailSummary


def summary(
    *,
    message_id: str,
    sender: str,
    subject: str,
    headers_subset: dict[str, str] | None = None,
    snippet: str = "",
    has_attachments: bool = False,
) -> MailSummary:
    return MailSummary(
        message_id=message_id,
        thread_id=f"thread-{message_id}",
        sender=sender,
        to="user@example.com",
        subject=subject,
        date="Sat, 02 May 2026 10:00:00 +0000",
        snippet=snippet,
        headers_subset=headers_subset or {"From": sender, "Subject": subject},
        has_attachments=has_attachments,
        label_ids=("INBOX",),
    )


def test_digest_renders_expected_groups() -> None:
    messages = [
        summary(
            message_id="newsletter-high",
            sender="newsletter@example.com",
            subject="Weekly research brief",
            snippet="Curated research and policy digest for the week.",
            headers_subset={"List-Unsubscribe": "<mailto:unsubscribe@example.com>"},
        ),
        summary(
            message_id="security",
            sender="security@bank.example",
            subject="Security login alert",
        ),
        summary(
            message_id="important",
            sender="person@example.com",
            subject="Action required by Friday",
        ),
        summary(
            message_id="review",
            sender="docs@example.com",
            subject="Document attached",
            has_attachments=True,
        ),
        summary(
            message_id="unknown",
            sender="hello@example.com",
            subject="Hello",
        ),
    ]

    payload = digest_payload(messages)
    rendered = render_shadow_digest(messages)

    assert payload["total_messages_scanned"] == 5
    assert payload["status"] == "success"
    assert payload["counts"]["newsletter_high_signal"] == 1
    assert payload["counts"]["critical"] == 1
    assert payload["counts"]["security"] == 1
    assert payload["counts"]["action_required"] == 1
    assert payload["counts"]["review_needed"] >= 2
    assert payload["counts"]["unknown"] >= 1
    assert "Gmail Shadow Digest" in rendered
    assert "Total messages scanned: 5" in rendered
    assert "Newsletter high signal: 1" in rendered
    assert "Security: 1" in rendered


def test_bucket_precedence_keeps_security_conservative() -> None:
    message = summary(
        message_id="security-newsletter",
        sender="security@bank.example",
        subject="Security login alert newsletter",
        snippet="New login from a new device.",
        headers_subset={"List-Unsubscribe": "<mailto:unsubscribe@example.com>"},
    )

    buckets = bucket_messages([message])

    assert buckets["critical"] == [message]
    assert buckets["security"] == [message]
    assert buckets["review_needed"] == [message]
