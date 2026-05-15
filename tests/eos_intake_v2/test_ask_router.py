from __future__ import annotations

from src.eos_intake_v2 import ask, route_query
from src.eos_intake_v2.intent_router import route_ask_intent
from src.eos_intake_v2.source_selector import select_sources


def fake_assistant_runner(command: str, **_: object) -> dict[str, object]:
    if command == "jetzt":
        return {
            "status": "warning",
            "command": "jetzt",
            "mode": "degraded",
            "summary_markdown": "Jetzt ist ein kurzer Fokusblock realistisch.",
            "actions": [{"label": "45 Minuten Fokusblock", "reason": "Kalenderfenster ist kurz."}],
            "source_status": {"calendar": {"status": "success"}},
            "privacy": {"external_writes_performed": False},
        }
    if command == "mail":
        return {
            "status": "warning",
            "command": "mail",
            "mode": "read_only",
            "summary_markdown": "Mail ist read-only.",
            "actions": [],
            "source_status": {"mail": {"status": "warning", "live_contract_verified": False}},
            "privacy": {"external_writes_performed": False},
        }
    return {
        "status": "success",
        "command": command,
        "mode": "live",
        "summary_markdown": "EOS ist nutzbar.",
        "actions": [],
        "source_status": {},
        "privacy": {"external_writes_performed": False},
    }


def test_routes_next_best_action_from_free_text() -> None:
    intent = route_ask_intent("Was soll ich jetzt machen?")

    assert intent.intent == "next_best_action"
    assert intent.confidence >= 0.9

    sources = select_sources(intent)
    assert [source.name for source in sources] == [
        "calendar_today",
        "tasks_open",
        "energy_today",
        "mail_action_required",
    ]


def test_route_query_is_read_only_and_source_aware() -> None:
    result = route_query("Muss ich auf irgendwas antworten?")

    assert result["status"] == "success"
    assert result["intent"]["intent"] == "mail_review"
    assert result["safety"]["external_writes_allowed"] is False
    assert result["safety"]["external_writes_performed"] is False
    assert any(source["name"] == "gmail_readonly" for source in result["sources_selected"])


def test_ask_renders_operational_answer_contract() -> None:
    result = ask("Was soll ich jetzt machen?", assistant_runner=fake_assistant_runner)

    assert result["status"] == "warning"
    assert result["command"] == "ask"
    assert result["intent"] == "next_best_action"
    assert "Antwort:" in result["summary_markdown"]
    assert "Warum:" in result["summary_markdown"]
    assert "Nächste Aktion:" in result["summary_markdown"]
    assert "Unsicherheit:" in result["summary_markdown"]
    assert "45 Minuten Fokusblock" in result["next_action"]
    assert result["privacy"]["external_writes_performed"] is False


def test_meeting_lookup_does_not_claim_unimplemented_context() -> None:
    result = ask("Was war nochmal das Meeting mit Max?", assistant_runner=fake_assistant_runner)

    assert result["intent"] == "meeting_lookup"
    assert "nicht live verdrahtet" in result["answer"]
    assert result["safety"]["external_writes_performed"] is False
    assert any("calendar_history" in item for item in result["uncertainty"])
