from __future__ import annotations

from statistics import mean

from src.eos_journal.types import DailySignalInput, HabitTrendOutput


def summarize_habit_trends(days: list[DailySignalInput]) -> HabitTrendOutput:
    ordered = sorted(days, key=lambda item: item.date)
    trend_summary: list[str] = []
    risk_flags: list[str] = []
    recommendations: list[str] = []

    if not ordered:
        return HabitTrendOutput(
            trend_summary=["Keine Wochensignale vorhanden."],
            risk_flags=[],
            recommendations=["Naechste Woche mindestens drei Check-ins sammeln."],
        )

    if _false_count([day.training_done for day in ordered]) >= 3:
        trend_summary.append("Training wurde wiederholt verpasst.")
        risk_flags.append("training_repeatedly_missed")
        recommendations.append("Training als 20-Minuten-Minimum planen.")

    if _true_count([day.deep_work_done for day in ordered]) >= 4:
        trend_summary.append("Deep Work war stabil.")
        recommendations.append("Deep Work Block beibehalten.")

    sleep_values = [day.sleep_quality for day in ordered if day.sleep_quality is not None]
    if sleep_values and (max(sleep_values) - min(sleep_values) >= 4 or sum(value <= 3 for value in sleep_values) >= 2):
        trend_summary.append("Schlaf war instabil.")
        risk_flags.append("sleep_unstable")
        recommendations.append("Abend Shutdown als Schutzblock behandeln.")

    mood_values = [day.mood_level for day in ordered if day.mood_level is not None]
    if _declining(mood_values):
        trend_summary.append("Stimmung faellt ueber die Woche.")
        risk_flags.append("mood_declining")
        recommendations.append("Naechste Woche Last frueh reduzieren.")

    overload_markers = [
        _is_overload(day)
        for day in ordered
    ]
    if _rising_bool(overload_markers):
        trend_summary.append("Ueberlastungsrisiko steigt.")
        risk_flags.append("overload_risk_rising")
        recommendations.append("Keine Zusatzbloecke auf volle Kalendertage legen.")

    if not trend_summary:
        trend_summary.append("Woche wirkt stabil.")
        recommendations.append("Aktuellen Rhythmus halten.")

    return HabitTrendOutput(
        trend_summary=trend_summary,
        risk_flags=risk_flags,
        recommendations=recommendations,
    )


def _false_count(values: list[bool | None]) -> int:
    return sum(value is False for value in values)


def _true_count(values: list[bool | None]) -> int:
    return sum(value is True for value in values)


def _declining(values: list[int]) -> bool:
    if len(values) < 4:
        return False
    midpoint = len(values) // 2
    return mean(values[:midpoint]) - mean(values[midpoint:]) >= 1.5


def _is_overload(day: DailySignalInput) -> bool:
    return (
        day.calendar_load_score is not None
        and day.calendar_load_score >= 0.85
    ) or (
        day.open_task_count is not None
        and day.open_task_count >= 12
    )


def _rising_bool(values: list[bool]) -> bool:
    if len(values) < 4:
        return False
    midpoint = len(values) // 2
    return sum(values[midpoint:]) > sum(values[:midpoint]) or sum(values[-3:]) >= 2
