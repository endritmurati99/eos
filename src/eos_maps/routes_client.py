from __future__ import annotations

from typing import Protocol

from src.eos_maps.types import RouteEstimate, RouteRequest


ALLOWED_TRAVEL_MODES = ("driving", "walking", "transit", "cycling")
DEFAULT_TRAVEL_MODE = "driving"


class RoutesReadOnlyClient(Protocol):
    def estimate_route(self, request: RouteRequest) -> RouteEstimate | None:
        ...


def normalize_travel_mode(mode: str | None) -> str:
    normalized = str(mode or "").strip().casefold()
    if normalized in ALLOWED_TRAVEL_MODES:
        return normalized
    return DEFAULT_TRAVEL_MODE
