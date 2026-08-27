from __future__ import annotations

from typing import Any

DEFAULT_DAILY_NOTIFICATION_LIMIT = 4
DEFAULT_QUIET_HOURS = {
    "start": "22:00",
    "end": "07:00",
    "active": False,
}


def parse_quiet_hours(quiet_hours: Any) -> dict[str, Any]:
    if quiet_hours is None:
        return dict(DEFAULT_QUIET_HOURS)
    if isinstance(quiet_hours, bool):
        return {"start": None, "end": None, "active": quiet_hours}
    if isinstance(quiet_hours, dict):
        return {
            "start": quiet_hours.get("start"),
            "end": quiet_hours.get("end"),
            "active": bool(quiet_hours.get("active", False)),
        }
    if isinstance(quiet_hours, str):
        normalized = quiet_hours.strip().lower()
        if normalized in {"active", "quiet", "on", "true"}:
            return {"start": None, "end": None, "active": True}
        if normalized in {"inactive", "off", "false"}:
            return {"start": None, "end": None, "active": False}
        if "-" in normalized:
            start, end = normalized.split("-", 1)
            return {"start": start.strip(), "end": end.strip(), "active": False}
    return dict(DEFAULT_QUIET_HOURS)


def daily_budget_remaining(current_daily_count: int, max_daily_count: int = DEFAULT_DAILY_NOTIFICATION_LIMIT) -> int:
    return max(0, max_daily_count - max(0, current_daily_count))
