from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any, Mapping

from src.eos_mail.gmail_client import (
    FORBIDDEN_GMAIL_WRITE_SCOPES,
    LIVE_CONTRACT_UNVERIFIED_ITEMS,
    PROVIDER_NAME,
    READONLY_SCOPE,
    detect_forbidden_gmail_write_scopes,
    sanitize_gmail_error_text,
)
from src.runtime import WORKSPACE_ROOT, load_env_file

SCOPE_ENV_NAMES = (
    "EOS_GMAIL_SCOPES",
    "EOS_GMAIL_SCOPE",
    "EOS_GOOGLE_SCOPES",
)


def run_gmail_auth_preflight(
    *,
    workspace_root: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    gog_bin: str | None = None,
    account: str | None = None,
) -> dict[str, Any]:
    root = Path(workspace_root) if workspace_root else WORKSPACE_ROOT
    load_env_file(root)
    source_env = env if env is not None else os.environ

    configured_gog = gog_bin or source_env.get("EOS_GOG_BIN") or "gog"
    gog_available = _gog_available(configured_gog)
    resolved_account = account or source_env.get("EOS_GOOGLE_ACCOUNT") or _load_default_account(root)
    token_path = source_env.get("EOS_GOOGLE_TOKEN_PATH")
    credentials_path = source_env.get("EOS_GOOGLE_CREDENTIALS_PATH")
    configured_scopes = _configured_scopes(source_env)
    forbidden_scopes = detect_forbidden_gmail_write_scopes(configured_scopes)
    readonly_scope_configured = not configured_scopes or READONLY_SCOPE in configured_scopes

    issues: list[dict[str, str]] = []
    if not gog_available:
        issues.append(_issue("error", "gog_missing", "gog binary unavailable; set EOS_GOG_BIN or add gog to PATH."))
    if not resolved_account:
        issues.append(
            _issue(
                "error",
                "account_missing",
                "Google account missing; set EOS_GOOGLE_ACCOUNT or integrations/calendar-source.json.account.",
            )
        )
    if forbidden_scopes:
        issues.append(_issue("error", "write_scope_forbidden", "Gmail write scopes are forbidden in Phase 1."))
    if not readonly_scope_configured:
        issues.append(_issue("error", "readonly_scope_missing", "Expected Gmail read-only scope is not configured."))
    if not token_path:
        issues.append(
            _issue(
                "warning",
                "token_path_missing",
                "EOS_GOOGLE_TOKEN_PATH is not configured; gog default token storage may be used.",
            )
        )
    elif not _path_exists(token_path):
        issues.append(_issue("warning", "token_path_not_found", "Configured token path does not exist."))
    if not credentials_path:
        issues.append(
            _issue(
                "warning",
                "credentials_path_missing",
                "EOS_GOOGLE_CREDENTIALS_PATH is not configured; OAuth client credentials must be prepared outside EOS.",
            )
        )
    elif not _path_exists(credentials_path):
        issues.append(_issue("warning", "credentials_path_not_found", "Configured credentials path does not exist."))
    for item in LIVE_CONTRACT_UNVERIFIED_ITEMS:
        issues.append(_issue("warning", "live_contract_unverified", item))

    return {
        "status": _status(issues),
        "provider": PROVIDER_NAME,
        "readonly_scope": READONLY_SCOPE,
        "forbidden_write_scopes": tuple(FORBIDDEN_GMAIL_WRITE_SCOPES),
        "write_scopes_detected": bool(forbidden_scopes),
        "forbidden_write_scope_count": len(forbidden_scopes),
        "readonly_scope_configured": readonly_scope_configured,
        "configured_scope_count": len(configured_scopes),
        "gog_available": gog_available,
        "provider_command_available": gog_available,
        "account_configured": bool(resolved_account),
        "token_path_configured": bool(token_path),
        "token_path_exists": _path_exists(token_path) if token_path else False,
        "credentials_path_configured": bool(credentials_path),
        "credentials_path_exists": _path_exists(credentials_path) if credentials_path else False,
        "live_contract_verified": False,
        "live_contract_unverified_items": list(LIVE_CONTRACT_UNVERIFIED_ITEMS),
        "issues": _sanitize_issues(issues),
        "gmail_write_actions_added": False,
    }


def _configured_scopes(env: Mapping[str, str]) -> tuple[str, ...]:
    values: list[str] = []
    for name in SCOPE_ENV_NAMES:
        raw = env.get(name)
        if raw:
            values.extend(part.strip() for part in raw.replace(",", " ").replace(";", " ").split())
    return tuple(value for value in values if value)


def _gog_available(raw_gog_bin: str) -> bool:
    if not raw_gog_bin:
        return False
    if os.sep in raw_gog_bin or raw_gog_bin.startswith("~"):
        return Path(raw_gog_bin).expanduser().exists()
    return shutil.which(raw_gog_bin) is not None


def _path_exists(raw_path: str) -> bool:
    try:
        return Path(raw_path).expanduser().exists()
    except (OSError, ValueError):
        return False


def _load_default_account(workspace_root: Path) -> str | None:
    calendar_source_path = workspace_root / "integrations" / "calendar-source.json"
    if not calendar_source_path.exists():
        return None
    try:
        payload = json.loads(calendar_source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = payload.get("account")
    return str(value) if value else None


def _issue(severity: str, code: str, message: str) -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
    }


def _sanitize_issues(issues: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "severity": sanitize_gmail_error_text(issue["severity"]),
            "code": sanitize_gmail_error_text(issue["code"]),
            "message": sanitize_gmail_error_text(issue["message"]),
        }
        for issue in issues
    ]


def _status(issues: list[dict[str, str]]) -> str:
    codes = {issue["code"] for issue in issues if issue["severity"] == "error"}
    if "write_scope_forbidden" in codes:
        return "failed"
    if codes:
        return "config_missing"
    if issues:
        return "warning"
    return "success"
