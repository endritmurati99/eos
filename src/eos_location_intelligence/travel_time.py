from __future__ import annotations

from datetime import datetime, timedelta

from src.eos_location_intelligence.location_extractor import (
    extract_event_location,
    is_same_location,
)
from src.eos_location_intelligence.types import CalendarLocationEvent, TravelTimeProposal
from src.eos_maps.routes_client import RoutesReadOnlyClient, normalize_travel_mode
from src.eos_maps.types import RouteRequest


DEFAULT_HOME_LOCATION_LABEL = "Home"
DEFAULT_BUFFER_MINUTES = 15


def build_travel_time_proposal(
    event: CalendarLocationEvent,
    *,
    origin: str = DEFAULT_HOME_LOCATION_LABEL,
    route_client: RoutesReadOnlyClient,
    mode: str = "driving",
    buffer_minutes: int = DEFAULT_BUFFER_MINUTES,
    previous_event_end: str | None = None,
) -> TravelTimeProposal:
    destination = extract_event_location(event)
    normalized_mode = normalize_travel_mode(mode)

    if destination is None:
        return TravelTimeProposal(
            event_id=event.event_id,
            origin=origin,
            destination="",
            depart_by=None,
            estimated_duration_minutes=0,
            buffer_minutes=buffer_minutes,
            risk_level="unknown",
            reason="Location missing; no travel estimate can be produced.",
            live_verified=False,
        )

    if is_same_location(origin, destination):
        return TravelTimeProposal(
            event_id=event.event_id,
            origin=origin,
            destination=destination,
            depart_by=None,
            estimated_duration_minutes=0,
            buffer_minutes=buffer_minutes,
            risk_level="low",
            reason="Same location; no travel needed.",
            live_verified=False,
        )

    estimate = route_client.estimate_route(
        RouteRequest(
            origin=origin,
            destination=destination,
            mode=normalized_mode,
            departure_time=previous_event_end,
        )
    )
    if estimate is None:
        return TravelTimeProposal(
            event_id=event.event_id,
            origin=origin,
            destination=destination,
            depart_by=None,
            estimated_duration_minutes=0,
            buffer_minutes=buffer_minutes,
            risk_level="medium",
            reason="Travel time unknown; protect extra buffer before this event.",
            live_verified=False,
        )

    duration = estimate.duration_in_traffic_minutes or estimate.duration_minutes
    event_start = _parse_datetime(event.start)
    depart_by = event_start - timedelta(minutes=duration + buffer_minutes)
    risk_level = "low"
    reason = "Travel estimate fits before the event with the configured buffer."

    if previous_event_end:
        previous_end = _parse_datetime(previous_event_end)
        required_arrival = previous_end + timedelta(minutes=duration + buffer_minutes)
        if required_arrival > event_start:
            risk_level = "high"
            reason = "Travel time plus buffer overlaps the next event start."

    return TravelTimeProposal(
        event_id=event.event_id,
        origin=origin,
        destination=destination,
        depart_by=depart_by.isoformat(),
        estimated_duration_minutes=duration,
        buffer_minutes=buffer_minutes,
        risk_level=risk_level,
        reason=reason,
        live_verified=estimate.live_verified,
    )


def _parse_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized)
