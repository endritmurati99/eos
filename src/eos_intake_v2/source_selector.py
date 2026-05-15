from __future__ import annotations

from src.eos_intake_v2.models import AskIntent, SourceRequest


_SOURCE_MAP: dict[str, tuple[SourceRequest, ...]] = {
    "daily_status": (
        SourceRequest("calendar_today", required=True, reason="hard events and focus windows"),
        SourceRequest("tasks_open", reason="open operational work"),
        SourceRequest("energy_today", reason="capacity check"),
        SourceRequest("vault_notes", reason="durable daily stand and project context"),
    ),
    "next_best_action": (
        SourceRequest("calendar_today", required=True, reason="available window"),
        SourceRequest("tasks_open", reason="candidate actions"),
        SourceRequest("energy_today", reason="realistic action size"),
        SourceRequest("mail_action_required", reason="urgent replies"),
    ),
    "mail_review": (
        SourceRequest("gmail_readonly", required=True, reason="read-only digest and action-required signals"),
        SourceRequest("mail_task_proposals", reason="possible follow-up tasks"),
    ),
    "open_loops": (
        SourceRequest("tasks_open", required=True, reason="active task loops"),
        SourceRequest("gmail_readonly", reason="reply loops"),
        SourceRequest("calendar_today", reason="today commitments"),
        SourceRequest("habits_today", reason="habit loops"),
    ),
    "meeting_lookup": (
        SourceRequest("calendar_history", required=True, reason="meeting identity/date"),
        SourceRequest("gmail_readonly", reason="related threads"),
        SourceRequest("tasks_open", reason="follow-up tasks"),
        SourceRequest("vault_notes", reason="durable notes if configured"),
    ),
    "weekly_review": (
        SourceRequest("calendar_week", required=True, reason="weekly load"),
        SourceRequest("tasks_open", reason="priority count"),
        SourceRequest("habits_week", reason="trend and energy signals"),
    ),
    "journal_reflection": (
        SourceRequest("daily_review", reason="evening review surface"),
        SourceRequest("habits_today", reason="what happened"),
        SourceRequest("energy_today", reason="energy drain"),
        SourceRequest("vault_notes", reason="daily note Verlauf and current stand"),
    ),
    "system_health": (
        SourceRequest("system_status", required=True, reason="runtime readiness"),
    ),
}


def select_sources(intent: AskIntent) -> list[SourceRequest]:
    return list(_SOURCE_MAP.get(intent.intent, _SOURCE_MAP["daily_status"]))
