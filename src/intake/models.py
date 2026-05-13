from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


SUPPORTED_INTENTS = (
    "habit_log",
    "habit_status",
    "habit_relapse",
    "habit_recovery",
    "habit_failure",
    "daily_checkin",
    "plan_request",
    "task_capture",
    "calendar_proposal_request",
    "review_request",
    "assistant_command",
    "confirm_response",
    "unknown",
)


@dataclass(frozen=True)
class IntakeResult:
    intent: str
    confidence: float
    entities: dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    confirmation_question: str | None = None
    ambiguity: str | None = None
    raw_input: str = ""
    normalized_input: str = ""
    matched_keywords: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["matched_keywords"] = list(self.matched_keywords)
        return payload
