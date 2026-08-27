from __future__ import annotations

from typing import Any

from src.eos_notifications.budget import DEFAULT_DAILY_NOTIFICATION_LIMIT, daily_budget_remaining, parse_quiet_hours

ALWAYS_ALLOWED_EVENTS = {
    "morning_prompt",
    "evening_review",
}

CRITICAL_EVENT_TYPES = {
    "security",
    "security_risk",
    "deadline",
    "deadline_risk",
}

NEVER_PUSH_EVENTS = {
    "newsletter",
    "low_priority_newsletter",
    "newsletter_low_priority",
}

HIGH_URGENCY = {"high", "critical"}
HIGH_RISK = {"high", "critical"}


def should_notify(
    event_type: str,
    urgency: str,
    current_daily_count: int,
    quiet_hours: Any,
    risk_level: str,
) -> dict[str, Any]:
    event = event_type.strip().lower()
    urgency_value = urgency.strip().lower()
    risk = risk_level.strip().lower()
    quiet = parse_quiet_hours(quiet_hours)
    remaining = daily_budget_remaining(current_daily_count)
    is_escalation = event in CRITICAL_EVENT_TYPES and urgency_value in HIGH_URGENCY and risk in HIGH_RISK

    if event in NEVER_PUSH_EVENTS:
        return _decision(False, event, urgency_value, risk, current_daily_count, remaining, quiet, "newsletter_never_push")

    if is_escalation:
        return _decision(True, event, urgency_value, risk, current_daily_count, remaining, quiet, "critical_risk_escalation")

    if quiet["active"]:
        return _decision(False, event, urgency_value, risk, current_daily_count, remaining, quiet, "quiet_hours")

    if remaining <= 0:
        return _decision(False, event, urgency_value, risk, current_daily_count, remaining, quiet, "daily_budget_exhausted")

    if event in ALWAYS_ALLOWED_EVENTS:
        return _decision(True, event, urgency_value, risk, current_daily_count, remaining, quiet, "scheduled_anchor_allowed")

    if urgency_value in {"low", "normal"} and risk in {"low", "normal"}:
        return _decision(False, event, urgency_value, risk, current_daily_count, remaining, quiet, "low_signal_suppressed")

    return _decision(True, event, urgency_value, risk, current_daily_count, remaining, quiet, "within_budget")


def _decision(
    allowed: bool,
    event_type: str,
    urgency: str,
    risk_level: str,
    current_daily_count: int,
    budget_remaining: int,
    quiet_hours: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    return {
        "notification_allowed": allowed,
        "event_type": event_type,
        "urgency": urgency,
        "risk_level": risk_level,
        "current_daily_count": current_daily_count,
        "daily_limit": DEFAULT_DAILY_NOTIFICATION_LIMIT,
        "budget_remaining": budget_remaining,
        "quiet_hours_active": bool(quiet_hours["active"]),
        "reason": reason,
    }
