from __future__ import annotations

import os
import re
from typing import Any, Mapping

from src.eos_drive.metadata_client import (
    ALLOWED_DRIVE_METADATA_FIELDS,
    FORBIDDEN_DRIVE_ACTIONS,
)
from src.eos_google_workspace.auth_matrix import (
    DRIVE_METADATA_READONLY_SCOPE,
    detect_forbidden_google_write_scopes,
)


SCOPE_ENV_NAMES = (
    "EOS_DRIVE_SCOPES",
    "EOS_GOOGLE_SCOPES",
)


def run_drive_readonly_preflight(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source_env = env if env is not None else os.environ
    configured_scopes = _configured_scopes(source_env)
    forbidden_scopes = detect_forbidden_google_write_scopes(configured_scopes)
    enabled = _as_bool(source_env.get("EOS_DRIVE_READONLY_ENABLED"))

    issues: list[dict[str, str]] = []
    if not enabled:
        issues.append(_issue("warning", "drive_readonly_disabled", "Drive metadata read-only is disabled."))
    if forbidden_scopes:
        issues.append(_issue("error", "write_scope_forbidden", "Google Drive write scopes are forbidden."))
    if configured_scopes and DRIVE_METADATA_READONLY_SCOPE not in configured_scopes:
        issues.append(_issue("warning", "readonly_scope_missing", "Drive metadata read-only scope is not configured."))
    issues.append(_issue("warning", "live_contract_unverified", "Drive metadata provider contract is not live verified."))

    return {
        "status": _status(issues),
        "drive_readonly_enabled": enabled,
        "readonly_scope": DRIVE_METADATA_READONLY_SCOPE,
        "readonly_scope_configured": not configured_scopes or DRIVE_METADATA_READONLY_SCOPE in configured_scopes,
        "write_actions_available": False,
        "write_scopes_detected": bool(forbidden_scopes),
        "live_verified": False,
        "allowed_metadata_fields": list(ALLOWED_DRIVE_METADATA_FIELDS),
        "forbidden_actions": list(FORBIDDEN_DRIVE_ACTIONS),
        "account_configured": bool(source_env.get("EOS_GOOGLE_ACCOUNT")),
        "token_path_configured": bool(source_env.get("EOS_GOOGLE_TOKEN_PATH")),
        "credentials_path_configured": bool(source_env.get("EOS_GOOGLE_CREDENTIALS_PATH")),
        "issues": issues,
    }


def _configured_scopes(env: Mapping[str, str]) -> tuple[str, ...]:
    values: list[str] = []
    for name in SCOPE_ENV_NAMES:
        raw = env.get(name)
        if raw:
            values.extend(part.strip() for part in re.split(r"[\s,;]+", raw))
    return tuple(value for value in values if value)


def _as_bool(value: str | None) -> bool:
    return str(value or "").strip().casefold() in {"1", "true", "yes", "on"}


def _issue(severity: str, code: str, message: str) -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
    }


def _status(issues: list[dict[str, str]]) -> str:
    if any(issue["severity"] == "error" for issue in issues):
        return "failed"
    if issues:
        return "warning"
    return "success"
