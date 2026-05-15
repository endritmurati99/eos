from __future__ import annotations

import json

from src import eos_cli


def test_cli_intake_route_outputs_source_selection(capsys) -> None:
    code = eos_cli.main(["--json-only", "intake", "route", "Muss ich auf irgendwas antworten?"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["intent"]["intent"] == "mail_review"
    assert any(source["name"] == "gmail_readonly" for source in payload["sources_selected"])
    assert payload["safety"]["external_writes_performed"] is False


def test_cli_vault_daily_stand_writes_daily_note(monkeypatch, tmp_path, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(eos_cli, "WORKSPACE_ROOT", tmp_path)

    code = eos_cli.main([
        "--json-only",
        "vault",
        "daily-stand",
        "--date",
        "2026-05-15",
        "--summary",
        "Solara soll morgen an 5 Klienten gehen.",
        "--done",
        "Solara Profile vorbereitet",
        "--next-step",
        "Testklienten onboarden",
        "--project",
        "Solara",
    ])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "success"
    assert "Solara" in (tmp_path / "vault" / "11 Daily Notes" / "2026-05-15.md").read_text(encoding="utf-8")


def test_cli_ask_uses_ask_service(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        eos_cli,
        "run_ask_query",
        lambda text, target_date=None: {
            "status": "success",
            "command": "ask",
            "query": text,
            "intent": "daily_status",
            "confidence": 0.86,
            "summary_markdown": "Antwort:\nHeute ist ein Fokusblock realistisch.\n\nWarum:\n- Test\n\nNächste Aktion:\nFokusblock\n\nUnsicherheit:\n- Keine",
            "privacy": {"external_writes_performed": False},
        },
    )

    code = eos_cli.main(["--json-only", "ask", "Was ist heute wichtig?"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "ask"
    assert payload["intent"] == "daily_status"
    assert payload["privacy"]["external_writes_performed"] is False
