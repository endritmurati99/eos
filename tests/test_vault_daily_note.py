from __future__ import annotations

from datetime import date, datetime

from src.vault import DailyStandEntry, capture_brain_dump, read_daily_context, upsert_daily_stand


def test_upsert_daily_stand_creates_structured_daily_note(tmp_path) -> None:
    result = upsert_daily_stand(
        day=date(2026, 5, 15),
        entry=DailyStandEntry(
            captured_at=datetime(2026, 5, 15, 8, 45),
            summary="Solara-Testausgabe vorbereitet; morgen 5 Klienten onboarden.",
            done=("Solara Profilanlage verbessert", "EOS Second Brain Daily Notes geplant"),
            next_steps=("5 Testklienten Solara geben",),
            projects=("Solara", "EOS"),
            irrelevant=("13 Areas nicht als Tageslog verwenden",),
            raw_text="Wir haben Solara verbessert und wollen morgen 5 Klienten testen lassen.",
        ),
        workspace_root=tmp_path,
    )

    assert result["status"] == "success"
    assert result["external_mutations"] == []

    daily_path = tmp_path / "vault" / "11 Daily Notes" / "2026-05-15.md"
    note = daily_path.read_text(encoding="utf-8")
    assert "## Tagesstand" in note
    assert "Solara-Testausgabe vorbereitet" in note
    assert "- Solara Profilanlage verbessert" in note
    assert "- 5 Testklienten Solara geben" in note
    assert "- [[Solara]]" in note
    assert "- 13 Areas nicht als Tageslog verwenden" in note
    assert "```text" in note


def test_read_daily_context_returns_compact_daily_stand(tmp_path) -> None:
    upsert_daily_stand(
        day=date(2026, 5, 15),
        entry=DailyStandEntry(
            captured_at=datetime(2026, 5, 15, 9, 0),
            summary="EOS liest Daily Notes als Tagesstand.",
            done=("Daily Note Writer implementiert",),
            next_steps=("Ask-Router nutzt vault_notes",),
            projects=("EOS",),
        ),
        workspace_root=tmp_path,
    )

    result = read_daily_context(day=date(2026, 5, 15), workspace_root=tmp_path)

    assert result["status"] == "success"
    assert "## Tagesstand" in result["summary_markdown"]
    assert "EOS liest Daily Notes" in result["summary_markdown"]
    assert "Ask-Router nutzt vault_notes" in result["summary_markdown"]


def test_read_daily_context_preserves_legacy_brain_dump_daily_sections(tmp_path) -> None:
    capture_brain_dump(
        "Alpha Projektstand festhalten.",
        captured_at=datetime(2026, 5, 15, 9, 0),
        project_slugs=["Alpha"],
        idea_slugs=["second-brain-cleanup"],
        workspace_root=tmp_path,
    )

    result = read_daily_context(day=date(2026, 5, 15), workspace_root=tmp_path)

    assert result["status"] == "success"
    assert "## Brain Dumps" in result["summary_markdown"]
    assert "[[2026-05-15-0900-brain-dump]]" in result["summary_markdown"]
    assert "## Active Projects" in result["summary_markdown"]
    assert "[[Alpha]]" in result["summary_markdown"]
    assert "<key note or decision>" not in result["summary_markdown"]
    assert "ohne verdichteten Tagesstand" not in result["summary_markdown"]


def test_read_daily_context_keeps_brain_dump_link_without_project_slugs(tmp_path) -> None:
    capture_brain_dump(
        "Nur ein Rohdump ohne Projektlink.",
        captured_at=datetime(2026, 5, 15, 9, 30),
        workspace_root=tmp_path,
    )

    result = read_daily_context(day=date(2026, 5, 15), workspace_root=tmp_path)

    assert result["status"] == "success"
    assert "## Brain Dumps" in result["summary_markdown"]
    assert "[[2026-05-15-0930-brain-dump]]" in result["summary_markdown"]
    assert "## Active Projects" not in result["summary_markdown"]


def test_read_daily_context_uses_latest_note_when_no_date(tmp_path) -> None:
    for day in (date(2026, 5, 14), date(2026, 5, 15)):
        upsert_daily_stand(
            day=day,
            entry=DailyStandEntry(captured_at=datetime(2026, 5, 15, 9, 0), summary=f"Stand {day.isoformat()}"),
            workspace_root=tmp_path,
        )

    result = read_daily_context(workspace_root=tmp_path)

    assert result["status"] == "success"
    assert result["day"] == "2026-05-15"
