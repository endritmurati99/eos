from __future__ import annotations

import json
from pathlib import Path

from src.eos_maps import (
    ALLOWED_TRAVEL_MODES,
    FakeRoutesClient,
    RouteRequest,
    normalize_travel_mode,
    run_maps_routes_preflight,
)


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "google_workspace"


def load_routes_client() -> FakeRoutesClient:
    payload = json.loads((FIXTURE_ROOT / "routes_fake_estimates.json").read_text(encoding="utf-8"))
    return FakeRoutesClient.from_fixture_payload(payload)


def test_fake_routes_client_returns_deterministic_readonly_estimate() -> None:
    client = load_routes_client()

    estimate = client.estimate_route(
        RouteRequest(
            origin="Office Example",
            destination="Clinic Example",
            mode="driving",
            departure_time="2026-05-07T12:30:00",
        )
    )

    assert estimate is not None
    assert estimate.duration_minutes == 25
    assert estimate.duration_in_traffic_minutes == 30
    assert estimate.provider == "fake_google_routes"
    assert estimate.live_verified is False


def test_travel_modes_are_bounded_and_invalid_mode_falls_back_to_driving() -> None:
    assert ALLOWED_TRAVEL_MODES == ("driving", "walking", "transit", "cycling")
    assert normalize_travel_mode("walking") == "walking"
    assert normalize_travel_mode("spaceship") == "driving"


def test_maps_preflight_is_unverified_and_sanitized() -> None:
    result = run_maps_routes_preflight(
        env={
            "EOS_MAPS_ROUTES_ENABLED": "true",
            "EOS_GOOGLE_MAPS_API_KEY": "secret-map-key-123",
            "EOS_DEFAULT_TRAVEL_MODE": "transit",
        }
    )
    rendered = str(result)

    assert result["status"] == "warning"
    assert result["api_key_configured"] is True
    assert result["live_verified"] is False
    assert result["write_actions_available"] is False
    assert result["default_travel_mode"] == "transit"
    assert "secret-map-key-123" not in rendered


def test_routes_source_has_no_live_google_call_dependencies() -> None:
    package_root = Path(__file__).resolve().parents[2] / "src" / "eos_maps"
    source = "\n".join(path.read_text(encoding="utf-8") for path in package_root.glob("*.py")).lower()

    for forbidden in ("requests", "urllib", "googlemaps", "google.cloud", "subprocess"):
        assert forbidden not in source
    forbidden_methods = {"send", "delete", "trash", "archive", "modify", "label", "unsubscribe"}
    assert forbidden_methods.isdisjoint(set(dir(FakeRoutesClient)))
