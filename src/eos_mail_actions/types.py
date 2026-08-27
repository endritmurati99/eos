from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class MailActionInput:
    message_id: str | None
    thread_id: str | None
    sender: str
    subject: str
    snippet: str
    body_excerpt: str | None
    categories: list[str] = field(default_factory=list)
    priority: str | None = None
    received_at: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class DeadlineExtraction:
    due: str | None
    confidence: float
    reason: str
    requires_approval: bool = False
    risk_flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ActionExtraction:
    action_type: str
    confidence: float
    reason: str
    due: str | None = None
    requires_approval: bool = True
    risk_flags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TaskProposal:
    source: str
    source_message_id: str | None
    title: str
    notes: str
    due: str | None
    list_name: str
    confidence: float
    requires_approval: bool
    reason: str
    risk_flags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
