from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class MailInput:
    message_id: str | None
    thread_id: str | None
    sender: str
    subject: str
    snippet: str
    body_excerpt: str | None
    headers: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MailClassification:
    categories: list[str]
    priority: str
    requires_reply: bool
    safe_to_archive: bool
    confidence: float
    reason: str
    risk_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
