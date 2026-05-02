from __future__ import annotations

from typing import Any

from src.intake.confidence import CONFIDENCE_HIGH, CONFIDENCE_MEDIUM, requires_confirmation
from src.intake.models import IntakeResult
from src.intake.normalizer import normalize_text, tokenize


_HABIT_NAME_HINTS: tuple[str, ...] = (
    "morgenroutine",
    "morning routine",
    "abendroutine",
    "evening routine",
    "klimmzug",
    "klimmzugstange",
    "hang",
    "haengen",
    "yoga",
    "skin care",
    "skincare",
    "infrarot",
    "kokosoel",
)

_HABIT_DONE_KEYWORDS: tuple[str, ...] = (
    "erledigt",
    "fertig",
    "done",
    "geschafft",
    "abgehakt",
    "complete",
    "completed",
)

_HABIT_PARTIAL_KEYWORDS: tuple[str, ...] = (
    "partial",
    "minimum",
    "minimal",
    "halb",
    "kurz",
    "reduziert",
)

_HABIT_SKIP_KEYWORDS: tuple[str, ...] = (
    "skip",
    "auslassen",
    "ausgelassen",
    "uebersprungen",
    "uebergehen",
    "nicht gemacht",
    "ausfall",
    "ausgefallen",
)

_HABIT_STATUS_KEYWORDS: tuple[str, ...] = (
    "habit status",
    "habits status",
    "habits heute",
    "habit heute",
    "wie stehen meine habits",
    "wie stehen die habits",
    "habit stand",
    "habits stand",
)

_DAILY_CHECKIN_KEYWORDS: tuple[str, ...] = (
    "energie checkin",
    "checkin",
    "check-in",
    "morgen check",
    "tagescheck",
    "wie geht es mir",
    "schlafqualitaet",
    "schlaf qualitaet",
    "energy",
    "energie heute",
)

_PLAN_REQUEST_KEYWORDS: tuple[str, ...] = (
    "plan mir",
    "plane mir",
    "plane heute",
    "plane morgen",
    "plan heute",
    "plan morgen",
    "tagesplan",
    "wie sieht mein tag aus",
    "wie sieht morgen aus",
    "was steht heute an",
    "was steht morgen an",
)

_TASK_CAPTURE_KEYWORDS: tuple[str, ...] = (
    "neue aufgabe",
    "neuer task",
    "new task",
    "todo",
    "to do",
    "to-do",
    "merken",
    "notiere",
    "erinner mich",
    "erinnere mich",
)

_CALENDAR_PROPOSAL_KEYWORDS: tuple[str, ...] = (
    "kalender vorschlag",
    "schlag mir vor",
    "schlage mir vor",
    "trag in den kalender",
    "trage in den kalender",
    "block fuer",
    "deep work block",
    "fokusblock",
    "schreib in kalender",
    "in kalender schreiben",
)

_REVIEW_REQUEST_KEYWORDS: tuple[str, ...] = (
    "review",
    "rueckblick",
    "wochenrueckblick",
    "weekly review",
    "wie war meine woche",
    "wie lief die woche",
    "wie war mein tag",
    "tagesreview",
    "tages review",
)

_HABIT_SCOPE_ALL_KEYWORDS: tuple[str, ...] = (
    "alles",
    "alle habits",
    "alle routinen",
    "alle drei",
    "everything",
)

_HABIT_RELAPSE_KEYWORDS: tuple[str, ...] = (
    "rueckfall",
    "rueckgefallen",
    "wieder gescrollt",
    "wieder geschrolt",
    "wieder gegessen",
    "wieder geraucht",
    "nochmal gemacht",
    "doch gemacht",
    "trotzdem gescrollt",
    "hab nachgegeben",
    "nachgegeben",
    "hab geschwacht",
    "war schwach",
)

_HABIT_RECOVERY_KEYWORDS: tuple[str, ...] = (
    "2 minuten",
    "zwei minuten",
    "2min",
    "minimalversion",
    "minimal version",
    "notfallversion",
    "notfall version",
    "reset gemacht",
    "two minute reset",
    "trotzdem kurz gemacht",
    "minimalroutine",
)

_HABIT_FAILURE_KEYWORDS: tuple[str, ...] = (
    "verschlafen",
    "vergessen",
    "keine zeit gehabt",
    "hatte keine zeit",
    "nicht geschafft",
    "nicht gemacht",
    "nicht hingekommen",
    "war zu muede",
    "war zu muede dafuer",
    "zu muede gewesen",
    "keine lust gehabt",
    "hatte keine lust",
    "ausgefallen wegen",
    "fiel aus wegen",
)

_FAILURE_MODE_HINTS: dict[str, str] = {
    "verschlafen": "verschlafen",
    "vergessen": "vergessen",
    "keine zeit": "keine_zeit",
    "keine lust": "keine_lust",
    "muede": "muede",
    "zu muede": "muede",
    "krank": "krank",
    "arbeit": "arbeit",
}

_ENERGY_FIELD_PATTERNS: tuple[tuple[str, ...], str] = (  # type: ignore[assignment]
    (("schlaf", "sleep", "schlafqualitaet"), "sleep_quality"),
    (("energie", "energy", "energielevel"), "energy_level"),
    (("stress",), "stress"),
    (("koerper", "koerpermued", "fatigue", "physisch", "muskelkater", "kater", "soreness"), "physical_fatigue"),
    (("mental", "kopf", "konzentration", "geistig"), "mental_load"),
    (("motivation", "motiviert", "lust"), "motivation"),
)


def _extract_energy_entities(normalized: str) -> dict[str, Any]:
    import re
    entities: dict[str, Any] = {}
    number_pattern = re.compile(r"(\d+)(?:\s*(?:/10|von\s*10))?")
    tokens = normalized.split()
    for i, token in enumerate(tokens):
        for keywords, field in _ENERGY_FIELD_PATTERNS:
            if any(kw in token for kw in keywords):
                for j in range(i + 1, min(i + 4, len(tokens))):
                    m = number_pattern.fullmatch(tokens[j])
                    if m:
                        val = int(m.group(1))
                        if 1 <= val <= 10:
                            entities[field] = val
                        break
                break
    numbers_found = number_pattern.findall(normalized)
    if not entities and len(numbers_found) == 1:
        val = int(numbers_found[0])
        if 1 <= val <= 10:
            entities["energy_level"] = val
    return entities


def _matches_any(normalized: str, keywords: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(keyword for keyword in keywords if keyword in normalized)


def _detect_habit_name(normalized: str) -> str | None:
    for hint in _HABIT_NAME_HINTS:
        if hint in normalized:
            return hint
    return None


def _detect_completion_mode(normalized: str) -> str | None:
    if _matches_any(normalized, _HABIT_PARTIAL_KEYWORDS):
        return "done_partial"
    if _matches_any(normalized, _HABIT_DONE_KEYWORDS):
        return "done_full"
    return None


def classify_intent(raw_text: str) -> IntakeResult:
    raw = (raw_text or "").strip()
    normalized = normalize_text(raw)

    if not raw:
        return IntakeResult(
            intent="unknown",
            confidence=0.0,
            entities={},
            requires_confirmation=True,
            confirmation_question="Eingabe ist leer. Bitte schreib mir, was du erfasst haben moechtest.",
            ambiguity="empty_input",
            raw_input=raw,
            normalized_input=normalized,
            matched_keywords=(),
        )

    if matched := _matches_any(normalized, _HABIT_STATUS_KEYWORDS):
        return IntakeResult(
            intent="habit_status",
            confidence=0.95,
            entities={},
            requires_confirmation=False,
            confirmation_question=None,
            ambiguity=None,
            raw_input=raw,
            normalized_input=normalized,
            matched_keywords=matched,
        )

    if matched := _matches_any(normalized, _HABIT_RELAPSE_KEYWORDS):
        habit_name = _detect_habit_name(normalized)
        entities: dict[str, Any] = {}
        if habit_name:
            entities["habit_hint"] = habit_name
        return IntakeResult(
            intent="habit_relapse",
            confidence=0.88,
            entities=entities,
            requires_confirmation=False,
            confirmation_question=None,
            ambiguity=None,
            raw_input=raw,
            normalized_input=normalized,
            matched_keywords=matched,
        )

    if matched := _matches_any(normalized, _HABIT_RECOVERY_KEYWORDS):
        habit_name = _detect_habit_name(normalized)
        entities = {}
        if habit_name:
            entities["habit_hint"] = habit_name
        return IntakeResult(
            intent="habit_recovery",
            confidence=0.87,
            entities=entities,
            requires_confirmation=False,
            confirmation_question=None,
            ambiguity=None,
            raw_input=raw,
            normalized_input=normalized,
            matched_keywords=matched,
        )

    if matched := _matches_any(normalized, _HABIT_FAILURE_KEYWORDS):
        habit_name = _detect_habit_name(normalized)
        entities = {}
        if habit_name:
            entities["habit_hint"] = habit_name
        for hint_text, canonical in _FAILURE_MODE_HINTS.items():
            if hint_text in normalized:
                entities["failure_mode"] = canonical
                break
        return IntakeResult(
            intent="habit_failure",
            confidence=0.84,
            entities=entities,
            requires_confirmation=False,
            confirmation_question=None,
            ambiguity=None,
            raw_input=raw,
            normalized_input=normalized,
            matched_keywords=matched,
        )

    if matched := _matches_any(normalized, _DAILY_CHECKIN_KEYWORDS):
        energy_entities = _extract_energy_entities(normalized)
        return IntakeResult(
            intent="daily_checkin",
            confidence=0.88,
            entities=energy_entities,
            requires_confirmation=False,
            confirmation_question=None,
            ambiguity=None,
            raw_input=raw,
            normalized_input=normalized,
            matched_keywords=matched,
        )

    energy_entities = _extract_energy_entities(normalized)
    if energy_entities:
        return IntakeResult(
            intent="daily_checkin",
            confidence=0.82,
            entities=energy_entities,
            requires_confirmation=False,
            confirmation_question=None,
            ambiguity=None,
            raw_input=raw,
            normalized_input=normalized,
            matched_keywords=tuple(energy_entities.keys()),
        )

    if matched := _matches_any(normalized, _CALENDAR_PROPOSAL_KEYWORDS):
        return IntakeResult(
            intent="calendar_proposal_request",
            confidence=0.82,
            entities={},
            requires_confirmation=True,
            confirmation_question="Ich erzeuge einen Vorschlag, schreibe aber nichts ohne deine Zustimmung. OK?",
            ambiguity=None,
            raw_input=raw,
            normalized_input=normalized,
            matched_keywords=matched,
        )

    if matched := _matches_any(normalized, _PLAN_REQUEST_KEYWORDS):
        return IntakeResult(
            intent="plan_request",
            confidence=0.86,
            entities={},
            requires_confirmation=False,
            confirmation_question=None,
            ambiguity=None,
            raw_input=raw,
            normalized_input=normalized,
            matched_keywords=matched,
        )

    if matched := _matches_any(normalized, _REVIEW_REQUEST_KEYWORDS):
        return IntakeResult(
            intent="review_request",
            confidence=0.85,
            entities={},
            requires_confirmation=False,
            confirmation_question=None,
            ambiguity=None,
            raw_input=raw,
            normalized_input=normalized,
            matched_keywords=matched,
        )

    skip_match = _matches_any(normalized, _HABIT_SKIP_KEYWORDS)
    completion = _detect_completion_mode(normalized)
    habit_name = _detect_habit_name(normalized)

    if skip_match or completion is not None:
        scope_all = bool(_matches_any(normalized, _HABIT_SCOPE_ALL_KEYWORDS))
        scope = "specific" if habit_name else ("all_today" if scope_all else "unknown")
        completion_value = "skipped" if skip_match else completion
        entities: dict[str, Any] = {
            "completion": completion_value,
            "scope": scope,
        }
        if habit_name:
            entities["habit_hint"] = habit_name

        if scope == "specific":
            confidence = 0.92
            ambiguity = None
            confirmation_question = None
        elif scope == "all_today":
            confidence = 0.78
            ambiguity = None
            confirmation_question = (
                "Ich interpretiere das als alle heutigen Habits. Stimmt das, oder nur eine bestimmte Routine?"
            )
        else:
            confidence = 0.65
            ambiguity = "scope_unclear"
            confirmation_question = (
                "Meinst du alle heutigen Habits oder eine bestimmte Routine?"
            )

        return IntakeResult(
            intent="habit_log",
            confidence=confidence,
            entities=entities,
            requires_confirmation=requires_confirmation(confidence, has_ambiguity=ambiguity is not None),
            confirmation_question=confirmation_question,
            ambiguity=ambiguity,
            raw_input=raw,
            normalized_input=normalized,
            matched_keywords=tuple(skip_match) if skip_match else (completion or "",),
        )

    if matched := _matches_any(normalized, _TASK_CAPTURE_KEYWORDS):
        return IntakeResult(
            intent="task_capture",
            confidence=0.7,
            entities={"raw_text": raw},
            requires_confirmation=True,
            confirmation_question="Soll ich das als neue Aufgabe in Google Tasks anlegen?",
            ambiguity=None,
            raw_input=raw,
            normalized_input=normalized,
            matched_keywords=matched,
        )

    return IntakeResult(
        intent="unknown",
        confidence=0.0,
        entities={},
        requires_confirmation=True,
        confirmation_question=(
            "Ich verstehe das nicht eindeutig. Meinst du Habit, Tagesplan, Aufgabe, Kalender-Vorschlag oder Review?"
        ),
        ambiguity="no_keyword_match",
        raw_input=raw,
        normalized_input=normalized,
        matched_keywords=(),
    )


__all__ = [
    "classify_intent",
    "CONFIDENCE_HIGH",
    "CONFIDENCE_MEDIUM",
]
