#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.gateways.google_tasks import TaskGateway  # noqa: E402


class MissingListGateway(TaskGateway):
    def __init__(self) -> None:
        self.gog_bin = "/bin/false"
        self.account = "person@example.com"
        self.credentials_path = None
        self.token_root = "/tmp/eos-config"
        self.tasks_enabled = True

    def _run_raw(self, args, *, require_account, include_json_flags=True):  # noqa: ANN001,ARG002
        return {
            "returncode": 0,
            "stdout": '[{"id":"list-inbox","title":"Inbox"}]',
            "stderr": "",
            "command": ["fake", *args],
        }


class AmbiguousTitleGateway(TaskGateway):
    def __init__(self) -> None:
        self.gog_bin = "/bin/false"
        self.account = "person@example.com"
        self.credentials_path = None
        self.token_root = "/tmp/eos-config"
        self.tasks_enabled = True

    def get_open_tasks(self, list_name: str) -> dict[str, object]:
        if list_name == "Next":
            return {
                "status": "success",
                "provider": "gog_tasks",
                "list_name": "Next",
                "list_id": "next-list",
                "tasks": [{"id": "task-a", "title": "Mit Max Ruecksprache halten"}],
                "error": None,
            }
        if list_name == "This Week":
            return {
                "status": "success",
                "provider": "gog_tasks",
                "list_name": "This Week",
                "list_id": "week-list",
                "tasks": [{"id": "task-b", "title": "Mit Max Ruecksprache halten"}],
                "error": None,
            }
        return {
            "status": "success",
            "provider": "gog_tasks",
            "list_name": list_name,
            "list_id": f"{list_name}-list",
            "tasks": [],
            "error": None,
        }


def main() -> int:
    previous_env = {
        key: os.environ.get(key)
        for key in (
            "EOS_GOG_BIN",
            "EOS_GOOGLE_TOKEN_PATH",
            "EOS_GOOGLE_ACCOUNT",
            "EOS_GOOGLE_TASKS_ENABLED",
        )
    }
    os.environ["EOS_GOG_BIN"] = "/tmp/eos-fake-gog"
    os.environ["EOS_GOOGLE_TOKEN_PATH"] = "/tmp/eos-config"
    os.environ["EOS_GOOGLE_ACCOUNT"] = "person@example.com"
    os.environ["EOS_GOOGLE_TASKS_ENABLED"] = "false"
    disabled_gateway = TaskGateway()
    assert disabled_gateway.get_auth_status()["status"] == "provider_disabled"
    assert disabled_gateway.list_structure()["status"] == "provider_disabled"
    assert disabled_gateway.readOpenTasks()["task_read_status"] == "provider_disabled"
    assert disabled_gateway.createTask({"title": "blocked"})["status"] == "provider_disabled"
    assert disabled_gateway.completeTask({"taskId": "blocked"})["status"] == "provider_disabled"

    os.environ["EOS_GOOGLE_TASKS_ENABLED"] = "true"
    env_gateway = TaskGateway()
    assert env_gateway.gog_bin == "/tmp/eos-fake-gog"
    assert env_gateway.token_root == "/tmp/eos-config"
    assert env_gateway.account == "person@example.com"
    for key, value in previous_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    gateway = TaskGateway(gog_bin="/bin/false", account="person@example.com")

    disabled_status = gateway._status_from_command(  # noqa: SLF001
        {
            "returncode": 1,
            "stdout": "",
            "stderr": "googleapi: Error 403: accessNotConfigured",
        }
    )
    assert disabled_status == "provider_disabled"

    disabled_status_json = gateway._status_from_command(  # noqa: SLF001
        {
            "returncode": 1,
            "stdout": '{"error":{"status":"SERVICE_DISABLED"}}',
            "stderr": "",
        }
    )
    assert disabled_status_json == "provider_disabled"

    assert gateway._aggregate_read_status([], 0) == "success"  # noqa: SLF001
    assert gateway._aggregate_read_status(  # noqa: SLF001
        [{"list_name": "Inbox", "status": "provider_disabled", "error": "disabled"}],
        0,
    ) == "provider_disabled"
    assert gateway._aggregate_read_status(  # noqa: SLF001
        [{"list_name": "Inbox", "status": "provider_error", "error": "boom"}],
        2,
    ) == "partial"

    list_result = MissingListGateway().list_structure()
    assert list_result["status"] == "not_found"
    assert "Next" in list_result["missing_lists"]

    ensure_result = MissingListGateway().ensure_canonical_lists()
    assert ensure_result["status"] == "would_create"
    assert ensure_result["dry_run"] is True
    assert ensure_result["created_lists"] == []

    ambiguous_result = AmbiguousTitleGateway().completeTask("Mit Max Ruecksprache halten")
    assert ambiguous_result["status"] == "ambiguous"
    assert "multiple open tasks" in ambiguous_result["error"]

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
