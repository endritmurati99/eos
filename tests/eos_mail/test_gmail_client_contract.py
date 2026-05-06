from __future__ import annotations

from src.eos_mail.gmail_client import (
    ALLOWED_HEADER_NAMES,
    GOG_GMAIL_CONTRACT_COMMANDS,
    GogGmailReadOnlyClient,
    GmailClientError,
    READONLY_SCOPE,
    detect_forbidden_gmail_write_scopes,
)


def test_gog_contract_commands_are_read_only() -> None:
    forbidden_terms = (
        "send",
        "delete",
        "trash",
        "archive",
        "modify",
        "labels",
        "create-label",
        "mark-read",
        "mark-unread",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://mail.google.com/",
    )

    for command in GOG_GMAIL_CONTRACT_COMMANDS.values():
        rendered = " ".join(command).lower().replace("list-unsubscribe", "")
        for forbidden in forbidden_terms:
            assert forbidden not in rendered


def test_gog_contract_documents_metadata_headers_only() -> None:
    search_command = GOG_GMAIL_CONTRACT_COMMANDS["messages_search"]
    metadata_command = GOG_GMAIL_CONTRACT_COMMANDS["metadata_get"]

    assert search_command[:6] == ("gog", "-a", "<account>", "gmail", "messages", "search")
    assert "--max" in search_command
    assert "--json" in search_command
    assert "--results-only" in search_command
    assert "--no-input" in search_command
    assert metadata_command[:5] == ("gog", "-a", "<account>", "gmail", "get")
    assert "--format" in metadata_command
    assert "metadata" in metadata_command
    assert ",".join(ALLOWED_HEADER_NAMES) in metadata_command
    assert "List-Unsubscribe" in " ".join(metadata_command)


def test_readonly_scope_is_exact_and_write_scopes_are_detected() -> None:
    assert READONLY_SCOPE == "https://www.googleapis.com/auth/gmail.readonly"

    detected = detect_forbidden_gmail_write_scopes(
        f"{READONLY_SCOPE},https://www.googleapis.com/auth/gmail.send"
    )

    assert detected == ("https://www.googleapis.com/auth/gmail.send",)


def test_phase_one_client_interface_has_no_write_like_methods() -> None:
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

    assert forbidden.isdisjoint(set(dir(GogGmailReadOnlyClient)))


def test_error_dictionary_redacts_secret_values() -> None:
    error = GmailClientError(
        "provider_error",
        "Bearer ya29.super-secret for person@example.test using /tmp/oauth/client_secret.json auth https://auth.example.test/callback?code=abc123",
        command=[
            "gog",
            "-a",
            "person@example.test",
            "gmail",
            "messages",
            "search",
        ],
    )

    payload = error.to_dict()
    rendered = str(payload)

    assert "ya29.super-secret" not in rendered
    assert "person@example.test" not in rendered
    assert "client_secret.json" not in rendered
    assert "code=abc123" not in rendered
    assert payload["command"][2] == "<redacted>"
