from __future__ import annotations

from src.eos_mail.gmail_client import (
    GogGmailReadOnlyClient,
    MailSummary,
    MessageRef,
    normalize_gmail_message,
)
from src.eos_mail.ingestion import query_from_last, run_shadow_ingestion


class FakeGmailClient:
    def __init__(self) -> None:
        self.write_calls: list[str] = []

    def list_messages(self, query: str, max_results: int) -> list[MessageRef]:
        assert query == "newer_than:7d"
        assert max_results == 2
        return [
            MessageRef(message_id="msg-1", thread_id="thread-1"),
            MessageRef(message_id="msg-2", thread_id="thread-2"),
        ]

    def get_message_summary(self, message_id: str) -> MailSummary:
        return MailSummary(
            message_id=message_id,
            thread_id=f"thread-{message_id[-1]}",
            sender="news@example.com" if message_id == "msg-1" else "bank@example.com",
            to="user@example.com",
            subject="Newsletter" if message_id == "msg-1" else "Security login alert",
            date="Sat, 02 May 2026 10:00:00 +0000",
            snippet="short metadata-only snippet",
            headers_subset={
                "From": "news@example.com" if message_id == "msg-1" else "bank@example.com",
                "To": "user@example.com",
                "Subject": "Newsletter" if message_id == "msg-1" else "Security login alert",
                "Date": "Sat, 02 May 2026 10:00:00 +0000",
                "List-Unsubscribe": "<mailto:unsubscribe@example.com>",
            }
            if message_id == "msg-1"
            else {
                "From": "bank@example.com",
                "To": "user@example.com",
                "Subject": "Security login alert",
                "Date": "Sat, 02 May 2026 10:00:00 +0000",
            },
            has_attachments=False,
            label_ids=("INBOX",),
        )


def test_gmail_message_metadata_is_normalized() -> None:
    payload = {
        "id": "abc123",
        "threadId": "thread123",
        "labelIds": ["INBOX", "IMPORTANT"],
        "snippet": "snippet only",
        "payload": {
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "user@example.com"},
                {"name": "Subject", "value": "Action required"},
                {"name": "Date", "value": "Sat, 02 May 2026 10:00:00 +0000"},
                {"name": "List-Unsubscribe", "value": "<mailto:unsubscribe@example.com>"},
                {"name": "X-Private-Header", "value": "must not persist"},
            ],
            "parts": [{"filename": "invoice.pdf"}],
        },
    }

    summary = normalize_gmail_message(payload)

    assert summary.message_id == "abc123"
    assert summary.thread_id == "thread123"
    assert summary.sender == "sender@example.com"
    assert summary.subject == "Action required"
    assert summary.has_attachments is True
    assert summary.headers_subset["List-Unsubscribe"] == "<mailto:unsubscribe@example.com>"
    assert "X-Private-Header" not in summary.headers_subset


def test_shadow_ingestion_persists_no_raw_body() -> None:
    result = run_shadow_ingestion(
        client=FakeGmailClient(),
        query=query_from_last("7d"),
        max_results=2,
        dry_run=True,
    )

    assert result["status"] == "success"
    assert result["dry_run"] is True
    assert result["messages_seen"] == 2
    for message in result["messages"]:
        assert "body" not in message
        assert "raw" not in message
        assert "payload" not in message
        assert "headers_subset" in message


def test_dry_run_does_not_use_write_actions() -> None:
    client = FakeGmailClient()

    result = run_shadow_ingestion(
        client=client,
        query="newer_than:7d",
        max_results=2,
        dry_run=True,
    )

    assert result["status"] == "success"
    assert client.write_calls == []


def test_non_dry_run_is_forbidden() -> None:
    result = run_shadow_ingestion(
        client=FakeGmailClient(),
        query="newer_than:7d",
        max_results=2,
        dry_run=False,
    )

    assert result["status"] == "failed"
    assert result["error_class"] == "write_mode_forbidden"
    assert result["messages_seen"] == 0


def test_phase_one_client_interface_has_no_write_methods() -> None:
    forbidden = {"send", "delete", "archive", "unsubscribe", "modify_labels", "apply_labels"}
    exposed = set(dir(GogGmailReadOnlyClient))

    assert forbidden.isdisjoint(exposed)
