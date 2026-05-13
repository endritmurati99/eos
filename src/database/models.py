from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = "./var/eos_v2.db"


def resolve_db_path(db_path: str | None = None) -> Path:
    raw_path = db_path or os.getenv("EOS_DB_PATH") or DEFAULT_DB_PATH
    return Path(raw_path).expanduser()


def connect_db(db_path: str | None = None) -> sqlite3.Connection:
    resolved_path = resolve_db_path(db_path)
    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(resolved_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def _ensure_columns(
    connection: sqlite3.Connection,
    table: str,
    columns: dict[str, str],
) -> None:
    existing = _column_names(connection, table)
    for column, definition in columns.items():
        if column in existing:
            continue
        connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db(db_path: str | None = None) -> sqlite3.Connection:
    connection = connect_db(db_path)
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS job_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job TEXT NOT NULL,
            run_id TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            target_window_start_berlin TEXT,
            target_window_end_berlin TEXT,
            target_business_date_berlin TEXT,
            run_status TEXT NOT NULL,
            calendar_read_status TEXT NOT NULL,
            task_read_status TEXT NOT NULL,
            delivery_status TEXT NOT NULL,
            message_digest TEXT,
            last_error TEXT,
            created_at_utc TEXT NOT NULL,
            updated_at_utc TEXT NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_job_runs_job_idempotency
            ON job_runs(job, idempotency_key);

        CREATE INDEX IF NOT EXISTS idx_job_runs_target_business_date
            ON job_runs(target_business_date_berlin);

        CREATE TABLE IF NOT EXISTS daily_evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_date_berlin TEXT NOT NULL,
            evaluation_source TEXT NOT NULL,
            traffic_light_status TEXT NOT NULL,
            reasons_json TEXT NOT NULL,
            assessment_text TEXT NOT NULL,
            recommendation_text TEXT NOT NULL,
            warning_text TEXT,
            task_snapshot_id INTEGER,
            created_at_utc TEXT NOT NULL
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_evaluations_business_source
            ON daily_evaluations(business_date_berlin, evaluation_source);

        CREATE TABLE IF NOT EXISTS task_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_scope TEXT NOT NULL,
            business_date_berlin TEXT NOT NULL,
            captured_at_utc TEXT NOT NULL,
            provider TEXT NOT NULL,
            provider_status TEXT NOT NULL,
            is_partial INTEGER NOT NULL DEFAULT 0,
            failed_lists_json TEXT,
            tasks_by_list_json TEXT NOT NULL,
            open_task_count INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_task_snapshots_business_date
            ON task_snapshots(business_date_berlin);

        CREATE TABLE IF NOT EXISTS habit_definitions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            frequency TEXT NOT NULL,
            target_time TEXT,
            routine_ref TEXT,
            minimum_version_json TEXT NOT NULL,
            full_version_json TEXT NOT NULL,
            aliases_json TEXT NOT NULL,
            created_at_utc TEXT NOT NULL,
            updated_at_utc TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS habit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id TEXT NOT NULL,
            business_date_berlin TEXT NOT NULL,
            event_type TEXT NOT NULL,
            source TEXT NOT NULL,
            notes TEXT,
            created_at_utc TEXT NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habit_definitions(id)
        );

        CREATE INDEX IF NOT EXISTS idx_habit_events_date
            ON habit_events(business_date_berlin);

        CREATE TABLE IF NOT EXISTS habit_daily_status (
            habit_id TEXT NOT NULL,
            business_date_berlin TEXT NOT NULL,
            final_status TEXT NOT NULL,
            source TEXT NOT NULL,
            notes TEXT,
            updated_at_utc TEXT NOT NULL,
            PRIMARY KEY (habit_id, business_date_berlin),
            FOREIGN KEY (habit_id) REFERENCES habit_definitions(id)
        );

        CREATE INDEX IF NOT EXISTS idx_habit_daily_status_date
            ON habit_daily_status(business_date_berlin);

        CREATE TABLE IF NOT EXISTS habit_relapses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_id TEXT NOT NULL,
            business_date_berlin TEXT NOT NULL,
            trigger_context TEXT,
            replacement_used TEXT,
            severity TEXT NOT NULL,
            notes TEXT,
            created_at_utc TEXT NOT NULL,
            FOREIGN KEY (habit_id) REFERENCES habit_definitions(id)
        );

        CREATE INDEX IF NOT EXISTS idx_habit_relapses_habit_date
            ON habit_relapses(habit_id, business_date_berlin);

        CREATE TABLE IF NOT EXISTS pending_confirmations (
            id TEXT PRIMARY KEY,
            created_at_utc TEXT NOT NULL,
            expires_at_utc TEXT NOT NULL,
            user_id TEXT NOT NULL DEFAULT 'cli',
            source TEXT NOT NULL DEFAULT 'cli',
            original_text TEXT NOT NULL,
            parsed_intent TEXT NOT NULL,
            parsed_entities_json TEXT,
            missing_fields_json TEXT,
            confirmation_question TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            resolved_at_utc TEXT,
            resolution_json TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_pending_confirmations_status_user
            ON pending_confirmations(status, user_id);

        CREATE TABLE IF NOT EXISTS daily_energy_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            local_date TEXT NOT NULL,
            timestamp_utc TEXT NOT NULL,
            sleep_quality INTEGER,
            energy_level INTEGER,
            physical_fatigue INTEGER,
            mental_load INTEGER,
            stress INTEGER,
            motivation INTEGER,
            soreness INTEGER,
            notes_json TEXT,
            source TEXT NOT NULL DEFAULT 'cli'
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_energy_logs_date_source
            ON daily_energy_logs(local_date, source);

        CREATE TABLE IF NOT EXISTS dispatch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_utc TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'cli',
            input_hash TEXT NOT NULL,
            intent TEXT NOT NULL,
            confidence REAL NOT NULL,
            action_type TEXT NOT NULL,
            target_service TEXT,
            result_status TEXT NOT NULL,
            idempotency_key TEXT,
            error_json TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_dispatch_log_timestamp
            ON dispatch_log(timestamp_utc);
        """
    )

    _ensure_columns(
        connection,
        "habit_definitions",
        {
            "habit_type": "TEXT NOT NULL DEFAULT 'build'",
            "failure_modes_json": "TEXT",
            "replacement_actions_json": "TEXT",
            "recovery_rule_json": "TEXT",
            "trigger_window_json": "TEXT",
        },
    )

    _ensure_columns(
        connection,
        "habit_events",
        {
            "failure_mode": "TEXT",
            "recovery_used": "INTEGER NOT NULL DEFAULT 0",
        },
    )

    connection.commit()
    return connection
