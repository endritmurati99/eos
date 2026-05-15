from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.vault.brain_dump import VAULT_DIRS, _ensure_vault_dirs


@dataclass(frozen=True)
class DailyStandEntry:
    """A concise daily-state entry for the EOS Second Brain.

    The raw user text is preserved when provided, but the durable structure stays
    small: what happened, what matters next, active projects, and what to ignore.
    """

    captured_at: datetime
    summary: str | None = None
    done: tuple[str, ...] = field(default_factory=tuple)
    next_steps: tuple[str, ...] = field(default_factory=tuple)
    projects: tuple[str, ...] = field(default_factory=tuple)
    irrelevant: tuple[str, ...] = field(default_factory=tuple)
    raw_text: str | None = None
    source: str = "chat"


def upsert_daily_stand(
    *,
    day: date,
    entry: DailyStandEntry,
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(workspace_root) if workspace_root is not None else Path(__file__).resolve().parents[2]
    vault_root = root / "vault"
    _ensure_vault_dirs(vault_root)
    daily_path = vault_root / VAULT_DIRS["daily"] / f"{day.isoformat()}.md"

    content = daily_path.read_text(encoding="utf-8") if daily_path.exists() else _daily_template(day)
    content = _ensure_daily_sections(content)
    content = _append_under_heading(content, "## Tagesstand", _render_tagesstand_line(entry))

    for item in _clean_items(entry.done):
        content = _append_under_heading(content, "## Heute gemacht", f"- {item}")
    for item in _clean_items(entry.next_steps):
        content = _append_under_heading(content, "## Nächste Schritte", f"- {item}")
    for project in _clean_items(entry.projects):
        content = _append_under_heading(content, "## Aktive Projekte", f"- [[{project}]]")
    for item in _clean_items(entry.irrelevant):
        content = _append_under_heading(content, "## Nicht weiter nutzen", f"- {item}")
    if entry.raw_text and entry.raw_text.strip():
        content = _append_under_heading(content, "## Rohinput", _render_raw_block(entry))

    daily_path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return {
        "status": "success",
        "daily_note": str(daily_path),
        "external_mutations": [],
        "summary_markdown": _daily_status_summary(day, entry),
    }


def read_daily_context(
    *,
    day: date | None = None,
    workspace_root: str | Path | None = None,
    max_chars: int = 5000,
) -> dict[str, Any]:
    root = Path(workspace_root) if workspace_root is not None else Path(__file__).resolve().parents[2]
    vault_root = root / "vault"
    daily_root = vault_root / VAULT_DIRS["daily"]
    target = _daily_path_for_read(daily_root, day)
    if target is None:
        return {
            "status": "not_found",
            "daily_note": None,
            "summary_markdown": "Keine Daily Note gefunden.",
            "external_mutations": [],
        }

    content = target.read_text(encoding="utf-8")
    clipped = content[:max_chars]
    return {
        "status": "success",
        "daily_note": str(target),
        "day": target.stem,
        "summary_markdown": _compact_daily_context(clipped),
        "content_excerpt": clipped,
        "external_mutations": [],
    }


def _daily_path_for_read(daily_root: Path, day: date | None) -> Path | None:
    if day is not None:
        path = daily_root / f"{day.isoformat()}.md"
        return path if path.exists() else None
    if not daily_root.exists():
        return None
    candidates = sorted(daily_root.glob("????-??-??.md"), reverse=True)
    return candidates[0] if candidates else None


def _daily_template(day: date) -> str:
    return "\n".join(
        [
            "---",
            "type: daily_note",
            f"date: {day.isoformat()}",
            "---",
            "",
            f"# {day.isoformat()}",
            "",
            "## Tagesstand",
            "",
            "## Heute gemacht",
            "",
            "## Nächste Schritte",
            "",
            "## Aktive Projekte",
            "",
            "## Nicht weiter nutzen",
            "",
            "## Brain Dumps",
            "",
            "## Rohinput",
            "",
        ]
    )


def _ensure_daily_sections(content: str) -> str:
    required = (
        "## Tagesstand",
        "## Heute gemacht",
        "## Nächste Schritte",
        "## Aktive Projekte",
        "## Nicht weiter nutzen",
        "## Brain Dumps",
        "## Rohinput",
    )
    for heading in required:
        if heading not in content:
            content = f"{content.rstrip()}\n\n{heading}\n"
    return content


def _render_tagesstand_line(entry: DailyStandEntry) -> str:
    timestamp = entry.captured_at.strftime("%H:%M")
    summary = (entry.summary or "Tagesstand aktualisiert.").strip()
    return f"- `{timestamp}` {summary}"


def _render_raw_block(entry: DailyStandEntry) -> str:
    timestamp = entry.captured_at.strftime("%H:%M")
    raw = (entry.raw_text or "").strip()
    return f"### {timestamp} · {entry.source}\n\n```text\n{raw}\n```"


def _append_under_heading(content: str, heading: str, block: str) -> str:
    block = block.rstrip()
    if not block or block in content:
        return content
    marker = f"{heading}\n"
    if marker not in content:
        return f"{content.rstrip()}\n\n{heading}\n{block}\n"
    return content.replace(marker, f"{marker}{block}\n", 1)


def _clean_items(items: tuple[str, ...]) -> tuple[str, ...]:
    cleaned = tuple(str(item).strip() for item in items if str(item).strip())
    return cleaned[:12]


def _daily_status_summary(day: date, entry: DailyStandEntry) -> str:
    lines = [f"Daily Note {day.isoformat()} aktualisiert."]
    if entry.summary:
        lines.append(f"Stand: {entry.summary.strip()}")
    if entry.projects:
        lines.append("Projekte: " + ", ".join(_clean_items(entry.projects)))
    if entry.next_steps:
        lines.append("Nächste Schritte: " + "; ".join(_clean_items(entry.next_steps)[:3]))
    return "\n".join(lines)


def _compact_daily_context(content: str) -> str:
    headings = ("## Tagesstand", "## Heute gemacht", "## Nächste Schritte", "## Aktive Projekte", "## Nicht weiter nutzen")
    lines = [line.rstrip() for line in content.splitlines()]
    keep: list[str] = []
    active = False
    for line in lines:
        if line.startswith("## "):
            active = line in headings
            if active:
                keep.append(line)
            continue
        if active and line.strip():
            keep.append(line)
    if not keep:
        return "Daily Note vorhanden, aber ohne verdichteten Tagesstand."
    return "\n".join(keep[:60])
