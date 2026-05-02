#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys
import tempfile

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.vault import archive_brain_dump, capture_brain_dump  # noqa: E402


def main() -> int:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        result = capture_brain_dump(
            "Google Tasks reparieren und Vault sauber routen.",
            captured_at=datetime(2026, 4, 28, 9, 30),
            source="chat",
            context="implementation test",
            summary="Tasks und Vault sollen getrennte Rollen behalten.",
            project_slugs=["eos-personal-assistant"],
            idea_slugs=["second-brain-cleanup"],
            task_candidates=["Google Tasks API im Cloud-Projekt aktivieren"],
            workspace_root=root,
        )

        assert result["status"] == "success"
        assert result["external_mutations"] == []

        inbox_path = root / "vault" / "10 Inbox" / "2026-04-28-0930-brain-dump.md"
        daily_path = root / "vault" / "11 Daily Notes" / "2026-04-28.md"
        assert inbox_path.exists()
        assert daily_path.exists()

        inbox = inbox_path.read_text(encoding="utf-8")
        daily = daily_path.read_text(encoding="utf-8")
        assert "## Rohdump" in inbox
        assert "Google Tasks reparieren" in inbox
        assert "[task_candidate] Google Tasks API im Cloud-Projekt aktivieren" in inbox
        assert "[[2026-04-28-0930-brain-dump]]" in daily
        assert "[[eos-personal-assistant]]" in daily
        assert "[[second-brain-cleanup]]" in daily

        archive_result = archive_brain_dump(
            "2026-04-28-0930-brain-dump",
            workspace_root=root,
        )
        archive_path = root / "vault" / "90 Archive" / "2026-04-28-0930-brain-dump.md"
        assert archive_result["status"] == "success"
        assert not inbox_path.exists()
        assert archive_path.exists()

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
