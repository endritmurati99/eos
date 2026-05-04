#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SOFT_CLASSES = {
    "environment_issue",
    "gmail_live_unverified",
    "google_drive_live_unverified",
    "maps_live_unverified",
    "missing_credentials",
    "missing_gog",
    "missing_python_alias",
    "missing_systemctl",
    "provider_auth_required",
    "readonly_database",
}

HARD_CLASSES = {
    "gmail_write_scope_detected",
    "real_code_failure",
    "secret_output_detected",
    "sensitive_output_detected",
    "unknown",
}

SENSITIVE_KEY_PATTERN = re.compile(
    r"(?i)(\"|\b)(attendees|calendar[_-]?title|chat[_-]?id|description|email|"
    r"event[_-]?title|gmail[_-]?id|location|message[_-]?id|notes|"
    r"output_markdown|snippet|summary|telegram[_-]?(target|chat|to)|"
    r"thread[_-]?id|title)\1?\s*[:=]"
)
SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"(?i)\btelegram:\d+\b"),
    re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
    re.compile(r"(?i)\b(thread|message|gmail)[_-]?[a-z0-9]{8,}\b"),
    re.compile(r"(?i)(/home|/users|/root|/docker)/[^,\s\"']+"),
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"\bgh[opsu]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"(?i)\b(token|secret|password|api[_-]?key|client_secret)\b\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{8,}"),
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


def contains_secret_output(text: str) -> bool:
    if not text:
        return False
    return any(pattern.search(text) for pattern in SECRET_VALUE_PATTERNS)


def classify_error(stdout: str, stderr: str) -> str:
    combined_raw = f"{stdout}\n{stderr}"
    combined = combined_raw.lower()
    if contains_secret_output(combined_raw):
        return "secret_output_detected"
    if "gmail_write_scope_detected" in combined:
        return "gmail_write_scope_detected"
    if "attempt to write a readonly database" in combined or "readonly database" in combined:
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
    if re.search(r"(?i)(missing|required|not configured).{0,80}(credential|secret|token|api key)", combined_raw):
        return "missing_credentials"
    if re.search(r"(?i)(credential|secret|token).{0,80}(missing|required|not configured|not found)", combined_raw):
        return "missing_credentials"
    if re.search(r"(?i)(unauthorized|authorization required|auth required|login required|oauth|invalid_grant)", combined_raw):
        return "provider_auth_required"
    if "gmail live e2e unverified" in combined:
        return "gmail_live_unverified"
    if "maps live api unverified" in combined:
        return "maps_live_unverified"
    if "google drive live api unverified" in combined:
        return "google_drive_live_unverified"
    if (
        "traceback (most recent call last)" in combined
        or "assertionerror" in combined
        or "syntaxerror" in combined
        or "indentationerror" in combined
        or "importerror" in combined
        or "modulenotfounderror" in combined
    ):
        return "real_code_failure"
    if not combined.strip():
        return "unknown"
    return "unknown"


def summarize_command(
    command_name: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    *,
    readonly_database_hard: bool = False,
) -> dict[str, Any]:
    sensitive_output_detected = contains_sensitive_output(stdout) or contains_sensitive_output(stderr)
    secret_output_detected = contains_secret_output(stdout) or contains_secret_output(stderr)
    error_class = classify_error(stdout, stderr)
    if secret_output_detected:
        error_class = "secret_output_detected"
    elif sensitive_output_detected:
        error_class = "sensitive_output_detected"

    reported_status = _extract_reported_status(stdout)

    if error_class == "readonly_database" and readonly_database_hard:
        status = "failed"
    elif error_class in {"secret_output_detected", "sensitive_output_detected", "gmail_write_scope_detected"}:
        status = "failed"
    elif error_class in HARD_CLASSES:
        status = "failed" if exit_code != 0 else "pass"
    elif error_class in SOFT_CLASSES:
        status = "warning"
    elif reported_status in {"warning", "yellow", "partial"}:
        status = "warning"
    elif exit_code == 0:
        status = "pass"
    else:
        status = "failed"

    return {
        "command_name": _safe_identifier(command_name),
        "status": status,
        "exit_code": int(exit_code),
        "error_class": error_class,
        "reported_status": reported_status,
        "stdout_line_count": _line_count(stdout),
        "stderr_line_count": _line_count(stderr),
        "sensitive_output_detected": sensitive_output_detected,
        "secret_output_detected": secret_output_detected,
        "raw_output_printed": False,
    }


def format_summary_line(summary: dict[str, Any]) -> str:
    parts = [
        f"- {summary['command_name']}: {summary['status']}",
        f"exit_code={summary['exit_code']}",
        f"error_class={summary['error_class']}",
    ]
    if summary.get("reported_status"):
        parts.append(f"reported_status={summary['reported_status']}")
    parts.append(f"stdout_lines={summary['stdout_line_count']}")
    parts.append(f"stderr_lines={summary['stderr_line_count']}")
    parts.append("sensitive_output_detected=" + ("yes" if summary["sensitive_output_detected"] else "no"))
    parts.append("secret_output_detected=" + ("yes" if summary["secret_output_detected"] else "no"))
    parts.append("raw_output_printed=no")
    return " ".join(parts)


def run_self_test() -> int:
    raw_secret = "example-secret-value"
    raw_private = "telegram:123456789 raw@example.com"
    assert mask_value(raw_private) == f"<masked:{len(raw_private)}>"
    assert contains_sensitive_output('{"title": "Private task", "location": "Home"}')
    assert contains_sensitive_output(raw_private)
    assert contains_secret_output(f"token={raw_secret}")
    assert classify_error("", "sqlite3.OperationalError: attempt to write a readonly database") == "readonly_database"
    assert classify_error("", "bash: python: command not found") == "missing_python_alias"
    assert classify_error("", "gog: command not found") == "missing_gog"
    assert classify_error("", "systemctl unavailable") == "missing_systemctl"
    assert classify_error("", "credentials not configured") == "missing_credentials"
    assert classify_error("", "oauth login required") == "provider_auth_required"
    assert classify_error("", "Traceback (most recent call last)") == "real_code_failure"
    assert classify_error("", "") == "unknown"
    assert classify_error("", "gmail_write_scope_detected") == "gmail_write_scope_detected"
    summary = summarize_command("daily_plan", 1, "", "attempt to write a readonly database")
    assert summary["status"] == "warning"
    hard_summary = summarize_command(
        "daily_plan",
        1,
        "",
        "attempt to write a readonly database",
        readonly_database_hard=True,
    )
    assert hard_summary["status"] == "failed"
    sensitive_summary = summarize_command("daily_plan", 0, '{"title": "Private task"}', "")
    assert sensitive_summary["status"] == "failed"
    assert sensitive_summary["error_class"] == "sensitive_output_detected"
    secret_summary = summarize_command("auth", 0, "", f"token={raw_secret}")
    assert secret_summary["status"] == "failed"
    assert secret_summary["error_class"] == "secret_output_detected"
    serialized = json.dumps(summary)
    assert "attempt to write" not in serialized
    print("eos_safe_smoke_summary self-test: ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize EOS smoke output without leaking raw data.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--command-name")
    parser.add_argument("--exit-code", type=int, default=0)
    parser.add_argument("--stdout-file")
    parser.add_argument("--stderr-file")
    parser.add_argument("--format", choices=("line", "json"), default="line")
    parser.add_argument("--readonly-database-hard", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()
    if not args.command_name:
        parser.error("--command-name is required unless --self-test is used")

    stdout = _read_optional_file(args.stdout_file)
    stderr = _read_optional_file(args.stderr_file)
    summary = summarize_command(
        args.command_name,
        args.exit_code,
        stdout,
        stderr,
        readonly_database_hard=args.readonly_database_hard,
    )
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
    raise SystemExit(main(sys.argv[1:]))
