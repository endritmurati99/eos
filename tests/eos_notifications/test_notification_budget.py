from __future__ import annotations

from src.eos_notifications.budget import DEFAULT_DAILY_NOTIFICATION_LIMIT, daily_budget_remaining, parse_quiet_hours
from src.eos_notifications.decision import should_notify


def test_morning_and_evening_prompts_allowed_within_budget() -> None:
    morning = should_notify("morning_prompt", "normal", 0, {"active": False}, "normal")
    evening = should_notify("evening_review", "normal", 1, {"active": False}, "normal")

    assert morning["notification_allowed"] is True
    assert evening["notification_allowed"] is True
    assert morning["reason"] == "scheduled_anchor_allowed"


def test_quiet_hours_block_non_critical_notifications() -> None:
    decision = should_notify("habit_nudge", "normal", 0, {"active": True}, "normal")

    assert decision["notification_allowed"] is False
    assert decision["quiet_hours_active"] is True
    assert decision["reason"] == "quiet_hours"


def test_critical_security_and_deadline_risks_can_escalate_in_quiet_hours() -> None:
    security = should_notify("security_risk", "critical", DEFAULT_DAILY_NOTIFICATION_LIMIT, {"active": True}, "critical")
    deadline = should_notify("deadline_risk", "high", DEFAULT_DAILY_NOTIFICATION_LIMIT, {"active": True}, "high")

    assert security["notification_allowed"] is True
    assert deadline["notification_allowed"] is True
    assert security["reason"] == "critical_risk_escalation"


def test_notification_budget_blocks_low_and_normal_priority() -> None:
    decision = should_notify("habit_nudge", "normal", DEFAULT_DAILY_NOTIFICATION_LIMIT, {"active": False}, "normal")

    assert decision["notification_allowed"] is False
    assert decision["budget_remaining"] == 0
    assert decision["reason"] == "daily_budget_exhausted"


def test_low_priority_newsletter_never_pushes() -> None:
    decision = should_notify("low_priority_newsletter", "high", 0, {"active": False}, "high")

    assert decision["notification_allowed"] is False
    assert decision["reason"] == "newsletter_never_push"


def test_quiet_hours_parser_and_budget_remaining() -> None:
    assert parse_quiet_hours(True)["active"] is True
    assert parse_quiet_hours("22:00-07:00")["start"] == "22:00"
    assert daily_budget_remaining(2) == 2
    assert daily_budget_remaining(6) == 0
