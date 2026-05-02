from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

from src.runtime import load_env_file

CANONICAL_LISTS = ("Inbox", "Next", "Waiting", "This Week")
PROVIDER_NAME = "gog_tasks"
EXIT_AUTH_REQUIRED = 4
EXIT_NOT_FOUND = 5
EXIT_CONFIG = 10
AUTH_URL_RE = re.compile(r"https://accounts\.google\.com/\S+")
PROVIDER_DISABLED_MARKERS = (
    "accessnotconfigured",
    "service_disabled",
    "api has not been used",
    "has not been used in project",
    "google tasks api has not been used",
    "google tasks api is disabled",
)
DISABLED_BY_ENV_ERROR = "Google Tasks integration is disabled by EOS_GOOGLE_TASKS_ENABLED=false."


def _env_flag_enabled(raw_value: str) -> bool:
    return raw_value.strip().lower() not in {"0", "false", "no", "off", "disabled"}


class TaskGateway:
    def __init__(
        self,
        gog_bin: str | None = None,
        account: str | None = None,
        credentials_path: str | None = None,
        token_root: str | None = None,
    ) -> None:
        self.workspace_root = Path(__file__).resolve().parents[2]
        load_env_file(self.workspace_root)
        self.calendar_source_path = self.workspace_root / "integrations" / "calendar-source.json"
        self.gog_bin = gog_bin or os.getenv("EOS_GOG_BIN") or shutil.which("gog")
        self.account = account or os.getenv("EOS_GOOGLE_ACCOUNT") or self._load_default_account()
        self.credentials_path = credentials_path or os.getenv("EOS_GOOGLE_CREDENTIALS_PATH")
        self.token_root = token_root or os.getenv("EOS_GOOGLE_TOKEN_PATH")
        self.tasks_enabled = _env_flag_enabled(os.getenv("EOS_GOOGLE_TASKS_ENABLED", "true"))

    def build_command_env(self) -> dict[str, str]:
        env = os.environ.copy()
        if self.token_root:
            token_root_path = Path(self.token_root).expanduser()
            token_root_path.mkdir(parents=True, exist_ok=True)
            env["XDG_CONFIG_HOME"] = str(token_root_path)
        return env

    def get_auth_status(self) -> dict[str, Any]:
        if not self.tasks_enabled:
            return self._base_status(
                status="provider_disabled",
                error=DISABLED_BY_ENV_ERROR,
            )

        if not self.gog_bin:
            return self._base_status(
                status="config_missing",
                error="gog binary not found; set EOS_GOG_BIN or add gog to PATH.",
            )

        if not self.account:
            return self._base_status(
                status="config_missing",
                error="Google account missing; set EOS_GOOGLE_ACCOUNT or integrations/calendar-source.json.account.",
            )

        status_cmd = self._run_raw(["auth", "status"], require_account=False)
        credentials_cmd = self._run_raw(["auth", "credentials", "list"], require_account=False)
        tokens_cmd = self._run_raw(["auth", "list"], require_account=False)

        parsed_status = self._load_json_payload(status_cmd["stdout"]) or {}
        credentials_payload = self._load_json_payload(credentials_cmd["stdout"])
        tokens_payload = self._load_json_payload(tokens_cmd["stdout"])

        credentials_missing = not bool(self._extract_items(credentials_payload))
        tokens_missing = not bool(self._extract_items(tokens_payload))

        config_path = None
        if isinstance(parsed_status, dict):
            config_path = (parsed_status.get("config") or {}).get("path")

        if credentials_missing:
            status = "config_missing"
            error = "OAuth client credentials are not stored yet."
        elif tokens_missing:
            status = "auth_required"
            error = "OAuth refresh token is not stored yet."
        else:
            status = "success"
            error = None

        return {
            "status": status,
            "provider": PROVIDER_NAME,
            "account": self.account,
            "gog_bin": self.gog_bin,
            "credentials_path": self.credentials_path,
            "token_root": self.token_root,
            "config_path": config_path,
            "credentials_configured": not credentials_missing,
            "tokens_configured": not tokens_missing,
            "error": error,
            "raw": {
                "auth_status": status_cmd,
                "credentials": credentials_cmd,
                "tokens": tokens_cmd,
            },
        }

    def prepare_headless_auth(self) -> dict[str, Any]:
        auth_status = self.get_auth_status()
        if auth_status["status"] == "provider_disabled":
            return {
                **auth_status,
                "next_step": "Set EOS_GOOGLE_TASKS_ENABLED=true before preparing Google Tasks auth.",
            }
        if auth_status["status"] == "success":
            return {
                **auth_status,
                "next_step": "OAuth is already configured.",
            }

        if auth_status["status"] == "config_missing" and not self.credentials_path:
            return {
                **auth_status,
                "next_step": "Set EOS_GOOGLE_CREDENTIALS_PATH to a local OAuth client JSON before bootstrapping auth.",
            }

        if self.credentials_path:
            credentials_file = Path(self.credentials_path).expanduser()
            if not credentials_file.exists():
                return self._base_status(
                    status="config_missing",
                    error=f"Credentials file does not exist: {credentials_file}",
                )

            credentials_cmd = self._run_raw(
                ["auth", "credentials", "set", str(credentials_file)],
                require_account=False,
                include_json_flags=False,
            )
            if credentials_cmd["returncode"] != 0:
                return self._base_status(
                    status="config_missing",
                    error=self._best_error(credentials_cmd) or "Failed to import OAuth client credentials.",
                    raw=credentials_cmd,
                )

        if not self.account:
            return self._base_status(
                status="config_missing",
                error="Google account missing; cannot start remote auth flow.",
            )

        step1_cmd = self._run_raw(
            ["auth", "add", self.account, "--remote", "--step", "1", "--services", "tasks"],
            require_account=False,
            include_json_flags=False,
        )
        if step1_cmd["returncode"] != 0:
            return self._base_status(
                status=self._status_from_command(step1_cmd),
                error=self._best_error(step1_cmd) or "Failed to prepare headless auth flow.",
                raw=step1_cmd,
            )

        combined_output = "\n".join(
            part for part in [step1_cmd["stdout"], step1_cmd["stderr"]] if part
        )
        auth_url_match = AUTH_URL_RE.search(combined_output)

        return {
            "status": "auth_required",
            "provider": PROVIDER_NAME,
            "account": self.account,
            "auth_url": auth_url_match.group(0) if auth_url_match else None,
            "next_step": "Open the auth_url, finish consent, and pass the full redirect URL to finalize_headless_auth().",
            "error": None if auth_url_match else "Auth URL was not found in gog output.",
            "raw": step1_cmd,
        }

    def finalize_headless_auth(self, redirect_url: str) -> dict[str, Any]:
        if not self.tasks_enabled:
            return self._base_status(
                status="provider_disabled",
                error=DISABLED_BY_ENV_ERROR,
            )

        if not redirect_url:
            return self._base_status(
                status="config_missing",
                error="redirect_url is required for finalize_headless_auth().",
            )

        if not self.gog_bin:
            return self._base_status(
                status="config_missing",
                error="gog binary not found; set EOS_GOG_BIN or add gog to PATH.",
            )

        if not self.account:
            return self._base_status(
                status="config_missing",
                error="Google account missing; cannot finalize headless auth flow.",
            )

        if self.credentials_path:
            credentials_file = Path(self.credentials_path).expanduser()
            if credentials_file.exists():
                self._run_raw(
                    ["auth", "credentials", "set", str(credentials_file)],
                    require_account=False,
                    include_json_flags=False,
                )

        step2_cmd = self._run_raw(
            [
                "auth",
                "add",
                self.account,
                "--remote",
                "--step",
                "2",
                "--services",
                "tasks",
                "--auth-url",
                redirect_url,
            ],
            require_account=False,
            include_json_flags=False,
        )
        if step2_cmd["returncode"] != 0:
            return self._base_status(
                status=self._status_from_command(step2_cmd),
                error=self._best_error(step2_cmd) or "Failed to exchange redirect URL for refresh token.",
                raw=step2_cmd,
            )

        return {
            **self.get_auth_status(),
            "raw": step2_cmd,
        }

    def get_open_tasks(self, list_name: str) -> dict[str, Any]:
        if not self.tasks_enabled:
            return self._task_result(
                status="provider_disabled",
                list_name=list_name,
                error=DISABLED_BY_ENV_ERROR,
            )

        if list_name not in CANONICAL_LISTS:
            return self._task_result(
                status="not_found",
                list_name=list_name,
                error=f"Unsupported list name: {list_name}",
            )

        resolution = self._resolve_list_id(list_name)
        if resolution["status"] != "success":
            return self._task_result(
                status=resolution["status"],
                list_name=list_name,
                error=resolution.get("error"),
                list_id=resolution.get("list_id"),
            )

        command = self._run_raw(
            ["tasks", "list", resolution["list_id"], "--all"],
            require_account=True,
        )
        if command["returncode"] != 0:
            return self._task_result(
                status=self._status_from_command(command),
                list_name=list_name,
                list_id=resolution["list_id"],
                error=self._best_error(command),
            )

        tasks_payload = self._load_json_payload(command["stdout"])
        tasks = [
            self._normalize_task(task)
            for task in self._extract_items(tasks_payload)
            if task.get("status") != "completed"
            and not task.get("deleted", False)
            and not task.get("hidden", False)
        ]

        return {
            "status": "success",
            "provider": PROVIDER_NAME,
            "list_name": list_name,
            "list_id": resolution["list_id"],
            "tasks": tasks,
            "error": None,
        }

    def list_structure(self) -> dict[str, Any]:
        if not self.tasks_enabled:
            return {
                "status": "provider_disabled",
                "provider": PROVIDER_NAME,
                "canonical_lists": list(CANONICAL_LISTS),
                "task_lists": [],
                "missing_lists": list(CANONICAL_LISTS),
                "duplicate_lists": [],
                "error": DISABLED_BY_ENV_ERROR,
            }

        command = self._run_raw(["tasks", "lists", "list"], require_account=True)
        if command["returncode"] != 0:
            return {
                "status": self._status_from_command(command),
                "provider": PROVIDER_NAME,
                "canonical_lists": list(CANONICAL_LISTS),
                "task_lists": [],
                "missing_lists": list(CANONICAL_LISTS),
                "duplicate_lists": [],
                "error": self._best_error(command),
            }

        payload = self._load_json_payload(command["stdout"])
        task_lists = [
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "updated": item.get("updated"),
            }
            for item in self._extract_items(payload)
        ]
        titles = [item["title"] for item in task_lists]
        missing_lists = [name for name in CANONICAL_LISTS if name not in titles]
        duplicate_lists = [
            name
            for name in CANONICAL_LISTS
            if sum(1 for title in titles if title == name) > 1
        ]

        status = "success"
        error = None
        if duplicate_lists:
            status = "ambiguous"
            error = f"Duplicate canonical Google Tasks lists: {', '.join(duplicate_lists)}"
        elif missing_lists:
            status = "not_found"
            error = f"Missing canonical Google Tasks lists: {', '.join(missing_lists)}"

        return {
            "status": status,
            "provider": PROVIDER_NAME,
            "canonical_lists": list(CANONICAL_LISTS),
            "task_lists": task_lists,
            "missing_lists": missing_lists,
            "duplicate_lists": duplicate_lists,
            "error": error,
        }

    def ensure_canonical_lists(self, *, dry_run: bool = True) -> dict[str, Any]:
        structure = self.list_structure()
        if structure["status"] not in {"success", "not_found"}:
            return {
                **structure,
                "dry_run": dry_run,
                "created_lists": [],
            }

        missing_lists = list(structure["missing_lists"])
        if not missing_lists:
            return {
                **structure,
                "status": "success",
                "dry_run": dry_run,
                "created_lists": [],
            }

        if dry_run:
            return {
                **structure,
                "status": "would_create",
                "dry_run": True,
                "created_lists": [],
                "error": None,
            }

        created_lists = []
        for list_name in missing_lists:
            command = self._run_raw(
                ["tasks", "lists", "create", list_name],
                require_account=True,
            )
            if command["returncode"] != 0:
                return {
                    "status": self._status_from_command(command),
                    "provider": PROVIDER_NAME,
                    "canonical_lists": list(CANONICAL_LISTS),
                    "task_lists": structure["task_lists"],
                    "missing_lists": missing_lists,
                    "duplicate_lists": structure["duplicate_lists"],
                    "dry_run": False,
                    "created_lists": created_lists,
                    "error": self._best_error(command),
                }

            payload = self._load_json_payload(command["stdout"])
            created_lists.append(
                {
                    "id": (payload or {}).get("id"),
                    "title": (payload or {}).get("title") or list_name,
                }
            )

        return {
            **self.list_structure(),
            "dry_run": False,
            "created_lists": created_lists,
        }

    def readOpenTasks(self, listNames: tuple[str, ...] | list[str] | None = None) -> dict[str, Any]:  # noqa: N802
        normalized_names = tuple(listNames) if listNames is not None else None
        return self.get_canonical_open_tasks(normalized_names)

    def get_canonical_open_tasks(
        self,
        list_names: tuple[str, ...] | None = None,
    ) -> dict[str, Any]:
        read_order = list_names or CANONICAL_LISTS
        tasks_by_list: dict[str, list[dict[str, Any]]] = {}
        failed_lists: list[dict[str, str]] = []

        for list_name in read_order:
            read_result = self.get_open_tasks(list_name)
            if read_result["status"] == "success":
                tasks_by_list[list_name] = [
                    {**task, "list_name": list_name}
                    for task in read_result["tasks"]
                ]
                continue

            tasks_by_list[list_name] = []
            failed_lists.append(
                {
                    "list_name": list_name,
                    "status": read_result["status"],
                    "error": read_result.get("error") or "",
                }
            )

        open_task_count = sum(len(tasks) for tasks in tasks_by_list.values())
        return {
            "provider": PROVIDER_NAME,
            "task_read_status": self._aggregate_read_status(failed_lists, open_task_count),
            "tasks_by_list": tasks_by_list,
            "failed_lists": failed_lists,
            "open_task_count": open_task_count,
        }

    def createTask(self, input: Mapping[str, Any]) -> dict[str, Any]:  # noqa: A002,N802
        title = str(input.get("title") or "")
        list_name = str(input.get("listName") or input.get("list_name") or "Inbox")
        notes = input.get("notes")
        due = input.get("due")
        return self.create_task(
            list_name=list_name,
            title=title,
            notes=str(notes) if notes is not None else None,
            due=str(due) if due is not None else None,
        )

    def create_task(
        self,
        list_name: str,
        title: str,
        notes: str | None = None,
        due: str | None = None,
    ) -> dict[str, Any]:
        if not self.tasks_enabled:
            return self._mutation_result(
                status="provider_disabled",
                list_name=list_name,
                error=DISABLED_BY_ENV_ERROR,
            )

        if not title.strip():
            return self._mutation_result(
                status="provider_error",
                list_name=list_name,
                error="Task title is required.",
            )

        resolution = self._resolve_list_id(list_name)
        if resolution["status"] != "success":
            return self._mutation_result(
                status=resolution["status"],
                list_name=list_name,
                error=resolution.get("error"),
            )

        args = ["tasks", "add", resolution["list_id"], "--title", title]
        if notes:
            args.extend(["--notes", notes])
        if due:
            args.extend(["--due", due])

        command = self._run_raw(args, require_account=True)
        if command["returncode"] != 0:
            return self._mutation_result(
                status=self._status_from_command(command),
                list_name=list_name,
                error=self._best_error(command),
            )

        payload = self._load_json_payload(command["stdout"])
        return self._mutation_result(
            status="success",
            list_name=list_name,
            task_id=(payload or {}).get("id"),
            error=None,
        )

    def completeTask(self, ref: str | Mapping[str, Any]) -> dict[str, Any]:  # noqa: N802
        if isinstance(ref, Mapping):
            task_id = ref.get("taskId") or ref.get("task_id") or ref.get("id")
            list_name = ref.get("listName") or ref.get("list_name")
            title = ref.get("title")
            if task_id:
                return self.complete_task(str(task_id), str(list_name) if list_name else None)
            if title:
                resolved = self._resolve_open_task_by_title(str(title))
                if resolved["status"] != "success":
                    return self._mutation_result(
                        status=resolved["status"],
                        list_name=resolved.get("list_name"),
                        error=resolved.get("error"),
                    )
                return self.complete_task(resolved["task_id"], resolved["list_name"])
            return self._mutation_result(
                status="provider_error",
                list_name=None,
                error="completeTask requires taskId, id, or title.",
            )

        task_id_result = self.complete_task(str(ref))
        if task_id_result["status"] != "not_found":
            return task_id_result

        resolved = self._resolve_open_task_by_title(str(ref))
        if resolved["status"] != "success":
            return self._mutation_result(
                status=resolved["status"],
                list_name=resolved.get("list_name"),
                error=resolved.get("error"),
            )
        return self.complete_task(resolved["task_id"], resolved["list_name"])

    def complete_task(self, task_id: str, list_name: str | None = None) -> dict[str, Any]:
        if not self.tasks_enabled:
            return self._mutation_result(
                status="provider_disabled",
                list_name=list_name,
                error=DISABLED_BY_ENV_ERROR,
            )

        if not task_id:
            return self._mutation_result(
                status="provider_error",
                list_name=list_name,
                error="task_id is required.",
            )

        if list_name:
            resolution = self._resolve_list_id(list_name)
            if resolution["status"] != "success":
                return self._mutation_result(
                    status=resolution["status"],
                    list_name=list_name,
                    error=resolution.get("error"),
                )
            target_list_name = list_name
            target_list_id = resolution["list_id"]
        else:
            matches = []
            failed_lists: list[dict[str, str]] = []
            for candidate in CANONICAL_LISTS:
                read_result = self.get_open_tasks(candidate)
                if read_result["status"] != "success":
                    failed_lists.append(
                        {
                            "list_name": candidate,
                            "status": read_result["status"],
                            "error": read_result.get("error") or "",
                        }
                    )
                    continue
                for task in read_result["tasks"]:
                    if task.get("id") == task_id:
                        matches.append((candidate, read_result["list_id"]))
                        break

            if not matches:
                if failed_lists:
                    return self._mutation_result(
                        status=self._aggregate_read_status(failed_lists, 0),
                        list_name=None,
                        error="Could not verify open tasks before completion.",
                    )
                return self._mutation_result(
                    status="not_found",
                    list_name=None,
                    error=f"Task {task_id} was not found in open tasks.",
                )
            if len(matches) > 1:
                return self._mutation_result(
                    status="ambiguous",
                    list_name=None,
                    error=f"Task {task_id} matched multiple lists.",
                )
            target_list_name, target_list_id = matches[0]

        command = self._run_raw(
            ["tasks", "done", target_list_id, task_id],
            require_account=True,
        )
        if command["returncode"] != 0:
            return self._mutation_result(
                status=self._status_from_command(command),
                list_name=target_list_name,
                error=self._best_error(command),
            )

        payload = self._load_json_payload(command["stdout"])
        completed_task_id = (payload or {}).get("id") or task_id
        return self._mutation_result(
            status="success",
            list_name=target_list_name,
            task_id=completed_task_id,
            error=None,
        )

    def _resolve_open_task_by_title(self, title: str) -> dict[str, Any]:
        if not title.strip():
            return {
                "status": "provider_error",
                "error": "Task title is required.",
                "task_id": None,
                "list_name": None,
            }

        matches = []
        failed_lists: list[dict[str, str]] = []
        for list_name in CANONICAL_LISTS:
            read_result = self.get_open_tasks(list_name)
            if read_result["status"] != "success":
                failed_lists.append(
                    {
                        "list_name": list_name,
                        "status": read_result["status"],
                        "error": read_result.get("error") or "",
                    }
                )
                continue
            for task in read_result["tasks"]:
                if task.get("title") == title:
                    matches.append(
                        {
                            "task_id": task.get("id"),
                            "title": task.get("title"),
                            "list_name": list_name,
                            "list_id": read_result["list_id"],
                        }
                    )

        if len(matches) == 1:
            return {
                "status": "success",
                "error": None,
                **matches[0],
            }
        if len(matches) > 1:
            locations = ", ".join(match["list_name"] for match in matches)
            return {
                "status": "ambiguous",
                "error": f"Task title matched multiple open tasks: {locations}",
                "matches": matches,
                "task_id": None,
                "list_name": None,
            }
        if failed_lists:
            return {
                "status": self._aggregate_read_status(failed_lists, 0),
                "error": "Could not verify open tasks before resolving title.",
                "failed_lists": failed_lists,
                "task_id": None,
                "list_name": None,
            }
        return {
            "status": "not_found",
            "error": f"Open task title was not found: {title}",
            "task_id": None,
            "list_name": None,
        }

    def _resolve_list_id(self, list_name: str) -> dict[str, Any]:
        if list_name not in CANONICAL_LISTS:
            return {
                "status": "not_found",
                "error": f"Unsupported list name: {list_name}",
                "list_id": None,
            }

        list_command = self._run_raw(["tasks", "lists", "list"], require_account=True)
        if list_command["returncode"] != 0:
            return {
                "status": self._status_from_command(list_command),
                "error": self._best_error(list_command),
                "list_id": None,
            }

        payload = self._load_json_payload(list_command["stdout"])
        lists = self._extract_items(payload)
        matches = [item for item in lists if item.get("title") == list_name]
        if not matches:
            return {
                "status": "not_found",
                "error": f"Canonical Google Tasks list missing: {list_name}",
                "list_id": None,
            }
        if len(matches) > 1:
            return {
                "status": "ambiguous",
                "error": f"Multiple Google Tasks lists matched title: {list_name}",
                "list_id": None,
            }

        return {
            "status": "success",
            "error": None,
            "list_id": matches[0].get("id"),
        }

    def _run_raw(
        self,
        args: list[str],
        *,
        require_account: bool,
        include_json_flags: bool = True,
    ) -> dict[str, Any]:
        if not self.gog_bin:
            return {
                "returncode": EXIT_CONFIG,
                "stdout": "",
                "stderr": "gog binary not found.",
                "command": [],
            }

        command = [self.gog_bin]
        if require_account:
            if not self.account:
                return {
                    "returncode": EXIT_CONFIG,
                    "stdout": "",
                    "stderr": "Google account is not configured.",
                    "command": [],
                }
            command.extend(["-a", self.account])

        command.extend(args)
        if include_json_flags:
            command.extend(["--json", "--results-only", "--no-input"])
        else:
            command.append("--no-input")

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            env=self.build_command_env(),
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "command": command,
        }

    def _load_default_account(self) -> str | None:
        if not self.calendar_source_path.exists():
            return None

        try:
            payload = json.loads(self.calendar_source_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return payload.get("account")

    def _load_json_payload(self, raw_output: str) -> Any:
        if not raw_output.strip():
            return None
        try:
            return json.loads(raw_output)
        except json.JSONDecodeError:
            return None

    def _extract_items(self, payload: Any) -> list[dict[str, Any]]:
        if payload is None:
            return []
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("items", "results", "tasks"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
            return [payload]
        return []

    def _normalize_task(self, task: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": task.get("id"),
            "title": task.get("title") or "(ohne Titel)",
            "notes": task.get("notes"),
            "status": task.get("status"),
            "due": task.get("due"),
            "updated": task.get("updated"),
            "completed": task.get("completed"),
        }

    def _status_from_command(self, command: dict[str, Any]) -> str:
        error_text = self._best_error(command) or ""
        normalized_error = error_text.lower()
        if any(marker in normalized_error for marker in PROVIDER_DISABLED_MARKERS):
            return "provider_disabled"
        if command["returncode"] == EXIT_CONFIG or "OAuth client credentials missing" in error_text:
            return "config_missing"
        if command["returncode"] == EXIT_AUTH_REQUIRED or "No tokens stored" in error_text:
            return "auth_required"
        if command["returncode"] == EXIT_NOT_FOUND:
            return "not_found"
        return "provider_error"

    def _aggregate_read_status(
        self,
        failed_lists: list[dict[str, str]],
        open_task_count: int,
    ) -> str:
        if failed_lists and open_task_count:
            return "partial"
        if failed_lists:
            return failed_lists[0]["status"] or "provider_error"
        return "success"

    def _best_error(self, command: dict[str, Any]) -> str | None:
        for value in (command.get("stderr"), command.get("stdout")):
            if value:
                return value
        return None

    def _contains_text(self, command: dict[str, Any], needle: str) -> bool:
        combined = "\n".join(
            part for part in [command.get("stdout", ""), command.get("stderr", "")] if part
        )
        return needle in combined

    def _base_status(
        self,
        *,
        status: str,
        error: str | None,
        raw: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "status": status,
            "provider": PROVIDER_NAME,
            "account": self.account,
            "gog_bin": self.gog_bin,
            "credentials_path": self.credentials_path,
            "token_root": self.token_root,
            "error": error,
            "raw": raw,
        }

    def _task_result(
        self,
        *,
        status: str,
        list_name: str | None,
        list_id: str | None = None,
        error: str | None,
    ) -> dict[str, Any]:
        return {
            "status": status,
            "provider": PROVIDER_NAME,
            "list_name": list_name,
            "list_id": list_id,
            "tasks": [],
            "error": error,
        }

    def _mutation_result(
        self,
        *,
        status: str,
        list_name: str | None,
        task_id: str | None = None,
        error: str | None,
    ) -> dict[str, Any]:
        return {
            "status": status,
            "provider": PROVIDER_NAME,
            "task_id": task_id,
            "list_name": list_name,
            "error": error,
        }
