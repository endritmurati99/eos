from __future__ import annotations

import argparse

import pytest

from src import eos_cli


def _args(command: str, *, dry_run: bool = True) -> argparse.Namespace:
    values: dict[str, object] = {
        "command": "mail",
        "mail_command": command,
        "dry_run": dry_run,
    }
    if command == "audit":
        values["last"] = "1d"
    if command == "digest":
        values["today"] = True
    return argparse.Namespace(**values)


def test_mail_auth_check_command_exists() -> None:
    args = eos_cli._build_parser().parse_args(["mail", "auth-check", "--dry-run"])

    assert args.command == "mail"
    assert args.mail_command == "auth-check"
    assert args.dry_run is True


def test_mail_audit_command_exists() -> None:
    args = eos_cli._build_parser().parse_args(["mail", "audit", "--last", "1d", "--dry-run"])

    assert args.command == "mail"
    assert args.mail_command == "audit"
    assert args.last == "1d"
    assert args.dry_run is True


def test_mail_digest_command_exists() -> None:
    args = eos_cli._build_parser().parse_args(["mail", "digest", "--today", "--dry-run"])

    assert args.command == "mail"
    assert args.mail_command == "digest"
    assert args.today is True
    assert args.dry_run is True


@pytest.mark.parametrize("command", ("auth-check", "audit", "digest"))
def test_mail_no_dry_run_is_blocked(command: str) -> None:
    result = eos_cli.command_mail(_args(command, dry_run=False))

    assert result["status"] == "failed"
    assert result["error_class"] == "no_dry_run_forbidden"
    assert result["dry_run"] is False
    assert result["gmail_write_actions_added"] is False
    assert result["live_google_calls_made"] is False


def test_mail_auth_check_missing_credentials_does_not_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.eos_mail.auth_preflight as auth_preflight

    monkeypatch.setattr(
        auth_preflight,
        "run_gmail_auth_preflight",
        lambda: {
            "status": "config_missing",
            "issues": ["gog_missing", "scope_not_verifiable"],
            "readonly_scope_configured": False,
            "provider_contract_verified": False,
            "live_e2e_verified": False,
        },
    )

    result = eos_cli.command_mail(_args("auth-check"))

    assert result["status"] == "config_missing"
    assert result["mail_command"] == "auth-check"
    assert result["readonly_scope_configured"] is False
    assert "scope_not_verifiable" in result["issues"]


def test_mail_audit_dry_run_does_not_call_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.eos_mail.auth_preflight as auth_preflight

    monkeypatch.setattr(
        auth_preflight,
        "run_gmail_auth_preflight",
        lambda: {
            "status": "warning",
            "issues": ["scope_not_verifiable"],
            "readonly_scope_configured": False,
        },
    )

    result = eos_cli.command_mail(_args("audit"))

    assert result["status"] == "warning"
    assert result["provider_read_status"] == "not_attempted"
    assert result["provider_read_blocked_reason"] == "dry_run_no_live_reads"
    assert result["messages_seen"] == 0
    assert result["gmail_write_actions_added"] is False
    assert result["live_google_calls_made"] is False


def test_mail_digest_dry_run_does_not_call_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    import src.eos_mail.auth_preflight as auth_preflight

    monkeypatch.setattr(
        auth_preflight,
        "run_gmail_auth_preflight",
        lambda: {
            "status": "warning",
            "issues": ["scope_not_verifiable"],
            "readonly_scope_configured": False,
        },
    )

    result = eos_cli.command_mail(_args("digest"))

    assert result["status"] == "warning"
    assert result["provider_read_status"] == "not_attempted"
    assert result["digest"]["total_messages_scanned"] == 0
    assert result["gmail_write_actions_added"] is False
    assert result["live_google_calls_made"] is False
