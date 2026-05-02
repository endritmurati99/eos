from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

VAULT_DIRS = {
    "inbox": "10 Inbox",
    "daily": "11 Daily Notes",
    "projects": "12 Projects",
    "areas": "13 Areas",
    "knowledge": "14 Knowledge",
    "ideas": "15 Ideas",
    "archive": "90 Archive",
}


def capture_brain_dump(
    raw_dump: str,
    *,
    captured_at: datetime,
    source: str = "chat",
    context: str = "brain dump",
    summary: str | None = None,
    project_slugs: list[str] | None = None,
    idea_slugs: list[str] | None = None,
    task_candidates: list[str] | None = None,
    calendar_candidates: list[str] | None = None,
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(workspace_root) if workspace_root is not None else Path(__file__).resolve().parents[2]
    vault_root = root / "vault"
    _ensure_vault_dirs(vault_root)

    timestamp = captured_at.strftime("%Y-%m-%d-%H%M")
    day = captured_at.strftime("%Y-%m-%d")
    note_name = f"{timestamp}-brain-dump"
    inbox_path = vault_root / VAULT_DIRS["inbox"] / f"{note_name}.md"
    daily_path = vault_root / VAULT_DIRS["daily"] / f"{day}.md"

    projects = project_slugs or []
    ideas = idea_slugs or []
    tasks = task_candidates or []
    calendar_items = calendar_candidates or []

    inbox_path.write_text(
        _render_brain_dump_note(
            captured_at=captured_at,
            source=source,
            context=context,
            raw_dump=raw_dump,
            summary=summary,
            daily_link=day,
            project_slugs=projects,
            idea_slugs=ideas,
            task_candidates=tasks,
            calendar_candidates=calendar_items,
        ),
        encoding="utf-8",
    )

    _upsert_daily_brain_dump_link(
        daily_path=daily_path,
        day=day,
        note_name=note_name,
        project_slugs=projects,
        idea_slugs=ideas,
    )

    return {
        "status": "success",
        "brain_dump_note": str(inbox_path),
        "daily_note": str(daily_path),
        "project_links": projects,
        "idea_links": ideas,
        "task_candidates": tasks,
        "calendar_candidates": calendar_items,
        "external_mutations": [],
    }


def archive_brain_dump(
    note_name: str,
    *,
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(workspace_root) if workspace_root is not None else Path(__file__).resolve().parents[2]
    vault_root = root / "vault"
    _ensure_vault_dirs(vault_root)

    normalized_name = note_name if note_name.endswith(".md") else f"{note_name}.md"
    source_path = vault_root / VAULT_DIRS["inbox"] / normalized_name
    archive_path = vault_root / VAULT_DIRS["archive"] / normalized_name

    if not source_path.exists():
        return {
            "status": "not_found",
            "source": str(source_path),
            "archive": str(archive_path),
            "error": "Brain dump note is not in 10 Inbox.",
        }
    if archive_path.exists():
        return {
            "status": "provider_error",
            "source": str(source_path),
            "archive": str(archive_path),
            "error": "Archive destination already exists.",
        }

    source_path.rename(archive_path)
    return {
        "status": "success",
        "source": str(source_path),
        "archive": str(archive_path),
        "error": None,
    }


def _ensure_vault_dirs(vault_root: Path) -> None:
    for folder in VAULT_DIRS.values():
        (vault_root / folder).mkdir(parents=True, exist_ok=True)


def _render_brain_dump_note(
    *,
    captured_at: datetime,
    source: str,
    context: str,
    raw_dump: str,
    summary: str | None,
    daily_link: str,
    project_slugs: list[str],
    idea_slugs: list[str],
    task_candidates: list[str],
    calendar_candidates: list[str],
) -> str:
    rendered_summary = summary or "Noch nicht verdichtet."
    project_lines = _wikilink_lines(project_slugs)
    idea_lines = _wikilink_lines(idea_slugs)
    task_lines = _candidate_lines("task_candidate", task_candidates)
    calendar_lines = _candidate_lines("calendar_candidate", calendar_candidates)

    return "\n".join(
        [
            "# EOS Brain Dump Note",
            "",
            "## Capture",
            f"- Time: `{captured_at.strftime('%Y-%m-%d %H:%M')}`",
            f"- Source: `{source}`",
            f"- Context: `{context}`",
            "",
            "## Rohdump",
            raw_dump,
            "",
            "## Kurzsummary",
            f"- {rendered_summary}",
            "",
            "## Moegliche Links",
            f"- Daily Note: `[[{daily_link}]]`",
            "- Projects:",
            *project_lines,
            "- Ideas:",
            *idea_lines,
            "",
            "## Moegliche Handoffs",
            *task_lines,
            *calendar_lines,
            "",
            "## Triage Status",
            "- Status: `open`",
            "- Next review: `<optional>`",
            "",
        ]
    )


def _upsert_daily_brain_dump_link(
    *,
    daily_path: Path,
    day: str,
    note_name: str,
    project_slugs: list[str],
    idea_slugs: list[str],
) -> None:
    link_line = f"- [[{note_name}]]"
    if daily_path.exists():
        content = daily_path.read_text(encoding="utf-8")
    else:
        content = _daily_template(day)

    if link_line not in content:
        content = _append_under_heading(content, "## Brain Dumps", link_line)

    for slug in project_slugs:
        content = _append_under_heading(content, "## Active Projects", f"- [[{slug}]]")
    for slug in idea_slugs:
        content = _append_under_heading(content, "## Active Ideas / Open Loops", f"- [[{slug}]]")

    daily_path.write_text(content, encoding="utf-8")


def _daily_template(day: str) -> str:
    return "\n".join(
        [
            "# EOS Daily Note",
            "",
            "## Day Context",
            f"- Date: `{day}`",
            "- Context: `<main constraints, energy, or important frame>`",
            "",
            "## Brain Dumps",
            "",
            "## Active Projects",
            "",
            "## Active Ideas / Open Loops",
            "",
            "## Verlauf",
            "- `<key note or decision>`",
            "",
            "## Carry Forward",
            "- `<open loop or next thing to remember>`",
            "",
        ]
    )


def _append_under_heading(content: str, heading: str, line: str) -> str:
    if line in content:
        return content
    marker = f"{heading}\n"
    if marker not in content:
        return f"{content.rstrip()}\n\n{heading}\n{line}\n"
    return content.replace(marker, f"{marker}{line}\n", 1)


def _wikilink_lines(slugs: list[str]) -> list[str]:
    if not slugs:
        return ["  - `<none>`"]
    return [f"  - `[[{slug}]]`" for slug in slugs]


def _candidate_lines(marker: str, candidates: list[str]) -> list[str]:
    if not candidates:
        return [f"- `[{marker}] <none>`"]
    return [f"- `[{marker}] {candidate}`" for candidate in candidates]
