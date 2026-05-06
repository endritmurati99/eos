from __future__ import annotations

import json
from pathlib import Path

from src.eos_location_intelligence import CalendarLocationEvent, build_travel_time_proposal
from src.eos_maps import FakeRoutesClient


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "google_workspace"


def load_routes_client() -> FakeRoutesClient:
    payload = json.loads((FIXTURE_ROOT / "routes_fake_estimates.json").read_text(encoding="utf-8"))
    return FakeRoutesClient.from_fixture_payload(payload)


def event(**overrides: object) -> CalendarLocationEvent:
    payload = {
        "event_id": "event",
        "title": "Event",
        "start": "2026-05-04T09:00:00",
        "end": "2026-05-04T09:30:00",
        "location": "Office Example",
        "calendar_role": "primary",
    }
    payload.update(overrides)
    return CalendarLocationEvent.from_dict(payload)


def test_missing_location_returns_unknown_without_estimate() -> None:
    proposal = build_travel_time_proposal(
        event(location=None),
        route_client=load_routes_client(),
    )

    assert proposal.risk_level == "unknown"
    assert proposal.depart_by is None
    assert proposal.estimated_duration_minutes == 0
    assert proposal.live_verified is False


def test_same_location_returns_low_risk_zero_duration() -> None:
    proposal = build_travel_time_proposal(
        event(location="Office Example"),
        origin="Office Example",
        route_client=load_routes_client(),
    )

    assert proposal.risk_level == "low"
    assert proposal.estimated_duration_minutes == 0
    assert proposal.depart_by is None
    assert "no travel needed" in proposal.reason


def test_known_home_route_returns_depart_by_and_low_risk() -> None:
    proposal = build_travel_time_proposal(
        event(start="2026-05-04T09:00:00", location="Office Example"),
        route_client=load_routes_client(),
    )

    assert proposal.origin == "Home"
    assert proposal.destination == "Office Example"
    assert proposal.estimated_duration_minutes == 24
    assert proposal.depart_by == "2026-05-04T08:21:00"
    assert proposal.risk_level == "low"


def test_unknown_route_returns_medium_risk() -> None:
    proposal = build_travel_time_proposal(
        event(location="Ambiguous Example"),
        route_client=load_routes_client(),
    )

    assert proposal.risk_level == "medium"
    assert proposal.depart_by is None
    assert proposal.estimated_duration_minutes == 0


def test_travel_time_plus_buffer_overlap_is_high_risk() -> None:
    proposal = build_travel_time_proposal(
        event(
            event_id="tight_clinic",
            start="2026-05-07T13:00:00",
            end="2026-05-07T13:30:00",
            location="Clinic Example",
        ),
        origin="Office Example",
        previous_event_end="2026-05-07T12:30:00",
        route_client=load_routes_client(),
        buffer_minutes=15,
    )

    assert proposal.estimated_duration_minutes == 30
    assert proposal.risk_level == "high"
    assert "overlaps" in proposal.reason


def test_enough_buffer_remains_low_risk() -> None:
    proposal = build_travel_time_proposal(
        event(
            event_id="buffer_clinic",
            start="2026-05-07T11:30:00",
            end="2026-05-07T12:00:00",
            location="Clinic Example",
        ),
        origin="Office Example",
        previous_event_end="2026-05-07T10:00:00",
        route_client=load_routes_client(),
        buffer_minutes=15,
    )

    assert proposal.risk_level == "low"
    assert proposal.depart_by == "2026-05-07T10:45:00"
