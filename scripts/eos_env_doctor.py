#!/usr/bin/env python3
"""Emit a secret-free JSON diagnosis for the local EOS development workspace."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


EOS_REPO = "endritmurati99/eos"
RECOMMENDED_CD = "/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant"


def run(args: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    completed = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def first_line(value: str) -> str:
    return value.splitlines()[0] if value else ""


def git_toplevel(cwd: Path) -> str:
    code, stdout, _ = run(["git", "rev-parse", "--show-toplevel"], cwd)
    return stdout if code == 0 else ""


def origin_url(cwd: Path) -> str:
    code, stdout, _ = run(["git", "remote", "get-url", "origin"], cwd)
    return stdout if code == 0 else ""


def has_path(cwd: Path, relative: str) -> bool:
    return (cwd / relative).exists()


def remote_points_to_eos(remote_url: str) -> bool:
    return EOS_REPO in remote_url or "endritmurati99/eos.git" in remote_url


def classify_repo(cwd: Path, remote_url: str) -> str:
    if has_path(cwd, "data/.openclaw/workspaces/personal-assistant"):
        return "openclaw_wrapper"

    markers = [
        has_path(cwd, "src/eos_cli.py"),
        has_path(cwd, "docs/eos"),
        has_path(cwd, "src/database/models.py"),
        has_path(cwd, "src/jobs"),
        has_path(cwd, "AGENTS.md") or has_path(cwd, "EOS-MASTER-CONTEXT.md"),
        remote_points_to_eos(remote_url),
    ]
    if sum(markers) >= 2:
        return "eos"

    code, log, _ = run(["git", "log", "--oneline", "-5"], cwd)
    log_text = log.lower() if code == 0 else ""
    if "solara" in log_text or has_path(cwd, "data/.openclaw/workspaces/solara"):
        return "solara"
    return "unknown"


def command_available(name: str) -> bool:
    return shutil.which(name) is not None


def likely_issue(repo_kind: str, has_origin: bool, remote_url: str) -> str:
    if repo_kind == "eos" and has_origin and remote_points_to_eos(remote_url):
        return "environment_ok_use_this_cwd"
    if repo_kind == "openclaw_wrapper":
        return "codex_started_in_openclaw_wrapper_cd_to_nested_eos_workspace"
    if repo_kind == "solara":
        return "current_repo_is_solara_not_eos"
    if repo_kind == "eos" and not has_origin:
        return "eos_repo_missing_origin"
    if has_origin and not remote_points_to_eos(remote_url):
        return "wrong_remote"
    return "unknown_workspace_or_missing_git_remote"


def main() -> int:
    cwd = Path.cwd()
    top = git_toplevel(cwd)
    remote_url = origin_url(cwd)
    repo_kind = classify_repo(cwd, remote_url)
    has_origin = bool(remote_url)
    gh_available = command_available("gh")
    codex_available = command_available("codex")

    output = {
        "cwd": str(cwd),
        "git_toplevel": top,
        "repo_kind": repo_kind,
        "has_origin": has_origin,
        "origin_url": remote_url,
        "gh_available": gh_available,
        "codex_available": codex_available,
        "likely_issue": likely_issue(repo_kind, has_origin, remote_url),
        "recommended_cd": RECOMMENDED_CD,
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
