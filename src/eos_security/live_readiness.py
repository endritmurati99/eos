"""Offline Google live-readiness gates."""

from __future__ import annotations


TRUE_VALUES = frozenset({"1", "true", "yes", "y", "on"})


def _enabled(config: dict, *keys: str) -> bool:
    for key in keys:
        if key not in config:
            continue
        value = config[key]
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in TRUE_VALUES
        return bool(value)
    return False


def google_live_readiness_status(config: dict) -> dict:
    """Return local readiness flags without making any Google API calls."""

    cfg = config or {}
    live_e2e_enabled = _enabled(cfg, "EOS_GOOGLE_LIVE_E2E_ENABLED", "google_live_e2e_enabled", "live_e2e_enabled")
    gmail_readonly_enabled = _enabled(cfg, "EOS_GMAIL_READONLY_ENABLED", "gmail_readonly_enabled")
    drive_readonly_enabled = _enabled(cfg, "EOS_DRIVE_READONLY_ENABLED", "drive_readonly_enabled")
    maps_routes_enabled = _enabled(cfg, "EOS_MAPS_ROUTES_ENABLED", "maps_routes_enabled")

    gmail_live_allowed = live_e2e_enabled and gmail_readonly_enabled
    drive_live_allowed = live_e2e_enabled and drive_readonly_enabled
    maps_live_allowed = live_e2e_enabled and maps_routes_enabled
    calendar_live_allowed = False

    return {
        "status": "ready"
        if any((gmail_live_allowed, drive_live_allowed, maps_live_allowed, calendar_live_allowed))
        else "blocked",
        "live_e2e_enabled": live_e2e_enabled,
        "gmail_live_allowed": gmail_live_allowed,
        "drive_live_allowed": drive_live_allowed,
        "maps_live_allowed": maps_live_allowed,
        "calendar_live_allowed": calendar_live_allowed,
    }
