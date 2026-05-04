from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.eos_mail.gmail_client import MailSummary


@dataclass
class InMemoryMailShadowRepository:
    messages: list[MailSummary] = field(default_factory=list)
    audit_runs: list[dict[str, Any]] = field(default_factory=list)

    def save_message(self, summary: MailSummary) -> None:
        self.messages.append(summary)

    def save_audit_run(self, audit_run: dict[str, Any]) -> None:
        self.audit_runs.append(audit_run)

    def message_dicts(self) -> list[dict[str, Any]]:
        return [message.to_dict() for message in self.messages]
