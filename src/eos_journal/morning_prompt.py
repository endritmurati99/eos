from __future__ import annotations

from src.eos_journal.minimum_day import recommend_minimum_day
from src.eos_journal.signal_interpreter import (
    STATUS_OVERLOADED,
    STATUS_RECOVERY_NEEDED,
    STATUS_STABLE,
    interpret_daily_signals,
)
from src.eos_journal.types import DailySignalInput, JournalCoachOutput


def generate_morning_prompt(signal: DailySignalInput) -> JournalCoachOutput:
    interpretation = interpret_daily_signals(signal)
    actions = recommend_minimum_day(signal)
    focus = _focus_for_status(interpretation.status)
    risk = interpretation.reasons[0] if interpretation.reasons else "Keine harte Gegenkraft sichtbar."
    minimum = actions[0]
    headline = _headline_for_status(interpretation.status)
    message = "\n".join(
        [
            f"Fokus: {focus}",
            f"Minimum: {minimum}.",
            f"Risiko: {risk}",
            "Zitat: Klein halten, klar bleiben.",
        ]
    )

    return JournalCoachOutput(
        status=interpretation.status,
        tone=interpretation.tone,
        headline=headline,
        message=message,
        minimum_day_actions=actions,
        risks=interpretation.risk_flags,
        notification_allowed=True,
        reason="morning_prompt_allowed",
    )


def _headline_for_status(status: str) -> str:
    if status == STATUS_STABLE:
        return "Heute: klarer Standardtag"
    if status == STATUS_OVERLOADED:
        return "Heute: Last reduzieren"
    if status == STATUS_RECOVERY_NEEDED:
        return "Heute: Minimum stabilisieren"
    return "Heute: eng, aber steuerbar"


def _focus_for_status(status: str) -> str:
    if status == STATUS_STABLE:
        return "Ein Deep Work Block vor neuen Inputs."
    if status == STATUS_OVERLOADED:
        return "Pflichttermine plus die wichtigste Aufgabe."
    if status == STATUS_RECOVERY_NEEDED:
        return "Einen kleinen Fokusblock sauber abschliessen."
    return "Eine wichtige Aufgabe vor Zusatzarbeit."
