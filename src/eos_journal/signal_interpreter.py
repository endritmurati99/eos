from __future__ import annotations

from src.eos_journal.types import DailySignalInput, SignalInterpretation

STATUS_STABLE = "stable"
STATUS_TIGHT = "tight"
STATUS_OVERLOADED = "overloaded"
STATUS_RECOVERY_NEEDED = "recovery_needed"

TONE_BY_STATUS = {
    STATUS_STABLE: "klar",
    STATUS_TIGHT: "ruhig-operativ",
    STATUS_OVERLOADED: "reduziert",
    STATUS_RECOVERY_NEEDED: "recovery",
}


def interpret_daily_signals(signal: DailySignalInput) -> SignalInterpretation:
    risks: list[str] = []
    reasons: list[str] = []
    score = 0

    score += _add_if(risks, reasons, "low_sleep", "Schlaf niedrig.", signal.sleep_quality is not None and signal.sleep_quality <= 3, 2)
    score += _add_if(risks, reasons, "low_energy", "Energie niedrig.", signal.energy_level is not None and signal.energy_level <= 3, 2)
    score += _add_if(risks, reasons, "low_mood", "Stimmung niedrig.", signal.mood_level is not None and signal.mood_level <= 3, 2)
    score += _add_if(risks, reasons, "high_stress", "Stress hoch.", signal.stress_level is not None and signal.stress_level >= 8, 2)
    score += _add_if(
        risks,
        reasons,
        "high_calendar_load",
        "Kalenderlast hoch.",
        signal.calendar_load_score is not None and signal.calendar_load_score >= 0.85,
        2,
    )
    score += _add_if(
        risks,
        reasons,
        "too_many_open_tasks",
        "Viele offene Aufgaben.",
        signal.open_task_count is not None and signal.open_task_count >= 12,
        2,
    )
    score += _add_if(risks, reasons, "missed_training", "Training offen.", signal.training_done is False, 1)
    score += _add_if(risks, reasons, "no_deep_work", "Deep Work offen.", signal.deep_work_done is False, 1)
    score += _add_if(
        risks,
        reasons,
        "missed_evening_shutdown",
        "Abend Shutdown offen.",
        signal.evening_shutdown_done is False,
        1,
    )

    status = _status_for(signal, risks, score)
    return SignalInterpretation(
        status=status,
        tone=TONE_BY_STATUS[status],
        risk_flags=risks,
        reasons=reasons,
        score=score,
    )


def _add_if(
    risks: list[str],
    reasons: list[str],
    flag: str,
    reason: str,
    condition: bool,
    weight: int,
) -> int:
    if not condition:
        return 0
    risks.append(flag)
    reasons.append(reason)
    return weight


def _status_for(signal: DailySignalInput, risks: list[str], score: int) -> str:
    recovery_markers = {
        "low_sleep",
        "low_energy",
        "low_mood",
        "high_stress",
    }
    recovery_count = len(recovery_markers.intersection(risks))
    if recovery_count >= 3:
        return STATUS_RECOVERY_NEEDED
    if (
        signal.sleep_quality is not None
        and signal.energy_level is not None
        and signal.stress_level is not None
        and signal.sleep_quality <= 3
        and signal.energy_level <= 3
        and signal.stress_level >= 7
    ):
        return STATUS_RECOVERY_NEEDED
    if "high_calendar_load" in risks or "too_many_open_tasks" in risks:
        return STATUS_OVERLOADED
    if score > 0:
        return STATUS_TIGHT
    return STATUS_STABLE
