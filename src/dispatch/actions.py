from __future__ import annotations

import hashlib
from datetime import date

ACTION_HABIT_MARK_DONE = "habit_mark_done"
ACTION_HABIT_SKIP = "habit_skip"
ACTION_HABIT_RELAPSE = "habit_relapse"
ACTION_HABIT_RECOVERY = "habit_recovery"
ACTION_HABIT_FAILURE = "habit_failure"
ACTION_ENERGY_LOG = "energy_log"
ACTION_PENDING_CONFIRMATION = "pending_confirmation"
ACTION_CONFIRMATION_RESOLVE = "confirmation_resolve"
ACTION_NOOP = "noop"

ALL_ACTION_TYPES = (
    ACTION_HABIT_MARK_DONE,
    ACTION_HABIT_SKIP,
    ACTION_HABIT_RELAPSE,
    ACTION_HABIT_RECOVERY,
    ACTION_HABIT_FAILURE,
    ACTION_ENERGY_LOG,
    ACTION_PENDING_CONFIRMATION,
    ACTION_CONFIRMATION_RESOLVE,
    ACTION_NOOP,
)

INTENT_TO_ACTION: dict[str, str] = {
    "habit_log": ACTION_HABIT_MARK_DONE,
    "habit_relapse": ACTION_HABIT_RELAPSE,
    "habit_recovery": ACTION_HABIT_RECOVERY,
    "habit_failure": ACTION_HABIT_FAILURE,
    "daily_checkin": ACTION_ENERGY_LOG,
    "confirm_response": ACTION_CONFIRMATION_RESOLVE,
}


def input_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def idempotency_key(action_type: str, habit_id: str | None, target_date: date) -> str | None:
    if action_type in (ACTION_HABIT_MARK_DONE, ACTION_HABIT_SKIP, ACTION_HABIT_RECOVERY, ACTION_HABIT_FAILURE):
        if habit_id:
            return f"{action_type}:{habit_id}:{target_date.isoformat()}"
    return None
