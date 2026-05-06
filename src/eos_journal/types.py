from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DailySignalInput:
    date: str
    sleep_quality: int | None
    energy_level: int | None
    mood_level: int | None
    stress_level: int | None
    deep_work_done: bool | None
    training_done: bool | None
    evening_shutdown_done: bool | None
    open_task_count: int | None
    calendar_load_score: float | None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "DailySignalInput":
        return cls(
            date=str(payload["date"]),
            sleep_quality=_optional_int(payload.get("sleep_quality")),
            energy_level=_optional_int(payload.get("energy_level")),
            mood_level=_optional_int(payload.get("mood_level")),
            stress_level=_optional_int(payload.get("stress_level")),
            deep_work_done=_optional_bool(payload.get("deep_work_done")),
            training_done=_optional_bool(payload.get("training_done")),
            evening_shutdown_done=_optional_bool(payload.get("evening_shutdown_done")),
            open_task_count=_optional_int(payload.get("open_task_count")),
            calendar_load_score=_optional_float(payload.get("calendar_load_score")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SignalInterpretation:
    status: str
    tone: str
    risk_flags: list[str]
    reasons: list[str]
    score: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JournalCoachOutput:
    status: str
    tone: str
    headline: str
    message: str
    minimum_day_actions: list[str]
    risks: list[str]
    notification_allowed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HabitTrendOutput:
    trend_summary: list[str]
    risk_flags: list[str]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)
