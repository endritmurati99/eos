#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src import eos_cli


def main() -> None:
    original_db_path = os.environ.get("EOS_DB_PATH")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["EOS_DB_PATH"] = str(Path(tmp) / "eos.db")
            jobs_path = Path(tmp) / "jobs.json"
            jobs_path.write_text(
                json.dumps(
                    {
                        "jobs": [
                            {
                                "id": "ok",
                                "name": "Daily OK",
                                "enabled": True,
                                "delivery": {
                                    "mode": "announce",
                                    "channel": "telegram",
                                    "to": "telegram:123",
                                },
                                "state": {},
                                "payload": {"model": "gpt-5.4-mini"},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = eos_cli.main(["--json-only", "cron-audit", "--jobs-path", str(jobs_path)])

            payload = json.loads(stdout.getvalue())
            assert code == 0
            assert payload["status"] == "success"
            assert payload["enabled_count"] == 1
            assert payload["issues"] == []

            habit_stdout = io.StringIO()
            with contextlib.redirect_stdout(habit_stdout):
                habit_code = eos_cli.main(["--json-only", "habits", "today", "--date", "2026-04-28"])
            habit_payload = json.loads(habit_stdout.getvalue())
            assert habit_code == 0
            assert habit_payload["status"] == "success"
            assert habit_payload["active_count"] == 3
    finally:
        if original_db_path is None:
            os.environ.pop("EOS_DB_PATH", None)
        else:
            os.environ["EOS_DB_PATH"] = original_db_path
    print("verify_eos_cli: ok")


if __name__ == "__main__":
    main()
