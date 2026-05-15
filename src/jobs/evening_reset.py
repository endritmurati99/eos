from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from src.database import init_db
from src.gateways.google_tasks import CANONICAL_LISTS, TaskGateway
from src.jobs.briefing_render import calendar_shape_line, compact_event_lines, hydration_check_line

BERLIN = ZoneInfo("Europe/Berlin")
TARGET_CALENDAR_ROLES = ("primary", "sport")
ACTIONABLE_LISTS = ("Next", "This Week", "Inbox")
READ_ORDER = ("Next", "This Week", "Inbox", "Waiting")
SUPPORTED_REASONS = {
    "hard_shift_plus_fixed_sport",
    "too_many_heavy_blocks",
    "missing_task_basis",
    "prep_risk",
    "poor_distribution",
}


def run_evening_reset(
    target_date: date | None = None,
    dry_run: bool = True,
    allow_stub_calendar: bool = False,
    force: bool = False,
    db_path: str | None = None,
) -> dict[str, Any]:
    workspace_root = Path(__file__).resolve().parents[2]
    template_path = workspace_root / "templates" / "evening-reset-output.md"
    _ensure_template_contract(template_path)

    target_date_berlin = target_date or (
        datetime.now(BERLIN).date() + timedelta(days=1)
    )
    target_window_start = datetime.combine(target_date_berlin, time.min, tzinfo=BERLIN)
    target_window_end = target_window_start + timedelta(days=1)
    idempotency_key = f"evening_reset:{target_date_berlin.isoformat()}"
    run_id = str(uuid.uuid4())
    timestamp_utc = _utc_now_iso()

    connection = init_db(db_path)
    existing_job_run = _fetch_job_run(connection, "evening_reset", idempotency_key)
    if (
        not dry_run
        and not force
        and existing_job_run
        and existing_job_run["run_status"] in {"generated", "sent"}
    ):
        connection.close()
        return {
            "status": "blocked",
            "job": "evening_reset",
            "run_id": run_id,
            "idempotency_key": idempotency_key,
            "target_date_berlin": target_date_berlin.isoformat(),
            "reason": "A generated or sent run already exists for this target date.",
        }

    gateway = TaskGateway()
    calendar_result = _load_calendar_events(
        gateway=gateway,
        workspace_root=workspace_root,
        target_date_berlin=target_date_berlin,
        dry_run=dry_run,
        allow_stub_calendar=allow_stub_calendar,
    )
    if calendar_result["status"] == "failed":
        _persist_job_run(
            connection=connection,
            existing_job_run=existing_job_run,
            run_id=run_id,
            idempotency_key=idempotency_key,
            target_window_start=target_window_start,
            target_window_end=target_window_end,
            target_business_date=target_date_berlin.isoformat(),
            run_status="failed",
            calendar_read_status=calendar_result["calendar_read_status"],
            task_read_status="not_attempted",
            delivery_status="not_attempted" if dry_run else "delivery_disabled",
            message_digest=None,
            last_error=calendar_result.get("error"),
            created_at_utc=timestamp_utc,
            updated_at_utc=timestamp_utc,
            allow_overwrite_blocking=False,
        )
        connection.close()
        return {
            "status": "failed",
            "job": "evening_reset",
            "run_id": run_id,
            "idempotency_key": idempotency_key,
            "target_date_berlin": target_date_berlin.isoformat(),
            "calendar_read_status": calendar_result["calendar_read_status"],
            "error": calendar_result.get("error"),
        }

    task_bundle = _load_tasks(gateway, target_date_berlin)
    task_snapshot_id = _persist_task_snapshot(connection, task_bundle)

    evaluation = _evaluate_tomorrow(
        target_date_berlin=target_date_berlin,
        calendar_result=calendar_result,
        task_bundle=task_bundle,
    )
    rendered_output = _render_evening_reset(
        target_date_berlin=target_date_berlin,
        calendar_result=calendar_result,
        task_bundle=task_bundle,
        evaluation=evaluation,
    )
    message_digest = hashlib.sha256(rendered_output.encode("utf-8")).hexdigest()

    _persist_daily_evaluation(
        connection=connection,
        target_date_berlin=target_date_berlin.isoformat(),
        evaluation=evaluation,
        task_snapshot_id=task_snapshot_id,
        created_at_utc=timestamp_utc,
    )

    run_status = "dry_run" if dry_run else "generated"
    calendar_read_status = calendar_result["calendar_read_status"]
    task_read_status = task_bundle["task_read_status"]
    delivery_status = "not_attempted" if dry_run else "delivery_disabled"

    job_run_persisted = _persist_job_run(
        connection=connection,
        existing_job_run=existing_job_run,
        run_id=run_id,
        idempotency_key=idempotency_key,
        target_window_start=target_window_start,
        target_window_end=target_window_end,
        target_business_date=target_date_berlin.isoformat(),
        run_status=run_status,
        calendar_read_status=calendar_read_status,
        task_read_status=task_read_status,
        delivery_status=delivery_status,
        message_digest=message_digest,
        last_error=None,
        created_at_utc=timestamp_utc,
        updated_at_utc=timestamp_utc,
        allow_overwrite_blocking=dry_run is False and force,
    )
    connection.close()

    overall_status = "success"
    if calendar_read_status != "success" or task_read_status != "success":
        overall_status = "partial"

    return {
        "status": overall_status,
        "job": "evening_reset",
        "run_id": run_id,
        "idempotency_key": idempotency_key,
        "target_date_berlin": target_date_berlin.isoformat(),
        "dry_run": dry_run,
        "calendar_read_status": calendar_read_status,
        "calendar_source": calendar_result["source"],
        "task_read_status": task_read_status,
        "load_status": evaluation["status"],
        "reasons": evaluation["reasons"],
        "recommendation": evaluation["recommendation"],
        "warning": evaluation["warning"],
        "task_snapshot_id": task_snapshot_id,
        "job_run_persisted": job_run_persisted,
        "output_markdown": rendered_output,
    }


def _load_calendar_events(
    *,
    gateway: TaskGateway,
    workspace_root: Path,
    target_date_berlin: date,
    dry_run: bool,
    allow_stub_calendar: bool,
) -> dict[str, Any]:
    calendar_source_path = workspace_root / "integrations" / "calendar-source.json"
    if calendar_source_path.exists():
        calendar_source = json.loads(calendar_source_path.read_text(encoding="utf-8"))
    else:
        calendar_source = {}

    live_result = _load_live_calendar_events(
        gog_bin=gateway.gog_bin,
        account=gateway.account,
        token_root=gateway.token_root,
        calendar_source=calendar_source,
        target_date_berlin=target_date_berlin,
    )
    if live_result["status"] == "success":
        return live_result

    if dry_run or allow_stub_calendar:
        stub_result = _load_stub_calendar_events(
            workspace_root=workspace_root,
            target_date_berlin=target_date_berlin,
            live_error=live_result.get("error"),
            live_status=live_result.get("calendar_read_status"),
        )
        if stub_result["status"] == "success":
            return stub_result

    return {
        "status": "failed",
        "source": "unavailable",
        "calendar_read_status": live_result.get("calendar_read_status", "provider_error"),
        "events": [],
        "hard_events": [],
        "has_fixed_sport": False,
        "error": live_result.get("error", "Calendar read failed and no fallback was allowed."),
    }


def _load_live_calendar_events(
    *,
    gog_bin: str | None,
    account: str | None,
    token_root: str | None,
    calendar_source: dict[str, Any],
    target_date_berlin: date,
) -> dict[str, Any]:
    if not gog_bin:
        return {
            "status": "failed",
            "calendar_read_status": "config_missing",
            "source": "live_gog",
            "error": "gog binary not configured.",
        }
    if not account:
        return {
            "status": "failed",
            "calendar_read_status": "config_missing",
            "source": "live_gog",
            "error": "Google account is missing for calendar read.",
        }

    calendar_ids = [
        item.get("id")
        for item in calendar_source.get("calendars", [])
        if item.get("role") in TARGET_CALENDAR_ROLES and item.get("id")
    ]
    if not calendar_ids:
        return {
            "status": "failed",
            "calendar_read_status": "config_missing",
            "source": "live_gog",
            "error": "No primary/sport calendars are configured in integrations/calendar-source.json.",
        }

    env = os.environ.copy()
    if token_root:
        token_root_path = Path(token_root).expanduser()
        token_root_path.mkdir(parents=True, exist_ok=True)
        env["XDG_CONFIG_HOME"] = str(token_root_path)

    target_end = target_date_berlin + timedelta(days=1)
    command = [
        gog_bin,
        "-a",
        account,
        "calendar",
        "events",
        "--from",
        target_date_berlin.isoformat(),
        "--to",
        target_end.isoformat(),
        "--calendars",
        ",".join(calendar_ids),
        "--json",
        "--results-only",
        "--no-input",
    ]
    completed = subprocess.run(command, capture_output=True, text=True, env=env)
    if completed.returncode != 0:
        status = "provider_error"
        stderr = completed.stderr.strip()
        if completed.returncode == 10 or "OAuth client credentials missing" in stderr:
            status = "config_missing"
        elif completed.returncode == 4 or "No tokens stored" in stderr:
            status = "auth_required"
        return {
            "status": "failed",
            "calendar_read_status": status,
            "source": "live_gog",
            "error": stderr or completed.stdout.strip() or "Live calendar read failed.",
        }

    payload = json.loads(completed.stdout or "[]")
    raw_events = payload if isinstance(payload, list) else payload.get("items", [])
    normalized_events = [_normalize_live_calendar_event(item) for item in raw_events]
    hard_events = [event for event in normalized_events if event["is_hard_event"]]
    has_fixed_sport = any(event["is_fixed_sport"] for event in normalized_events)

    return {
        "status": "success",
        "calendar_read_status": "success",
        "source": "live_gog",
        "events": normalized_events,
        "hard_events": hard_events,
        "has_fixed_sport": has_fixed_sport,
        "error": None,
    }


def _load_stub_calendar_events(
    *,
    workspace_root: Path,
    target_date_berlin: date,
    live_error: str | None,
    live_status: str | None,
) -> dict[str, Any]:
    stub_path = workspace_root / "data" / "calendar.json"
    if not stub_path.exists():
        return {
            "status": "failed",
            "calendar_read_status": live_status or "provider_error",
            "source": "stub_file",
            "error": "data/calendar.json is missing and no live calendar is available.",
        }

    payload = json.loads(stub_path.read_text(encoding="utf-8"))
    weekday = target_date_berlin.strftime("%A").lower()

    events = []
    for item in payload.get("events", []):
        if item.get("weekday", "").lower() != weekday:
            continue
        item_type = item.get("type")
        is_work_signal = item_type == "work_block"
        is_hard_event = bool(item.get("fixed")) or is_work_signal
        if not is_hard_event:
            continue
        events.append(
            {
                "title": item.get("title") or "(ohne Titel)",
                "start_display": item.get("start") or "",
                "end_display": item.get("end") or "",
                "is_hard_event": True,
                "is_fixed_sport": item_type == "sport_class" and bool(item.get("fixed")),
                "is_work_signal": is_work_signal,
                "source_note": "stub",
            }
        )

    return {
        "status": "success",
        "calendar_read_status": "stub_fallback",
        "source": "stub_file",
        "events": events,
        "hard_events": events,
        "has_fixed_sport": any(event["is_fixed_sport"] for event in events),
        "error": live_error,
    }


def _normalize_live_calendar_event(event: dict[str, Any]) -> dict[str, Any]:
    title = event.get("summary") or event.get("title") or "(ohne Titel)"
    start_display = _format_event_time(event.get("start"))
    end_display = _format_event_time(event.get("end"))
    lower_title = title.lower()
    is_fixed_sport = any(keyword in lower_title for keyword in ("kickbox", "bjj", "jiu-jitsu"))
    is_work_signal = "arbeit" in lower_title

    return {
        "title": title,
        "start_display": start_display,
        "end_display": end_display,
        "is_hard_event": True,
        "is_fixed_sport": is_fixed_sport,
        "is_work_signal": is_work_signal,
        "source_note": "live",
    }


def _load_tasks(gateway: TaskGateway, target_date_berlin: date) -> dict[str, Any]:
    read_bundle = gateway.get_canonical_open_tasks(READ_ORDER)
    tasks_by_list = {
        list_name: sorted(
            tasks,
            key=lambda item: (
                item.get("due") is None,
                item.get("due") or "",
                item.get("title") or "",
            ),
        )
        for list_name, tasks in read_bundle["tasks_by_list"].items()
    }

    return {
        "provider": read_bundle["provider"],
        "task_read_status": read_bundle["task_read_status"],
        "tasks_by_list": tasks_by_list,
        "failed_lists": read_bundle["failed_lists"],
        "open_task_count": read_bundle["open_task_count"],
        "snapshot_scope": f"evening_reset:{target_date_berlin.isoformat()}",
    }


def _evaluate_tomorrow(
    *,
    target_date_berlin: date,
    calendar_result: dict[str, Any],
    task_bundle: dict[str, Any],
) -> dict[str, Any]:
    weekday = target_date_berlin.strftime("%A").lower()
    is_hard_load_day = weekday in {"thursday", "friday", "saturday"}
    has_fixed_sport = calendar_result["has_fixed_sport"]
    missing_task_basis = task_bundle["task_read_status"] != "success"

    actionable_tasks = []
    for list_name in ACTIONABLE_LISTS:
        actionable_tasks.extend(task_bundle["tasks_by_list"].get(list_name, []))

    waiting_tasks = task_bundle["tasks_by_list"].get("Waiting", [])
    prep_items = _derive_prep_items(calendar_result["events"])

    reasons: list[str] = []
    if missing_task_basis:
        reasons.append("missing_task_basis")
    if is_hard_load_day and has_fixed_sport:
        reasons.append("hard_shift_plus_fixed_sport")
    if is_hard_load_day and len(actionable_tasks) > 1:
        reasons.append("too_many_heavy_blocks")
    if prep_items and (is_hard_load_day or has_fixed_sport):
        reasons.append("prep_risk")
    if not missing_task_basis and len(actionable_tasks) > 2 and not is_hard_load_day:
        reasons.append("poor_distribution")

    reasons = [reason for reason in reasons if reason in SUPPORTED_REASONS]

    if is_hard_load_day and has_fixed_sport:
        status = "red"
    elif missing_task_basis or is_hard_load_day or has_fixed_sport:
        status = "yellow"
    else:
        status = "green"

    top_count = 1 if (
        is_hard_load_day
        or has_fixed_sport
        or missing_task_basis
        or status == "red"
    ) else 3

    if missing_task_basis:
        priorities = []
    else:
        priorities = actionable_tasks[:top_count]

    recommendation_key, recommendation_text = _pick_recommendation(
        status=status,
        is_hard_load_day=is_hard_load_day,
        has_fixed_sport=has_fixed_sport,
        missing_task_basis=missing_task_basis,
        has_prep_items=bool(prep_items),
        actionable_count=len(actionable_tasks),
    )
    warning_text = _pick_warning(
        status=status,
        missing_task_basis=missing_task_basis,
        is_hard_load_day=is_hard_load_day,
        has_fixed_sport=has_fixed_sport,
    )

    assessment_text = _build_assessment(
        status=status,
        is_hard_load_day=is_hard_load_day,
        has_fixed_sport=has_fixed_sport,
        missing_task_basis=missing_task_basis,
        actionable_count=len(actionable_tasks),
        waiting_count=len(waiting_tasks),
    )

    return {
        "status": status,
        "reasons": reasons,
        "assessment": assessment_text,
        "recommendation_key": recommendation_key,
        "recommendation": recommendation_text,
        "warning": warning_text,
        "priorities": priorities,
        "prep_items": prep_items,
    }


def _pick_recommendation(
    *,
    status: str,
    is_hard_load_day: bool,
    has_fixed_sport: bool,
    missing_task_basis: bool,
    has_prep_items: bool,
    actionable_count: int,
) -> tuple[str, str]:
    if status == "red" and has_fixed_sport:
        return (
            "protect_recovery",
            "Halte morgen nur Pflicht plus Erholung offen und streiche jeden zweiten schweren Zusatzblock.",
        )
    if is_hard_load_day and actionable_count > 1:
        return (
            "cut_extra_block",
            "Reduziere morgen auf einen Schwerpunkt neben den festen Bloecken.",
        )
    if missing_task_basis:
        return (
            "pick_top1",
            "Arbeite morgen nur mit einem Top-Ziel und orientiere dich sonst an den harten Terminen.",
        )
    if is_hard_load_day or has_fixed_sport:
        return (
            "use_single_focus_block",
            "Wenn ueberhaupt, plane morgen nur einen 60-Minuten-Fokusblock mit 10 Minuten Spaziergang danach.",
        )
    if has_prep_items:
        return (
            "prepare_tonight",
            "Bereite heute Abend alles fuer morgen vor, damit morgen kein Reibungsverlust entsteht.",
        )
    return (
        "use_single_focus_block",
        "Plane morgen hoechstens einen klaren Fokusblock statt mehrerer halber Anlaeufe.",
    )


def _pick_warning(
    *,
    status: str,
    missing_task_basis: bool,
    is_hard_load_day: bool,
    has_fixed_sport: bool,
) -> str | None:
    if status == "red":
        return "Morgen ist ein harter Belastungstag mit fixem Sportblock. Kein weiterer schwerer Block."
    if missing_task_basis:
        return "Die Aufgabenbasis ist gerade nicht vollstaendig verifiziert."
    if is_hard_load_day and has_fixed_sport:
        return "Morgen wird schnell zu voll, wenn noch Zusatzlast dazukommt."
    return None


def _build_assessment(
    *,
    status: str,
    is_hard_load_day: bool,
    has_fixed_sport: bool,
    missing_task_basis: bool,
    actionable_count: int,
    waiting_count: int,
) -> str:
    parts = [f"Status: {status.upper()}."]
    if is_hard_load_day:
        parts.append("Morgen liegt auf einem konservativen Belastungsprofil.")
    if has_fixed_sport:
        parts.append("Ein fixer Sportblock zaehlt als harte Zusatzlast.")
    if missing_task_basis:
        parts.append("Die Aufgabenbasis ist nur teilweise oder gar nicht live bestaetigt.")
    elif actionable_count:
        parts.append(f"{actionable_count} offene handlungsnahe Tasks liegen vor.")
    if waiting_count:
        parts.append(f"{waiting_count} Waiting-Punkte bleiben Beobachtungsthema.")
    return " ".join(parts)


def _derive_prep_items(events: list[dict[str, Any]]) -> list[str]:
    workspace_root = Path(__file__).resolve().parents[2]
    routines_path = workspace_root / "data" / "routines.json"
    if not routines_path.exists():
        return []

    routines_payload = json.loads(routines_path.read_text(encoding="utf-8"))
    routines_by_id = {
        routine["id"]: routine["checklist"]
        for routine in routines_payload.get("routines", [])
        if routine.get("id") and routine.get("checklist")
    }

    selected_routine_ids: list[str] = []
    for event in events:
        title_lower = event["title"].lower()
        if "bjj" in title_lower:
            selected_routine_ids.append("routine-bjj")
        if "kickbox" in title_lower:
            selected_routine_ids.append("routine-kickboxen-calisthenics")
        if event.get("is_work_signal"):
            selected_routine_ids.append("routine-workday")

    deduped_items: list[str] = []
    seen = set()
    for routine_id in selected_routine_ids:
        for item in routines_by_id.get(routine_id, []):
            if item in seen:
                continue
            seen.add(item)
            deduped_items.append(item)
            if len(deduped_items) >= 5:
                return deduped_items
    return deduped_items


def _render_evening_reset(
    *,
    target_date_berlin: date,
    calendar_result: dict[str, Any],
    task_bundle: dict[str, Any],
    evaluation: dict[str, Any],
) -> str:
    lines = []

    lines.append("🌙 EOS-Check-in für morgen")
    lines.append("")
    lines.append("📌 Morgen steht fest")
    if calendar_result["source"] == "stub_file":
        lines.append(
            "- Kalenderbasis im Dry-Run aus `data/calendar.json`, nicht aus Live-Calendar-Read."
        )

    if calendar_result["hard_events"]:
        lines.append(f"- {calendar_shape_line(calendar_result['hard_events'], prefix='Morgenkalender')}")
        for label in compact_event_lines(calendar_result["hard_events"]):
            lines.append(f"- {label}")
    else:
        lines.append("- Keine harten Termine bestaetigt.")

    lines.append("")
    lines.append("🧩 Offene Punkte")
    waiting_tasks = task_bundle["tasks_by_list"].get("Waiting", [])
    if waiting_tasks:
        for task in waiting_tasks[:3]:
            lines.append(f"- {task['title']}")
    elif task_bundle["task_read_status"] != "success":
        lines.append("- Aufgabenbasis gerade nicht live verfuegbar.")
    else:
        lines.append("- Keine Waiting-Punkte.")

    lines.append("")
    lines.append("🎯 Morgenfokus")
    if evaluation["priorities"]:
        for task in evaluation["priorities"]:
            due_suffix = _format_task_due_suffix(task, target_date_berlin)
            lines.append(f"- {task['title']}{due_suffix}")
    elif task_bundle["task_read_status"] != "success":
        lines.append("- Aufgabenbasis fehlt gerade; morgen nur auf harte Termine und Vorbereitung stuetzen.")
    else:
        lines.append("- Noch kein klarer Task-Fokus fuer morgen vorhanden.")

    lines.append("")
    lines.append("✅ Hast du das schon vorbereitet?")
    prep_lines = [hydration_check_line(), *evaluation["prep_items"]]
    if prep_lines:
        for item in prep_lines[:6]:
            lines.append(f"- {item}")
    else:
        lines.append("- Keine zusaetzliche Vorbereitung noetig.")

    lines.append("")
    lines.append("🧠 Meine Einschätzung")
    lines.append(f"- {evaluation['assessment']}")

    lines.append("")
    lines.append("➡️ Empfehlung")
    lines.append(f"- {evaluation['recommendation']}")

    lines.append("")
    lines.append("⚠️ Warnung")
    if evaluation["warning"]:
        lines.append(f"- {evaluation['warning']}")
    else:
        lines.append("- Keine akute Warnung.")

    return "\n".join(lines).strip() + "\n"


def _format_event_line(event: dict[str, Any]) -> str:
    if event.get("start_display") and event.get("end_display"):
        return f"{event['start_display']}-{event['end_display']} {event['title']}"
    return event["title"]


def _format_task_due_suffix(task: dict[str, Any], target_date_berlin: date) -> str:
    raw_due = task.get("due")
    if not raw_due:
        return ""

    try:
        due_date = date.fromisoformat(str(raw_due)[:10])
    except ValueError:
        return f" (due {raw_due})"
    if due_date < target_date_berlin:
        return f" (ueberfaellig seit {due_date.isoformat()})"
    if due_date == target_date_berlin:
        return f" (due {due_date.isoformat()})"
    return f" (spaeter due {due_date.isoformat()})"


def _format_event_time(raw_value: Any) -> str:
    if isinstance(raw_value, dict):
        date_time = raw_value.get("dateTime")
        if date_time:
            parsed = datetime.fromisoformat(date_time.replace("Z", "+00:00"))
            return parsed.astimezone(BERLIN).strftime("%H:%M")
        if raw_value.get("date"):
            return "Ganztags"
    if isinstance(raw_value, str) and raw_value:
        try:
            parsed = datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
            return parsed.astimezone(BERLIN).strftime("%H:%M")
        except ValueError:
            return raw_value
    return ""


def _persist_task_snapshot(connection: sqlite3.Connection, task_bundle: dict[str, Any]) -> int:
    cursor = connection.execute(
        """
        INSERT INTO task_snapshots (
            snapshot_scope,
            business_date_berlin,
            captured_at_utc,
            provider,
            provider_status,
            is_partial,
            failed_lists_json,
            tasks_by_list_json,
            open_task_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_bundle["snapshot_scope"],
            task_bundle["snapshot_scope"].split(":", 1)[1],
            _utc_now_iso(),
            task_bundle["provider"],
            task_bundle["task_read_status"],
            1 if task_bundle["task_read_status"] != "success" else 0,
            json.dumps(task_bundle["failed_lists"], ensure_ascii=True),
            json.dumps(task_bundle["tasks_by_list"], ensure_ascii=True),
            task_bundle["open_task_count"],
        ),
    )
    connection.commit()
    return int(cursor.lastrowid)


def _persist_daily_evaluation(
    *,
    connection: sqlite3.Connection,
    target_date_berlin: str,
    evaluation: dict[str, Any],
    task_snapshot_id: int,
    created_at_utc: str,
) -> None:
    connection.execute(
        """
        INSERT INTO daily_evaluations (
            business_date_berlin,
            evaluation_source,
            traffic_light_status,
            reasons_json,
            assessment_text,
            recommendation_text,
            warning_text,
            task_snapshot_id,
            created_at_utc
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(business_date_berlin, evaluation_source)
        DO UPDATE SET
            traffic_light_status = excluded.traffic_light_status,
            reasons_json = excluded.reasons_json,
            assessment_text = excluded.assessment_text,
            recommendation_text = excluded.recommendation_text,
            warning_text = excluded.warning_text,
            task_snapshot_id = excluded.task_snapshot_id,
            created_at_utc = excluded.created_at_utc
        """,
        (
            target_date_berlin,
            "evening_reset",
            evaluation["status"],
            json.dumps(evaluation["reasons"], ensure_ascii=True),
            evaluation["assessment"],
            evaluation["recommendation"],
            evaluation["warning"],
            task_snapshot_id,
            created_at_utc,
        ),
    )
    connection.commit()


def _fetch_job_run(
    connection: sqlite3.Connection,
    job: str,
    idempotency_key: str,
) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT *
        FROM job_runs
        WHERE job = ? AND idempotency_key = ?
        """,
        (job, idempotency_key),
    ).fetchone()


def mark_evening_reset_delivery(
    *,
    idempotency_key: str,
    sent: bool,
    delivery_status: str,
    error: str | None = None,
    db_path: str | None = None,
) -> bool:
    connection = init_db(db_path)
    timestamp_utc = _utc_now_iso()
    row = _fetch_job_run(connection, "evening_reset", idempotency_key)
    if row is None:
        connection.close()
        return False

    connection.execute(
        """
        UPDATE job_runs
        SET
            run_status = ?,
            delivery_status = ?,
            last_error = ?,
            updated_at_utc = ?
        WHERE job = ? AND idempotency_key = ?
        """,
        (
            "sent" if sent else row["run_status"],
            delivery_status,
            None if sent else error,
            timestamp_utc,
            "evening_reset",
            idempotency_key,
        ),
    )
    connection.commit()
    connection.close()
    return True


def _persist_job_run(
    *,
    connection: sqlite3.Connection,
    existing_job_run: sqlite3.Row | None,
    run_id: str,
    idempotency_key: str,
    target_window_start: datetime,
    target_window_end: datetime,
    target_business_date: str,
    run_status: str,
    calendar_read_status: str,
    task_read_status: str,
    delivery_status: str,
    message_digest: str | None,
    last_error: str | None,
    created_at_utc: str,
    updated_at_utc: str,
    allow_overwrite_blocking: bool,
) -> bool:
    if existing_job_run and existing_job_run["run_status"] in {"generated", "sent"}:
        if run_status == "dry_run" and not allow_overwrite_blocking:
            return False
        if not allow_overwrite_blocking:
            return False

    if existing_job_run:
        connection.execute(
            """
            UPDATE job_runs
            SET
                run_id = ?,
                target_window_start_berlin = ?,
                target_window_end_berlin = ?,
                target_business_date_berlin = ?,
                run_status = ?,
                calendar_read_status = ?,
                task_read_status = ?,
                delivery_status = ?,
                message_digest = ?,
                last_error = ?,
                updated_at_utc = ?
            WHERE job = ? AND idempotency_key = ?
            """,
            (
                run_id,
                target_window_start.isoformat(),
                target_window_end.isoformat(),
                target_business_date,
                run_status,
                calendar_read_status,
                task_read_status,
                delivery_status,
                message_digest,
                last_error,
                updated_at_utc,
                "evening_reset",
                idempotency_key,
            ),
        )
    else:
        connection.execute(
            """
            INSERT INTO job_runs (
                job,
                run_id,
                idempotency_key,
                target_window_start_berlin,
                target_window_end_berlin,
                target_business_date_berlin,
                run_status,
                calendar_read_status,
                task_read_status,
                delivery_status,
                message_digest,
                last_error,
                created_at_utc,
                updated_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "evening_reset",
                run_id,
                idempotency_key,
                target_window_start.isoformat(),
                target_window_end.isoformat(),
                target_business_date,
                run_status,
                calendar_read_status,
                task_read_status,
                delivery_status,
                message_digest,
                last_error,
                created_at_utc,
                updated_at_utc,
            ),
        )
    connection.commit()
    return True


def _ensure_template_contract(template_path: Path) -> None:
    if not template_path.exists():
        raise FileNotFoundError(f"Evening reset template missing: {template_path}")

    content = template_path.read_text(encoding="utf-8")
    required_sections = (
        "### Morgen steht fest",
        "### Offene Punkte",
        "### Morgenfokus",
        "### Vorbereitung heute",
        "### Meine Einschaetzung",
        "### Meine Empfehlung",
        "### Warnung",
    )
    missing_sections = [section for section in required_sections if section not in content]
    if missing_sections:
        raise ValueError(
            "Evening reset template is missing required sections: "
            + ", ".join(missing_sections)
        )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
