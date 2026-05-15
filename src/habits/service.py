from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Iterable

from src.database import init_db
from src.eos_core import load_state
from src.habits.patterns import PatternSignal, detect_patterns
from src.habits.triggers import classify_trigger, normalize_replacement
from src.habits.types import (
    DEFAULT_HABIT_TYPE,
    HABIT_TYPES,
    RELAPSE_SEVERITIES,
    coerce_habit_type,
    coerce_severity,
)


EVENT_DONE_FULL = "done_full"
EVENT_DONE_PARTIAL = "done_partial"
EVENT_SKIPPED = "skipped"
EVENT_MISSED = "missed"
EVENT_PAUSED = "paused"
FINAL_STATUSES = {EVENT_DONE_FULL, EVENT_DONE_PARTIAL, EVENT_SKIPPED, EVENT_MISSED}
BERLIN = ZoneInfo("Europe/Berlin")


class HabitService:
    def __init__(
        self,
        *,
        workspace_root: str | Path | None = None,
        db_path: str | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root) if workspace_root is not None else Path(__file__).resolve().parents[2]
        self.connection = init_db(db_path)
        self.seed_from_state()

    def close(self) -> None:
        self.connection.close()

    def health(self) -> dict[str, Any]:
        definitions = self.list_definitions(include_paused=True)
        active = [habit for habit in definitions if habit["status"] == "active"]
        return {
            "status": "success" if active else "warning",
            "definition_count": len(definitions),
            "active_count": len(active),
            "error": None if active else "No active habits configured.",
        }

    def seed_from_state(self) -> None:
        state_path = self.workspace_root / "data" / "eos_state.json"
        if not state_path.exists():
            return

        now = _utc_now()
        state = load_state(state_path)
        for habit in state.get("habits", []):
            aliases = _aliases_for(habit["id"], habit["name"])
            habit_type = coerce_habit_type(habit.get("type"))
            failure_modes = habit.get("failure_modes")
            replacement_actions = habit.get("replacement_actions")
            recovery_rule = habit.get("recovery_rule")
            trigger_window = habit.get("trigger_window")
            self.connection.execute(
                """
                INSERT INTO habit_definitions (
                    id, name, status, frequency, target_time, routine_ref,
                    minimum_version_json, full_version_json, aliases_json,
                    habit_type, failure_modes_json, replacement_actions_json,
                    recovery_rule_json, trigger_window_json, schedule_rule_json,
                    category, salience, briefing_policy_json, created_at_utc, updated_at_utc
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO NOTHING
                """,
                (
                    habit["id"],
                    habit["name"],
                    habit.get("status", "active"),
                    habit.get("frequency", "daily"),
                    habit.get("target_time"),
                    habit.get("routine_ref"),
                    json.dumps(habit.get("minimum_version", []), ensure_ascii=False),
                    json.dumps(habit.get("full_version", []), ensure_ascii=False),
                    json.dumps(aliases, ensure_ascii=False),
                    habit_type,
                    json.dumps(failure_modes, ensure_ascii=False) if failure_modes is not None else None,
                    json.dumps(replacement_actions, ensure_ascii=False) if replacement_actions is not None else None,
                    json.dumps(recovery_rule, ensure_ascii=False) if recovery_rule is not None else None,
                    json.dumps(trigger_window, ensure_ascii=False) if trigger_window is not None else None,
                    json.dumps(habit.get("schedule_rule"), ensure_ascii=False) if habit.get("schedule_rule") else None,
                    habit.get("category"),
                    int(habit.get("salience", 3)),
                    json.dumps(habit.get("briefing_policy"), ensure_ascii=False) if habit.get("briefing_policy") else None,
                    now,
                    now,
                ),
            )
        self.connection.commit()

    def list_definitions(self, *, include_paused: bool = False) -> list[dict[str, Any]]:
        query = "SELECT * FROM habit_definitions"
        params: tuple[Any, ...] = ()
        if not include_paused:
            query += " WHERE status = ?"
            params = ("active",)
        query += " ORDER BY target_time IS NULL, target_time, name"
        rows = self.connection.execute(query, params).fetchall()
        return [self._row_to_definition(row) for row in rows]

    def status(self, target_date: date | None = None) -> dict[str, Any]:
        day = target_date or _business_today()
        habits = []
        for habit in self.list_definitions(include_paused=True):
            daily = self._daily_status(habit["id"], day)
            habits.append(
                {
                    **habit,
                    "today": daily,
                    "current_streak": self._streak_through(habit["id"], day),
                    "scheduled_today": _is_scheduled_for_day(habit, day),
                    "pending": habit["status"] == "active" and daily["final_status"] is None and _is_scheduled_for_day(habit, day),
                }
            )
        return {
            "status": "success",
            "business_date_berlin": day.isoformat(),
            "habits": habits,
            "active_count": sum(1 for habit in habits if habit["status"] == "active"),
            "pending_count": sum(1 for habit in habits if habit["pending"]),
        }

    def today(self, target_date: date | None = None) -> dict[str, Any]:
        result = self.status(target_date)
        result["habits"] = [habit for habit in result["habits"] if habit["status"] == "active"]
        result["pending_count"] = sum(1 for habit in result["habits"] if habit["pending"])
        return result

    def add_habit(
        self,
        *,
        name: str,
        target_time: str | None = None,
        frequency: str = "daily",
        minimum_version: Iterable[str] | None = None,
        full_version: Iterable[str] | None = None,
        habit_type: str | None = None,
        failure_modes: list[str] | None = None,
        replacement_actions: list[str] | None = None,
        recovery_rule: dict[str, Any] | None = None,
        trigger_window: dict[str, Any] | None = None,
        schedule_weekdays: list[int] | None = None,
        category: str | None = None,
        salience: int = 3,
        briefing_policy: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        clean_name = name.strip()
        if not clean_name:
            return {"status": "config_missing", "error": "Habit name is required."}
        if frequency not in {"daily", "weekly"}:
            return {"status": "config_missing", "error": "frequency must be daily or weekly."}
        if target_time and not re.fullmatch(r"\d{2}:\d{2}", target_time):
            return {"status": "config_missing", "error": "target_time must use HH:MM."}
        try:
            schedule_rule = _schedule_rule_from_weekdays(schedule_weekdays)
            if not 1 <= int(salience) <= 5:
                return {"status": "config_missing", "error": "salience must be between 1 and 5."}
            resolved_type = coerce_habit_type(habit_type)
        except ValueError as error:
            return {"status": "config_missing", "error": str(error)}

        habit_id = _unique_habit_id(self.connection, clean_name)
        full_items = list(full_version or [clean_name])
        minimum_items = list(minimum_version or full_items[:1])
        now = _utc_now()
        aliases = _aliases_for(habit_id, clean_name)
        self.connection.execute(
            """
            INSERT INTO habit_definitions (
                id, name, status, frequency, target_time, routine_ref,
                minimum_version_json, full_version_json, aliases_json,
                habit_type, failure_modes_json, replacement_actions_json,
                recovery_rule_json, trigger_window_json, schedule_rule_json,
                category, salience, briefing_policy_json, created_at_utc, updated_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                habit_id,
                clean_name,
                "active",
                frequency,
                target_time,
                None,
                json.dumps(minimum_items, ensure_ascii=False),
                json.dumps(full_items, ensure_ascii=False),
                json.dumps(aliases, ensure_ascii=False),
                resolved_type,
                json.dumps(failure_modes, ensure_ascii=False) if failure_modes else None,
                json.dumps(replacement_actions, ensure_ascii=False) if replacement_actions else None,
                json.dumps(recovery_rule, ensure_ascii=False) if recovery_rule else None,
                json.dumps(trigger_window, ensure_ascii=False) if trigger_window else None,
                json.dumps(schedule_rule, ensure_ascii=False) if schedule_rule else None,
                category,
                int(salience),
                json.dumps(briefing_policy, ensure_ascii=False) if briefing_policy else None,
                now,
                now,
            ),
        )
        self.connection.commit()
        return {
            "status": "success",
            "habit": self.get_definition(habit_id),
        }

    def set_habit_type(self, query: str, habit_type: str) -> dict[str, Any]:
        try:
            resolved_type = coerce_habit_type(habit_type)
        except ValueError as error:
            return {"status": "config_missing", "error": str(error)}
        resolved = self.resolve_habit(query)
        if resolved["status"] != "success":
            return resolved
        habit = resolved["habit"]
        now = _utc_now()
        self.connection.execute(
            "UPDATE habit_definitions SET habit_type = ?, updated_at_utc = ? WHERE id = ?",
            (resolved_type, now, habit["id"]),
        )
        self.connection.commit()
        return {"status": "success", "habit": self.get_definition(habit["id"])}

    def log_failure_mode(
        self,
        query: str,
        *,
        failure_mode: str,
        target_date: date | None = None,
        source: str = "cli",
        notes: str | None = None,
    ) -> dict[str, Any]:
        clean_mode = (failure_mode or "").strip()
        if not clean_mode:
            return {"status": "config_missing", "error": "failure_mode is required."}
        resolved = self.resolve_habit(query)
        if resolved["status"] != "success":
            return resolved
        habit = resolved["habit"]
        day = target_date or _business_today()
        now = _utc_now()
        self._insert_event(
            habit["id"],
            day,
            EVENT_MISSED,
            source,
            notes,
            now,
            failure_mode=clean_mode,
        )
        self.connection.execute(
            """
            INSERT INTO habit_daily_status (
                habit_id, business_date_berlin, final_status, source, notes, updated_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(habit_id, business_date_berlin) DO UPDATE SET
                final_status = excluded.final_status,
                source = excluded.source,
                notes = excluded.notes,
                updated_at_utc = excluded.updated_at_utc
            """,
            (habit["id"], day.isoformat(), EVENT_MISSED, source, notes, now),
        )
        self.connection.commit()
        return {
            "status": "success",
            "habit_id": habit["id"],
            "habit_name": habit["name"],
            "business_date_berlin": day.isoformat(),
            "final_status": EVENT_MISSED,
            "failure_mode": clean_mode,
            "current_streak": self._streak_through(habit["id"], day),
        }

    def log_relapse(
        self,
        query: str,
        *,
        trigger: str | None,
        replacement: str | None = None,
        severity: str = "moderate",
        target_date: date | None = None,
        source: str = "cli",
        notes: str | None = None,
    ) -> dict[str, Any]:
        try:
            resolved_severity = coerce_severity(severity)
        except ValueError as error:
            return {"status": "config_missing", "error": str(error)}
        resolved = self.resolve_habit(query)
        if resolved["status"] != "success":
            return resolved
        habit = resolved["habit"]
        if habit.get("habit_type") != "reduce":
            return {
                "status": "config_missing",
                "error": (
                    f"log_relapse only supported for habit_type='reduce', got "
                    f"{habit.get('habit_type')!r}."
                ),
            }
        day = target_date or _business_today()
        now = _utc_now()
        canonical_trigger = classify_trigger(trigger)
        normalized_replacement = normalize_replacement(replacement)

        self.connection.execute(
            """
            INSERT INTO habit_relapses (
                habit_id, business_date_berlin, trigger_context,
                replacement_used, severity, notes, created_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                habit["id"],
                day.isoformat(),
                canonical_trigger,
                normalized_replacement,
                resolved_severity,
                notes,
                now,
            ),
        )
        self._insert_event(
            habit["id"],
            day,
            EVENT_SKIPPED,
            source,
            notes,
            now,
            failure_mode=canonical_trigger,
            recovery_used=False,
        )
        self.connection.execute(
            """
            INSERT INTO habit_daily_status (
                habit_id, business_date_berlin, final_status, source, notes, updated_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(habit_id, business_date_berlin) DO UPDATE SET
                final_status = excluded.final_status,
                source = excluded.source,
                notes = excluded.notes,
                updated_at_utc = excluded.updated_at_utc
            """,
            (habit["id"], day.isoformat(), EVENT_SKIPPED, source, notes, now),
        )
        self.connection.commit()
        return {
            "status": "success",
            "habit_id": habit["id"],
            "habit_name": habit["name"],
            "business_date_berlin": day.isoformat(),
            "final_status": EVENT_SKIPPED,
            "trigger_context": canonical_trigger,
            "replacement_used": normalized_replacement,
            "severity": resolved_severity,
        }

    def log_recovery(
        self,
        query: str,
        *,
        target_date: date | None = None,
        source: str = "cli",
        notes: str | None = None,
    ) -> dict[str, Any]:
        resolved = self.resolve_habit(query)
        if resolved["status"] != "success":
            return resolved
        habit = resolved["habit"]
        day = target_date or _business_today()
        now = _utc_now()
        self._insert_event(
            habit["id"],
            day,
            EVENT_DONE_PARTIAL,
            source,
            notes,
            now,
            recovery_used=True,
        )
        self.connection.execute(
            """
            INSERT INTO habit_daily_status (
                habit_id, business_date_berlin, final_status, source, notes, updated_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(habit_id, business_date_berlin) DO UPDATE SET
                final_status = excluded.final_status,
                source = excluded.source,
                notes = excluded.notes,
                updated_at_utc = excluded.updated_at_utc
            """,
            (habit["id"], day.isoformat(), EVENT_DONE_PARTIAL, source, notes, now),
        )
        self.connection.commit()
        return {
            "status": "success",
            "habit_id": habit["id"],
            "habit_name": habit["name"],
            "business_date_berlin": day.isoformat(),
            "final_status": EVENT_DONE_PARTIAL,
            "recovery_used": True,
            "current_streak": self._streak_through(habit["id"], day),
        }

    def week_patterns(self, reference_date: date | None = None) -> dict[str, Any]:
        day = reference_date or _business_today()
        signals: list[PatternSignal] = detect_patterns(self.connection, reference_date=day)
        return {
            "status": "success",
            "reference_date_berlin": day.isoformat(),
            "pattern_count": len(signals),
            "patterns": [signal.to_dict() for signal in signals],
        }

    def daily_summary(self, target_date: date | None = None) -> dict[str, Any]:
        day = target_date or _business_today()
        status = self.status(day)
        habits = []
        counts = {
            EVENT_DONE_FULL: 0,
            EVENT_DONE_PARTIAL: 0,
            EVENT_SKIPPED: 0,
            EVENT_MISSED: 0,
            "pending": 0,
        }
        for habit in status["habits"]:
            final_status = habit["today"]["final_status"]
            pending = habit["pending"]
            first_trackable_day = _date_from_iso(habit["created_at_utc"]) or day
            if habit["status"] == "active" and final_status is None and _is_scheduled_for_day(habit, day) and first_trackable_day <= day < _business_today():
                final_status = EVENT_MISSED
                pending = False
            if final_status in counts:
                counts[final_status] += 1
            elif pending:
                counts["pending"] += 1
            habits.append(
                {
                    "id": habit["id"],
                    "name": habit["name"],
                    "habit_type": habit["habit_type"],
                    "target_time": habit["target_time"],
                    "final_status": final_status,
                    "pending": pending,
                    "scheduled_today": habit.get("scheduled_today", True),
                    "current_streak": habit["current_streak"],
                    "minimum_version": habit["minimum_version"],
                    "notes": habit["today"].get("notes"),
                }
            )
        relapses = self._relapses_for_day(day)
        result = {
            "status": "success",
            "business_date_berlin": day.isoformat(),
            "counts": counts,
            "relapse_count": len(relapses),
            "relapses": relapses,
            "habits": habits,
        }
        result["output_markdown"] = _render_daily_summary(result)
        return result

    def weekly_review(self, week_start: date) -> dict[str, Any]:
        report = self.weekly_report(week_start)
        week_end = week_start + timedelta(days=7)
        reference_day = week_end - timedelta(days=1)
        patterns = self.week_patterns(reference_day)
        habits = []
        total_full = 0
        total_partial = 0
        total_skipped = 0
        total_missed = 0
        for habit in report["habits"]:
            total_full += habit["full_count"]
            total_partial += habit["partial_count"]
            total_skipped += habit["skipped_count"]
            total_missed += habit["missed_count"]
            trackable_days = max(int(habit.get("trackable_day_count") or 0), 1)
            completion_rate = round((habit["full_count"] + 0.5 * habit["partial_count"]) / trackable_days, 3)
            habits.append({**habit, "completion_rate": completion_rate})
        total_slots = max(sum(int(habit.get("trackable_day_count") or 0) for habit in habits), 1)
        result = {
            "status": "success",
            "week_start_berlin": week_start.isoformat(),
            "week_end_berlin": week_end.isoformat(),
            "week_end_inclusive_berlin": reference_day.isoformat(),
            "totals": {
                "full": total_full,
                "partial": total_partial,
                "skipped": total_skipped,
                "missed": total_missed,
                "completion_rate": round((total_full + 0.5 * total_partial) / total_slots, 3),
            },
            "habits": habits,
            "patterns": patterns["patterns"],
            "main_pattern": _select_main_pattern(patterns["patterns"]),
        }
        result["output_markdown"] = _render_weekly_review(result)
        return result

    def pause_habit(self, query: str, *, source: str = "cli", notes: str | None = None) -> dict[str, Any]:
        resolved = self.resolve_habit(query)
        if resolved["status"] != "success":
            return resolved
        habit = resolved["habit"]
        now = _utc_now()
        self.connection.execute(
            "UPDATE habit_definitions SET status = ?, updated_at_utc = ? WHERE id = ?",
            ("paused", now, habit["id"]),
        )
        self._insert_event(habit["id"], _business_today(), EVENT_PAUSED, source, notes, now)
        self.connection.commit()
        return {"status": "success", "habit": self.get_definition(habit["id"])}

    def mark_done(
        self,
        query: str,
        *,
        target_date: date | None = None,
        mode: str = "full",
        source: str = "cli",
        notes: str | None = None,
    ) -> dict[str, Any]:
        if mode not in {"full", "partial", "minimum"}:
            return {"status": "config_missing", "error": "mode must be full, partial, or minimum."}
        event_type = EVENT_DONE_FULL if mode == "full" else EVENT_DONE_PARTIAL
        return self._set_final_status(query, event_type, target_date or _business_today(), source, notes)

    def skip_habit(
        self,
        query: str,
        *,
        target_date: date | None = None,
        source: str = "cli",
        notes: str | None = None,
    ) -> dict[str, Any]:
        return self._set_final_status(query, EVENT_SKIPPED, target_date or _business_today(), source, notes)

    def weekly_report(self, week_start: date) -> dict[str, Any]:
        week_end = week_start + timedelta(days=7)
        habits = []
        for habit in self.list_definitions(include_paused=True):
            first_trackable_day = _date_from_iso(habit["created_at_utc"]) or week_start
            day_statuses = []
            for offset in range(7):
                day = week_start + timedelta(days=offset)
                daily = self._daily_status(habit["id"], day)
                final_status = daily["final_status"]
                if habit["status"] == "active" and final_status is None and _is_scheduled_for_day(habit, day) and first_trackable_day <= day < _business_today():
                    final_status = EVENT_MISSED
                day_statuses.append(
                    {
                        "date": day.isoformat(),
                        "final_status": final_status,
                        "source": daily["source"],
                        "notes": daily["notes"],
                    }
                )
            full_count = sum(1 for item in day_statuses if item["final_status"] == EVENT_DONE_FULL)
            partial_count = sum(1 for item in day_statuses if item["final_status"] == EVENT_DONE_PARTIAL)
            skipped_count = sum(1 for item in day_statuses if item["final_status"] == EVENT_SKIPPED)
            missed_count = sum(1 for item in day_statuses if item["final_status"] == EVENT_MISSED)
            latest_trackable_day = min(week_end - timedelta(days=1), _business_today())
            if habit["status"] == "active":
                trackable_day_count = 0
                for item in day_statuses:
                    item_day = date.fromisoformat(item["date"])
                    if item["final_status"] is not None:
                        trackable_day_count += 1
                        continue
                    if item_day < first_trackable_day:
                        continue
                    if item_day <= latest_trackable_day and _is_scheduled_for_day(habit, item_day):
                        trackable_day_count += 1
            else:
                trackable_day_count = sum(1 for item in day_statuses if item["final_status"] is not None)
            streak_date = self._weekly_streak_anchor(habit["id"], week_start, min(week_end - timedelta(days=1), _business_today()))
            habits.append(
                {
                    "id": habit["id"],
                    "name": habit["name"],
                    "status": habit["status"],
                    "target_time": habit["target_time"],
                    "salience": habit.get("salience", 3),
                    "category": habit.get("category"),
                    "current_streak": self._streak_through(habit["id"], streak_date),
                    "full_count": full_count,
                    "partial_count": partial_count,
                    "skipped_count": skipped_count,
                    "missed_count": missed_count,
                    "trackable_day_count": trackable_day_count,
                    "full_rate": round(full_count / max(trackable_day_count, 1), 3),
                    "days": day_statuses,
                }
            )
        return {
            "status": "success",
            "week_start_berlin": week_start.isoformat(),
            "week_end_berlin": week_end.isoformat(),
            "habits": habits,
        }

    def handle_text(self, text: str, *, target_date: date | None = None, source: str = "telegram") -> dict[str, Any]:
        raw = text.strip()
        normalized = _normalize(raw)
        day = target_date or _business_today()
        if not raw:
            return {"status": "config_missing", "error": "Text is required."}
        if "status" in normalized:
            return self.status(day)
        if normalized.startswith("neuer habit ") or normalized.startswith("new habit "):
            return self._handle_add_text(raw)
        if "skip" in normalized or "auslassen" in normalized:
            query, notes = _split_notes(_remove_words(raw, {"skip", "auslassen", "heute"}))
            return self.skip_habit(query, target_date=day, source=source, notes=notes)
        if any(word in normalized for word in ("erledigt", "done", "full", "partial", "minimum", "minimal")):
            mode = "partial" if any(word in normalized for word in ("partial", "minimum", "minimal")) else "full"
            query, notes = _split_notes(_remove_words(raw, {"erledigt", "done", "full", "partial", "minimum", "minimal", "heute"}))
            return self.mark_done(query, target_date=day, mode=mode, source=source, notes=notes)
        if "heute" in normalized or normalized in {"habits", "habit"}:
            return self.today(day)
        return {
            "status": "not_found",
            "error": "Habit command not recognized.",
            "examples": [
                "habit status",
                "habits heute",
                "morgenroutine erledigt",
                "klimmzug skip heute, zu muede",
                "neuer habit Lesen taeglich 22:00",
            ],
        }

    def get_definition(self, habit_id: str) -> dict[str, Any] | None:
        row = self.connection.execute("SELECT * FROM habit_definitions WHERE id = ?", (habit_id,)).fetchone()
        if not row:
            return None
        return self._row_to_definition(row)

    def resolve_habit(self, query: str) -> dict[str, Any]:
        normalized_query = _normalize(query)
        if not normalized_query:
            return {"status": "config_missing", "error": "Habit reference is required."}

        exact_matches = []
        fuzzy_matches = []
        for habit in self.list_definitions(include_paused=True):
            search_terms = {habit["id"], habit["name"], *habit["aliases"]}
            normalized_terms = {_normalize(term) for term in search_terms}
            if normalized_query in normalized_terms:
                exact_matches.append(habit)
                continue
            if any(normalized_query in term or term in normalized_query for term in normalized_terms):
                fuzzy_matches.append(habit)

        matches = exact_matches or fuzzy_matches
        unique = {habit["id"]: habit for habit in matches}
        if len(unique) == 1:
            return {"status": "success", "habit": next(iter(unique.values())), "error": None}
        if len(unique) > 1:
            return {
                "status": "ambiguous",
                "error": f"Habit reference matched multiple habits: {', '.join(habit['name'] for habit in unique.values())}",
                "matches": list(unique.values()),
            }
        return {"status": "not_found", "error": f"Habit was not found: {query}"}

    def _set_final_status(
        self,
        query: str,
        final_status: str,
        target_date: date,
        source: str,
        notes: str | None,
    ) -> dict[str, Any]:
        if final_status not in FINAL_STATUSES:
            return {"status": "config_missing", "error": f"Unsupported final status: {final_status}"}
        resolved = self.resolve_habit(query)
        if resolved["status"] != "success":
            return resolved
        habit = resolved["habit"]
        now = _utc_now()
        self._insert_event(habit["id"], target_date, final_status, source, notes, now)
        self.connection.execute(
            """
            INSERT INTO habit_daily_status (
                habit_id, business_date_berlin, final_status, source, notes, updated_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(habit_id, business_date_berlin) DO UPDATE SET
                final_status = excluded.final_status,
                source = excluded.source,
                notes = excluded.notes,
                updated_at_utc = excluded.updated_at_utc
            """,
            (habit["id"], target_date.isoformat(), final_status, source, notes, now),
        )
        self.connection.commit()
        return {
            "status": "success",
            "habit_id": habit["id"],
            "habit_name": habit["name"],
            "business_date_berlin": target_date.isoformat(),
            "final_status": final_status,
            "current_streak": self._streak_through(habit["id"], target_date),
        }

    def _insert_event(
        self,
        habit_id: str,
        target_date: date,
        event_type: str,
        source: str,
        notes: str | None,
        created_at_utc: str,
        *,
        failure_mode: str | None = None,
        recovery_used: bool = False,
    ) -> None:
        self.connection.execute(
            """
            INSERT INTO habit_events (
                habit_id, business_date_berlin, event_type, source, notes, created_at_utc,
                failure_mode, recovery_used, event_uuid, recorded_at_utc, effective_at_local, actor
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                habit_id,
                target_date.isoformat(),
                event_type,
                source,
                notes,
                created_at_utc,
                failure_mode,
                1 if recovery_used else 0,
                str(uuid.uuid4()),
                created_at_utc,
                target_date.isoformat(),
                source,
            ),
        )

    def _daily_status(self, habit_id: str, target_date: date) -> dict[str, Any]:
        row = self.connection.execute(
            """
            SELECT final_status, source, notes, updated_at_utc
            FROM habit_daily_status
            WHERE habit_id = ? AND business_date_berlin = ?
            """,
            (habit_id, target_date.isoformat()),
        ).fetchone()
        if not row:
            return {
                "final_status": None,
                "source": None,
                "notes": None,
                "updated_at_utc": None,
            }
        return dict(row)

    def _relapses_for_day(self, target_date: date) -> list[dict[str, Any]]:
        rows = self.connection.execute(
            """
            SELECT r.habit_id, h.name, r.trigger_context, r.replacement_used, r.severity, r.notes
            FROM habit_relapses r
            LEFT JOIN habit_definitions h ON h.id = r.habit_id
            WHERE r.business_date_berlin = ?
            ORDER BY h.target_time IS NULL, h.target_time, h.name
            """,
            (target_date.isoformat(),),
        ).fetchall()
        return [dict(row) for row in rows]

    def _streak_through(self, habit_id: str, target_date: date) -> int:
        streak = 0
        cursor = target_date
        if not self._day_keeps_streak(habit_id, cursor):
            cursor -= timedelta(days=1)
        while self._day_keeps_streak(habit_id, cursor):
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def _day_keeps_streak(self, habit_id: str, target_date: date) -> bool:
        final_status = self._daily_status(habit_id, target_date)["final_status"]
        if final_status == EVENT_DONE_FULL:
            return True
        return self._day_used_recovery(habit_id, target_date)

    def _day_used_recovery(self, habit_id: str, target_date: date) -> bool:
        row = self.connection.execute(
            """
            SELECT 1 FROM habit_events
            WHERE habit_id = ? AND business_date_berlin = ? AND recovery_used = 1
            LIMIT 1
            """,
            (habit_id, target_date.isoformat()),
        ).fetchone()
        return row is not None

    def _weekly_streak_anchor(self, habit_id: str, week_start: date, latest_day: date) -> date:
        cursor = latest_day
        while cursor >= week_start and self._daily_status(habit_id, cursor)["final_status"] is None:
            cursor -= timedelta(days=1)
        return cursor

    def _row_to_definition(self, row: sqlite3.Row) -> dict[str, Any]:
        keys = row.keys() if hasattr(row, "keys") else []
        habit_type = row["habit_type"] if "habit_type" in keys else None
        failure_modes_raw = row["failure_modes_json"] if "failure_modes_json" in keys else None
        replacement_raw = row["replacement_actions_json"] if "replacement_actions_json" in keys else None
        recovery_raw = row["recovery_rule_json"] if "recovery_rule_json" in keys else None
        trigger_raw = row["trigger_window_json"] if "trigger_window_json" in keys else None
        schedule_raw = row["schedule_rule_json"] if "schedule_rule_json" in keys else None
        briefing_raw = row["briefing_policy_json"] if "briefing_policy_json" in keys else None
        return {
            "id": row["id"],
            "name": row["name"],
            "status": row["status"],
            "frequency": row["frequency"],
            "target_time": row["target_time"],
            "routine_ref": row["routine_ref"],
            "minimum_version": json.loads(row["minimum_version_json"]),
            "full_version": json.loads(row["full_version_json"]),
            "aliases": json.loads(row["aliases_json"]),
            "habit_type": habit_type or DEFAULT_HABIT_TYPE,
            "failure_modes": json.loads(failure_modes_raw) if failure_modes_raw else None,
            "replacement_actions": json.loads(replacement_raw) if replacement_raw else None,
            "recovery_rule": json.loads(recovery_raw) if recovery_raw else None,
            "trigger_window": json.loads(trigger_raw) if trigger_raw else None,
            "timezone": row["timezone"] if "timezone" in keys else "Europe/Berlin",
            "start_date_berlin": row["start_date_berlin"] if "start_date_berlin" in keys else None,
            "end_date_berlin": row["end_date_berlin"] if "end_date_berlin" in keys else None,
            "schedule_rule": json.loads(schedule_raw) if schedule_raw else None,
            "category": row["category"] if "category" in keys else None,
            "salience": row["salience"] if "salience" in keys else 3,
            "briefing_policy": json.loads(briefing_raw) if briefing_raw else None,
            "created_at_utc": row["created_at_utc"],
            "updated_at_utc": row["updated_at_utc"],
        }

    def _handle_add_text(self, text: str) -> dict[str, Any]:
        body = re.sub(r"^\s*(neuer|new)\s+habit\s+", "", text, flags=re.IGNORECASE).strip()
        time_match = re.search(r"(\d{2}:\d{2})", body)
        target_time = time_match.group(1) if time_match else None
        name = body
        if time_match:
            name = body[: time_match.start()].strip()
        name = re.sub(r"\b(täglich|taeglich|daily|jeden tag)\b", "", name, flags=re.IGNORECASE).strip()
        return self.add_habit(name=name, target_time=target_time, frequency="daily")



def _is_scheduled_for_day(habit: dict[str, Any], day: date) -> bool:
    start = _date_from_iso(habit.get("start_date_berlin"))
    end = _date_from_iso(habit.get("end_date_berlin"))
    if start and day < start:
        return False
    if end and day > end:
        return False

    rule = habit.get("schedule_rule") or {}
    weekdays = rule.get("weekdays") if isinstance(rule, dict) else None
    if weekdays is not None:
        try:
            return day.weekday() in {int(item) for item in weekdays}
        except (TypeError, ValueError):
            return False

    frequency = habit.get("frequency") or "daily"
    if frequency == "daily":
        return True
    if frequency == "weekly":
        # Weekly habits need an explicit schedule before EOS auto-prompts or auto-misses them.
        return False
    return True


def _schedule_rule_from_weekdays(schedule_weekdays: list[int] | None) -> dict[str, Any] | None:
    if schedule_weekdays is None:
        return None
    weekdays = sorted({int(day) for day in schedule_weekdays})
    if any(day < 0 or day > 6 for day in weekdays):
        raise ValueError("schedule_weekdays must contain integers 0..6 where Monday=0.")
    return {"weekdays": weekdays}


def _select_weekly_review_habits(habits: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    return sorted(
        habits,
        key=lambda habit: (
            -(habit.get("missed_count", 0) + habit.get("skipped_count", 0)),
            -habit.get("partial_count", 0),
            -habit.get("salience", 3),
            habit.get("name", ""),
        ),
    )[:limit]

def _unique_habit_id(connection: sqlite3.Connection, name: str) -> str:
    base = "habit-" + re.sub(r"[^a-z0-9]+", "-", _normalize(name)).strip("-")
    candidate = base or "habit-custom"
    suffix = 2
    while connection.execute("SELECT 1 FROM habit_definitions WHERE id = ?", (candidate,)).fetchone():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _aliases_for(habit_id: str, name: str) -> list[str]:
    aliases = {habit_id, name, name.replace("Haengenlassen an der ", ""), name.replace("Routine", "routine")}
    normalized_name = _normalize(name)
    if "morgen" in normalized_name:
        aliases.update({"morgen", "morgenroutine", "morning"})
    if "abend" in normalized_name:
        aliases.update({"abend", "abendroutine", "evening"})
    if "klimmzug" in normalized_name or "hang" in normalized_name:
        aliases.update({"klimmzug", "klimmzugstange", "hang", "pullup"})
    return sorted(alias for alias in aliases if alias)


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", ascii_value.lower()).strip()


def _remove_words(text: str, words: set[str]) -> str:
    result = text
    for word in words:
        result = re.sub(rf"\b{re.escape(word)}\b", " ", result, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", result).strip(" ,")


def _split_notes(text: str) -> tuple[str, str | None]:
    if "," not in text:
        return text.strip(), None
    query, notes = text.split(",", 1)
    return query.strip(), notes.strip() or None


def _render_daily_summary(result: dict[str, Any]) -> str:
    counts = result["counts"]
    happened = _habit_names_by_state(result["habits"], {EVENT_DONE_FULL, EVENT_DONE_PARTIAL})
    not_happened = _habit_names_by_state(result["habits"], {EVENT_SKIPPED, EVENT_MISSED, None})
    lines = [
        f"# Habit-Tagescheck {result['business_date_berlin']}",
        "",
        "## Kurzstatus",
        (
            f"- Voll: {counts[EVENT_DONE_FULL]}, Teil/Recovery: {counts[EVENT_DONE_PARTIAL]}, "
            f"Ausgelassen: {counts[EVENT_SKIPPED]}, Verfehlt: {counts[EVENT_MISSED]}, "
            f"Offen: {counts['pending']}"
        ),
        f"- Rueckfaelle: {result['relapse_count']}",
        "",
        "## Was heute passiert ist",
    ]
    if happened:
        lines.append(f"- Erledigt/gerettet: {_format_limited_names(happened, limit=4)}")
    else:
        lines.append("- Noch nichts als erledigt oder Recovery markiert.")
    lines.extend(["", "## Was heute nicht passiert ist"])
    if not_happened:
        lines.append(f"- Offen/ausgelassen/verfehlt: {_format_limited_names(not_happened, limit=5)}")
    else:
        lines.append("- Keine offenen oder verfehlten Gewohnheiten im Tagesstand.")
    lines.extend(["", "## Morgen besser"])
    if not_happened or counts["pending"] or counts[EVENT_MISSED] or counts[EVENT_SKIPPED]:
        focus = not_happened[0] if not_happened else "die wichtigste offene Gewohnheit"
        lines.append(f"- Nicht alle Gewohnheiten diskutieren: morgen zuerst nur {focus} minimal absichern.")
        lines.append("- Im Abendgespraech klaeren: Was lief gut? Was ist ausgefallen? Welche eine Barriere macht morgen leichter?")
    elif result["relapse_count"]:
        lines.append("- Rueckfall-Trigger notieren und morgen eine konkrete Barriere setzen.")
    else:
        lines.append("- Tag stabil halten; keine neue Gewohnheit erzwingen.")
    if result["relapses"]:
        lines.extend(["", "## Rueckfaelle"])
        for relapse in result["relapses"][:3]:
            replacement = relapse.get("replacement_used") or "keine Ersatzhandlung"
            lines.append(
                f"- {relapse.get('name') or relapse['habit_id']}: "
                f"{relapse['trigger_context']} / {relapse['severity']} / {replacement}"
            )
        remaining = len(result["relapses"]) - 3
        if remaining > 0:
            lines.append(f"- + {remaining} weitere Rueckfaelle im Log.")
    return "\n".join(lines) + "\n"


def _render_weekly_review(result: dict[str, Any]) -> str:
    totals = result["totals"]
    lines = [
        f"# Habit-Wochenreview {result['week_start_berlin']} bis {result['week_end_inclusive_berlin']}",
        "",
        "## Woche in Zahlen",
        (
            f"- Voll: {totals['full']}, Teil/Recovery: {totals['partial']}, "
            f"Ausgelassen: {totals['skipped']}, Verfehlt: {totals['missed']}"
        ),
        f"- Gewichtete Erfuellungsrate: {round(totals['completion_rate'] * 100)}%",
        "",
        "## Auffaellige Gewohnheiten",
    ]
    visible_habits = _select_weekly_review_habits(result["habits"], limit=5)
    if visible_habits:
        for habit in visible_habits:
            lines.append(
                f"- {habit['name']}: {round(habit['completion_rate'] * 100)}% "
                f"({habit['full_count']} voll, {habit['partial_count']} teil, "
                f"{habit['skipped_count']} ausgelassen, {habit['missed_count']} verfehlt)"
            )
        remaining = len(result["habits"]) - len(visible_habits)
        if remaining > 0:
            lines.append(f"- + {remaining} weitere Gewohnheiten bleiben im Log.")
    else:
        lines.append("- Keine auffaellige Gewohnheit im Wochenfenster.")
    lines.extend(["", "## Wichtigstes Muster"])
    main_pattern = result.get("main_pattern")
    if main_pattern:
        lines.append(f"- {main_pattern['implication']}")
    else:
        lines.append("- Kein starkes Muster erkannt; System stabil halten und weiter Daten sammeln.")
    lines.extend(
        [
            "",
            "## Empfehlung fuer naechste Woche",
            "- Maximal eine Gewohnheit veraendern oder eine Barriere fuer ein wiederkehrendes Muster setzen.",
            "- Keine neuen Habits hinzufuegen, wenn offene/missed Tage dominieren.",
        ]
    )
    return "\n".join(lines) + "\n"


def _select_main_pattern(patterns: list[dict[str, Any]]) -> dict[str, Any] | None:
    severity_rank = {"major": 0, "moderate": 1, "info": 2}
    if not patterns:
        return None
    return sorted(patterns, key=lambda item: (severity_rank.get(item.get("severity"), 9), item.get("key") or ""))[0]


def _habit_names_by_state(habits: list[dict[str, Any]], states: set[str | None]) -> list[str]:
    names = []
    for habit in habits:
        if habit.get("scheduled_today") is False and habit.get("final_status") is None:
            continue
        if habit.get("final_status") in states:
            names.append(str(habit["name"]))
    return names


def _format_limited_names(names: list[str], *, limit: int) -> str:
    visible = names[:limit]
    suffix = len(names) - len(visible)
    rendered = ", ".join(visible)
    if suffix > 0:
        return f"{rendered} (+ {suffix} weitere)"
    return rendered


def _business_today() -> date:
    return datetime.now(BERLIN).date()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _date_from_iso(raw: str | None) -> date | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        return None
