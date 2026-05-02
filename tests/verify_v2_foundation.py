#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path


def main() -> int:
    workspace_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(workspace_root))

    verified_gog_path = Path("/docker/openclaw-qt6t/data/linuxbrew/.linuxbrew/bin/gog")
    if "EOS_GOG_BIN" not in os.environ and verified_gog_path.exists():
        os.environ["EOS_GOG_BIN"] = str(verified_gog_path)

    from src.database import init_db
    from src.gateways.google_tasks import TaskGateway
    from src.jobs.evening_reset import run_evening_reset

    db_ok = False
    tasks_ok = False
    live_calendar_ok = False
    evening_reset_ok = False
    partial_reason = []

    try:
        connection = init_db()
        connection.execute(
            """
            INSERT INTO daily_evaluations (
                business_date_berlin,
                evaluation_source,
                traffic_light_status,
                reasons_json,
                assessment_text,
                recommendation_text,
                warning_text,
                task_snapshot_id,
                created_at_utc
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(business_date_berlin, evaluation_source)
            DO UPDATE SET
                traffic_light_status = excluded.traffic_light_status,
                reasons_json = excluded.reasons_json,
                assessment_text = excluded.assessment_text,
                recommendation_text = excluded.recommendation_text,
                warning_text = excluded.warning_text,
                task_snapshot_id = excluded.task_snapshot_id,
                created_at_utc = excluded.created_at_utc
            """,
            (
                "2099-12-31",
                "verify_v2_foundation",
                "green",
                json.dumps(["smoke"], ensure_ascii=True),
                "Smoke test entry.",
                "Smoke test recommendation.",
                None,
                None,
                "2099-12-31T00:00:00+00:00",
            ),
        )
        connection.commit()
        connection.close()
        db_ok = True
        print("[OK] Database initialized and smoke row written.")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Database initialization/write failed: {exc}")

    gateway = TaskGateway()
    auth_status = gateway.get_auth_status()
    print("[INFO] TaskGateway auth status:")
    print(json.dumps(auth_status, indent=2, ensure_ascii=True, default=str))

    verify_list = os.getenv("EOS_VERIFY_TASK_LIST", "Inbox")
    try:
        task_result = gateway.get_open_tasks(verify_list)
        print("[INFO] TaskGateway read result:")
        print(json.dumps(task_result, indent=2, ensure_ascii=True, default=str))
        if task_result["status"] == "success":
            tasks_ok = True
            print(f"[OK] Open tasks in {verify_list}: {len(task_result['tasks'])}")
        else:
            partial_reason.append(f"tasks:{task_result['status']}")
            print(f"[PARTIAL] Task read is not live-ready: {task_result['status']}")
    except Exception as exc:  # noqa: BLE001
        partial_reason.append("tasks:exception")
        print(f"[PARTIAL] TaskGateway call raised an exception: {exc}")

    try:
        evening_result = run_evening_reset(dry_run=True, allow_stub_calendar=True)
        print("[INFO] evening_reset result:")
        print(json.dumps(evening_result, indent=2, ensure_ascii=True, default=str))
        if evening_result["status"] in {"success", "partial"}:
            evening_reset_ok = True
            if evening_result["calendar_source"] == "live_gog":
                live_calendar_ok = True
            else:
                partial_reason.append(f"calendar:{evening_result['calendar_source']}")
            print("[OK] evening_reset dry-run generated output.")
        else:
            partial_reason.append(f"evening_reset:{evening_result['status']}")
            print(f"[FAIL] evening_reset dry-run failed: {evening_result['status']}")
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] evening_reset dry-run crashed: {exc}")

    if db_ok and tasks_ok and evening_reset_ok and live_calendar_ok:
        print("OK")
        return 0

    if db_ok and evening_reset_ok:
        if partial_reason:
            print(f"PARTIAL ({', '.join(partial_reason)})")
        else:
            print("PARTIAL")
        return 3

    print("FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
