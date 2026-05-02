from __future__ import annotations

import copy
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_PATH = WORKSPACE_ROOT / "data" / "eos_state.json"
DEFAULT_SCHEMA_PATH = WORKSPACE_ROOT / "data" / "eos_state.schema.json"

PRIORITY_SCORE = {
    "P1": 3000,
    "P2": 2000,
    "P3": 1000,
    "untriaged": 0,
}

LIST_SCORE = {
    "Next": 30,
    "This Week": 20,
    "Inbox": 10,
    "Waiting": 0,
}

DEFAULT_UNTRIAGED_ANNOTATION: dict[str, Any] = {
    "priority": "untriaged",
    "energy_required": "unknown",
    "estimated_minutes": None,
    "priority_source": "missing",
    "last_reviewed_at": None,
    "triage_status": "needs_triage",
}


def load_state(state_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(state_path) if state_path is not None else DEFAULT_STATE_PATH
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_state(
    state: Mapping[str, Any],
    schema_path: str | Path | None = None,
) -> None:
    path = Path(schema_path) if schema_path is not None else DEFAULT_SCHEMA_PATH
    with path.open(encoding="utf-8") as handle:
        schema = json.load(handle)

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(state), key=lambda error: list(error.path))
    if errors:
        rendered = "\n".join(f"{list(error.path)}: {error.message}" for error in errors)
        raise ValueError(f"Invalid EOS state:\n{rendered}")


def normalize_task_annotation(
    task_id: str,
    annotations: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if annotations is None:
        annotations = load_state().get("task_annotations", {})

    annotation = annotations.get(task_id)
    if not annotation:
        return copy.deepcopy(DEFAULT_UNTRIAGED_ANNOTATION)

    normalized = copy.deepcopy(DEFAULT_UNTRIAGED_ANNOTATION)
    normalized.update(dict(annotation))
    return normalized


def rank_tasks(
    tasks: list[Mapping[str, Any]],
    current_energy: str,
    annotations: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    ranked_tasks = []
    for index, task in enumerate(tasks):
        task_copy = dict(task)
        task_id = str(task_copy.get("id") or "")
        annotation = normalize_task_annotation(task_id, annotations)
        score = _task_score(task_copy, annotation, current_energy)
        task_copy["eos_annotation"] = annotation
        task_copy["eos_score"] = score
        task_copy["_eos_original_index"] = index
        ranked_tasks.append(task_copy)

    ranked_tasks.sort(
        key=lambda task: (
            task["eos_score"],
            _due_sort_key(task.get("due")),
            -task["_eos_original_index"],
        ),
        reverse=True,
    )
    for task in ranked_tasks:
        task.pop("_eos_original_index", None)
    return ranked_tasks


def check_day_capacity(
    calendar_blocks: list[Mapping[str, Any]],
    tasks: list[Mapping[str, Any]],
    state: Mapping[str, Any],
) -> dict[str, Any]:
    planning_policy = state["planning_policy"]
    wake_window = planning_policy["wake_window"]
    wake_total_min = _minutes_between(wake_window["start"], wake_window["end"])
    buffer_min = int(wake_total_min * planning_policy["buffer_ratio"])

    blocked_min = 0
    unmeasured_blocks: list[str] = []
    for block in calendar_blocks:
        duration = _block_duration_min(block)
        if duration is None:
            unmeasured_blocks.append(str(block.get("id") or block.get("title") or "unknown"))
            continue
        blocked_min += duration

    annotations = state.get("task_annotations", {})
    task_load_min = 0
    missing_estimate_task_ids: list[str] = []
    untriaged_task_ids: list[str] = []

    for task in tasks:
        if _is_completed_task(task):
            continue
        task_id = str(task.get("id") or "")
        annotation = normalize_task_annotation(task_id, annotations)
        if annotation["priority"] == "untriaged" or annotation["triage_status"] != "ready":
            untriaged_task_ids.append(task_id)

        estimate = annotation.get("estimated_minutes")
        if estimate is None and isinstance(task.get("estimated_minutes"), int):
            estimate = task["estimated_minutes"]

        if isinstance(estimate, int) and estimate > 0:
            task_load_min += estimate
        else:
            missing_estimate_task_ids.append(task_id)

    available_min = max(0, wake_total_min - blocked_min - buffer_min)
    surplus_min = available_min - task_load_min

    return {
        "wake_total_min": wake_total_min,
        "blocked_min": blocked_min,
        "buffer_min": buffer_min,
        "available_min": available_min,
        "task_load_min": task_load_min,
        "surplus_min": surplus_min,
        "overloaded": task_load_min > available_min,
        "unmeasured_calendar_block_ids": unmeasured_blocks,
        "missing_estimate_task_ids": missing_estimate_task_ids,
        "untriaged_task_ids": untriaged_task_ids,
    }


def select_habit_version(
    habit: Mapping[str, Any],
    has_calendar_conflict: bool,
) -> dict[str, Any]:
    if has_calendar_conflict:
        policy = habit["collision_policy"]["on_calendar_conflict"]
        if policy == "preserve_minimum_version":
            return {
                "habit_id": habit["id"],
                "name": habit["name"],
                "version": "minimum",
                "items": list(habit["minimum_version"]),
                "reason": "calendar_conflict",
            }

    return {
        "habit_id": habit["id"],
        "name": habit["name"],
        "version": "full",
        "items": list(habit["full_version"]),
        "reason": None,
    }


def should_trigger_review(
    last_review_date: str | date | None,
    today: date | None = None,
) -> bool:
    if last_review_date is None:
        return True

    today_value = today or date.today()
    if isinstance(last_review_date, date):
        last_value = last_review_date
    else:
        last_value = date.fromisoformat(last_review_date)

    return (today_value - last_value).days >= 7


def _task_score(
    task: Mapping[str, Any],
    annotation: Mapping[str, Any],
    current_energy: str,
) -> int:
    priority = str(annotation.get("priority") or "untriaged")
    score = PRIORITY_SCORE.get(priority, 0)

    if annotation.get("energy_required") == current_energy:
        score += 50

    score += _deadline_bonus(task.get("due"))
    score += LIST_SCORE.get(str(task.get("list_name") or ""), 0)
    return score


def _deadline_bonus(raw_due: Any) -> int:
    due_date = _parse_due_date(raw_due)
    if due_date is None:
        return 0

    today = date.today()
    days_until_due = (due_date - today).days
    if days_until_due < 0:
        return 90
    if days_until_due == 0:
        return 80
    if days_until_due <= 2:
        return 50
    if days_until_due <= 7:
        return 25
    return 5


def _due_sort_key(raw_due: Any) -> int:
    due_date = _parse_due_date(raw_due)
    if due_date is None:
        return -999999
    return -due_date.toordinal()


def _parse_due_date(raw_due: Any) -> date | None:
    if not isinstance(raw_due, str) or not raw_due:
        return None
    try:
        return datetime.fromisoformat(raw_due.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(raw_due[:10])
        except ValueError:
            return None


def _is_completed_task(task: Mapping[str, Any]) -> bool:
    status = str(task.get("status") or "").lower()
    return status in {"completed", "done"} or bool(task.get("completed"))


def _block_duration_min(block: Mapping[str, Any]) -> int | None:
    duration = block.get("duration_min")
    if isinstance(duration, int) and duration >= 0:
        return duration

    start = block.get("start") or block.get("start_display")
    end = block.get("end") or block.get("end_display")
    if isinstance(start, str) and isinstance(end, str):
        try:
            return _minutes_between(start, end)
        except ValueError:
            return None
    return None


def _minutes_between(start: str, end: str) -> int:
    start_min = _time_to_minutes(start)
    end_min = _time_to_minutes(end)
    if end_min < start_min:
        end_min += 24 * 60
    return max(0, end_min - start_min)


def _time_to_minutes(value: str) -> int:
    if value == "Ganztags":
        raise ValueError("all-day blocks do not have a precise duration")
    parts = value.split(":")
    if len(parts) != 2:
        raise ValueError(f"invalid time value: {value}")
    hour = int(parts[0])
    minute = int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"invalid time value: {value}")
    return hour * 60 + minute
