from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CalendarLocationEvent:
    event_id: str
    title: str
    start: str
    end: str
    location: str | None
    calendar_role: str | None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "CalendarLocationEvent":
        return cls(
            event_id=str(payload["event_id"]),
            title=str(payload["title"]),
            start=str(payload["start"]),
            end=str(payload["end"]),
            location=_optional_str(payload.get("location")),
            calendar_role=_optional_str(payload.get("calendar_role")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TravelTimeProposal:
    event_id: str
    origin: str
    destination: str
    depart_by: str | None
    estimated_duration_minutes: int
    buffer_minutes: int
    risk_level: str
    reason: str
    live_verified: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    rendered = str(value).strip()
    return rendered if rendered else None
