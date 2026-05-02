from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DispatchResult:
    status: str
    action_type: str
    intent: str
    confidence: float
    response_text: str
    response_markdown: str
    habit_id: str | None = None
    energy_log_id: int | None = None
    confirmation_id: str | None = None
    error: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "action_type": self.action_type,
            "intent": self.intent,
            "confidence": self.confidence,
            "response_text": self.response_text,
            "response_markdown": self.response_markdown,
            "habit_id": self.habit_id,
            "energy_log_id": self.energy_log_id,
            "confirmation_id": self.confirmation_id,
            "error": self.error,
            **self.extra,
        }
