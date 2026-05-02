#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = WORKSPACE_ROOT / "data" / "eos_state.json"
SCHEMA_PATH = WORKSPACE_ROOT / "data" / "eos_state.schema.json"

PRIORITY_RANK = {
    "P1": 30,
    "P2": 20,
    "P3": 10,
    "untriaged": 0,
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_json_schema(state: dict[str, Any], schema: dict[str, Any]) -> None:
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(state), key=lambda error: list(error.path))
    if errors:
        rendered = "\n".join(f"{list(error.path)}: {error.message}" for error in errors)
        raise AssertionError(f"eos_state.json failed schema validation:\n{rendered}")


def default_untriaged_annotation() -> dict[str, Any]:
    return {
        "priority": "untriaged",
        "energy_required": "unknown",
        "estimated_minutes": None,
        "priority_source": "missing",
        "last_reviewed_at": None,
        "triage_status": "needs_triage",
    }


def normalize_annotation(task_id: str, annotations: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return annotations.get(task_id) or default_untriaged_annotation()


def task_score(
    task: dict[str, Any],
    annotations: dict[str, dict[str, Any]],
    current_energy: str,
) -> int:
    annotation = normalize_annotation(task["id"], annotations)
    score = PRIORITY_RANK[annotation["priority"]]
    if annotation["energy_required"] == current_energy:
        score += 5
    return score


def select_habit_version(habit: dict[str, Any], has_calendar_conflict: bool) -> list[str]:
    if not has_calendar_conflict:
        return habit["full_version"]
    if habit["collision_policy"]["on_calendar_conflict"] == "preserve_minimum_version":
        return habit["minimum_version"]
    raise AssertionError(f"Unsupported habit collision policy: {habit['id']}")


def review_pending(last_weekly_review_date: str | None, today: date) -> bool:
    if last_weekly_review_date is None:
        return True
    return date.fromisoformat(last_weekly_review_date) <= today - timedelta(days=7)


def assert_smoke_contract(state: dict[str, Any]) -> None:
    assert state["schema_version"] == 1
    assert state["timezone"] == "Europe/Berlin"
    assert state["planning_policy"]["buffer_ratio"] == 0.2
    assert state["planning_policy"]["wake_window"] == {"start": "06:00", "end": "22:00"}
    assert {habit["id"] for habit in state["habits"]} == set(state["habit_log"])

    valid_priorities = set(PRIORITY_RANK)
    valid_energy = {"high", "medium", "low", "unknown"}
    for task_id, annotation in state["task_annotations"].items():
        assert annotation["priority"] in valid_priorities, task_id
        assert annotation["energy_required"] in valid_energy, task_id
        if annotation["priority"] == "untriaged":
            assert annotation["priority_source"] == "missing", task_id
            assert annotation["triage_status"] == "needs_triage", task_id


def assert_prioritization_fixture() -> None:
    tasks = [
        {"id": "fixture-missing-deadline", "due": "2026-04-24"},
        {"id": "fixture-p2-admin", "due": None},
        {"id": "fixture-p1-focus", "due": None},
    ]
    annotations = {
        "fixture-p1-focus": {
            "priority": "P1",
            "energy_required": "high",
            "estimated_minutes": 90,
            "priority_source": "explicit",
            "last_reviewed_at": "2026-04-24T00:00:00Z",
            "triage_status": "ready",
        },
        "fixture-p2-admin": {
            "priority": "P2",
            "energy_required": "low",
            "estimated_minutes": 20,
            "priority_source": "explicit",
            "last_reviewed_at": "2026-04-24T00:00:00Z",
            "triage_status": "ready",
        },
    }

    ordered = sorted(
        tasks,
        key=lambda task: task_score(task, annotations, current_energy="high"),
        reverse=True,
    )

    assert [task["id"] for task in ordered] == [
        "fixture-p1-focus",
        "fixture-p2-admin",
        "fixture-missing-deadline",
    ]
    missing = normalize_annotation("fixture-missing-deadline", annotations)
    assert missing["priority"] == "untriaged"
    assert missing["priority_source"] == "missing"


def assert_habit_collision_fixture(state: dict[str, Any]) -> None:
    morning = next(habit for habit in state["habits"] if habit["id"] == "habit-morning-routine")
    assert select_habit_version(morning, has_calendar_conflict=False) == morning["full_version"]
    assert select_habit_version(morning, has_calendar_conflict=True) == morning["minimum_version"]
    assert morning["minimum_version"] != morning["full_version"]


def assert_review_fixture(state: dict[str, Any]) -> None:
    today = date(2026, 4, 24)
    assert review_pending(state["review_state"]["last_weekly_review_date"], today) is True
    assert review_pending("2026-04-17", today) is True
    assert review_pending("2026-04-20", today) is False


def main() -> int:
    state = load_json(STATE_PATH)
    schema = load_json(SCHEMA_PATH)

    validate_json_schema(state, schema)
    assert_smoke_contract(state)
    assert_prioritization_fixture()
    assert_habit_collision_fixture(state)
    assert_review_fixture(state)

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
