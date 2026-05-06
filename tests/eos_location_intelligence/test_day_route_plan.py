from __future__ import annotations

import json
from pathlib import Path

from src.eos_location_intelligence import CalendarLocationEvent, plan_day_routes
from src.eos_maps import FakeRoutesClient


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "google_workspace"
ALLOWED_SYNTHETIC_LOCATIONS = {
    "Home",
    "Office Example",
    "University Example",
    "Clinic Example",
    "Gym Example",
    "Ambiguous Example",
}


def load_cases() -> dict[str, dict[str, object]]:
    payload = json.loads((FIXTURE_ROOT / "calendar_locations_day.json").read_text(encoding="utf-8"))
    return {str(item["case_id"]): item for item in payload["cases"]}


def load_events(case_id: str) -> list[CalendarLocationEvent]:
    case = load_cases()[case_id]
    return [CalendarLocationEvent.from_dict(event) for event in case["events"]]  # type: ignore[index]


def load_routes_client() -> FakeRoutesClient:
    payload = json.loads((FIXTURE_ROOT / "routes_fake_estimates.json").read_text(encoding="utf-8"))
    return FakeRoutesClient.from_fixture_payload(payload)


def test_fixture_contains_exactly_twelve_synthetic_cases() -> None:
    cases = load_cases()

    assert set(cases) == {
        "home_to_meeting",
        "meeting_to_meeting",
        "same_location",
        "missing_location",
        "sport_location_after_work",
        "university_after_home",
        "doctor_after_meeting",
        "travel_time_too_tight",
        "enough_buffer",
        "transit_mode",
        "walking_mode",
        "ambiguous_location",
    }
    assert len(cases) == 12


def test_day_route_plan_sorts_events_and_flags_tight_travel() -> None:
    proposals = plan_day_routes(
        list(reversed(load_events("travel_time_too_tight"))),
        route_client=load_routes_client(),
    )

    assert [proposal.event_id for proposal in proposals] == ["office_before_clinic", "tight_clinic"]
    assert proposals[0].risk_level == "low"
    assert proposals[1].origin == "Office Example"
    assert proposals[1].destination == "Clinic Example"
    assert proposals[1].risk_level == "high"


def test_day_route_plan_handles_same_missing_and_unknown_locations() -> None:
    same = plan_day_routes(load_events("same_location"), route_client=load_routes_client())
    missing = plan_day_routes(load_events("missing_location"), route_client=load_routes_client())
    ambiguous = plan_day_routes(load_events("ambiguous_location"), route_client=load_routes_client())

    assert same[1].estimated_duration_minutes == 0
    assert same[1].risk_level == "low"
    assert missing[0].risk_level == "unknown"
    assert ambiguous[0].risk_level == "medium"


def test_day_route_plan_supports_transit_and_walking_modes() -> None:
    transit = plan_day_routes(
        load_events("transit_mode"),
        route_client=load_routes_client(),
        mode="transit",
    )
    walking = plan_day_routes(
        load_events("walking_mode"),
        route_client=load_routes_client(),
        mode="walking",
    )

    assert transit[0].estimated_duration_minutes == 38
    assert walking[1].estimated_duration_minutes == 20


def test_fixtures_use_only_synthetic_place_labels_and_store_no_history() -> None:
    payload = json.loads((FIXTURE_ROOT / "calendar_locations_day.json").read_text(encoding="utf-8"))
    rendered = json.dumps(payload)

    for case in payload["cases"]:
        for event in case["events"]:
            location = event.get("location")
            if location:
                assert location in ALLOWED_SYNTHETIC_LOCATIONS

    forbidden_fragments = (
        "street",
        "avenue",
        "road",
        "postal",
        "latitude",
        "longitude",
        "api_key",
        "location_history",
    )
    for forbidden in forbidden_fragments:
        assert forbidden not in rendered.lower()
