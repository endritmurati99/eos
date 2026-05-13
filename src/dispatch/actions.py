from __future__ import annotations

import hashlib
from datetime import date

ACTION_HABIT_MARK_DONE = "habit_mark_done"
ACTION_HABIT_SKIP = "habit_skip"
ACTION_HABIT_RELAPSE = "habit_relapse"
ACTION_HABIT_RECOVERY = "habit_recovery"
ACTION_HABIT_FAILURE = "habit_failure"
ACTION_HABIT_STATUS = "habit_status"
ACTION_ENERGY_LOG = "energy_log"
ACTION_TASK_PROPOSAL = "task_proposal"
ACTION_CALENDAR_PROPOSAL = "calendar_proposal"
ACTION_PENDING_CONFIRMATION = "pending_confirmation"
ACTION_CONFIRMATION_RESOLVE = "confirmation_resolve"
ACTION_ASSISTANT_RESPONSE = "assistant_response"
ACTION_NOOP = "noop"

ALL_ACTION_TYPES = (
    ACTION_HABIT_MARK_DONE,
    ACTION_HABIT_SKIP,
    ACTION_HABIT_RELAPSE,
    ACTION_HABIT_RECOVERY,
    ACTION_HABIT_FAILURE,
    ACTION_HABIT_STATUS,
    ACTION_ENERGY_LOG,
    ACTION_TASK_PROPOSAL,
    ACTION_CALENDAR_PROPOSAL,
    ACTION_PENDING_CONFIRMATION,
    ACTION_CONFIRMATION_RESOLVE,
    ACTION_ASSISTANT_RESPONSE,
    ACTION_NOOP,
)

INTENT_TO_ACTION: dict[str, str] = {
    "habit_log": ACTION_HABIT_MARK_DONE,
    "habit_relapse": ACTION_HABIT_RELAPSE,
    "habit_recovery": ACTION_HABIT_RECOVERY,
    "habit_failure": ACTION_HABIT_FAILURE,
    "habit_status": ACTION_HABIT_STATUS,
    "daily_checkin": ACTION_ENERGY_LOG,
    "task_capture": ACTION_TASK_PROPOSAL,
    "calendar_proposal_request": ACTION_CALENDAR_PROPOSAL,
    "assistant_command": ACTION_ASSISTANT_RESPONSE,
    "plan_request": ACTION_ASSISTANT_RESPONSE,
    "review_request": ACTION_ASSISTANT_RESPONSE,
    "confirm_response": ACTION_CONFIRMATION_RESOLVE,
}


def input_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def idempotency_key(action_type: str, habit_id: str | None, target_date: date) -> str | None:
    if action_type in (ACTION_HABIT_MARK_DONE, ACTION_HABIT_SKIP, ACTION_HABIT_RECOVERY, ACTION_HABIT_FAILURE):
        if habit_id:
            return f"{action_type}:{habit_id}:{target_date.isoformat()}"
    return None
