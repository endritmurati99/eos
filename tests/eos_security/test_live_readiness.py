from eos_security import google_live_readiness_status


def test_google_live_readiness_default_is_blocked() -> None:
    assert google_live_readiness_status({}) == {
        "status": "blocked",
        "live_e2e_enabled": False,
        "gmail_live_allowed": False,
        "drive_live_allowed": False,
        "maps_live_allowed": False,
        "calendar_live_allowed": False,
    }


def test_service_flags_do_not_allow_live_without_global_gate() -> None:
    status = google_live_readiness_status(
        {
            "EOS_GMAIL_READONLY_ENABLED": "true",
            "EOS_DRIVE_READONLY_ENABLED": "true",
            "EOS_MAPS_ROUTES_ENABLED": "true",
        }
    )

    assert status["status"] == "blocked"
    assert status["gmail_live_allowed"] is False
    assert status["drive_live_allowed"] is False
    assert status["maps_live_allowed"] is False
    assert status["calendar_live_allowed"] is False


def test_calendar_live_is_not_allowed_by_default_or_service_flags() -> None:
    status = google_live_readiness_status(
        {
            "EOS_GOOGLE_LIVE_E2E_ENABLED": "true",
            "EOS_GMAIL_READONLY_ENABLED": "false",
            "EOS_DRIVE_READONLY_ENABLED": "false",
            "EOS_MAPS_ROUTES_ENABLED": "false",
        }
    )

    assert status["status"] == "blocked"
    assert status["calendar_live_allowed"] is False


def test_explicit_global_and_service_flags_allow_bounded_readiness() -> None:
    status = google_live_readiness_status(
        {
            "EOS_GOOGLE_LIVE_E2E_ENABLED": "true",
            "EOS_GMAIL_READONLY_ENABLED": "true",
            "EOS_DRIVE_READONLY_ENABLED": "false",
            "EOS_MAPS_ROUTES_ENABLED": "false",
        }
    )

    assert status["status"] == "ready"
    assert status["live_e2e_enabled"] is True
    assert status["gmail_live_allowed"] is True
    assert status["drive_live_allowed"] is False
    assert status["maps_live_allowed"] is False
    assert status["calendar_live_allowed"] is False
