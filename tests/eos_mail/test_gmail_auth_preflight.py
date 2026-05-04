from __future__ import annotations

import pytest

import src.eos_mail.auth_preflight as auth_preflight
from src.eos_mail.auth_preflight import run_gmail_auth_preflight
from src.eos_mail.gmail_client import READONLY_SCOPE


def test_preflight_does_not_crash_without_gog(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(auth_preflight.shutil, "which", lambda _: None)

    result = run_gmail_auth_preflight(workspace_root=tmp_path, env={})

    assert result["status"] == "config_missing"
    assert result["gog_available"] is False
    assert result["provider_command_available"] is False
    assert "gog_missing" in result["issues"]
    assert "scope_not_verifiable" in result["issues"]
    assert result["gmail_write_actions_added"] is False


def test_preflight_missing_account_is_sanitized_config_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(auth_preflight.shutil, "which", lambda _: "/usr/bin/gog")

    result = run_gmail_auth_preflight(
        workspace_root=tmp_path,
        env={
            "EOS_GOG_BIN": "gog",
            "EOS_GMAIL_SCOPES": READONLY_SCOPE,
        },
    )

    assert result["status"] == "config_missing"
    assert result["account_configured"] is False
    assert "account_missing" in result["issues"]
    assert "@" not in str(result)


def test_preflight_masks_secret_like_configuration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(auth_preflight.shutil, "which", lambda _: "/usr/bin/gog")

    result = run_gmail_auth_preflight(
        workspace_root=tmp_path,
        env={
            "EOS_GOG_BIN": "gog",
            "EOS_GOOGLE_ACCOUNT": "person@example.test",
            "EOS_GOOGLE_TOKEN_PATH": "/tmp/oauth-token-root/ya29.secret-token",
            "EOS_GOOGLE_CREDENTIALS_PATH": "/tmp/oauth/client_secret_123.json",
            "EOS_GMAIL_SCOPES": READONLY_SCOPE,
        },
    )
    rendered = str(result)

    assert result["account_configured"] is True
    assert result["token_path_configured"] is True
    assert result["credentials_path_configured"] is True
    assert "person@example.test" not in rendered
    assert "ya29.secret-token" not in rendered
    assert "client_secret_123.json" not in rendered
    assert "/tmp/oauth" not in rendered


def test_preflight_readonly_scope_is_exact(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(auth_preflight.shutil, "which", lambda _: "/usr/bin/gog")

    result = run_gmail_auth_preflight(
        workspace_root=tmp_path,
        env={
            "EOS_GOG_BIN": "gog",
            "EOS_GOOGLE_ACCOUNT": "synthetic@example.test",
            "EOS_GMAIL_SCOPES": READONLY_SCOPE,
        },
    )

    assert result["readonly_scope"] == "https://www.googleapis.com/auth/gmail.readonly"
    assert result["readonly_scope_configured"] is True
    assert result["readonly_scope_only"] is True
    assert result["write_scopes_detected"] is False


def test_preflight_rejects_write_scopes(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(auth_preflight.shutil, "which", lambda _: "/usr/bin/gog")

    result = run_gmail_auth_preflight(
        workspace_root=tmp_path,
        env={
            "EOS_GOG_BIN": "gog",
            "EOS_GOOGLE_ACCOUNT": "synthetic@example.test",
            "EOS_GMAIL_SCOPES": f"{READONLY_SCOPE} https://www.googleapis.com/auth/gmail.modify",
        },
    )

    assert result["status"] == "failed"
    assert result["write_scopes_detected"] is True
    assert result["forbidden_write_scope_count"] == 1
    assert "write_scope_forbidden" in result["issues"]
