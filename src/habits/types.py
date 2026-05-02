from __future__ import annotations

from enum import Enum


class HabitType(str, Enum):
    BUILD = "build"
    REDUCE = "reduce"
    MAINTAIN = "maintain"
    RECOVERY = "recovery"


HABIT_TYPES = tuple(member.value for member in HabitType)
DEFAULT_HABIT_TYPE = HabitType.BUILD.value


class RelapseSeverity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"


RELAPSE_SEVERITIES = tuple(member.value for member in RelapseSeverity)


def coerce_habit_type(value: str | None) -> str:
    if value is None or value == "":
        return DEFAULT_HABIT_TYPE
    if value not in HABIT_TYPES:
        raise ValueError(
            f"Unknown habit_type {value!r}. Allowed: {HABIT_TYPES}."
        )
    return value


def coerce_severity(value: str | None) -> str:
    if value is None or value == "":
        return RelapseSeverity.MODERATE.value
    if value not in RELAPSE_SEVERITIES:
        raise ValueError(
            f"Unknown severity {value!r}. Allowed: {RELAPSE_SEVERITIES}."
        )
    return value


__all__ = [
    "DEFAULT_HABIT_TYPE",
    "HABIT_TYPES",
    "HabitType",
    "RELAPSE_SEVERITIES",
    "RelapseSeverity",
    "coerce_habit_type",
    "coerce_severity",
]
