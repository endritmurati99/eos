from __future__ import annotations

from src.eos_journal.signal_interpreter import (
    STATUS_OVERLOADED,
    STATUS_RECOVERY_NEEDED,
    interpret_daily_signals,
)
from src.eos_journal.types import DailySignalInput

NORMAL_DAY_ACTIONS = [
    "1 Deep Work Block",
    "Mailblock",
    "Sport/Routine",
]

BAD_DAY_ACTIONS = [
    "20 Minuten Bewegung",
    "1 kleiner Fokusblock",
    "Abend Shutdown",
]

OVERLOADED_DAY_ACTIONS = [
    "Nur Pflichttermine",
    "1 wichtigste Aufgabe",
    "keine Zusatzbloecke",
]


def recommend_minimum_day(signal: DailySignalInput) -> list[str]:
    interpretation = interpret_daily_signals(signal)
    if interpretation.status == STATUS_OVERLOADED:
        return list(OVERLOADED_DAY_ACTIONS)
    if interpretation.status == STATUS_RECOVERY_NEEDED:
        return list(BAD_DAY_ACTIONS)
    return list(NORMAL_DAY_ACTIONS)
