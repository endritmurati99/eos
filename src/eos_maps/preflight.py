from __future__ import annotations

import os
from typing import Any, Mapping

from src.eos_maps.routes_client import ALLOWED_TRAVEL_MODES, normalize_travel_mode


def run_maps_routes_preflight(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source_env = env if env is not None else os.environ
    enabled = _as_bool(source_env.get("EOS_MAPS_ROUTES_ENABLED"))
    api_key_configured = bool(source_env.get("EOS_GOOGLE_MAPS_API_KEY"))
    mode = normalize_travel_mode(source_env.get("EOS_DEFAULT_TRAVEL_MODE"))
    issues: list[dict[str, str]] = []

    if not enabled:
        issues.append(_issue("warning", "maps_routes_disabled", "Maps routes readiness is disabled."))
    if enabled and not api_key_configured:
        issues.append(_issue("warning", "api_key_missing", "Maps API key is not configured."))
    issues.append(_issue("warning", "live_contract_unverified", "Maps Routes contract is not live verified."))

    return {
        "status": "warning" if issues else "success",
        "maps_routes_enabled": enabled,
        "api_key_configured": api_key_configured,
        "default_travel_mode": mode,
        "allowed_travel_modes": list(ALLOWED_TRAVEL_MODES),
        "write_actions_available": False,
        "live_verified": False,
        "issues": issues,
    }


def _as_bool(value: str | None) -> bool:
    return str(value or "").strip().casefold() in {"1", "true", "yes", "on"}


def _issue(severity: str, code: str, message: str) -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "message": message,
    }
