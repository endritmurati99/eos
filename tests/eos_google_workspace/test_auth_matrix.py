from __future__ import annotations

from src.eos_google_workspace import (
    GoogleIntegrationAuth,
    detect_forbidden_google_write_scopes,
    get_google_auth_matrix,
)


def test_auth_matrix_contains_required_integrations_readonly_unverified() -> None:
    matrix = get_google_auth_matrix()

    assert set(matrix) == {
        "gmail_readonly",
        "drive_metadata_readonly",
        "calendar_readonly",
        "maps_routes_readonly",
    }
    assert all(isinstance(item, GoogleIntegrationAuth) for item in matrix.values())
    assert all(item.write_capable is False for item in matrix.values())
    assert all(item.live_verified is False for item in matrix.values())
    assert matrix["gmail_readonly"].required_scope_or_key == "https://www.googleapis.com/auth/gmail.readonly"
    assert matrix["drive_metadata_readonly"].required_scope_or_key == "https://www.googleapis.com/auth/drive.metadata.readonly"
    assert matrix["calendar_readonly"].required_scope_or_key == "https://www.googleapis.com/auth/calendar.readonly"
    assert matrix["maps_routes_readonly"].required_scope_or_key == "EOS_GOOGLE_MAPS_API_KEY"


def test_auth_matrix_serializes_to_plain_dicts() -> None:
    payload = get_google_auth_matrix()["drive_metadata_readonly"].to_dict()

    assert payload["service_name"] == "drive_metadata_readonly"
    assert payload["write_capable"] is False
    assert payload["live_verified"] is False
    assert isinstance(payload["allowed_actions"], list)
    assert isinstance(payload["forbidden_actions"], list)


def test_forbidden_google_write_scopes_detected_without_flagging_readonly() -> None:
    detected = detect_forbidden_google_write_scopes(
        "https://www.googleapis.com/auth/gmail.readonly "
        "https://www.googleapis.com/auth/gmail.modify,"
        "https://www.googleapis.com/auth/calendar.events"
    )

    assert detected == (
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/calendar.events",
    )
