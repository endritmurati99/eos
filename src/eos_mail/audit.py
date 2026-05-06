from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from src.eos_mail.gmail_client import GmailClientError, GmailReadOnlyClient, MailSummary
from src.eos_mail.repository import InMemoryMailShadowRepository


def run_mail_audit(
    *,
    client: GmailReadOnlyClient,
    query: str,
    max_results: int,
    dry_run: bool = True,
    repository: InMemoryMailShadowRepository | None = None,
) -> dict[str, Any]:
    repo = repository or InMemoryMailShadowRepository()
    started_at = _now_iso()
    audit_run_id = str(uuid.uuid4())
    messages: list[MailSummary] = []
    errors: list[dict[str, Any]] = []

    if not dry_run:
        finished_at = _now_iso()
        result = {
            "status": "failed",
            "error_class": "write_mode_forbidden",
            "audit_run_id": audit_run_id,
            "started_at": started_at,
            "finished_at": finished_at,
            "query": query,
            "max_results": max_results,
            "dry_run": dry_run,
            "messages_seen": 0,
            "messages": [],
            "errors": [
                {
                    "status": "write_mode_forbidden",
                    "error": "Gmail shadow mode is read-only; use --dry-run.",
                }
            ],
        }
        repo.save_audit_run(result)
        return result

    try:
        refs = client.list_messages(query=query, max_results=max_results)
        for ref in refs:
            try:
                summary = client.get_message_summary(ref.message_id)
                messages.append(summary)
                repo.save_message(summary)
            except GmailClientError as exc:
                errors.append({"message_id": ref.message_id, **exc.to_dict()})
    except GmailClientError as exc:
        errors.append(exc.to_dict())

    finished_at = _now_iso()
    top_status = _top_status(errors)
    result = {
        "status": top_status,
        "audit_run_id": audit_run_id,
        "started_at": started_at,
        "finished_at": finished_at,
        "query": query,
        "max_results": max_results,
        "dry_run": True,
        "messages_seen": len(messages),
        "messages": [message.to_dict() for message in messages],
        "errors": errors,
    }
    repo.save_audit_run(result)
    return result


def _top_status(errors: list[dict[str, Any]]) -> str:
    if not errors:
        return "success"
    statuses = {str(error.get("status") or "") for error in errors}
    if statuses & {"config_missing"}:
        return "config_missing"
    if statuses & {"auth_required"}:
        return "auth_required"
    if statuses and statuses != {"provider_error"}:
        return "partial"
    return "provider_error"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
