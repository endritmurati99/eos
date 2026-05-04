from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RouteRequest:
    origin: str
    destination: str
    mode: str
    departure_time: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RouteEstimate:
    origin: str
    destination: str
    mode: str
    duration_minutes: int
    duration_in_traffic_minutes: int | None
    distance_text: str | None
    provider: str
    live_verified: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
