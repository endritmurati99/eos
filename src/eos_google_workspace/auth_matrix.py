from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
DRIVE_METADATA_READONLY_SCOPE = "https://www.googleapis.com/auth/drive.metadata.readonly"
CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
MAPS_ROUTES_KEY_NAME = "EOS_GOOGLE_MAPS_API_KEY"

FORBIDDEN_GOOGLE_WRITE_SCOPES = (
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
)


@dataclass(frozen=True)
class GoogleIntegrationAuth:
    service_name: str
    api_name: str
    auth_type: str
    required_scope_or_key: str
    write_capable: bool
    live_verified: bool
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    eos_phase: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_name": self.service_name,
            "api_name": self.api_name,
            "auth_type": self.auth_type,
            "required_scope_or_key": self.required_scope_or_key,
            "write_capable": self.write_capable,
            "live_verified": self.live_verified,
            "allowed_actions": list(self.allowed_actions),
            "forbidden_actions": list(self.forbidden_actions),
            "eos_phase": self.eos_phase,
        }


def get_google_auth_matrix() -> dict[str, GoogleIntegrationAuth]:
    return {
        "gmail_readonly": GoogleIntegrationAuth(
            service_name="gmail_readonly",
            api_name="Gmail API",
            auth_type="oauth_scope",
            required_scope_or_key=GMAIL_READONLY_SCOPE,
            write_capable=False,
            live_verified=False,
            allowed_actions=(
                "list messages",
                "get message metadata",
                "get selected headers",
                "get snippets",
            ),
            forbidden_actions=(
                "send mail",
                "delete mail",
                "archive mail",
                "modify labels",
                "unsubscribe",
            ),
            eos_phase="phase_1_readonly_shadow",
        ),
        "drive_metadata_readonly": GoogleIntegrationAuth(
            service_name="drive_metadata_readonly",
            api_name="Google Drive API",
            auth_type="oauth_scope",
            required_scope_or_key=DRIVE_METADATA_READONLY_SCOPE,
            write_capable=False,
            live_verified=False,
            allowed_actions=(
                "list file metadata",
                "read filename",
                "read mime type",
                "read modified time",
                "read web link",
            ),
            forbidden_actions=(
                "download file content",
                "write files",
                "delete files",
                "change permissions",
                "persist raw documents",
            ),
            eos_phase="phase_1_readonly_context",
        ),
        "calendar_readonly": GoogleIntegrationAuth(
            service_name="calendar_readonly",
            api_name="Google Calendar API",
            auth_type="oauth_scope",
            required_scope_or_key=CALENDAR_READONLY_SCOPE,
            write_capable=False,
            live_verified=False,
            allowed_actions=(
                "read event metadata",
                "read event time",
                "read event location",
                "read calendar role",
            ),
            forbidden_actions=(
                "create events",
                "update events",
                "delete events",
                "change attendees",
            ),
            eos_phase="phase_1_readonly_planning",
        ),
        "maps_routes_readonly": GoogleIntegrationAuth(
            service_name="maps_routes_readonly",
            api_name="Google Maps Routes API",
            auth_type="api_key",
            required_scope_or_key=MAPS_ROUTES_KEY_NAME,
            write_capable=False,
            live_verified=False,
            allowed_actions=(
                "estimate route duration",
                "estimate distance text",
                "compare travel modes",
            ),
            forbidden_actions=(
                "store location history",
                "perform live tracking",
                "write location data",
            ),
            eos_phase="phase_1_readiness_fake_provider",
        ),
    }


def detect_forbidden_google_write_scopes(
    scopes: str | list[str] | tuple[str, ...] | set[str] | None,
) -> tuple[str, ...]:
    if scopes is None:
        return ()
    if isinstance(scopes, str):
        candidates = re.split(r"[\s,;]+", scopes)
    else:
        candidates = [str(scope) for scope in scopes]
    normalized = {scope.strip() for scope in candidates if scope and scope.strip()}
    return tuple(scope for scope in FORBIDDEN_GOOGLE_WRITE_SCOPES if scope in normalized)
