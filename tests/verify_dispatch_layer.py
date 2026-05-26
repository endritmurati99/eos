#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from datetime import date, timedelta
from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.database.models import init_db  # noqa: E402
from src.dispatch import dispatch_text, DispatchResult  # noqa: E402
from src.dispatch.actions import ACTION_NOOP, ACTION_ENERGY_LOG, ACTION_HABIT_MARK_DONE, ACTION_PENDING_CONFIRMATION  # noqa: E402
from src.confirmations import ConfirmationService  # noqa: E402
from src.energy import EnergyService, parse_energy_text, EnergyLog  # noqa: E402
from src.intake.models import SUPPORTED_INTENTS  # noqa: E402
from src.intake.intent_router import classify_intent  # noqa: E402


def assert_eq(actual, expected, label):
    assert actual == expected, f"{label}: expected {expected!r}, got {actual!r}"


def load_cli_json(stdout: str) -> dict:
    payload = stdout.strip()
    assert payload, "CLI stdout must contain JSON"
    return json.loads(payload)


# ── 1. New intents in SUPPORTED_INTENTS ────────────────────────────────────

def test_new_intents_in_supported():
    for intent in ("habit_relapse", "habit_recovery", "habit_failure", "confirm_response"):
        assert intent in SUPPORTED_INTENTS, f"'{intent}' must be in SUPPORTED_INTENTS"


# ── 2. Intent router recognises new keywords ───────────────────────────────

def test_intent_relapse_keyword():
    result = classify_intent("ich hatte einen rueckfall")
    assert_eq(result.intent, "habit_relapse", "relapse intent")
    assert result.confidence >= 0.85

def test_intent_recovery_keyword():
    result = classify_intent("2 minuten reset gemacht")
    assert_eq(result.intent, "habit_recovery", "recovery intent")

def test_intent_failure_keyword():
    result = classify_intent("heute verschlafen morgenroutine")
    assert_eq(result.intent, "habit_failure", "failure intent")
    assert result.entities.get("failure_mode") == "verschlafen"

def test_energy_entity_extraction():
    result = classify_intent("schlaf 6 energie 5 stress 7")
    assert_eq(result.intent, "daily_checkin", "checkin intent")
    assert result.entities.get("sleep_quality") == 6
    assert result.entities.get("energy_level") == 5
    assert result.entities.get("stress") == 7


# ── 3. DB schema — three new tables ────────────────────────────────────────

def test_init_db_phase3_tables():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        conn = init_db(db_path)
        tables = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        for tbl in ("pending_confirmations", "daily_energy_logs", "dispatch_log"):
            assert tbl in tables, f"Table '{tbl}' must exist"
        conn.close()


def test_init_db_idempotent_phase3():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        conn1 = init_db(db_path)
        conn1.close()
        conn2 = init_db(db_path)
        cols = {row["name"] for row in conn2.execute("PRAGMA table_info(pending_confirmations)").fetchall()}
        assert "confirmation_question" in cols
        conn2.close()


# ── 4. ConfirmationService ──────────────────────────────────────────────────

def test_confirmation_create_and_list():
    with tempfile.TemporaryDirectory() as tmp:
        conn = init_db(str(Path(tmp) / "test.db"))
        intake = classify_intent("hab alles erledigt")
        conf = ConfirmationService.create(intake, user_id="test-user", source="cli", connection=conn)
        assert conf["status"] == "pending"
        assert conf["id"]
        pending = ConfirmationService.list_pending("test-user", connection=conn)
        assert len(pending) == 1
        assert_eq(pending[0]["parsed_intent"], "habit_log", "pending intent")
        conn.close()


def test_confirmation_resolve():
    with tempfile.TemporaryDirectory() as tmp:
        conn = init_db(str(Path(tmp) / "test.db"))
        intake = classify_intent("hab alles erledigt")
        conf = ConfirmationService.create(intake, user_id="u1", source="cli", connection=conn)
        resolved = ConfirmationService.resolve_with_text(conf["id"], "morgenroutine", connection=conn)
        assert_eq(resolved["status"], "resolved", "resolved status")
        assert resolved["resolved_at_utc"] is not None
        pending = ConfirmationService.list_pending("u1", connection=conn)
        assert_eq(len(pending), 0, "no pending after resolve")
        conn.close()


def test_confirmation_expire_all():
    with tempfile.TemporaryDirectory() as tmp:
        conn = init_db(str(Path(tmp) / "test.db"))
        intake = classify_intent("hab alles erledigt")
        conf = ConfirmationService.create(intake, user_id="u2", source="cli", connection=conn)
        conn.execute(
            "UPDATE pending_confirmations SET expires_at_utc = '2020-01-01T00:00:00+00:00' WHERE id = ?",
            (conf["id"],),
        )
        conn.commit()
        count = ConfirmationService.expire_all(connection=conn)
        assert count >= 1, "at least 1 expired"
        conn.close()


# ── 5. EnergyLog parse ──────────────────────────────────────────────────────

def test_energy_parse_full():
    log = parse_energy_text("schlaf 6, energie 5, stress 7, körper müde 4")
    assert_eq(log.sleep_quality, 6, "sleep_quality")
    assert_eq(log.energy_level, 5, "energy_level")
    assert_eq(log.stress, 7, "stress")


def test_energy_parse_partial():
    log = parse_energy_text("energie 8")
    assert_eq(log.energy_level, 8, "energy_level")
    assert log.sleep_quality is None
    assert log.stress is None


def test_energy_parse_out_of_range():
    raised = False
    try:
        parse_energy_text("energie 11")
    except ValueError:
        raised = True
    assert raised, "out-of-range value must raise ValueError"


# ── 6. EnergyService ────────────────────────────────────────────────────────

def test_energy_service_log_and_today():
    with tempfile.TemporaryDirectory() as tmp:
        conn = init_db(str(Path(tmp) / "test.db"))
        from datetime import datetime, timezone
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("Europe/Berlin")
        except Exception:
            import pytz
            tz = pytz.timezone("Europe/Berlin")
        today = datetime.now(tz).date().isoformat()
        log = EnergyLog(local_date=today, energy_level=7, stress=4, source="cli")
        result = EnergyService.log(log, connection=conn)
        assert result["energy_level"] == 7
        today_result = EnergyService.today(connection=conn)
        assert today_result is not None
        assert_eq(today_result["energy_level"], 7, "today energy_level")
        conn.close()


def test_energy_service_upsert_same_day():
    with tempfile.TemporaryDirectory() as tmp:
        conn = init_db(str(Path(tmp) / "test.db"))
        from datetime import datetime, timezone
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("Europe/Berlin")
        except Exception:
            import pytz
            tz = pytz.timezone("Europe/Berlin")
        today = datetime.now(tz).date().isoformat()
        log1 = EnergyLog(local_date=today, energy_level=5, source="cli")
        log2 = EnergyLog(local_date=today, energy_level=8, source="cli")
        EnergyService.log(log1, connection=conn)
        EnergyService.log(log2, connection=conn)
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM daily_energy_logs WHERE local_date = ?", (today,)
        ).fetchone()
        assert_eq(row["cnt"], 1, "only one row per day per source")
        today_result = EnergyService.today(connection=conn)
        assert_eq(today_result["energy_level"], 8, "second log overwrites first")
        conn.close()


# ── 7. dispatch_text flows ──────────────────────────────────────────────────

def test_dispatch_habit_log_specific():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        result = dispatch_text("morgenroutine erledigt", db_path=db_path)
        assert result.intent == "habit_log"
        assert result.status in ("ok", "skipped", "error")
        conn = init_db(db_path)
        row = conn.execute(
            "SELECT action_type FROM dispatch_log WHERE intent = 'habit_log' LIMIT 1"
        ).fetchone()
        assert row is not None, "dispatch_log must have an entry"
        conn.close()


def test_dispatch_ambiguous_creates_pending():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        result = dispatch_text("hab alles erledigt", user_id="test-user", db_path=db_path)
        assert result.status == "pending"
        assert result.action_type == ACTION_PENDING_CONFIRMATION
        assert result.confirmation_id is not None
        conn = init_db(db_path)
        pending = ConfirmationService.list_pending("test-user", connection=conn)
        assert len(pending) >= 1
        conn.close()


def test_dispatch_unknown_no_write():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        result = dispatch_text("war ganz okay heute irgendwie", db_path=db_path)
        assert result.status in ("pending", "skipped")
        conn = init_db(db_path)
        habit_rows = conn.execute("SELECT COUNT(*) as cnt FROM habit_events").fetchone()
        assert_eq(habit_rows["cnt"], 0, "no habit_events written for unknown input")
        conn.close()


def test_dispatch_energy_checkin():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        result = dispatch_text("schlaf 6 energie 5 stress 7", db_path=db_path)
        assert result.intent == "daily_checkin"
        assert result.status == "ok"
        assert result.action_type == ACTION_ENERGY_LOG
        conn = init_db(db_path)
        row = conn.execute("SELECT energy_level, sleep_quality, stress FROM daily_energy_logs LIMIT 1").fetchone()
        assert row is not None, "energy log must be written"
        assert_eq(row["energy_level"], 5, "energy_level persisted")
        assert_eq(row["sleep_quality"], 6, "sleep_quality persisted")
        assert_eq(row["stress"], 7, "stress persisted")
        conn.close()


def test_dispatch_idempotency():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        first = dispatch_text("morgenroutine erledigt", db_path=db_path)
        second = dispatch_text("morgenroutine erledigt", db_path=db_path)
        if first.status == "ok":
            assert second.status in ("ok", "skipped"), "idempotent second dispatch"


def test_dispatch_log_always_written():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = str(Path(tmp) / "test.db")
        dispatch_text("völlig unklar blablabla", db_path=db_path)
        conn = init_db(db_path)
        count = conn.execute("SELECT COUNT(*) as cnt FROM dispatch_log").fetchone()["cnt"]
        assert count >= 1, "dispatch_log written even for unknown/noop"
        conn.close()


# ── 8. CLI smoke tests ───────────────────────────────────────────────────────

def test_cli_dispatch_handle_json():
    import subprocess
    result = subprocess.run(
        [sys.executable, "-m", "src.eos_cli", "--json-only", "dispatch", "handle", "morgenroutine erledigt"],
        capture_output=True, text=True, cwd=str(WORKSPACE_ROOT)
    )
    assert result.returncode in (0, 1), f"CLI exited with {result.returncode}: {result.stderr}"
    data = load_cli_json(result.stdout)
    assert "intent" in data, f"JSON must contain 'intent', got: {data}"
    assert "status" in data


def test_cli_energy_today_empty():
    import subprocess
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run(
            [sys.executable, "-m", "src.eos_cli", "--json-only", "energy", "today"],
            capture_output=True, text=True, cwd=str(WORKSPACE_ROOT),
            env={**__import__("os").environ, "EOS_DB_PATH": str(Path(tmp) / "test.db")}
        )
        assert result.returncode in (0, 1)
        data = load_cli_json(result.stdout)
        assert data.get("status") in ("no_data", "success")


def test_cli_confirmations_list_empty():
    import subprocess
    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run(
            [sys.executable, "-m", "src.eos_cli", "--json-only", "confirmations", "list"],
            capture_output=True, text=True, cwd=str(WORKSPACE_ROOT),
            env={**__import__("os").environ, "EOS_DB_PATH": str(Path(tmp) / "test.db")}
        )
        assert result.returncode in (0, 1)
        data = load_cli_json(result.stdout)
        assert "confirmations" in data
        assert data["confirmations"] == []


# ── 9. No calendar/planning imports in dispatch ──────────────────────────────

def test_no_calendar_write_no_planning():
    import src.dispatch.router as router_module
    src_text = Path(router_module.__file__).read_text(encoding="utf-8")
    assert "calendar_write" not in src_text.lower(), "dispatch/router must not call calendar_write"
    assert "create_event" not in src_text.lower(), "dispatch/router must not call create_event"
    assert "planning_proposal" not in src_text.lower(), "dispatch/router must not call planning_proposal"


def main():
    test_new_intents_in_supported()
    test_intent_relapse_keyword()
    test_intent_recovery_keyword()
    test_intent_failure_keyword()
    test_energy_entity_extraction()
    test_init_db_phase3_tables()
    test_init_db_idempotent_phase3()
    test_confirmation_create_and_list()
    test_confirmation_resolve()
    test_confirmation_expire_all()
    test_energy_parse_full()
    test_energy_parse_partial()
    test_energy_parse_out_of_range()
    test_energy_service_log_and_today()
    test_energy_service_upsert_same_day()
    test_dispatch_habit_log_specific()
    test_dispatch_ambiguous_creates_pending()
    test_dispatch_unknown_no_write()
    test_dispatch_energy_checkin()
    test_dispatch_idempotency()
    test_dispatch_log_always_written()
    test_cli_dispatch_handle_json()
    test_cli_energy_today_empty()
    test_cli_confirmations_list_empty()
    test_no_calendar_write_no_planning()
    print("verify_dispatch_layer: ok")


if __name__ == "__main__":
    main()
