from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from src.eos_core import (
    check_day_capacity,
    load_state,
    rank_tasks,
    select_habit_version,
    should_trigger_review,
    validate_state,
)
from src.gateways.google_tasks import CANONICAL_LISTS, TaskGateway
from src.habits import HabitService

BERLIN = ZoneInfo("Europe/Berlin")
ACTIONABLE_LISTS = ("Next", "This Week", "Inbox")


def run_daily_capacity(
    target_date: date | None = None,
    *,
    dry_run: bool = True,
    allow_stub_calendar: bool = False,
    allow_stub_tasks: bool = False,
    prefer_live_calendar: bool = True,
    prefer_live_tasks: bool = True,
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(workspace_root) if workspace_root is not None else Path(__file__).resolve().parents[2]
    target_date_berlin = target_date or datetime.now(BERLIN).date()

    state = load_state(root / "data" / "eos_state.json")
    validate_state(state, root / "data" / "eos_state.schema.json")

    calendar_result = _load_calendar_blocks(
        root,
        target_date_berlin,
        allow_stub_calendar=allow_stub_calendar,
        prefer_live_calendar=prefer_live_calendar,
    )
    task_result = _load_tasks(
        root,
        allow_stub_tasks=allow_stub_tasks,
        prefer_live_tasks=prefer_live_tasks,
    )

    open_tasks = _flatten_open_tasks(task_result["tasks_by_list"])
    capacity = check_day_capacity(calendar_result["calendar_blocks"], open_tasks, state)
    ranked_tasks = rank_tasks(open_tasks, _energy_for_date(state, target_date_berlin), state["task_annotations"])
    ready_ranked_tasks = [
        task
        for task in ranked_tasks
        if task["eos_annotation"]["priority"] != "untriaged"
        and task["eos_annotation"]["triage_status"] == "ready"
    ]
    top_tasks = ready_ranked_tasks[:3] if len(ready_ranked_tasks) >= 3 else []

    habit_versions = [
        select_habit_version(habit, _habit_has_calendar_conflict(habit, calendar_result["calendar_blocks"]))
        for habit in state["habits"]
        if habit.get("status") == "active"
    ]
    habit_service = HabitService(workspace_root=root)
    try:
        habit_status = habit_service.today(target_date_berlin)
    finally:
        habit_service.close()

    status = _capacity_status(capacity, calendar_result, task_result, top_tasks)
    recommendation = _recommendation(status, capacity, top_tasks, task_result)

    return {
        "status": status,
        "job": "daily_capacity",
        "dry_run": dry_run,
        "target_date_berlin": target_date_berlin.isoformat(),
        "calendar_source": calendar_result["source"],
        "calendar_read_status": calendar_result["calendar_read_status"],
        "task_source": task_result["source"],
        "task_read_status": task_result["task_read_status"],
        "capacity": capacity,
        "top_tasks": _public_tasks(top_tasks),
        "ranked_tasks": _public_tasks(ranked_tasks),
        "triage_required": bool(capacity["untriaged_task_ids"] or capacity["missing_estimate_task_ids"]),
        "untriaged_tasks": _tasks_by_ids(open_tasks, capacity["untriaged_task_ids"]),
        "missing_estimate_tasks": _tasks_by_ids(open_tasks, capacity["missing_estimate_task_ids"]),
        "habit_versions": habit_versions,
        "habit_status": habit_status,
        "review_pending": should_trigger_review(
            state["review_state"]["last_weekly_review_date"],
            target_date_berlin,
        ),
        "recommendation": recommendation,
    }


def _load_calendar_blocks(
    workspace_root: Path,
    target_date_berlin: date,
    *,
    allow_stub_calendar: bool,
    prefer_live_calendar: bool,
) -> dict[str, Any]:
    if prefer_live_calendar:
        live_result = _load_live_calendar_blocks(workspace_root, target_date_berlin)
        if live_result["calendar_read_status"] == "success":
            return live_result
        if not allow_stub_calendar:
            return live_result

    if allow_stub_calendar:
        # Stub calendar data is only for explicit tests and dry verification.
        return _load_stub_calendar_blocks(workspace_root, target_date_berlin)

    return {
        "source": "unavailable",
        "calendar_read_status": "not_attempted",
        "calendar_blocks": [],
        "error": "No calendar source was allowed.",
    }


def _load_live_calendar_blocks(workspace_root: Path, target_date_berlin: date) -> dict[str, Any]:
    from src.jobs.evening_reset import _load_calendar_events

    gateway = TaskGateway()
    result = _load_calendar_events(
        gateway=gateway,
        workspace_root=workspace_root,
        target_date_berlin=target_date_berlin,
        dry_run=False,
        allow_stub_calendar=False,
    )
    return {
        "source": result["source"],
        "calendar_read_status": result["calendar_read_status"],
        "calendar_blocks": [_event_to_block(event) for event in result.get("hard_events", [])],
        "error": result.get("error"),
    }


def _load_stub_calendar_blocks(workspace_root: Path, target_date_berlin: date) -> dict[str, Any]:
    path = workspace_root / "data" / "calendar.json"
    payload = _load_json(path)
    weekday = target_date_berlin.strftime("%A").lower()

    blocks = []
    for event in payload.get("events", []):
        if event.get("weekday", "").lower() != weekday:
            continue
        is_work = event.get("type") == "work_block"
        is_hard = bool(event.get("fixed")) or is_work
        if not is_hard:
            continue
        blocks.append(
            {
                "id": event.get("id"),
                "title": event.get("title") or "(ohne Titel)",
                "type": event.get("type"),
                "start": event.get("start"),
                "end": event.get("end"),
                "duration_min": _minutes_between(event.get("start"), event.get("end")),
                "source": "stub_file",
            }
        )

    return {
        "source": "stub_file",
        "calendar_read_status": "stub_fallback",
        "calendar_blocks": blocks,
        "error": None,
    }


def _load_tasks(
    workspace_root: Path,
    *,
    allow_stub_tasks: bool,
    prefer_live_tasks: bool,
) -> dict[str, Any]:
    if prefer_live_tasks:
        live_result = _load_live_tasks()
        if live_result["task_read_status"] == "success":
            return live_result
        if not allow_stub_tasks:
            return live_result

    if allow_stub_tasks:
        # Stub task data is only for explicit tests and dry verification.
        return _load_stub_tasks(workspace_root)

    return _load_live_tasks()


def _load_live_tasks() -> dict[str, Any]:
    gateway = TaskGateway()
    result = gateway.get_canonical_open_tasks(CANONICAL_LISTS)

    return {
        "source": "live_gog",
        "task_read_status": result["task_read_status"],
        "tasks_by_list": result["tasks_by_list"],
        "failed_lists": result["failed_lists"],
    }


def _load_stub_tasks(workspace_root: Path) -> dict[str, Any]:
    payload = _load_json(workspace_root / "data" / "tasks.json")
    tasks_by_list: dict[str, list[dict[str, Any]]] = {}
    for task_list in payload.get("lists", []):
        list_name = task_list.get("title") or ""
        tasks_by_list[list_name] = [
            {**task, "list_name": list_name}
            for task in task_list.get("tasks", [])
            if task.get("status") not in {"completed", "done"}
        ]

    return {
        "source": payload.get("provider") or "stub_file",
        "task_read_status": "stub_fallback",
        "tasks_by_list": tasks_by_list,
        "failed_lists": [],
    }


def _flatten_open_tasks(tasks_by_list: Mapping[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    tasks = []
    for list_name in ACTIONABLE_LISTS:
        tasks.extend(tasks_by_list.get(list_name, []))
    return tasks


def _public_tasks(tasks: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    public = []
    for task in tasks:
        annotation = task.get("eos_annotation", {})
        public.append(
            {
                "id": task.get("id"),
                "title": task.get("title"),
                "list_name": task.get("list_name"),
                "due": task.get("due"),
                "priority": annotation.get("priority"),
                "energy_required": annotation.get("energy_required"),
                "estimated_minutes": annotation.get("estimated_minutes"),
                "triage_status": annotation.get("triage_status"),
                "score": task.get("eos_score"),
            }
        )
    return public


def _tasks_by_ids(tasks: list[Mapping[str, Any]], task_ids: list[str]) -> list[dict[str, Any]]:
    wanted = set(task_ids)
    return [
        {
            "id": task.get("id"),
            "title": task.get("title"),
            "list_name": task.get("list_name"),
            "due": task.get("due"),
        }
        for task in tasks
        if task.get("id") in wanted
    ]


def _habit_has_calendar_conflict(habit: Mapping[str, Any], blocks: list[Mapping[str, Any]]) -> bool:
    target_time = habit.get("target_time")
    if not isinstance(target_time, str):
        return False
    target_min = _time_to_minutes(target_time)
    for block in blocks:
        start = block.get("start")
        end = block.get("end")
        if not isinstance(start, str) or not isinstance(end, str):
            continue
        start_min = _time_to_minutes(start)
        end_min = _time_to_minutes(end)
        if start_min <= target_min < end_min:
            return True
    return False


def _capacity_status(
    capacity: Mapping[str, Any],
    calendar_result: Mapping[str, Any],
    task_result: Mapping[str, Any],
    top_tasks: list[Mapping[str, Any]],
) -> str:
    if capacity["overloaded"]:
        return "red"
    if (
        capacity["untriaged_task_ids"]
        or capacity["missing_estimate_task_ids"]
        or calendar_result["calendar_read_status"] != "success"
        or task_result["task_read_status"] != "success"
        or not top_tasks
    ):
        return "yellow"
    return "green"


def _recommendation(
    status: str,
    capacity: Mapping[str, Any],
    top_tasks: list[Mapping[str, Any]],
    task_result: Mapping[str, Any],
) -> str:
    if status == "red":
        return "KUERZEN: remove or resize work until known task load fits the protected buffer."
    if capacity["untriaged_task_ids"] or capacity["missing_estimate_task_ids"]:
        return "TRIAGE FIRST: assign P1/P2/P3, energy, and estimates before making a Top-3 plan."
    if task_result["task_read_status"] != "success":
        return "TASK BASIS WEAK: use calendar structure and one conservative focus until tasks are verified."
    if not top_tasks:
        return "NO TOP-3 YET: keep calendar stable and pick one explicit focus manually."
    return "OK: capacity fits; keep the 20 percent buffer protected."


def _energy_for_date(state: Mapping[str, Any], target_date_berlin: date) -> str:
    del target_date_berlin
    for window in state["energy_profile"]["default_daily_windows"]:
        if window.get("label") == "deep_work_peak":
            return str(window["energy"])
    return "medium"


def _event_to_block(event: Mapping[str, Any]) -> dict[str, Any]:
    start = event.get("start_display")
    end = event.get("end_display")
    return {
        "id": event.get("id") or event.get("title"),
        "title": event.get("title") or "(ohne Titel)",
        "type": "calendar_event",
        "start": start,
        "end": end,
        "duration_min": _safe_minutes_between(start, end),
        "source": event.get("source_note") or "live_gog",
    }


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _safe_minutes_between(start: Any, end: Any) -> int | None:
    if not isinstance(start, str) or not isinstance(end, str):
        return None
    try:
        return _minutes_between(start, end)
    except (TypeError, ValueError):
        return None


def _minutes_between(start: Any, end: Any) -> int:
    return _time_to_minutes(str(end)) - _time_to_minutes(str(start))


def _time_to_minutes(value: str) -> int:
    hour, minute = value.split(":", 1)
    return int(hour) * 60 + int(minute)


if __name__ == "__main__":
    result = run_daily_capacity()
    print(json.dumps(result, indent=2, ensure_ascii=True))
