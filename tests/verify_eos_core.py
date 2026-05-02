#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.eos_core import (  # noqa: E402
    check_day_capacity,
    load_state,
    normalize_task_annotation,
    rank_tasks,
    select_habit_version,
    should_trigger_review,
    validate_state,
)


def explicit_annotation(priority: str, energy: str, minutes: int) -> dict[str, object]:
    return {
        "priority": priority,
        "energy_required": energy,
        "estimated_minutes": minutes,
        "priority_source": "explicit",
        "last_reviewed_at": "2026-04-24T00:00:00Z",
        "triage_status": "ready",
    }


def main() -> int:
    state = load_state()
    validate_state(state)

    missing = normalize_task_annotation("missing-task-id", state["task_annotations"])
    assert missing["priority"] == "untriaged"
    assert missing["triage_status"] == "needs_triage"

    annotations = {
        "p1": explicit_annotation("P1", "high", 90),
        "p3": explicit_annotation("P3", "low", 20),
    }
    ranked = rank_tasks(
        [
            {"id": "missing", "title": "Due today but untriaged", "due": "2026-04-24", "list_name": "Next"},
            {"id": "p3", "title": "Explicit P3", "due": None, "list_name": "Inbox"},
            {"id": "p1", "title": "Explicit P1", "due": None, "list_name": "This Week"},
        ],
        current_energy="high",
        annotations=annotations,
    )
    assert [task["id"] for task in ranked] == ["p1", "p3", "missing"]
    assert ranked[-1]["eos_annotation"]["priority"] == "untriaged"

    state_for_capacity = load_state()
    state_for_capacity["task_annotations"]["heavy"] = explicit_annotation("P1", "high", 300)
    capacity = check_day_capacity(
        [{"id": "long-block", "start": "06:00", "end": "20:00"}],
        [{"id": "heavy", "status": "needsAction"}],
        state_for_capacity,
    )
    assert capacity["overloaded"] is True
    assert capacity["buffer_min"] == 192

    habit = next(item for item in state["habits"] if item["id"] == "habit-morning-routine")
    full = select_habit_version(habit, has_calendar_conflict=False)
    minimum = select_habit_version(habit, has_calendar_conflict=True)
    assert full["version"] == "full"
    assert minimum["version"] == "minimum"
    assert minimum["items"] == habit["minimum_version"]

    assert should_trigger_review(None, date(2026, 4, 24)) is True
    assert should_trigger_review("2026-04-17", date(2026, 4, 24)) is True
    assert should_trigger_review("2026-04-20", date(2026, 4, 24)) is False

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
