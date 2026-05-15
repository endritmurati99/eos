from __future__ import annotations

from src.eos_journal.calendar_briefing import CalendarBriefingContext, summarize_calendar_context
from src.eos_journal.minimum_day import recommend_minimum_day
from src.eos_journal.signal_interpreter import interpret_daily_signals
from src.eos_journal.types import DailySignalInput, JournalCoachOutput


def generate_evening_review(
    signal: DailySignalInput,
    tomorrow_calendar: CalendarBriefingContext | None = None,
) -> JournalCoachOutput:
    interpretation = interpret_daily_signals(signal)
    actions = recommend_minimum_day(signal)
    calendar_lines = summarize_calendar_context(tomorrow_calendar)
    message = "\n".join(
        [
            f"Stabil: {_stable_line(signal)}",
            f"Offen: {_open_line(signal)}",
            *[f"Morgenkalender: {line.removeprefix('Kalender: ')}" for line in calendar_lines[:1]],
            *calendar_lines[1:],
            f"Energieverlust: {_energy_loss_line(interpretation.risk_flags)}",
            f"Morgen: {actions[0]}.",
        ]
    )

    return JournalCoachOutput(
        status=interpretation.status,
        tone=interpretation.tone,
        headline="Abend Review",
        message=message,
        minimum_day_actions=actions,
        risks=interpretation.risk_flags,
        notification_allowed=True,
        reason="evening_review_allowed",
    )


def _stable_line(signal: DailySignalInput) -> str:
    if signal.deep_work_done:
        return "Deep Work war erledigt."
    if signal.training_done:
        return "Training oder Routine war erledigt."
    if signal.evening_shutdown_done:
        return "Shutdown war erledigt."
    return "Ein kleiner Abschluss zaehlt."


def _open_line(signal: DailySignalInput) -> str:
    if signal.open_task_count is not None and signal.open_task_count > 0:
        return f"{signal.open_task_count} offene Aufgaben bleiben fuer Priorisierung."
    return "Keine offene Last gemeldet."


def _energy_loss_line(risks: list[str]) -> str:
    if "high_calendar_load" in risks:
        return "Kalenderlast war der groesste Treiber."
    if "too_many_open_tasks" in risks:
        return "Aufgabenlast war der groesste Treiber."
    if "high_stress" in risks:
        return "Stress war der groesste Treiber."
    if "low_sleep" in risks:
        return "Schlaf war der groesste Treiber."
    if "low_energy" in risks:
        return "Energie war begrenzt."
    return "Kein klarer Verlusttreiber gemeldet."
