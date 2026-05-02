from __future__ import annotations

import json
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from src.gateways.google_tasks import CANONICAL_LISTS, TaskGateway
from src.habits import HabitService
from src.jobs.evening_reset import BERLIN, _load_calendar_events


def run_weekly_plan(
    week_start: date | None = None,
    *,
    dry_run: bool = True,
    allow_stub_calendar: bool = False,
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(workspace_root) if workspace_root is not None else Path(__file__).resolve().parents[2]
    target_week_start = week_start or _next_monday(datetime.now(BERLIN).date())
    week_end = target_week_start + timedelta(days=7)
    run_id = str(uuid.uuid4())
    gateway = TaskGateway()

    days = []
    calendar_failures = []
    for offset in range(7):
        day = target_week_start + timedelta(days=offset)
        calendar_result = _load_calendar_events(
            gateway=gateway,
            workspace_root=root,
            target_date_berlin=day,
            dry_run=dry_run,
            allow_stub_calendar=allow_stub_calendar,
        )
        if calendar_result["calendar_read_status"] != "success":
            calendar_failures.append(
                {
                    "date": day.isoformat(),
                    "status": calendar_result["calendar_read_status"],
                    "error": calendar_result.get("error"),
                }
            )
        days.append(
            {
                "date": day.isoformat(),
                "weekday": day.strftime("%A"),
                "calendar_read_status": calendar_result["calendar_read_status"],
                "source": calendar_result["source"],
                "hard_events": calendar_result.get("hard_events", []),
            }
        )

    task_result = gateway.readOpenTasks(CANONICAL_LISTS)
    habit_service = HabitService(workspace_root=root)
    try:
        habit_report = habit_service.weekly_report(target_week_start)
    finally:
        habit_service.close()
    habit_collision_summary = _habit_collision_summary(days, habit_report)
    evaluation = _evaluate_week(days, task_result)
    output_markdown = _render_weekly_output(
        week_start=target_week_start,
        week_end=week_end,
        days=days,
        task_result=task_result,
        habit_report=habit_report,
        habit_collision_summary=habit_collision_summary,
        evaluation=evaluation,
    )

    status = "success"
    if calendar_failures or task_result["task_read_status"] != "success":
        status = "partial"

    return {
        "status": status,
        "job": "weekly_sync",
        "run_id": run_id,
        "dry_run": dry_run,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "week_start_berlin": target_week_start.isoformat(),
        "week_end_berlin": week_end.isoformat(),
        "calendar_failures": calendar_failures,
        "task_read_status": task_result["task_read_status"],
        "open_task_count": task_result["open_task_count"],
        "tasks_by_list": task_result["tasks_by_list"],
        "habit_report": habit_report,
        "habit_collision_summary": habit_collision_summary,
        "evaluation": evaluation,
        "output_markdown": output_markdown,
    }


def _next_monday(today: date) -> date:
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    return today + timedelta(days=days_until_monday)


def _evaluate_week(days: list[dict[str, Any]], task_result: dict[str, Any]) -> dict[str, Any]:
    hard_event_count = sum(len(day["hard_events"]) for day in days)
    stacked_days = [
        day["date"]
        for day in days
        if len(day["hard_events"]) >= 3
    ]
    sport_days = [
        day["date"]
        for day in days
        if any(_looks_like_sport(event.get("title", "")) for event in day["hard_events"])
    ]
    work_days = [
        day["date"]
        for day in days
        if any("arbeit" in str(event.get("title", "")).lower() for event in day["hard_events"])
    ]

    risks = []
    if stacked_days:
        risks.append("stacked_hard_days")
    if task_result["task_read_status"] != "success":
        risks.append("missing_task_basis")
    if len(sport_days) >= 4:
        risks.append("high_sport_density")

    return {
        "hard_event_count": hard_event_count,
        "stacked_days": stacked_days,
        "sport_days": sport_days,
        "work_days": work_days,
        "risks": risks,
        "recommended_deep_work_blocks": 1 if stacked_days else 2,
        "recommended_gym_blocks": 1 if len(sport_days) >= 4 else 2,
        "recommended_cardio_blocks": 1 if len(sport_days) >= 4 else 2,
    }


def _render_weekly_output(
    *,
    week_start: date,
    week_end: date,
    days: list[dict[str, Any]],
    task_result: dict[str, Any],
    habit_report: dict[str, Any],
    habit_collision_summary: dict[str, list[str]],
    evaluation: dict[str, Any],
) -> str:
    lines = [f"# Wochenplan {week_start.isoformat()} bis {week_end.isoformat()}", ""]

    lines.append("## Harte Termine")
    for day in days:
        lines.append(f"### {day['date']} ({day['weekday']})")
        if day["hard_events"]:
            for event in day["hard_events"]:
                lines.append(f"- {_event_label(event)}")
        else:
            lines.append("- Keine harten Termine live bestaetigt.")
    lines.append("")

    lines.append("## Offene Aufgaben")
    if task_result["task_read_status"] != "success":
        lines.append("- Google Tasks konnte nicht live gelesen werden. Keine erfundenen Aufgaben.")
    else:
        for list_name in CANONICAL_LISTS:
            tasks = task_result["tasks_by_list"].get(list_name, [])
            lines.append(f"- {list_name}: {len(tasks)} offen")
            for task in tasks[:3]:
                due = f" (due {task['due'][:10]})" if task.get("due") else ""
                lines.append(f"  - {task['title']}{due}")
    lines.append("")

    lines.append("## Habits")
    for habit in habit_report["habits"]:
        collision_days = habit_collision_summary.get(habit["id"], [])
        collision_note = f", calendar conflicts {len(collision_days)}" if collision_days else ""
        lines.append(
            f"- {habit['name']}: full {habit['full_count']}/7, "
            f"partial {habit['partial_count']}, skipped {habit['skipped_count']}, "
            f"missed {habit['missed_count']}, streak {habit['current_streak']}{collision_note}"
        )
    lines.append("")

    lines.append("## Engstellen")
    if evaluation["risks"]:
        for risk in evaluation["risks"]:
            lines.append(f"- {risk}")
    else:
        lines.append("- Keine harte Engstelle aus Live-Daten erkannt.")
    lines.append("")

    lines.append("## Empfohlene Verteilung")
    lines.append(f"- Deep Work: {evaluation['recommended_deep_work_blocks']} Block/Blocks konservativ platzieren")
    lines.append(f"- Gym: {evaluation['recommended_gym_blocks']} flexible Einheit(en)")
    lines.append(f"- Cardio: {evaluation['recommended_cardio_blocks']} flexible Einheit(en)")
    lines.append("")

    lines.append("## Gekuerzte oder riskante Punkte")
    if "high_sport_density" in evaluation["risks"]:
        lines.append("- Cardio/Gym reduzieren, weil bereits viele Sporttage im Kalender liegen.")
    elif "stacked_hard_days" in evaluation["risks"]:
        lines.append("- Zweiten Deep-Work-Block nur setzen, wenn ein echter freier Morgen bleibt.")
    else:
        lines.append("- Keine Reduktion aus Live-Daten zwingend.")
    lines.append("")

    lines.append("## Nicht vergessen")
    lines.append("- Sonntag 18:00 bleibt der Weekly-Plan-Anker.")
    lines.append("- Flexible Bloecke erst nach harten Terminen setzen.")
    return "\n".join(lines).strip() + "\n"


def _event_label(event: dict[str, Any]) -> str:
    start = event.get("start_display")
    end = event.get("end_display")
    if start and end:
        return f"{start}-{end} {event.get('title') or '(ohne Titel)'}"
    return event.get("title") or "(ohne Titel)"


def _habit_collision_summary(days: list[dict[str, Any]], habit_report: dict[str, Any]) -> dict[str, list[str]]:
    summary: dict[str, list[str]] = {}
    for habit in habit_report.get("habits", []):
        target_time = habit.get("target_time")
        if not target_time:
            continue
        collision_days = []
        for day in days:
            if any(_event_overlaps_time(event, target_time) for event in day.get("hard_events", [])):
                collision_days.append(day["date"])
        summary[habit["id"]] = collision_days
    return summary


def _event_overlaps_time(event: dict[str, Any], target_time: str) -> bool:
    start = _parse_hhmm(event.get("start_display"))
    end = _parse_hhmm(event.get("end_display"))
    target = _parse_hhmm(target_time)
    if start is None or end is None or target is None:
        return False
    return start <= target <= end


def _parse_hhmm(value: str | None) -> int | None:
    if not value or len(value) < 5:
        return None
    try:
        hour, minute = value[:5].split(":")
        return int(hour) * 60 + int(minute)
    except ValueError:
        return None


def _looks_like_sport(title: str) -> bool:
    lowered = title.lower()
    return any(
        keyword in lowered
        for keyword in ("kickbox", "bjj", "jiu", "gym", "cardio", "calisthenics", "turnen", "workout")
    )


if __name__ == "__main__":
    print(json.dumps(run_weekly_plan(), indent=2, ensure_ascii=True))
