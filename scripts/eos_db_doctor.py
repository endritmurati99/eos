#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pwd
import grp
import sqlite3
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = "data/eos_v2.db"
SIDECAR_SUFFIXES = ("-wal", "-shm", "-journal")


def run_doctor(
    db_path: str | None = None,
    *,
    workspace_root: Path | None = None,
    sqlite_probe: bool = True,
) -> dict[str, Any]:
    root = (workspace_root or Path.cwd()).resolve()
    resolved_db_path = resolve_db_path(db_path, workspace_root=root)
    effective_identity = current_identity()
    parent = resolved_db_path.parent
    target_identity = resolve_target_identity(default_target_path=parent)
    issues: list[dict[str, str]] = []
    if target_identity["summary"]["configured"] and not target_identity["summary"]["resolved"]:
        issues.append(
            issue(
                "warning",
                "target_identity_unresolved",
                "Configured target DB owner user/group could not be resolved.",
                error_class="environment_issue",
            )
        )

    parent_summary = summarize_path(parent, target_identity=target_identity)
    db_summary = summarize_path(resolved_db_path, target_identity=target_identity)

    if not parent.exists():
        issues.append(
            issue(
                "error",
                "parent_missing",
                "DB parent directory does not exist.",
                error_class="environment_issue",
            )
        )
    elif not parent_summary["writable"]:
        issues.append(
            issue(
                "error",
                "parent_not_writable",
                "DB parent directory is not writable.",
                error_class="readonly_database",
            )
        )

    if resolved_db_path.exists() and not db_summary["writable"]:
        issues.append(
            issue(
                "error",
                "db_not_writable",
                "DB file is not writable by the effective or target user.",
                error_class="readonly_database",
            )
        )

    probe_result = sqlite_write_probe(resolved_db_path) if sqlite_probe else {"status": "skipped"}
    if probe_result["status"] == "failed":
        issues.append(
            issue(
                "error",
                "sqlite_write_probe_failed",
                probe_result.get("error", "SQLite write probe failed."),
                error_class=probe_result.get("error_class", "unknown_failure"),
            )
        )

    parent_summary = summarize_path(parent, target_identity=target_identity)
    db_summary = summarize_path(resolved_db_path, target_identity=target_identity)
    sidecars = [summarize_path(sidecar_path(resolved_db_path, suffix), target_identity=target_identity) for suffix in SIDECAR_SUFFIXES]
    for sidecar in sidecars:
        if sidecar["exists"] and not sidecar["writable"]:
            issues.append(
                issue(
                    "warning",
                    "sidecar_not_writable",
                    f"SQLite sidecar is not writable: {sidecar['name']}",
                    error_class="readonly_database",
                )
            )

    status = status_from_issues(issues)
    db_owner_summary = db_summary["owner_summary"]
    parent_owner_summary = parent_summary["owner_summary"]
    return {
        "status": status,
        "error_class": error_class_from_issues(issues),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "db_path": str(resolved_db_path),
        "db_path_source": db_path_source(db_path),
        "exists": resolved_db_path.exists(),
        "parent_writable": parent_summary["writable"],
        "db_writable": db_summary["writable"] if resolved_db_path.exists() else parent_summary["writable"],
        "sqlite_write_probe": probe_result["status"],
        "sqlite_write_probe_detail": probe_result.get("detail"),
        "sqlite_write_probe_error_class": probe_result.get("error_class"),
        "effective_user": effective_identity,
        "owner_user": db_owner_summary.get("owner"),
        "owner_group": db_owner_summary.get("group"),
        "mode": db_owner_summary.get("mode"),
        "parent_owner_user": parent_owner_summary.get("owner"),
        "parent_owner_group": parent_owner_summary.get("group"),
        "parent_mode": parent_owner_summary.get("mode"),
        "owner_summary": db_summary["owner_summary"],
        "parent_summary": parent_summary["owner_summary"],
        "target_identity": target_identity["summary"],
        "sidecars": sidecars,
        "issues": issues,
    }


def resolve_db_path(db_path: str | None = None, *, workspace_root: Path | None = None) -> Path:
    raw_path = db_path or os.environ.get("EOS_DB_PATH") or DEFAULT_DB_PATH
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    return ((workspace_root or Path.cwd()) / path).resolve()


def db_path_source(explicit_path: str | None) -> str:
    if explicit_path:
        return "argument"
    if os.environ.get("EOS_DB_PATH"):
        return "EOS_DB_PATH"
    return "default"


def resolve_target_identity(default_target_path: Path | None = None) -> dict[str, Any]:
    user_name = os.environ.get("EOS_DB_OWNER_USER")
    group_name = os.environ.get("EOS_DB_OWNER_GROUP")
    configured = bool(user_name or group_name)
    uid = resolve_uid(user_name) if user_name else None
    gid = resolve_gid(group_name) if group_name else None
    inferred_from = None
    if not configured and os.geteuid() == 0 and default_target_path and default_target_path.exists():
        path_stat = default_target_path.stat()
        uid = path_stat.st_uid
        gid = path_stat.st_gid
        user_name = user_name_for_uid(uid)
        group_name = group_name_for_gid(gid)
        inferred_from = "db_parent_owner"
    gids = [gid] if gid is not None else []
    return {
        "user_name": user_name,
        "group_name": group_name,
        "uid": uid,
        "gid": gid,
        "gids": gids,
        "summary": {
            "configured": configured,
            "user": user_name,
            "group": group_name,
            "active": uid is not None or gid is not None,
            "inferred_from": inferred_from,
            "resolved": (uid is not None if user_name else True) and (gid is not None if group_name else True),
        },
    }


def current_identity() -> dict[str, Any]:
    uid = os.geteuid()
    gid = os.getegid()
    return {
        "uid": uid,
        "gid": gid,
        "user": user_name(uid),
        "group": group_name(gid),
        "groups": [group_name(group_id) for group_id in os.getgroups()],
    }


def summarize_path(path: Path, *, target_identity: dict[str, Any]) -> dict[str, Any]:
    exists = path.exists()
    owner_summary = owner_summary_for(path)
    effective_writable = os.access(path, os.W_OK) if exists else False
    mode_writable = mode_allows_current_write(path) if exists else False
    target_writable = target_allows_write(path, target_identity) if exists and target_identity["summary"]["active"] else None
    writable = target_writable if target_writable is not None else effective_writable and mode_writable
    return {
        "name": path.name,
        "path": str(path),
        "exists": exists,
        "effective_writable": effective_writable,
        "mode_writable": mode_writable,
        "target_writable": target_writable,
        "writable": bool(writable) if exists else False,
        "owner_summary": owner_summary,
    }


def owner_summary_for(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False}
    path_stat = path.stat()
    return {
        "exists": True,
        "owner": user_name(path_stat.st_uid),
        "group": group_name(path_stat.st_gid),
        "mode": oct(stat.S_IMODE(path_stat.st_mode)),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
    }


def mode_allows_current_write(path: Path) -> bool:
    return mode_allows_write(path, os.geteuid(), os.getegid(), os.getgroups())


def target_allows_write(path: Path, target_identity: dict[str, Any]) -> bool | None:
    uid = target_identity.get("uid")
    gid = target_identity.get("gid")
    if uid is None and gid is None:
        return None
    return mode_allows_write(path, uid if uid is not None else -1, gid if gid is not None else -1, target_identity["gids"])


def mode_allows_write(path: Path, uid: int, gid: int, gids: list[int]) -> bool:
    path_stat = path.stat()
    mode = path_stat.st_mode
    if uid == path_stat.st_uid:
        return bool(mode & stat.S_IWUSR)
    if gid == path_stat.st_gid or path_stat.st_gid in gids:
        return bool(mode & stat.S_IWGRP)
    return bool(mode & stat.S_IWOTH)


def sqlite_write_probe(db_path: Path) -> dict[str, str]:
    if not db_path.parent.exists():
        return {
            "status": "failed",
            "error_class": "environment_issue",
            "error": "DB parent directory does not exist.",
        }
    try:
        connection = sqlite3.connect(db_path)
        try:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS eos_db_write_probe (id INTEGER PRIMARY KEY, ts TEXT NOT NULL)"
            )
            connection.execute("INSERT INTO eos_db_write_probe (ts) VALUES (datetime('now'))")
            connection.commit()
            connection.execute("DELETE FROM eos_db_write_probe")
            connection.execute("DROP TABLE IF EXISTS eos_db_write_probe")
            connection.commit()
        finally:
            connection.close()
    except Exception as exc:  # noqa: BLE001 - diagnostics must classify any SQLite failure.
        error = f"{type(exc).__name__}: {exc}"
        return {
            "status": "failed",
            "error_class": classify_sqlite_error(error),
            "error": error,
        }
    return {
        "status": "success",
        "error_class": None,
        "detail": "probe table create/insert/delete/drop succeeded",
    }


def classify_sqlite_error(error: str) -> str:
    normalized = error.lower()
    if "attempt to write a readonly database" in normalized or "readonly database" in normalized:
        return "readonly_database"
    if "permission denied" in normalized or "unable to open database file" in normalized:
        return "readonly_database"
    return "unknown_failure"


def sidecar_path(db_path: Path, suffix: str) -> Path:
    return db_path.with_name(db_path.name + suffix)


def resolve_uid(user_name: str | None) -> int | None:
    if not user_name:
        return None
    try:
        return pwd.getpwnam(user_name).pw_uid
    except KeyError:
        return None


def resolve_gid(group_name: str | None) -> int | None:
    if not group_name:
        return None
    try:
        return grp.getgrnam(group_name).gr_gid
    except KeyError:
        return None


def user_name(uid: int) -> str:
    return user_name_for_uid(uid)


def group_name(gid: int) -> str:
    return group_name_for_gid(gid)


def user_name_for_uid(uid: int) -> str:
    try:
        return pwd.getpwuid(uid).pw_name
    except KeyError:
        return str(uid)


def group_name_for_gid(gid: int) -> str:
    try:
        return grp.getgrgid(gid).gr_name
    except KeyError:
        return str(gid)


def issue(severity: str, code: str, message: str, *, error_class: str) -> dict[str, str]:
    return {
        "severity": severity,
        "code": code,
        "error_class": error_class,
        "message": message,
    }


def status_from_issues(issues: list[dict[str, str]]) -> str:
    if any(item["severity"] == "error" for item in issues):
        return "failed"
    if issues:
        return "warning"
    return "success"


def error_class_from_issues(issues: list[dict[str, str]]) -> str | None:
    if not issues:
        return None
    for item in issues:
        if item["severity"] == "error":
            return item["error_class"]
    return issues[0]["error_class"]


def main(argv: list[str] | None = None) -> int:
    payload = run_doctor()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["status"] in {"success", "warning"} else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
