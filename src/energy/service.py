from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from src.energy.models import EnergyLog


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class EnergyService:
    @staticmethod
    def log(energy_log: EnergyLog, *, connection: Any) -> dict[str, Any]:
        connection.execute(
            """
            INSERT OR REPLACE INTO daily_energy_logs
                (local_date, timestamp_utc, sleep_quality, energy_level,
                 physical_fatigue, mental_load, stress, motivation, soreness,
                 notes_json, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                energy_log.local_date,
                _now_utc(),
                energy_log.sleep_quality,
                energy_log.energy_level,
                energy_log.physical_fatigue,
                energy_log.mental_load,
                energy_log.stress,
                energy_log.motivation,
                energy_log.soreness,
                json.dumps(energy_log.notes) if energy_log.notes else None,
                energy_log.source,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM daily_energy_logs WHERE local_date = ? AND source = ?",
            (energy_log.local_date, energy_log.source),
        ).fetchone()
        return dict(row) if row else energy_log.to_dict()

    @staticmethod
    def today(*, connection: Any, source: str = "cli") -> dict[str, Any] | None:
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo("Europe/Berlin")
        except Exception:
            import pytz
            tz = pytz.timezone("Europe/Berlin")
        today = datetime.now(tz).date().isoformat()
        row = connection.execute(
            "SELECT * FROM daily_energy_logs WHERE local_date = ? AND source = ?",
            (today, source),
        ).fetchone()
        return dict(row) if row else None

    @staticmethod
    def history(days: int, *, connection: Any) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            SELECT * FROM daily_energy_logs
            ORDER BY local_date DESC
            LIMIT ?
            """,
            (days,),
        ).fetchall()
        return [dict(r) for r in rows]
