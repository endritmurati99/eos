from __future__ import annotations

from datetime import date

from src.dispatch import dispatch_text
from src.dispatch.actions import (
    ACTION_ASSISTANT_RESPONSE,
    ACTION_CALENDAR_PROPOSAL,
    ACTION_HABIT_STATUS,
    ACTION_PENDING_CONFIRMATION,
    ACTION_TASK_PROPOSAL,
)
from src.eos_assistant import run_assistant_command
from src.eos_assistant import service as assistant_service
from src.eos_mail.gmail_client import MailSummary


def fake_daily_payload() -> dict[str, object]:
    return {
        "status": "green",
        "calendar_read_status": "success",
        "task_read_status": "success",
        "recommendation": "Heute einen Fokusblock schuetzen.",
        "top_tasks": [
            {
                "id": "task-1",
                "title": "Bachelorarbeit Abschnitt planen",
                "list_name": "Next",
            }
        ],
        "ranked_tasks": [],
        "triage_required": False,
        "habit_status": {
            "status": "success",
            "habits": [
                {"id": "morgenroutine", "name": "Morgenroutine", "pending": True},
            ],
        },
    }


def test_assistant_status_reports_degraded_without_raw_secret(monkeypatch) -> None:
    monkeypatch.setattr(
        assistant_service,
        "_collect_status_checks",
        lambda **_: {
            "calendar": {"status": "success"},
            "tasks": {"status": "success", "open_task_count": 2},
            "habits": {"status": "success"},
            "vault": {"status": "config_missing"},
            "cron": {"status": "warning", "issue_count": 1},
            "models": {"status": "success"},
            "mail": {"status": "warning", "live_contract_verified": False},
            "db": {"status": "failed", "issue_codes": ["db_not_writable"]},
        },
    )
    result = run_assistant_command("status")
    assert result["status"] == "warning"
    assert result["mode"] == "degraded"
    assert "telegram:" not in str(result)
    assert result["privacy"]["external_writes_performed"] is False


def test_assistant_home_returns_home_surface(monkeypatch) -> None:
    monkeypatch.setattr(
        assistant_service,
        "build_status",
        lambda **_: {
            "status": "warning",
            "mode": "degraded",
            "summary_markdown": "Status",
            "cards": [],
            "actions": [],
            "source_status": {
                "db": {"status": "failed"},
                "vault": {"status": "config_missing"},
            },
            "privacy": {"external_writes_performed": False},
        },
    )
    monkeypatch.setattr(
        assistant_service,
        "build_heute",
        lambda **_: {
            "status": "success",
            "mode": "live",
            "summary_markdown": "Heute: live.",
            "cards": [],
            "actions": [{"label": "Starte Fokusblock", "requires_confirmation": False, "reason": "Top-Aktion."}],
            "source_status": {"habits": {"pending_count": 1}},
            "privacy": {"external_writes_performed": False},
        },
    )
    monkeypatch.setattr(
        assistant_service,
        "build_mail",
        lambda **_: {
            "status": "warning",
            "mode": "read_only",
            "summary_markdown": "Mail read-only.",
            "cards": [],
            "actions": [],
            "source_status": {"mail": {"live_contract_verified": False}},
            "privacy": {"external_writes_performed": False, "gmail_write_actions_added": False},
        },
    )
    result = run_assistant_command("home", target_date=date(2026, 5, 6))
    assert result["command"] == "home"
    assert result["status"] == "warning"
    assert result["cards"]
    assert result["actions"][0]["label"] == "Starte Fokusblock"
    assert result["privacy"]["external_writes_performed"] is False


def test_assistant_heute_uses_live_success_fixture(monkeypatch) -> None:
    monkeypatch.setattr(assistant_service, "run_daily_capacity", lambda *_, **__: fake_daily_payload())
    monkeypatch.setattr(
        assistant_service,
        "_calendar_intelligence_for_date",
        lambda *_, **__: {"status": "success", "lines": ["Risiko: low", "Konflikte: 0"]},
    )
    monkeypatch.setattr(assistant_service, "_energy_today", lambda: {"energy_level": 7, "stress": 3})
    result = run_assistant_command("heute", target_date=date(2026, 5, 6))
    assert result["status"] == "success"
    assert result["mode"] == "live"
    assert result["actions"][0]["label"].startswith("Starte:")
    assert result["source_status"]["tasks"]["status"] == "success"


def test_assistant_jetzt_returns_exactly_one_primary_action(monkeypatch) -> None:
    monkeypatch.setattr(assistant_service, "run_daily_capacity", lambda *_, **__: fake_daily_payload())
    monkeypatch.setattr(
        assistant_service,
        "_calendar_intelligence_for_date",
        lambda *_, **__: {"status": "success", "lines": ["Risiko: low"]},
    )
    monkeypatch.setattr(assistant_service, "_energy_today", lambda: None)
    result = run_assistant_command("jetzt", target_date=date(2026, 5, 6))
    assert result["command"] == "jetzt"
    assert len(result["actions"]) == 1
    assert "Warum:" in result["summary_markdown"]


def test_assistant_abend_dry_run_does_not_claim_external_writes(monkeypatch) -> None:
    monkeypatch.setattr(assistant_service, "run_daily_capacity", lambda *_, **__: fake_daily_payload())
    monkeypatch.setattr(
        assistant_service,
        "_habit_today",
        lambda *_, **__: {"status": "success", "habits": []},
    )
    monkeypatch.setattr(
        assistant_service,
        "_calendar_intelligence_for_date",
        lambda *_, **__: {"status": "success", "lines": ["Risiko: low"]},
    )
    monkeypatch.setattr(assistant_service, "_energy_today", lambda: None)
    result = run_assistant_command("abend", target_date=date(2026, 5, 6), dry_run=True)
    assert result["privacy"]["external_writes_performed"] is False
    assert result["actions"]


def test_assistant_mail_stays_read_only_and_preserves_live_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        assistant_service,
        "run_gmail_auth_preflight",
        lambda: {
            "status": "warning",
            "provider_command_available": False,
            "account_configured": True,
            "write_scopes_detected": False,
            "live_contract_verified": False,
            "live_contract_unverified_items": ["shape not verified"],
        },
    )
    result = run_assistant_command("mail", max_results=0)
    assert result["mode"] == "read_only"
    assert result["privacy"]["gmail_write_actions_added"] is False
    assert result["source_status"]["mail"]["live_contract_verified"] is False
    assert result["source_status"]["mail"]["live_contract_unverified_items"] == ["shape not verified"]


def test_mail_task_proposal_count_does_not_expose_subject() -> None:
    message = MailSummary(
        message_id="m1",
        thread_id="t1",
        sender="person@example.invalid",
        to=None,
        subject="Reply by Friday",
        date="2026-05-06",
        snippet="Please reply by Friday.",
        headers_subset={},
        has_attachments=False,
        label_ids=(),
    )
    count = assistant_service._count_mail_task_proposals([message])
    assert count >= 1


def test_dispatch_routes_natural_assistant_phrase(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        "src.dispatch.router.run_assistant_command",
        lambda command, **_: {
            "status": "success",
            "command": command,
            "mode": "live",
            "summary_markdown": "Jetzt: Fokusblock starten.",
            "cards": [],
            "actions": [],
            "source_status": {},
            "privacy": {"external_writes_performed": False},
        },
    )
    result = dispatch_text("was soll ich jetzt machen", db_path=str(tmp_path / "dispatch.db"))
    assert result.action_type == ACTION_ASSISTANT_RESPONSE
    assert result.extra["assistant_command"] == "jetzt"


def test_dispatch_routes_slash_commands(monkeypatch, tmp_path) -> None:
    routed: list[str] = []

    def fake_run(command, **_):
        routed.append(command)
        return {
            "status": "success",
            "command": command,
            "mode": "live",
            "summary_markdown": f"EOS {command}",
            "cards": [{"title": "Blocker", "status": "success", "items": []}],
            "actions": [{"label": "Aktion", "requires_confirmation": False, "reason": "Test"}],
            "source_status": {},
            "privacy": {"external_writes_performed": False, "gmail_write_actions_added": False},
        }

    monkeypatch.setattr("src.dispatch.router.run_assistant_command", fake_run)
    db_path = str(tmp_path / "slash.db")
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
    for text, command in expected.items():
        result = dispatch_text(text, db_path=db_path)
        assert result.action_type == ACTION_ASSISTANT_RESPONSE
        assert result.extra["assistant_command"] == command
        assert result.response_markdown.startswith("EOS ")
        assert "{" not in result.response_markdown
        assert result.extra["assistant"]["privacy"]["external_writes_performed"] is False
    assert routed == list(expected.values())


def test_dispatch_habit_status_returns_habit_service_payload(tmp_path) -> None:
    result = dispatch_text("habit status", db_path=str(tmp_path / "habit-status.db"))
    assert result.status == "ok"
    assert result.intent == "habit_status"
    assert result.action_type == ACTION_HABIT_STATUS
    assert result.extra["target_service"] == "HabitService"
    assert "kann ich noch nicht" not in result.response_text.lower()
    assert result.extra["external_writes_performed"] is False


def test_dispatch_task_capture_stays_proposal_only(tmp_path) -> None:
    db_path = str(tmp_path / "task-proposal.db")
    first = dispatch_text("merken: Versicherung anrufen", user_id="u-task", db_path=db_path)
    assert first.status == "pending"
    assert first.action_type == ACTION_PENDING_CONFIRMATION
    assert "nichts extern" in first.response_text

    second = dispatch_text("ja", user_id="u-task", db_path=db_path)
    assert second.status == "ok"
    assert second.intent == "task_capture"
    assert second.action_type == ACTION_TASK_PROPOSAL
    assert second.extra["target_service"] == "TaskProposal"
    assert second.extra["external_writes_performed"] is False
    assert second.extra["google_tasks_write_performed"] is False
    assert second.extra["actions"][0]["requires_confirmation"] is True
    assert "Nicht in Google Tasks angelegt" in second.response_markdown


def test_dispatch_calendar_request_stays_proposal_only(tmp_path) -> None:
    db_path = str(tmp_path / "calendar-proposal.db")
    first = dispatch_text("trag in den kalender morgen 10 uhr zahnarzt", user_id="u-calendar", db_path=db_path)
    assert first.status == "pending"
    assert first.action_type == ACTION_PENDING_CONFIRMATION

    second = dispatch_text("ja", user_id="u-calendar", db_path=db_path)
    assert second.status == "ok"
    assert second.intent == "calendar_proposal_request"
    assert second.action_type == ACTION_CALENDAR_PROPOSAL
    assert second.extra["target_service"] == "CalendarProposal"
    assert second.extra["external_writes_performed"] is False
    assert second.extra["calendar_external_writes_performed"] is False
    assert second.extra["actions"][0]["requires_confirmation"] is True
    assert "Noch nichts eingetragen" in second.response_markdown
