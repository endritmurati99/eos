from __future__ import annotations

from src.eos_drive import ALLOWED_DRIVE_METADATA_FIELDS, DriveMetadataReadOnlyClient, run_drive_readonly_preflight


def test_drive_preflight_default_is_warning_and_readonly() -> None:
    result = run_drive_readonly_preflight(env={})

    assert result["status"] == "warning"
    assert result["drive_readonly_enabled"] is False
    assert result["live_verified"] is False
    assert result["write_actions_available"] is False
    assert result["allowed_metadata_fields"] == list(ALLOWED_DRIVE_METADATA_FIELDS)
    assert any(issue["code"] == "drive_readonly_disabled" for issue in result["issues"])


def test_drive_preflight_rejects_write_scopes() -> None:
    result = run_drive_readonly_preflight(
        env={
            "EOS_DRIVE_READONLY_ENABLED": "true",
            "EOS_DRIVE_SCOPES": "https://www.googleapis.com/auth/drive",
        }
    )

    assert result["status"] == "failed"
    assert result["write_scopes_detected"] is True
    assert any(issue["code"] == "write_scope_forbidden" for issue in result["issues"])


def test_drive_preflight_does_not_emit_secret_values() -> None:
    result = run_drive_readonly_preflight(
        env={
            "EOS_GOOGLE_ACCOUNT": "person@example.test",
            "EOS_GOOGLE_TOKEN_PATH": "/tmp/oauth-token-root/ya29.secret-token",
            "EOS_GOOGLE_CREDENTIALS_PATH": "/tmp/oauth/client_secret_123.json",
            "EOS_DRIVE_READONLY_ENABLED": "true",
            "EOS_DRIVE_SCOPES": "https://www.googleapis.com/auth/drive.metadata.readonly",
        }
    )
    rendered = str(result)

    assert result["account_configured"] is True
    assert result["token_path_configured"] is True
    assert result["credentials_path_configured"] is True
    assert "person@example.test" not in rendered
    assert "ya29.secret-token" not in rendered
    assert "client_secret_123.json" not in rendered


def test_drive_client_interface_has_no_content_or_write_methods() -> None:
    forbidden_methods = {
        "download",
        "download_file",
        "get_content",
        "write",
        "delete",
        "trash",
        "create",
        "update",
        "change_permissions",
    }

    assert forbidden_methods.isdisjoint(set(dir(DriveMetadataReadOnlyClient)))
