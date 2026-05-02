#!/usr/bin/env python3
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys
import tempfile

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.habits import (  # noqa: E402
    DEFAULT_HABIT_TYPE,
    HABIT_TYPES,
    PATTERN_KEYS,
    HabitService,
    classify_trigger,
    coerce_habit_type,
    coerce_severity,
    detect_patterns,
    normalize_replacement,
)
from src.habits.patterns import (  # noqa: E402
    PATTERN_RECOVERY_STREAK_SAVE,
    PATTERN_REPLACEMENT_WORKS,
    PATTERN_TIME_MISALIGNMENT,
    PATTERN_TRIGGER_CLUSTER,
    PATTERN_WEEKDAY_DROP,
)


def assert_eq(actual, expected, label):
    assert actual == expected, f"{label}: expected {expected!r}, got {actual!r}"


def test_default_habit_type_migration():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "habits.db")
        service = HabitService(workspace_root=WORKSPACE_ROOT, db_path=db_path)
        try:
            for habit in service.list_definitions(include_paused=True):
                assert habit["habit_type"] == "build", (
                    f"existing habit {habit['id']} should default to 'build', got {habit['habit_type']}"
                )
                assert habit["failure_modes"] is None
                assert habit["replacement_actions"] is None
                assert habit["recovery_rule"] is None
                assert habit["trigger_window"] is None
        finally:
            service.close()


def test_add_reduce_habit_with_metadata():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "habits.db")
        service = HabitService(workspace_root=WORKSPACE_ROOT, db_path=db_path)
        try:
            result = service.add_habit(
                name="Doomscrolling Night",
                target_time="22:00",
                habit_type="reduce",
                failure_modes=["muede", "stress", "langeweile"],
                replacement_actions=["zaehneputzen", "5_minuten_dehnen"],
                trigger_window={"start": "21:30", "end": "23:30"},
                recovery_rule={"fallback": "two_minute_reset"},
            )
            assert_eq(result["status"], "success", "reduce habit add status")
            habit = result["habit"]
            assert_eq(habit["habit_type"], "reduce", "habit_type")
            assert_eq(habit["failure_modes"], ["muede", "stress", "langeweile"], "failure modes")
            assert_eq(habit["replacement_actions"], ["zaehneputzen", "5_minuten_dehnen"], "replacements")
            assert habit["trigger_window"] == {"start": "21:30", "end": "23:30"}
            assert habit["recovery_rule"] == {"fallback": "two_minute_reset"}
        finally:
            service.close()


def test_set_habit_type_changes_existing():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "habits.db")
        service = HabitService(workspace_root=WORKSPACE_ROOT, db_path=db_path)
        try:
            result = service.set_habit_type("morgenroutine", "maintain")
            assert_eq(result["status"], "success", "set type status")
            assert_eq(result["habit"]["habit_type"], "maintain", "type after set")
        finally:
            service.close()


def test_log_relapse_writes_relapse_and_event():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "habits.db")
        service = HabitService(workspace_root=WORKSPACE_ROOT, db_path=db_path)
        try:
            service.add_habit(
                name="Doomscrolling Night",
                target_time="22:00",
                habit_type="reduce",
                failure_modes=["muede"],
                replacement_actions=["zaehneputzen"],
            )
            relapse = service.log_relapse(
                "Doomscrolling Night",
                trigger="ich war zu muede",
                replacement="Zaehneputzen direkt",
                severity="minor",
                target_date=date(2026, 4, 27),
            )
            assert_eq(relapse["status"], "success", "relapse status")
            assert_eq(relapse["trigger_context"], "muede", "canonical trigger")
            assert_eq(relapse["replacement_used"], "zaehneputzen_direkt", "normalized replacement")
            assert_eq(relapse["severity"], "minor", "severity")
            assert_eq(relapse["final_status"], "skipped", "skipped final")

            row = service.connection.execute(
                "SELECT trigger_context, replacement_used, severity FROM habit_relapses"
            ).fetchone()
            assert row is not None, "relapse row must exist"
            assert_eq(row["trigger_context"], "muede", "row trigger")
            assert_eq(row["severity"], "minor", "row severity")

            event = service.connection.execute(
                """
                SELECT event_type, failure_mode, recovery_used FROM habit_events
                WHERE habit_id = 'habit-doomscrolling-night'
                """
            ).fetchone()
            assert event is not None, "event row must exist"
            assert_eq(event["event_type"], "skipped", "event type")
            assert_eq(event["failure_mode"], "muede", "failure_mode")
            assert_eq(event["recovery_used"], 0, "recovery_used 0 for relapse")
        finally:
            service.close()


def test_log_relapse_only_for_reduce_habits():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "habits.db")
        service = HabitService(workspace_root=WORKSPACE_ROOT, db_path=db_path)
        try:
            result = service.log_relapse(
                "morgenroutine",
                trigger="muede",
                severity="moderate",
                target_date=date(2026, 4, 27),
            )
            assert_eq(result["status"], "config_missing", "build habit relapse rejected")
        finally:
            service.close()


def test_log_recovery_protects_streak():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "habits.db")
        service = HabitService(workspace_root=WORKSPACE_ROOT, db_path=db_path)
        try:
            service.mark_done("morgenroutine", target_date=date(2026, 4, 25), mode="full")
            service.mark_done("morgenroutine", target_date=date(2026, 4, 26), mode="full")
            recovery = service.log_recovery(
                "morgenroutine",
                target_date=date(2026, 4, 27),
                notes="2-min reset wegen verschlafen",
            )
            assert_eq(recovery["status"], "success", "recovery status")
            assert_eq(recovery["recovery_used"], True, "recovery flag")
            assert recovery["current_streak"] >= 2, (
                f"streak must be preserved by recovery, got {recovery['current_streak']}"
            )
            service.mark_done("morgenroutine", target_date=date(2026, 4, 28), mode="full")
            again = service.mark_done("morgenroutine", target_date=date(2026, 4, 29), mode="full")
            assert again["current_streak"] >= 2

            event = service.connection.execute(
                """
                SELECT recovery_used FROM habit_events
                WHERE habit_id = 'habit-morning-routine'
                  AND business_date_berlin = '2026-04-27'
                  AND recovery_used = 1
                """
            ).fetchone()
            assert event is not None, "recovery event must exist with recovery_used=1"
        finally:
            service.close()


def test_log_failure_mode_records_reason():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "habits.db")
        service = HabitService(workspace_root=WORKSPACE_ROOT, db_path=db_path)
        try:
            result = service.log_failure_mode(
                "morgenroutine",
                failure_mode="verschlafen",
                target_date=date(2026, 4, 27),
                notes="Wecker nicht gehoert",
            )
            assert_eq(result["status"], "success", "failure mode status")
            assert_eq(result["failure_mode"], "verschlafen", "failure_mode echo")
            event = service.connection.execute(
                """
                SELECT failure_mode FROM habit_events
                WHERE habit_id = 'habit-morning-routine' AND business_date_berlin = '2026-04-27'
                """
            ).fetchone()
            assert_eq(event["failure_mode"], "verschlafen", "event failure_mode persisted")
        finally:
            service.close()


def test_pattern_detection_finds_multiple_classes():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "habits.db")
        service = HabitService(workspace_root=WORKSPACE_ROOT, db_path=db_path)
        try:
            service.add_habit(
                name="Doomscrolling Night",
                target_time="22:00",
                habit_type="reduce",
                failure_modes=["muede"],
                replacement_actions=["zaehneputzen"],
            )

            today = date(2026, 4, 30)

            for offset in range(7):
                day = today - timedelta(days=offset)
                service.skip_habit(
                    "morgenroutine",
                    target_date=day,
                    notes=f"missed {day.isoformat()}",
                )

            for offset in range(4):
                day = today - timedelta(days=offset * 2)
                service.log_relapse(
                    "Doomscrolling Night",
                    trigger="ich war muede",
                    replacement="zaehneputzen direkt",
                    severity="minor",
                    target_date=day,
                )

            service.mark_done("habit-evening-routine", target_date=today - timedelta(days=4), mode="full")
            service.mark_done("habit-evening-routine", target_date=today - timedelta(days=3), mode="full")
            service.log_recovery("habit-evening-routine", target_date=today - timedelta(days=2))
            service.log_recovery("habit-evening-routine", target_date=today - timedelta(days=1))

            patterns = service.week_patterns(reference_date=today)
            assert_eq(patterns["status"], "success", "pattern status")
            keys = {pattern["key"] for pattern in patterns["patterns"]}
            for required in (
                PATTERN_TIME_MISALIGNMENT,
                PATTERN_TRIGGER_CLUSTER,
                PATTERN_RECOVERY_STREAK_SAVE,
                PATTERN_REPLACEMENT_WORKS,
            ):
                assert required in keys, f"expected {required} in detected patterns: {keys}"
        finally:
            service.close()


def test_trigger_classifier():
    assert_eq(classify_trigger("ich war richtig muede"), "muede", "trigger muede")
    assert_eq(classify_trigger("Stress in der Arbeit"), "stress", "trigger stress")
    assert_eq(classify_trigger("Langeweile"), "langeweile", "trigger langeweile")
    assert_eq(classify_trigger(""), "unbekannt", "empty trigger")
    assert_eq(classify_trigger(None), "unbekannt", "none trigger")
    assert_eq(classify_trigger("nur was zufaelliges"), "unbekannt", "no match -> unbekannt")


def test_replacement_normalizer():
    assert_eq(normalize_replacement("Zaehneputzen direkt"), "zaehneputzen_direkt", "replacement normalize")
    assert_eq(normalize_replacement("  5 Minuten Dehnen!  "), "5_minuten_dehnen", "with punctuation")
    assert normalize_replacement("") is None
    assert normalize_replacement(None) is None


def test_coerce_helpers():
    assert_eq(coerce_habit_type(None), "build", "default type")
    assert_eq(coerce_habit_type("reduce"), "reduce", "explicit type")
    assert_eq(coerce_severity(None), "moderate", "default severity")
    assert_eq(coerce_severity("major"), "major", "explicit severity")

    raised = False
    try:
        coerce_habit_type("nonsense")
    except ValueError:
        raised = True
    assert raised, "coerce_habit_type must raise on invalid value"


def test_no_telegram_no_calendar_writes():
    import src.habits.service as service_module
    src_text = Path(service_module.__file__).read_text(encoding="utf-8")
    assert "send_telegram_message" not in src_text, "habit service must not call telegram"
    assert "calendar_write" not in src_text.lower(), "habit service must not perform calendar write"


def test_init_db_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "habits.db")
        first = HabitService(workspace_root=WORKSPACE_ROOT, db_path=db_path)
        first.close()
        second = HabitService(workspace_root=WORKSPACE_ROOT, db_path=db_path)
        try:
            cols = {row["name"] for row in second.connection.execute("PRAGMA table_info(habit_definitions)").fetchall()}
            for col in (
                "habit_type",
                "failure_modes_json",
                "replacement_actions_json",
                "recovery_rule_json",
                "trigger_window_json",
            ):
                assert col in cols, f"column {col} missing after re-init"
            event_cols = {row["name"] for row in second.connection.execute("PRAGMA table_info(habit_events)").fetchall()}
            for col in ("failure_mode", "recovery_used"):
                assert col in event_cols, f"event column {col} missing"
            relapse_cols = {row["name"] for row in second.connection.execute("PRAGMA table_info(habit_relapses)").fetchall()}
            assert "trigger_context" in relapse_cols
        finally:
            second.close()


def test_pattern_keys_complete():
    expected = {
        PATTERN_TIME_MISALIGNMENT,
        PATTERN_WEEKDAY_DROP,
        PATTERN_TRIGGER_CLUSTER,
        PATTERN_RECOVERY_STREAK_SAVE,
        PATTERN_REPLACEMENT_WORKS,
    }
    assert set(PATTERN_KEYS) == expected, f"PATTERN_KEYS drifted: {PATTERN_KEYS}"


def test_default_habit_types_constant():
    assert "build" in HABIT_TYPES
    assert "reduce" in HABIT_TYPES
    assert "maintain" in HABIT_TYPES
    assert "recovery" in HABIT_TYPES
    assert_eq(DEFAULT_HABIT_TYPE, "build", "default constant")


def main():
    test_default_habit_type_migration()
    test_add_reduce_habit_with_metadata()
    test_set_habit_type_changes_existing()
    test_log_relapse_writes_relapse_and_event()
    test_log_relapse_only_for_reduce_habits()
    test_log_recovery_protects_streak()
    test_log_failure_mode_records_reason()
    test_pattern_detection_finds_multiple_classes()
    test_trigger_classifier()
    test_replacement_normalizer()
    test_coerce_helpers()
    test_no_telegram_no_calendar_writes()
    test_init_db_idempotent()
    test_pattern_keys_complete()
    test_default_habit_types_constant()
    print("verify_habit_coaching: ok")


if __name__ == "__main__":
    main()
