from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Callable

from src.eos_assistant import run_assistant_command
from src.eos_intake_v2.models import AskIntent, SourceRequest, SourceSnapshot
from src.vault import read_daily_context


def build_context(
    intent: AskIntent,
    sources: list[SourceRequest],
    *,
    target_date: date | None = None,
    workspace_root: str | Path | None = None,
    assistant_runner: Callable[..., dict] = run_assistant_command,
) -> list[SourceSnapshot]:
    snapshots: list[SourceSnapshot] = []
    assistant_commands = _assistant_commands_for_intent(intent.intent)
    for command in assistant_commands:
        try:
            payload = assistant_runner(
                command,
                target_date=target_date,
                dry_run=True,
                max_results=8,
                workspace_root=workspace_root,
            )
            snapshots.append(SourceSnapshot(name=f"assistant:{command}", status=str(payload.get("status", "unknown")), payload=_compact_payload(payload)))
        except Exception as exc:  # pragma: no cover - defensive runtime boundary.
            snapshots.append(SourceSnapshot(name=f"assistant:{command}", status="failed", error=f"{type(exc).__name__}:{exc}"))

    selected_names = {source.name for source in sources}
    if "vault_notes" in selected_names:
        payload = read_daily_context(day=target_date, workspace_root=workspace_root)
        snapshots.append(
            SourceSnapshot(
                name="vault_notes",
                status=str(payload.get("status", "unknown")),
                payload=_compact_vault_payload(payload),
                error=None if payload.get("status") == "success" else str(payload.get("summary_markdown", "vault note unavailable")),
            )
        )
    if "calendar_history" in selected_names:
        snapshots.append(SourceSnapshot(name="calendar_history", status="not_implemented", error="historical meeting lookup is not part of ask_router_v1"))
    if "calendar_week" in selected_names:
        snapshots.append(SourceSnapshot(name="calendar_week", status="not_implemented", error="weekly load context is not part of ask_router_v1"))
    return snapshots


def _assistant_commands_for_intent(intent: str) -> tuple[str, ...]:
    if intent == "next_best_action":
        return ("jetzt", "mail")
    if intent == "mail_review":
        return ("mail",)
    if intent == "open_loops":
        return ("heute", "mail")
    if intent == "meeting_lookup":
        return ("mail",)
    if intent == "weekly_review":
        return ("status", "heute")
    if intent == "journal_reflection":
        return ("abend",)
    if intent == "system_health":
        return ("status",)
    return ("heute",)


def _compact_payload(payload: dict) -> dict:
    return {
        "command": payload.get("command"),
        "status": payload.get("status"),
        "mode": payload.get("mode"),
        "summary_markdown": payload.get("summary_markdown"),
        "actions": payload.get("actions", [])[:3] if isinstance(payload.get("actions"), list) else [],
        "source_status": payload.get("source_status", {}),
        "privacy": payload.get("privacy", {}),
    }


def _compact_vault_payload(payload: dict) -> dict:
    return {
        "status": payload.get("status"),
        "daily_note": payload.get("daily_note"),
        "day": payload.get("day"),
        "summary_markdown": payload.get("summary_markdown"),
        "external_mutations": payload.get("external_mutations", []),
    }
