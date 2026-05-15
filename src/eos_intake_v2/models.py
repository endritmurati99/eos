from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AskIntent:
    intent: str
    confidence: float
    reason: str
    query: str
    entities: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceRequest:
    name: str
    mode: str = "read_only"
    required: bool = False
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SourceSnapshot:
    name: str
    status: str
    payload: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SafetyDecision:
    status: str
    external_writes_allowed: bool
    external_writes_performed: bool
    requires_confirmation_for_writes: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AskAnswer:
    status: str
    command: str
    query: str
    intent: str
    confidence: float
    answer: str
    why: list[str]
    next_action: str
    uncertainty: list[str]
    sources_selected: list[dict[str, Any]]
    source_status: dict[str, Any]
    safety: dict[str, Any]
    mode: str = "read_only"

    @property
    def summary_markdown(self) -> str:
        lines = ["Antwort:", self.answer.strip() or "Keine sichere Antwort ableitbar.", ""]
        lines.append("Warum:")
        lines.extend(f"- {item}" for item in (self.why or ["Keine belastbaren Quellen verfügbar."]))
        lines.extend(["", "Nächste Aktion:", self.next_action.strip() or "Kurz manuell prüfen.", ""])
        lines.append("Unsicherheit:")
        lines.extend(f"- {item}" for item in (self.uncertainty or ["Keine wesentliche Unsicherheit erkannt."]))
        return "\n".join(lines).strip()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["summary_markdown"] = self.summary_markdown
        data["privacy"] = {
            "contains_private_user_data": True,
            "raw_provider_output_included": False,
            "external_writes_performed": self.safety.get("external_writes_performed", False),
            "requires_approval_for_writes": self.safety.get("requires_confirmation_for_writes", True),
        }
        return data
