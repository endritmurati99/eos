from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from src.habits import HabitService
from src.jobs.daily_capacity import run_daily_capacity
from src.jobs.evening_reset import BERLIN, _load_calendar_events, run_evening_reset
from src.jobs.weekly_plan import run_weekly_plan
from src.gateways.google_tasks import TaskGateway


def run_eos_job(
    job: str,
    *,
    target_date: date | None = None,
    week_start: date | None = None,
    dry_run: bool = True,
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(workspace_root) if workspace_root is not None else Path(__file__).resolve().parents[2]
    run_id = str(uuid.uuid4())

    if job == "daily_morning":
        day = target_date or datetime.now(BERLIN).date()
        result = run_daily_capacity(day, dry_run=dry_run, workspace_root=root)
        return {
            "status": "success" if result["calendar_read_status"] == "success" else "partial",
            "job": job,
            "run_id": run_id,
            "dry_run": dry_run,
            "delivery_status": "not_attempted" if dry_run else "delivery_disabled",
            "target_date_berlin": day.isoformat(),
            "calendar_read_status": result["calendar_read_status"],
            "task_read_status": result["task_read_status"],
            "output_markdown": _render_daily_morning(result),
            "raw": result,
        }

    if job == "evening_briefing":
        day = target_date or (datetime.now(BERLIN).date() + timedelta(days=1))
        return run_evening_reset(day, dry_run=dry_run, allow_stub_calendar=False)

    if job == "weekly_sync":
        return run_weekly_plan(
            week_start,
            dry_run=dry_run,
            allow_stub_calendar=False,
            workspace_root=root,
        )

    if job == "daily_hang_reminder":
        day = target_date or datetime.now(BERLIN).date()
        return {
            "status": "success",
            "job": job,
            "run_id": run_id,
            "dry_run": dry_run,
            "delivery_status": "not_attempted" if dry_run else "delivery_disabled",
            "target_date_berlin": day.isoformat(),
            "output_markdown": _render_daily_hang_reminder(day),
        }

    if job in {"habit_checkin_morning", "habit_checkin_evening"}:
        day = target_date or datetime.now(BERLIN).date()
        service = HabitService(workspace_root=root)
        try:
            habit_result = service.today(day)
        finally:
            service.close()
        return {
            "status": "success",
            "job": job,
            "run_id": run_id,
            "dry_run": dry_run,
            "delivery_status": "not_attempted" if dry_run else "delivery_disabled",
            "target_date_berlin": day.isoformat(),
            "pending_count": habit_result["pending_count"],
            "habits": habit_result["habits"],
            "output_markdown": _render_habit_checkin(job, habit_result),
        }

    if job == "habit_daily_summary":
        day = target_date or datetime.now(BERLIN).date()
        service = HabitService(workspace_root=root)
        try:
            habit_result = service.daily_summary(day)
        finally:
            service.close()
        return {
            "status": "success",
            "job": job,
            "run_id": run_id,
            "dry_run": dry_run,
            "delivery_status": "not_attempted" if dry_run else "delivery_disabled",
            "target_date_berlin": day.isoformat(),
            **habit_result,
        }

    if job == "habit_weekly_review":
        selected_week_start = week_start or _week_start(datetime.now(BERLIN).date())
        service = HabitService(workspace_root=root)
        try:
            habit_result = service.weekly_review(selected_week_start)
        finally:
            service.close()
        return {
            "status": "success",
            "job": job,
            "run_id": run_id,
            "dry_run": dry_run,
            "delivery_status": "not_attempted" if dry_run else "delivery_disabled",
            **habit_result,
        }

    return {
        "status": "not_found",
        "job": job,
        "run_id": run_id,
        "error": f"Unsupported EOS job: {job}",
    }


def _render_daily_morning(result: dict[str, Any]) -> str:
    lines = ["☀️ Morgenbriefing", ""]
    lines.append("🎯 Fokus")
    if result["top_tasks"]:
        for task in result["top_tasks"]:
            lines.append(f"- {task['title']}")
    elif result["task_read_status"] != "success":
        lines.append("- Aufgaben gerade nicht live verfügbar: heute nur harte Termine + ein konservatives Top-Ziel.")
    else:
        lines.append("- Noch kein klarer Top-Task: erst kurz sortieren, dann starten.")
    lines.append("")

    calendar_blocks = result.get("capacity", {}).get("calendar_blocks") or []
    if calendar_blocks:
        lines.append("📌 Fix")
        for block in calendar_blocks[:3]:
            lines.append(f"- {_format_block(block)}")
        remaining_blocks = len(calendar_blocks) - 3
        if remaining_blocks > 0:
            lines.append(f"- + {remaining_blocks} weitere Termine im Kalender, nicht hier ausformuliert.")
        lines.append("")

    lines.append("🔁 Heute sichern")
    habit_status = result.get("habit_status") or {}
    habits = habit_status.get("habits", [])
    pending = [habit for habit in habits if habit.get("pending")]
    if not pending:
        lines.append("- Alle heutigen Gewohnheiten sind abgehakt.")
    elif len(pending) > 5:
        first = pending[0]
        lines.append(f"- {first['name']} zuerst minimal absichern; {len(pending) - 1} weitere bleiben im Log.")
    else:
        for habit in pending[:3]:
            time_label = habit["target_time"] or "heute"
            lines.append(f"- {time_label}: {habit['name']} minimal erledigen oder bewusst skippen.")
        remaining = len(pending) - 3
        if remaining > 0:
            lines.append(f"- + {remaining} weitere nur bei Luft.")

    lines.append("")
    lines.append("🧭 Minimum")
    lines.append("- Wenn der Tag voll wird: ein Fokus, eine saubere Vorbereitung, keine Perfektion.")
    return "\n".join(lines).strip() + "\n"


def _format_block(block: dict[str, Any]) -> str:
    start = block.get("start")
    end = block.get("end")
    title = block.get("title") or "(ohne Titel)"
    if start and end:
        return f"{start}-{end} {title}"
    if start:
        return f"{start} {title}"
    return title


def _render_habit_checkin(job: str, result: dict[str, Any]) -> str:
    lines = [f"🌙 Kurzer EOS-Check-in für {result['business_date_berlin']}", ""]
    pending = [habit for habit in result["habits"] if habit["pending"]]
    if not pending:
        lines.append("✅ Für heute ist alles abgehakt. Wenn sich etwas anders anfühlt, sag’s mir kurz.")
        return "\n".join(lines).strip() + "\n"
    is_evening = job == "habit_checkin_evening"
    if len(pending) > 5:
        lines.append(f"Es sind noch {len(pending)} Gewohnheiten offen — ich zähle die jetzt nicht alle runter.")
        lines.append("Lass uns nur die wichtigsten durchgehen:")
    else:
        lines.append("Hast du das schon gemacht?")
    for habit in pending[:5]:
        time_label = habit["target_time"] or "heute"
        lines.append(f"- {time_label}: {habit['name']} — erledigt, teilweise oder skip?")
    remaining = len(pending) - 5
    if remaining > 0:
        briefing_label = "Abendbriefing" if is_evening else "Check-in"
        lines.append(f"- + {remaining} weitere bleiben im Log, aber nicht in diesem {briefing_label}.")
    lines.append("")
    if is_evening:
        lines.append("Danach kurz: Was ist heute passiert? Was nicht? Was macht morgen leichter?")
    else:
        lines.append("Für jetzt reicht: Was ist wichtig, was ist optional, was ist die Minimum-Version?")
    return "\n".join(lines).strip() + "\n"


def _render_daily_hang_reminder(day: date) -> str:
    return (
        f"# Klimmzugstangen-Check fuer {day.isoformat()}\n\n"
        "21:00 Check-in: Haeng dich jetzt kurz an die Klimmzugstange. "
        "Wie war dein Tag? War dein Tag erfolgreich? Was haette besser laufen koennen, "
        "damit du dich weiter verbesserst?\n"
    )


def _looks_like_sport(title: str) -> bool:
    lowered = title.lower()
    return any(
        keyword in lowered
        for keyword in (
            "kickbox",
            "bjj",
            "jiu",
            "gym",
            "cardio",
            "calisthenics",
            "turnen",
            "workout",
            "sport",
            "training",
            "fitness",
            "plyometrics",
        )
    )


def _week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())
