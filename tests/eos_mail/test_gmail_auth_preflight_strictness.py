from __future__ import annotations

import pytest

import src.eos_mail.auth_preflight as auth_preflight
from src.eos_mail.auth_preflight import run_gmail_auth_preflight
from src.eos_mail.gmail_client import READONLY_SCOPE


def _gog_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth_preflight.shutil, "which", lambda _: "/usr/bin/gog")


def test_missing_explicit_scope_config_is_not_readonly_configured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    _gog_exists(monkeypatch)

    result = run_gmail_auth_preflight(
        workspace_root=tmp_path,
        env={
            "EOS_GOG_BIN": "gog",
            "EOS_GOOGLE_ACCOUNT": "synthetic@example.test",
        },
    )

    assert result["status"] == "warning"
    assert result["readonly_scope_configured"] is False
    assert result["readonly_scope_only"] is True
    assert result["write_scopes_detected"] is False
    assert result["scope_info_available"] is False
    assert result["scope_source"] is None
    assert "scope_not_verifiable" in result["issues"]
    assert result["config_readiness"] == "warning"
    assert result["provider_contract_readiness"] == "unverified"
    assert result["live_e2e_readiness"] == "unverified"
    assert result["provider_contract_verified"] is False
    assert result["live_e2e_verified"] is False


def test_explicit_readonly_scope_config_marks_readonly_configured(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    _gog_exists(monkeypatch)

    result = run_gmail_auth_preflight(
        workspace_root=tmp_path,
        env={
            "EOS_GOG_BIN": "gog",
            "EOS_GOOGLE_ACCOUNT": "synthetic@example.test",
            "EOS_GMAIL_SCOPES": READONLY_SCOPE,
        },
    )

    assert result["readonly_scope_configured"] is True
    assert result["scope_source"] == "config"
    assert "scope_not_verifiable" not in result["issues"]


def test_provider_auth_status_can_confirm_readonly_scope(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    _gog_exists(monkeypatch)

    result = run_gmail_auth_preflight(
        workspace_root=tmp_path,
        env={
            "EOS_GOG_BIN": "gog",
            "EOS_GOOGLE_ACCOUNT": "synthetic@example.test",
        },
        provider_auth_status={"granted_scopes": [READONLY_SCOPE]},
    )

    assert result["readonly_scope_configured"] is True
    assert result["scope_source"] == "provider"
    assert result["provider_scope_count"] == 1
    assert "scope_not_verifiable" not in result["issues"]


def test_scope_list_without_readonly_is_config_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    _gog_exists(monkeypatch)

    result = run_gmail_auth_preflight(
        workspace_root=tmp_path,
        env={
            "EOS_GOG_BIN": "gog",
            "EOS_GOOGLE_ACCOUNT": "synthetic@example.test",
            "EOS_GMAIL_SCOPES": "https://www.googleapis.com/auth/calendar.readonly",
        },
    )

    assert result["status"] == "config_missing"
    assert result["readonly_scope_configured"] is False
    assert result["scope_info_available"] is True
    assert "readonly_scope_missing" in result["issues"]
    assert "scope_not_verifiable" not in result["issues"]


def test_write_scopes_are_detected_only_from_explicit_scope_sources(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    _gog_exists(monkeypatch)

    missing_scope_result = run_gmail_auth_preflight(
        workspace_root=tmp_path,
        env={
            "EOS_GOG_BIN": "gog",
            "EOS_GOOGLE_ACCOUNT": "synthetic@example.test",
        },
    )
    write_scope_result = run_gmail_auth_preflight(
        workspace_root=tmp_path,
        env={
            "EOS_GOG_BIN": "gog",
            "EOS_GOOGLE_ACCOUNT": "synthetic@example.test",
            "EOS_GMAIL_SCOPES": f"{READONLY_SCOPE} https://www.googleapis.com/auth/gmail.send",
        },
    )

    assert missing_scope_result["write_scopes_detected"] is False
    assert write_scope_result["write_scopes_detected"] is True
    assert write_scope_result["status"] == "failed"
    assert "write_scope_forbidden" in write_scope_result["issues"]
