#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


KNOWN_WARNING_CLASSES = {
    "readonly_database",
    "missing_gog",
    "missing_systemctl",
    "missing_python_alias",
    "missing_secrets",
    "provider_auth_required",
    "environment_issue",
}

SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(\"|\b)(title|summary|location|snippet|thread[_-]?id|message[_-]?id|"
    r"gmail[_-]?id|email|attendees|description|notes|output_markdown|chat[_-]?id|"
    r"telegram[_-]?(target|chat|to))\1?\s*[:=]"
)
SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"(?i)\btelegram:\d+\b"),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    re.compile(r"(?i)\b(thread|message|gmail)[_-]?[a-z0-9]{8,}\b"),
    re.compile(r"(?i)\b(token|secret|password|api[_-]?key|client_secret)\b\s*[:=]"),
    re.compile(r"(?i)(/home|/users)/[^/\s]+/"),
)


def mask_value(value: object) -> object:
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, str):
        return f"<masked:{len(value)}>"
    if isinstance(value, list):
        return [mask_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(mask_value(item) for item in value)
    if isinstance(value, dict):
        return {str(key): mask_value(item) for key, item in value.items()}
    return "<masked>"


def contains_sensitive_output(text: str) -> bool:
    if not text:
        return False
    if SENSITIVE_KEY_PATTERN.search(text):
        return True
    return any(pattern.search(text) for pattern in SENSITIVE_VALUE_PATTERNS)


def classify_error(stdout: str, stderr: str) -> str:
    combined = f"{stdout}\n{stderr}".lower()
    if not combined.strip():
        return "unknown"

    if "attempt to write a readonly database" in combined or "readonly database" in combined:
        return "readonly_database"
    if "db_not_writable" in combined or "parent_not_writable" in combined:
        return "readonly_database"
    if "python: command not found" in combined or "python not found on path" in combined:
        return "missing_python_alias"
    if "no such file or directory: 'python'" in combined or 'no such file or directory: "python"' in combined:
        return "missing_python_alias"
    if "gog: command not found" in combined or "gog not found" in combined:
        return "missing_gog"
    if "no such file or directory: 'gog'" in combined or 'no such file or directory: "gog"' in combined:
        return "missing_gog"
    if "systemctl: command not found" in combined or "systemctl unavailable" in combined:
        return "missing_systemctl"
    if "system has not been booted with systemd" in combined or "failed to connect to bus" in combined:
        return "environment_issue"
    if "no tests collected" in combined or "pip is not available" in combined:
        return "environment_issue"
    if re.search(r"(?i)(missing|required|not configured).{0,80}(secret|token|credential|api key)", combined):
        return "missing_secrets"
    if re.search(r"(?i)(credential|secret|token).{0,80}(missing|required|not configured|not found)", combined):
        return "missing_secrets"
    if re.search(r"(?i)(unauthorized|authorization required|auth required|login required|oauth|invalid_grant)", combined):
        return "provider_auth_required"
    if "traceback (most recent call last)" in combined or "assertionerror" in combined or "syntaxerror" in combined:
        return "real_code_failure"
    return "unknown"


def summarize_command(command_name: str, exit_code: int, stdout: str, stderr: str) -> dict[str, Any]:
    error_class = classify_error(stdout, stderr)
    reported_status = _extract_reported_status(stdout)
    sensitive_output_detected = contains_sensitive_output(stdout) or contains_sensitive_output(stderr)

    if error_class in KNOWN_WARNING_CLASSES:
        status = "warning"
    elif exit_code == 0:
        status = "warning" if reported_status in {"warning", "yellow", "partial"} else "pass"
    else:
        status = "failed" if error_class in {"real_code_failure", "unknown"} else "warning"

    return {
        "command_name": _safe_identifier(command_name),
        "status": status,
        "exit_code": int(exit_code),
        "error_class": error_class,
        "reported_status": reported_status,
        "stdout_line_count": _line_count(stdout),
        "stderr_line_count": _line_count(stderr),
        "sensitive_output_detected": sensitive_output_detected,
        "raw_output_printed": False,
    }


def format_summary_line(summary: dict[str, Any]) -> str:
    parts = [
        f"- {summary['command_name']}: {summary['status']}",
        f"exit_code={summary['exit_code']}",
    ]
    if summary["error_class"] != "unknown":
        parts.append(f"error_class={summary['error_class']}")
    if summary.get("reported_status"):
        parts.append(f"reported_status={summary['reported_status']}")
    parts.append(f"stdout_lines={summary['stdout_line_count']}")
    parts.append(f"stderr_lines={summary['stderr_line_count']}")
    parts.append(
        "sensitive_output_detected="
        + ("yes" if summary["sensitive_output_detected"] else "no")
    )
    parts.append("raw_output_printed=no")
    return " ".join(parts)


def run_self_test() -> int:
    raw_secret = "telegram:123456789 raw@example.com"
    assert mask_value(raw_secret) == f"<masked:{len(raw_secret)}>"
    assert mask_value({"token": raw_secret}) == {"token": f"<masked:{len(raw_secret)}>"}
    assert contains_sensitive_output('{"title": "Private task", "location": "Home"}')
    assert contains_sensitive_output(raw_secret)
    assert contains_sensitive_output('{"delivery_to": "telegram:123456789"}')
    assert not contains_sensitive_output('{"delivery_target_configured": true, "delivery_target_type": "telegram"}')
    assert classify_error("", "sqlite3.OperationalError: attempt to write a readonly database") == "readonly_database"
    assert classify_error("", "bash: python: command not found") == "missing_python_alias"
    assert classify_error("", "gog: command not found") == "missing_gog"
    summary = summarize_command("daily_plan", 1, "", "attempt to write a readonly database")
    assert summary["status"] == "warning"
    assert summary["error_class"] == "readonly_database"
    serialized = json.dumps(summary)
    assert "attempt to write" not in serialized
    print("eos_safe_smoke_summary self-test: ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize EOS smoke command output without leaking raw data.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--command-name")
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--stdout-file")
    parser.add_argument("--stderr-file")
    parser.add_argument("--format", choices=("line", "json"), default="line")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()
    if not args.command_name:
        parser.error("--command-name is required unless --self-test is used")

    stdout = _read_optional_file(args.stdout_file)
    stderr = _read_optional_file(args.stderr_file)
    summary = summarize_command(args.command_name, args.exit_code, stdout, stderr)
    if args.format == "json":
        print(json.dumps(summary, sort_keys=True))
    else:
        print(format_summary_line(summary))
    return 0


def _extract_reported_status(stdout: str) -> str | None:
    payload = _try_load_json(stdout)
    if not isinstance(payload, dict):
        return None
    for key in ("status", "task_read_status", "auth_status", "calendar_read_status"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    return None


def _try_load_json(text: str) -> Any:
    stripped = text.strip()
    if not stripped.startswith("{"):
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def _line_count(text: str) -> int:
    if not text:
        return 0
    return len(text.splitlines())


def _safe_identifier(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    return cleaned or "command"


def _read_optional_file(path: str | None) -> str:
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    raise SystemExit(main())
