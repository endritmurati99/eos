from __future__ import annotations

from datetime import date
from typing import Any

from src.eos_mail.audit import run_mail_audit
from src.eos_mail.gmail_client import GmailReadOnlyClient
from src.eos_mail.repository import InMemoryMailShadowRepository


def run_shadow_ingestion(
    *,
    client: GmailReadOnlyClient,
    query: str,
    max_results: int,
    dry_run: bool = True,
    repository: InMemoryMailShadowRepository | None = None,
) -> dict[str, Any]:
    return run_mail_audit(
        client=client,
        query=query,
        max_results=max_results,
        dry_run=dry_run,
        repository=repository,
    )


def query_from_last(raw_last: str) -> str:
    value = raw_last.strip().lower()
    if value and value[:-1].isdigit() and value[-1] in {"d", "w", "m", "y"}:
        return f"newer_than:{value}"
    if value and value.isdigit():
        return f"newer_than:{value}d"
    return value or "newer_than:7d"


def query_for_today(today: date | None = None) -> str:
    target = today or date.today()
    return f"after:{target.strftime('%Y/%m/%d')}"
