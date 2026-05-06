from __future__ import annotations

from typing import Protocol

from src.eos_drive.types import DriveFileMetadata


ALLOWED_DRIVE_METADATA_FIELDS = (
    "id",
    "name",
    "mimeType",
    "modifiedTime",
    "webViewLink",
)

FORBIDDEN_DRIVE_ACTIONS = (
    "download file content",
    "write files",
    "delete files",
    "change permissions",
    "persist raw documents",
)


class DriveMetadataReadOnlyClient(Protocol):
    def list_metadata(self, query: str | None = None, max_results: int = 50) -> list[DriveFileMetadata]:
        ...
