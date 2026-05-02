from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import date, timedelta
from typing import Any


PATTERN_TIME_MISALIGNMENT = "habit_time_misalignment"
PATTERN_WEEKDAY_DROP = "weekday_drop"
PATTERN_TRIGGER_CLUSTER = "trigger_cluster"
PATTERN_RECOVERY_STREAK_SAVE = "recovery_streak_save"
PATTERN_REPLACEMENT_WORKS = "replacement_works"

PATTERN_KEYS = (
    PATTERN_TIME_MISALIGNMENT,
    PATTERN_WEEKDAY_DROP,
    PATTERN_TRIGGER_CLUSTER,
    PATTERN_RECOVERY_STREAK_SAVE,
    PATTERN_REPLACEMENT_WORKS,
)

LOOKBACK_DAYS = 28
WEEKDAY_LOOKBACK_WEEKS = 4
TRIGGER_CLUSTER_THRESHOLD = 3
TRIGGER_CLUSTER_WINDOW_DAYS = 14
TIME_MISALIGNMENT_THRESHOLD = 4
TIME_MISALIGNMENT_WINDOW_DAYS = 14
REPLACEMENT_RATE_THRESHOLD = 0.6
RECOVERY_SAVE_THRESHOLD = 2


@dataclass(frozen=True)
class PatternSignal:
    key: str
    severity: str
    habit_id: str | None
    evidence: dict[str, Any]
    implication: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def detect_patterns(
    connection: sqlite3.Connection,
    *,
    reference_date: date | None = None,
    lookback_days: int = LOOKBACK_DAYS,
) -> list[PatternSignal]:
    today = reference_date or date.today()
    window_start = today - timedelta(days=lookback_days - 1)

    signals: list[PatternSignal] = []
    signals.extend(_detect_time_misalignment(connection, today))
    signals.extend(_detect_weekday_drop(connection, today))
    signals.extend(_detect_trigger_cluster(connection, today))
    signals.extend(_detect_recovery_streak_save(connection, today))
    signals.extend(_detect_replacement_works(connection, today))
    return signals


def _detect_time_misalignment(connection: sqlite3.Connection, today: date) -> list[PatternSignal]:
    window_start = today - timedelta(days=TIME_MISALIGNMENT_WINDOW_DAYS - 1)
    rows = connection.execute(
        """
        SELECT habit_id, COUNT(*) AS missed_count
        FROM habit_daily_status
        WHERE final_status IN ('missed','skipped','done_partial')
          AND business_date_berlin >= ?
          AND business_date_berlin <= ?
        GROUP BY habit_id
        HAVING missed_count >= ?
        """,
        (window_start.isoformat(), today.isoformat(), TIME_MISALIGNMENT_THRESHOLD),
    ).fetchall()

    signals = []
    for row in rows:
        habit_id = row["habit_id"]
        target_time_row = connection.execute(
            "SELECT target_time, name FROM habit_definitions WHERE id = ?",
            (habit_id,),
        ).fetchone()
        if not target_time_row or not target_time_row["target_time"]:
            continue
        signals.append(
            PatternSignal(
                key=PATTERN_TIME_MISALIGNMENT,
                severity="moderate" if row["missed_count"] < TIME_MISALIGNMENT_THRESHOLD * 2 else "major",
                habit_id=habit_id,
                evidence={
                    "window_days": TIME_MISALIGNMENT_WINDOW_DAYS,
                    "missed_or_partial_count": row["missed_count"],
                    "target_time": target_time_row["target_time"],
                },
                implication=(
                    f"{target_time_row['name']} verfehlt {row['missed_count']} Mal in "
                    f"{TIME_MISALIGNMENT_WINDOW_DAYS} Tagen. Pruefe, ob Zielzeit zur Realitaet passt."
                ),
            )
        )
    return signals


def _detect_weekday_drop(connection: sqlite3.Connection, today: date) -> list[PatternSignal]:
    lookback_days = WEEKDAY_LOOKBACK_WEEKS * 7
    window_start = today - timedelta(days=lookback_days - 1)
    rows = connection.execute(
        """
        SELECT habit_id, business_date_berlin, final_status
        FROM habit_daily_status
        WHERE business_date_berlin >= ?
          AND business_date_berlin <= ?
        """,
        (window_start.isoformat(), today.isoformat()),
    ).fetchall()

    by_habit_weekday: dict[tuple[str, int], list[str]] = defaultdict(list)
    for row in rows:
        try:
            day = date.fromisoformat(row["business_date_berlin"])
        except ValueError:
            continue
        by_habit_weekday[(row["habit_id"], day.weekday())].append(row["final_status"])

    signals = []
    for (habit_id, weekday), statuses in by_habit_weekday.items():
        if len(statuses) < 2:
            continue
        non_full = sum(1 for status in statuses if status != "done_full")
        if non_full < 2:
            continue
        if non_full / len(statuses) < 0.75:
            continue
        habit_row = connection.execute(
            "SELECT name FROM habit_definitions WHERE id = ?",
            (habit_id,),
        ).fetchone()
        weekday_label = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")[weekday]
        signals.append(
            PatternSignal(
                key=PATTERN_WEEKDAY_DROP,
                severity="moderate",
                habit_id=habit_id,
                evidence={
                    "weekday": weekday_label,
                    "non_full_count": non_full,
                    "occurrence_count": len(statuses),
                },
                implication=(
                    f"{habit_row['name'] if habit_row else habit_id} kippt regelmaessig am "
                    f"{weekday_label} ({non_full}/{len(statuses)})."
                ),
            )
        )
    return signals


def _detect_trigger_cluster(connection: sqlite3.Connection, today: date) -> list[PatternSignal]:
    window_start = today - timedelta(days=TRIGGER_CLUSTER_WINDOW_DAYS - 1)
    rows = connection.execute(
        """
        SELECT habit_id, trigger_context
        FROM habit_relapses
        WHERE business_date_berlin >= ?
          AND business_date_berlin <= ?
          AND trigger_context IS NOT NULL
          AND trigger_context != ''
        """,
        (window_start.isoformat(), today.isoformat()),
    ).fetchall()

    counter: Counter[tuple[str, str]] = Counter()
    for row in rows:
        counter[(row["habit_id"], row["trigger_context"])] += 1

    signals = []
    for (habit_id, trigger), count in counter.items():
        if count < TRIGGER_CLUSTER_THRESHOLD:
            continue
        habit_row = connection.execute(
            "SELECT name FROM habit_definitions WHERE id = ?",
            (habit_id,),
        ).fetchone()
        signals.append(
            PatternSignal(
                key=PATTERN_TRIGGER_CLUSTER,
                severity="major" if count >= TRIGGER_CLUSTER_THRESHOLD * 2 else "moderate",
                habit_id=habit_id,
                evidence={
                    "trigger": trigger,
                    "count": count,
                    "window_days": TRIGGER_CLUSTER_WINDOW_DAYS,
                },
                implication=(
                    f"{habit_row['name'] if habit_row else habit_id}: Ausloeser '{trigger}' "
                    f"trat {count} Mal in {TRIGGER_CLUSTER_WINDOW_DAYS} Tagen auf. Setze gezielte Barriere."
                ),
            )
        )
    return signals


def _detect_recovery_streak_save(connection: sqlite3.Connection, today: date) -> list[PatternSignal]:
    window_start = today - timedelta(days=LOOKBACK_DAYS - 1)
    rows = connection.execute(
        """
        SELECT habit_id, COUNT(*) AS recovery_count
        FROM habit_events
        WHERE recovery_used = 1
          AND business_date_berlin >= ?
          AND business_date_berlin <= ?
        GROUP BY habit_id
        HAVING recovery_count >= ?
        """,
        (window_start.isoformat(), today.isoformat(), RECOVERY_SAVE_THRESHOLD),
    ).fetchall()

    signals = []
    for row in rows:
        habit_id = row["habit_id"]
        habit_row = connection.execute(
            "SELECT name FROM habit_definitions WHERE id = ?",
            (habit_id,),
        ).fetchone()
        signals.append(
            PatternSignal(
                key=PATTERN_RECOVERY_STREAK_SAVE,
                severity="info",
                habit_id=habit_id,
                evidence={
                    "recovery_count": row["recovery_count"],
                    "window_days": LOOKBACK_DAYS,
                },
                implication=(
                    f"{habit_row['name'] if habit_row else habit_id}: Recovery-Version hat den Streak "
                    f"{row['recovery_count']} Mal gerettet."
                ),
            )
        )
    return signals


def _detect_replacement_works(connection: sqlite3.Connection, today: date) -> list[PatternSignal]:
    window_start = today - timedelta(days=LOOKBACK_DAYS - 1)
    rows = connection.execute(
        """
        SELECT habit_id, replacement_used, severity
        FROM habit_relapses
        WHERE business_date_berlin >= ?
          AND business_date_berlin <= ?
          AND replacement_used IS NOT NULL
          AND replacement_used != ''
        """,
        (window_start.isoformat(), today.isoformat()),
    ).fetchall()

    grouped: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in rows:
        grouped[(row["habit_id"], row["replacement_used"])].append(row["severity"])

    signals = []
    for (habit_id, replacement), severities in grouped.items():
        total = len(severities)
        if total < 3:
            continue
        helpful = sum(1 for severity in severities if severity == "minor")
        rate = helpful / total
        if rate < REPLACEMENT_RATE_THRESHOLD:
            continue
        habit_row = connection.execute(
            "SELECT name FROM habit_definitions WHERE id = ?",
            (habit_id,),
        ).fetchone()
        signals.append(
            PatternSignal(
                key=PATTERN_REPLACEMENT_WORKS,
                severity="info",
                habit_id=habit_id,
                evidence={
                    "replacement": replacement,
                    "minor_rate": round(rate, 3),
                    "occurrences": total,
                },
                implication=(
                    f"{habit_row['name'] if habit_row else habit_id}: Ersatzhandlung '{replacement}' "
                    f"reduziert Schwere in {round(rate * 100)}% der Faelle."
                ),
            )
        )
    return signals


__all__ = [
    "LOOKBACK_DAYS",
    "PATTERN_KEYS",
    "PATTERN_RECOVERY_STREAK_SAVE",
    "PATTERN_REPLACEMENT_WORKS",
    "PATTERN_TIME_MISALIGNMENT",
    "PATTERN_TRIGGER_CLUSTER",
    "PATTERN_WEEKDAY_DROP",
    "PatternSignal",
    "detect_patterns",
]
