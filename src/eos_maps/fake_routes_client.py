from __future__ import annotations

from typing import Any, Mapping

from src.eos_maps.routes_client import normalize_travel_mode
from src.eos_maps.types import RouteEstimate, RouteRequest


FAKE_PROVIDER_NAME = "fake_google_routes"


class FakeRoutesClient:
    def __init__(self, estimates: Mapping[tuple[str, str, str], RouteEstimate] | None = None) -> None:
        self._estimates = dict(estimates or _default_estimates())

    @classmethod
    def from_fixture_payload(cls, payload: Mapping[str, Any]) -> "FakeRoutesClient":
        estimates: dict[tuple[str, str, str], RouteEstimate] = {}
        for item in payload.get("estimates", []):
            estimate = RouteEstimate(
                origin=str(item["origin"]),
                destination=str(item["destination"]),
                mode=normalize_travel_mode(str(item.get("mode"))),
                duration_minutes=int(item["duration_minutes"]),
                duration_in_traffic_minutes=_optional_int(item.get("duration_in_traffic_minutes")),
                distance_text=_optional_str(item.get("distance_text")),
                provider=FAKE_PROVIDER_NAME,
                live_verified=False,
            )
            estimates[_key(estimate.origin, estimate.destination, estimate.mode)] = estimate
        return cls(estimates)

    def estimate_route(self, request: RouteRequest) -> RouteEstimate | None:
        mode = normalize_travel_mode(request.mode)
        direct = self._estimates.get(_key(request.origin, request.destination, mode))
        if direct:
            return direct
        return self._estimates.get(_key(request.origin, request.destination, "driving"))


def _default_estimates() -> dict[tuple[str, str, str], RouteEstimate]:
    rows = (
        ("Home", "Office Example", "driving", 20, 24, "8 km"),
        ("Home", "University Example", "driving", 30, 35, "12 km"),
        ("Home", "University Example", "transit", 38, None, "11 km"),
        ("Home", "Clinic Example", "driving", 32, 38, "14 km"),
        ("Office Example", "University Example", "driving", 25, 30, "9 km"),
        ("Office Example", "Clinic Example", "driving", 25, 30, "10 km"),
        ("Office Example", "Gym Example", "driving", 15, 18, "5 km"),
        ("Office Example", "Gym Example", "walking", 20, None, "1.6 km"),
        ("University Example", "Gym Example", "cycling", 18, None, "4 km"),
    )
    return {
        _key(origin, destination, mode): RouteEstimate(
            origin=origin,
            destination=destination,
            mode=mode,
            duration_minutes=duration,
            duration_in_traffic_minutes=traffic,
            distance_text=distance,
            provider=FAKE_PROVIDER_NAME,
            live_verified=False,
        )
        for origin, destination, mode, duration, traffic, distance in rows
    }


def _key(origin: str, destination: str, mode: str) -> tuple[str, str, str]:
    return (origin.strip().casefold(), destination.strip().casefold(), normalize_travel_mode(mode))


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    rendered = str(value)
    return rendered if rendered else None
