#!/usr/bin/env python3
from __future__ import annotations

import importlib
import importlib.metadata
import importlib.util
import json
import os
import pkgutil
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_SCAN_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "credentials",
    "data",
    "node_modules",
    "tokens",
}
ENV_KEYS = (
    "EOS_DB_PATH",
    "EOS_ENV",
    "EOS_RUNTIME",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GOOGLE_CLIENT_ID",
    "GMAIL_CLIENT_ID",
    "OPENAI_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "PATH",
    "PYTHONPATH",
    "VIRTUAL_ENV",
)


def run_doctor(workspace_root: Path | None = None) -> dict[str, Any]:
    root = (workspace_root or WORKSPACE_ROOT).resolve()
    _ensure_workspace_on_path(root)
    issues: list[dict[str, Any]] = []

    imports = {
        "src.eos_cli": check_import("src.eos_cli"),
        "src.runtime": check_import("src.runtime"),
    }
    for name, result in imports.items():
        if result["status"] != "success":
            issues.append({"severity": "error", "code": "import_failed", "name": name, "detail": result["detail"]})

    tools = check_tools()
    for name, result in tools.items():
        if result["status"] != "success":
            issues.append({"severity": "warning", "code": "tool_missing", "name": name, "detail": result["detail"]})

    python_info = collect_python_info()
    if python_info["pip"]["status"] != "success":
        issues.append(
            {
                "severity": "warning",
                "code": "pip_unavailable",
                "name": "pip",
                "detail": python_info["pip"]["detail"],
            }
        )

    dependencies = scan_telekom_dependencies(root)
    if dependencies["telekom_related_packages"] or dependencies["telekom_related_modules"]:
        issues.append(
            {
                "severity": "warning",
                "code": "telekom_dependency_found",
                "detail": "One or more installed packages or modules contain 'telekom' in the name.",
            }
        )
    if dependencies["local_telekom_conflicts"]:
        issues.append(
            {
                "severity": "warning",
                "code": "telekom_local_conflict",
                "detail": "One or more local files contain 'telekom' in the name.",
            }
        )

    status = "success"
    if any(issue["severity"] == "error" for issue in issues):
        status = "error"
    elif issues:
        status = "warning"

    return {
        "status": status,
        "python": python_info,
        "cwd": str(Path.cwd()),
        "workspace_root": str(root),
        "sys_path": shorten_sys_path(sys.path),
        "environment": collect_environment(),
        "imports": imports,
        "tools": tools,
        "dependencies": dependencies,
        "issues": issues,
    }


def collect_python_info() -> dict[str, Any]:
    return {
        "executable": sys.executable,
        "version": sys.version.split()[0],
        "version_full": sys.version,
        "aliases": {
            "python": check_command_version("python", "--version"),
            "python3": check_command_version("python3", "--version"),
        },
        "pip": check_python_module_cli("pip", "--version"),
    }


def collect_environment(keys: tuple[str, ...] = ENV_KEYS) -> dict[str, dict[str, Any]]:
    environment: dict[str, dict[str, Any]] = {}
    for key in keys:
        value = os.environ.get(key)
        environment[key] = {
            "set": value is not None,
            "value": mask_env_value(value),
        }
    return environment


def mask_env_value(value: str | None) -> str | None:
    if value is None:
        return None
    return f"<masked:{len(value)}>"


def check_import(module_name: str) -> dict[str, str]:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - diagnostics should classify any import failure.
        return {"status": "failed", "detail": f"{type(exc).__name__}: {exc}"}

    module_file = getattr(module, "__file__", None)
    return {"status": "success", "detail": str(module_file or "<namespace>")}


def check_tools() -> dict[str, dict[str, str]]:
    pytest_spec = importlib.util.find_spec("pytest")
    return {
        "pytest": {
            "status": "success" if pytest_spec else "missing",
            "detail": str(pytest_spec.origin) if pytest_spec and pytest_spec.origin else "pytest module not importable",
        },
        "gog": check_command("gog"),
        "gh": check_command("gh"),
        "systemctl": check_command("systemctl"),
    }


def check_command(name: str) -> dict[str, str]:
    path = shutil.which(name)
    if not path:
        return {"status": "missing", "detail": f"{name} not found on PATH"}
    return {"status": "success", "detail": path}


def check_command_version(command: str, *args: str) -> dict[str, str]:
    path = shutil.which(command)
    if not path:
        return {"status": "missing", "detail": f"{command} not found on PATH"}
    result = _run_command((command, *args))
    if result["returncode"] != 0:
        return {"status": "failed", "detail": result["output"]}
    return {"status": "success", "detail": result["output"]}


def check_python_module_cli(module: str, *args: str) -> dict[str, str]:
    result = _run_command((sys.executable, "-m", module, *args))
    if result["returncode"] != 0:
        return {"status": "missing", "detail": result["output"]}
    return {"status": "success", "detail": result["output"]}


def scan_telekom_dependencies(workspace_root: Path) -> dict[str, Any]:
    return {
        "telekom_related_packages": scan_telekom_packages(),
        "telekom_related_modules": scan_telekom_modules(),
        "local_telekom_conflicts": scan_local_telekom_conflicts(workspace_root),
    }


def scan_telekom_packages() -> list[dict[str, str]]:
    packages: list[dict[str, str]] = []
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata.get("Name") or distribution.name
        if "telekom" in name.lower():
            packages.append(
                {
                    "name": name,
                    "version": distribution.version,
                    "location": str(distribution.locate_file("")),
                }
            )
    return sorted(packages, key=lambda item: item["name"].lower())


def scan_telekom_modules() -> list[dict[str, str]]:
    modules = []
    for module in pkgutil.iter_modules():
        if "telekom" in module.name.lower():
            modules.append(
                {
                    "name": module.name,
                    "importer": str(module.module_finder),
                }
            )
    return sorted(modules, key=lambda item: item["name"].lower())


def scan_local_telekom_conflicts(workspace_root: Path) -> list[dict[str, str]]:
    conflicts: list[dict[str, str]] = []
    if not workspace_root.exists():
        return conflicts

    for path in workspace_root.rglob("*"):
        if _should_skip(path, workspace_root):
            continue
        if "telekom" not in path.name.lower():
            continue
        conflicts.append(
            {
                "path": str(path.relative_to(workspace_root)),
                "kind": "directory" if path.is_dir() else "file",
            }
        )
    return sorted(conflicts, key=lambda item: item["path"].lower())


def shorten_sys_path(paths: list[str], *, limit: int = 12) -> list[str]:
    shortened = [path or "<cwd>" for path in paths[:limit]]
    if len(paths) > limit:
        shortened.append(f"<{len(paths) - limit} more>")
    return shortened


def main() -> int:
    payload = run_doctor()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _ensure_workspace_on_path(workspace_root: Path) -> None:
    root = str(workspace_root)
    if root not in sys.path:
        sys.path.insert(0, root)


def _run_command(command: tuple[str, ...]) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001 - command diagnostics should not crash the doctor.
        return {"returncode": 127, "output": f"{type(exc).__name__}: {exc}"}
    return {
        "returncode": completed.returncode,
        "output": completed.stdout.strip(),
    }


def _should_skip(path: Path, workspace_root: Path) -> bool:
    try:
        relative = path.relative_to(workspace_root)
    except ValueError:
        return True
    return any(part in EXCLUDED_SCAN_DIRS for part in relative.parts)


if __name__ == "__main__":
    raise SystemExit(main())
