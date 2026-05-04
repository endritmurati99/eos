from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DriveFileMetadata:
    file_id: str
    name: str
    mime_type: str
    modified_time: str | None
    web_link: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
