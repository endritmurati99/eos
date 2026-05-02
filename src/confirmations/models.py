from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PendingConfirmation:
    id: str
    created_at_utc: str
    expires_at_utc: str
    user_id: str
    source: str
    original_text: str
    parsed_intent: str
    parsed_entities: dict[str, Any]
    missing_fields: list[str]
    confirmation_question: str
    status: str
    resolved_at_utc: str | None = None
    resolution: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "created_at_utc": self.created_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "user_id": self.user_id,
            "source": self.source,
            "original_text": self.original_text,
            "parsed_intent": self.parsed_intent,
            "parsed_entities": self.parsed_entities,
            "missing_fields": self.missing_fields,
            "confirmation_question": self.confirmation_question,
            "status": self.status,
            "resolved_at_utc": self.resolved_at_utc,
            "resolution": self.resolution,
        }
