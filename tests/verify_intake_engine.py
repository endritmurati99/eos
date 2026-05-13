#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.intake import (  # noqa: E402
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    IntakeResult,
    SUPPORTED_INTENTS,
    classify_intent,
    confidence_band,
    normalize_text,
    requires_confirmation,
)


def assert_eq(actual, expected, label):
    assert actual == expected, f"{label}: expected {expected!r}, got {actual!r}"


def test_normalizer_handles_umlauts():
    assert_eq(normalize_text("Müde"), "muede", "umlaut fold")
    assert_eq(normalize_text("Übergehen"), "uebergehen", "uppercase umlaut")
    assert_eq(normalize_text("Straße"), "strasse", "eszett")
    assert_eq(normalize_text("  hallo   welt  "), "hallo welt", "whitespace collapse")
    assert_eq(normalize_text(""), "", "empty input")


def test_specific_habit_done_high_confidence():
    result = classify_intent("morgenroutine erledigt")
    assert isinstance(result, IntakeResult)
    assert_eq(result.intent, "habit_log", "specific habit intent")
    assert result.confidence >= CONFIDENCE_HIGH, f"expected high, got {result.confidence}"
    assert_eq(result.entities["completion"], "done_full", "completion value")
    assert_eq(result.entities["scope"], "specific", "scope")
    assert_eq(result.entities["habit_hint"], "morgenroutine", "habit hint")
    assert result.requires_confirmation is False, "specific high-confidence should not require confirmation"
    assert_eq(confidence_band(result.confidence), "high", "confidence band high")


def test_ambiguous_scope_triggers_clarification():
    result = classify_intent("hab alles erledigt")
    assert_eq(result.intent, "habit_log", "ambiguous habit intent")
    assert CONFIDENCE_MEDIUM <= result.confidence < CONFIDENCE_HIGH, (
        f"expected medium band, got {result.confidence}"
    )
    assert_eq(result.entities["completion"], "done_full", "completion full")
    assert_eq(result.entities["scope"], "all_today", "scope all_today")
    assert result.requires_confirmation is True, "ambiguous all_today must require confirmation"
    assert result.confirmation_question, "must include a confirmation_question"


def test_partial_completion_detected():
    result = classify_intent("morgenroutine partial heute")
    assert_eq(result.intent, "habit_log", "partial habit intent")
    assert_eq(result.entities["completion"], "done_partial", "partial completion")
    assert_eq(result.entities["scope"], "specific", "scope specific")


def test_skip_with_reason():
    result = classify_intent("klimmzug skip heute, zu muede")
    assert_eq(result.intent, "habit_log", "skip habit intent")
    assert_eq(result.entities["completion"], "skipped", "skipped completion")
    assert_eq(result.entities["scope"], "specific", "scope specific")
    assert result.confidence >= CONFIDENCE_HIGH, f"specific skip should be high confidence, got {result.confidence}"


def test_habit_status_query():
    for query in ("habit status", "habits heute", "habit heute"):
        result = classify_intent(query)
        assert_eq(result.intent, "habit_status", f"status query for {query}")
        assert result.confidence >= CONFIDENCE_HIGH, f"status confidence for {query}"
        assert result.requires_confirmation is False, f"status query {query} should not require confirmation"


def test_daily_checkin():
    result = classify_intent("Energie Checkin Schlafqualitaet 7")
    assert_eq(result.intent, "daily_checkin", "checkin intent")
    assert result.confidence >= CONFIDENCE_HIGH


def test_plan_request():
    for query in ("plane mir den tag", "wie sieht morgen aus", "tagesplan bitte"):
        result = classify_intent(query)
        assert_eq(result.intent, "plan_request", f"plan request for {query}")
        assert result.confidence >= CONFIDENCE_HIGH, f"plan confidence for {query}"


def test_calendar_proposal_routing():
    result = classify_intent("schlag mir vor wann ich Bachelorarbeit machen kann")
    assert_eq(result.intent, "calendar_proposal_request", "calendar proposal intent")
    assert result.requires_confirmation is True, "calendar proposal must require confirmation"


def test_task_capture():
    result = classify_intent("merken: Versicherung anrufen")
    assert_eq(result.intent, "task_capture", "task capture intent")
    assert result.requires_confirmation is True, "task capture must require confirmation"


def test_review_request():
    result = classify_intent("wie war meine woche?")
    assert_eq(result.intent, "review_request", "review intent")
    assert result.confidence >= CONFIDENCE_HIGH


def test_unknown_input_low_confidence():
    result = classify_intent("blah blubb foobar")
    assert_eq(result.intent, "unknown", "unknown intent")
    assert result.confidence < CONFIDENCE_MEDIUM, f"unknown should be low, got {result.confidence}"
    assert result.requires_confirmation is True, "unknown must require confirmation"
    assert result.ambiguity == "no_keyword_match"


def test_empty_input():
    result = classify_intent("")
    assert_eq(result.intent, "unknown", "empty intent")
    assert_eq(result.confidence, 0.0, "empty confidence")
    assert result.requires_confirmation is True
    assert result.ambiguity == "empty_input"


def test_supported_intents_complete():
    expected = {
        "habit_log",
        "habit_status",
        "daily_checkin",
        "plan_request",
        "task_capture",
        "calendar_proposal_request",
        "review_request",
        "assistant_command",
        "habit_relapse",
        "habit_recovery",
        "habit_failure",
        "confirm_response",
        "unknown",
    }
    assert set(SUPPORTED_INTENTS) == expected, f"intent set drifted: {SUPPORTED_INTENTS}"


def test_slash_assistant_commands():
    expected = {
        "/status": "status",
        "/heute": "heute",
        "/jetzt": "jetzt",
        "/abend": "abend",
        "/mail": "mail",
        "/eos": "home",
        "/start": "home",
        "/hilfe": "home",
        "/help": "home",
    }
    for raw, command in expected.items():
        result = classify_intent(raw)
        assert_eq(result.intent, "assistant_command", raw)
        assert_eq(result.entities["assistant_command"], command, raw)
        assert result.requires_confirmation is False


def test_intake_does_not_write_state():
    db_path = WORKSPACE_ROOT / "data" / "eos_v2.db"
    state_path = WORKSPACE_ROOT / "data" / "eos_state.json"
    db_mtime_before = db_path.stat().st_mtime if db_path.exists() else None
    state_mtime_before = state_path.stat().st_mtime if state_path.exists() else None

    for text in (
        "morgenroutine erledigt",
        "hab alles erledigt",
        "klimmzug skip heute",
        "habit status",
        "schlag mir vor wann ich lernen kann",
        "merken: einkaufen",
    ):
        classify_intent(text)

    db_mtime_after = db_path.stat().st_mtime if db_path.exists() else None
    state_mtime_after = state_path.stat().st_mtime if state_path.exists() else None
    assert db_mtime_before == db_mtime_after, "intake must not modify eos_v2.db"
    assert state_mtime_before == state_mtime_after, "intake must not modify eos_state.json"


def test_to_dict_serializable():
    result = classify_intent("morgenroutine erledigt")
    payload = result.to_dict()
    assert payload["intent"] == "habit_log"
    assert isinstance(payload["matched_keywords"], list)
    assert isinstance(payload["entities"], dict)


def test_requires_confirmation_helper():
    assert requires_confirmation(0.95) is False
    assert requires_confirmation(0.95, has_ambiguity=True) is True
    assert requires_confirmation(0.7) is True
    assert requires_confirmation(0.4) is True


def main():
    test_normalizer_handles_umlauts()
    test_specific_habit_done_high_confidence()
    test_ambiguous_scope_triggers_clarification()
    test_partial_completion_detected()
    test_skip_with_reason()
    test_habit_status_query()
    test_daily_checkin()
    test_plan_request()
    test_calendar_proposal_routing()
    test_task_capture()
    test_review_request()
    test_unknown_input_low_confidence()
    test_empty_input()
    test_supported_intents_complete()
    test_intake_does_not_write_state()
    test_to_dict_serializable()
    test_requires_confirmation_helper()
    print("verify_intake_engine: ok")


if __name__ == "__main__":
    main()
