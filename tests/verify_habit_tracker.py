#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from pathlib import Path
import sys
import tempfile

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.habits import HabitService  # noqa: E402


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "habits.db")
        service = HabitService(workspace_root=WORKSPACE_ROOT, db_path=db_path)
        try:
            health = service.health()
            assert health["status"] == "success"
            assert health["active_count"] == 3

            first = service.mark_done("morgenroutine", target_date=date(2026, 4, 27), mode="full")
            second = service.mark_done("morgenroutine", target_date=date(2026, 4, 28), mode="full")
            partial = service.mark_done("morgenroutine", target_date=date(2026, 4, 29), mode="partial")
            skipped = service.skip_habit("abendroutine", target_date=date(2026, 4, 28), notes="bewusst ausgelassen")

            assert first["current_streak"] == 1
            assert second["current_streak"] == 2
            assert partial["final_status"] == "done_partial"
            assert partial["current_streak"] == 2
            assert skipped["final_status"] == "skipped"

            added = service.add_habit(name="Morgen Yoga", target_time="06:30")
            assert added["status"] == "success"
            ambiguous = service.resolve_habit("morgen")
            assert ambiguous["status"] == "ambiguous"

            pause = service.pause_habit("Morgen Yoga")
            assert pause["status"] == "success"
            assert pause["habit"]["status"] == "paused"

            text = service.handle_text("klimmzug skip heute, zu muede", target_date=date(2026, 4, 28))
            assert text["status"] == "success"
            assert text["final_status"] == "skipped"

            report = service.weekly_report(date(2026, 4, 27))
            morning = next(habit for habit in report["habits"] if habit["id"] == "habit-morning-routine")
            assert morning["full_count"] == 2
            assert morning["partial_count"] == 1
            assert morning["current_streak"] == 2
        finally:
            service.close()

    print("verify_habit_tracker: ok")


if __name__ == "__main__":
    main()
