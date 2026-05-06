from __future__ import annotations

import argparse
from types import SimpleNamespace

import pytest

import src.eos_mail.gmail_client as gmail_client_module
from src.eos_cli import command_mail
from src.eos_mail.gmail_client import (
    GogGmailReadOnlyClient,
    GmailClientError,
    MailSummary,
    MessageRef,
    READONLY_SCOPE,
    gmail_scope_guidance,
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
            "body": {"data": "raw-body-must-not-persist"},
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "user@example.com"},
                {"name": "Subject", "value": "Action required"},
                {"name": "Date", "value": "Sat, 02 May 2026 10:00:00 +0000"},
                {"name": "list-unsubscribe", "value": "<mailto:unsubscribe@example.com>"},
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
    serialized = summary.to_dict()
    assert "body" not in serialized
    assert "payload" not in serialized
    assert "raw" not in serialized


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
    forbidden = {
        "send",
        "delete",
        "trash",
        "archive",
        "modify",
        "unsubscribe",
        "modify_labels",
        "apply_labels",
        "create_label",
        "create_labels",
        "mark_read",
        "mark_unread",
    }
    exposed = set(dir(GogGmailReadOnlyClient))

    assert forbidden.isdisjoint(exposed)


def test_missing_gog_binary_returns_config_missing(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("EOS_GOG_BIN", raising=False)
    monkeypatch.delenv("EOS_GOOGLE_ACCOUNT", raising=False)
    monkeypatch.setattr(gmail_client_module.shutil, "which", lambda _: None)

    client = GogGmailReadOnlyClient(account="synthetic@example.test", workspace_root=tmp_path)

    with pytest.raises(GmailClientError) as exc_info:
        client.list_messages(query="newer_than:1d", max_results=1)

    assert exc_info.value.status == "config_missing"


def test_invalid_gog_binary_path_returns_config_missing(tmp_path) -> None:
    client = GogGmailReadOnlyClient(
        gog_bin="/definitely/not/gog",
        account="synthetic@example.test",
        workspace_root=tmp_path,
    )

    with pytest.raises(GmailClientError) as exc_info:
        client.list_messages(query="newer_than:1d", max_results=1)

    payload = exc_info.value.to_dict()
    assert exc_info.value.status == "config_missing"
    assert payload["command"][2] == "<redacted>"


def test_missing_account_returns_config_missing(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("EOS_GOOGLE_ACCOUNT", raising=False)
    monkeypatch.delenv("EOS_GOOGLE_TOKEN_PATH", raising=False)

    client = GogGmailReadOnlyClient(gog_bin="/bin/echo", workspace_root=tmp_path)

    with pytest.raises(GmailClientError) as exc_info:
        client.list_messages(query="newer_than:1d", max_results=1)

    assert exc_info.value.status == "config_missing"


def test_invalid_provider_json_returns_provider_error(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv("EOS_GOOGLE_TOKEN_PATH", raising=False)

    def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        return SimpleNamespace(returncode=0, stdout="not-json", stderr="")

    monkeypatch.setattr(gmail_client_module.subprocess, "run", fake_run)
    client = GogGmailReadOnlyClient(
        gog_bin="/usr/bin/gog",
        account="synthetic@example.test",
        workspace_root=tmp_path,
    )

    with pytest.raises(GmailClientError) as exc_info:
        client.list_messages(query="newer_than:1d", max_results=1)

    assert exc_info.value.status == "provider_error"


def test_provider_errors_are_sanitized() -> None:
    error = GmailClientError(
        "provider_error",
        "token=secret-value for user@example.test at /tmp/gogcli/credentials.json auth https://auth.example.test/callback?code=abc",
        command=["gog", "-a", "user@example.test", "gmail", "messages", "search"],
    )

    payload = error.to_dict()
    rendered = str(payload)

    assert "secret-value" not in rendered
    assert "user@example.test" not in rendered
    assert "credentials.json" not in rendered
    assert "code=abc" not in rendered
    assert payload["command"][2] == "<redacted>"


def test_readonly_scope_guidance_marks_live_contract_unverified() -> None:
    guidance = gmail_scope_guidance()

    assert guidance["required_scope"] == READONLY_SCOPE
    assert guidance["write_scopes_added"] is False
    assert guidance["live_contract_verified"] is False
    assert "gog gmail messages search JSON shape in production" in guidance["live_contract_unverified_items"]


def test_mail_cli_no_dry_run_is_blocked() -> None:
    result = command_mail(
        argparse.Namespace(
            mail_command="audit",
            dry_run=False,
            query=None,
            last="7d",
            max_results=1,
        )
    )

    assert result["status"] == "failed"
    assert result["error_class"] == "write_mode_forbidden"
    assert result["gmail_write_actions_added"] is False


def test_mail_digest_cli_includes_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.eos_cli.GogGmailReadOnlyClient", lambda: FakeGmailClient())

    result = command_mail(
        argparse.Namespace(
            mail_command="digest",
            dry_run=True,
            query="newer_than:7d",
            last="7d",
            max_results=2,
        )
    )

    assert result["status"] == "success"
    assert result["dry_run"] is True
    assert result["gmail_write_actions_added"] is False
