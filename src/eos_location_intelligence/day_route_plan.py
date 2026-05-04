from __future__ import annotations

from src.eos_location_intelligence.location_extractor import extract_event_location
from src.eos_location_intelligence.travel_time import (
    DEFAULT_BUFFER_MINUTES,
    DEFAULT_HOME_LOCATION_LABEL,
    build_travel_time_proposal,
)
from src.eos_location_intelligence.types import CalendarLocationEvent, TravelTimeProposal
from src.eos_maps.routes_client import RoutesReadOnlyClient


def plan_day_routes(
    events: list[CalendarLocationEvent],
    *,
    route_client: RoutesReadOnlyClient,
    home_location: str = DEFAULT_HOME_LOCATION_LABEL,
    mode: str = "driving",
    buffer_minutes: int = DEFAULT_BUFFER_MINUTES,
) -> list[TravelTimeProposal]:
    sorted_events = sorted(events, key=lambda event: event.start)
    proposals: list[TravelTimeProposal] = []
    current_origin = home_location
    previous_end: str | None = None

    for index, event in enumerate(sorted_events):
        proposal = build_travel_time_proposal(
            event,
            origin=current_origin,
            route_client=route_client,
            mode=mode,
            buffer_minutes=buffer_minutes,
            previous_event_end=previous_end if index > 0 else None,
        )
        proposals.append(proposal)

        destination = extract_event_location(event)
        if destination:
            current_origin = destination
        previous_end = event.end

    return proposals
