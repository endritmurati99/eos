from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from src.runtime import WORKSPACE_ROOT, load_env_file

PROVIDER_NAME = "gog_gmail"
READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
FORBIDDEN_GMAIL_WRITE_SCOPES = (
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://mail.google.com/",
)
LIVE_CONTRACT_UNVERIFIED_ITEMS = (
    "gog gmail messages search JSON shape in production",
    "gog gmail get --format metadata JSON shape in production",
)
ALLOWED_HEADER_NAMES = (
    "From",
    "To",
    "Subject",
    "Date",
    "List-Unsubscribe",
    "Authentication-Results",
)
GOG_GMAIL_CONTRACT_COMMANDS = {
    "messages_search": (
        "gog",
        "-a",
        "<account>",
        "gmail",
        "messages",
        "search",
        "<query>",
        "--max",
        "<n>",
        "--json",
        "--results-only",
        "--no-input",
    ),
    "metadata_get": (
        "gog",
        "-a",
        "<account>",
        "gmail",
        "get",
        "<message_id>",
        "--format",
        "metadata",
        "--headers",
        ",".join(ALLOWED_HEADER_NAMES),
        "--json",
        "--results-only",
        "--no-input",
    ),
}
EXIT_AUTH_REQUIRED = 4
EXIT_CONFIG = 10


@dataclass(frozen=True)
class MessageRef:
    message_id: str
    thread_id: str | None = None
    label_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MailSummary:
    message_id: str
    thread_id: str | None
    sender: str | None
    to: str | None
    subject: str | None
    date: str | None
    snippet: str | None
    headers_subset: dict[str, str]
    has_attachments: bool
    label_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class GmailClientError(RuntimeError):
    def __init__(
        self,
        status: str,
        message: str,
        *,
        provider: str = PROVIDER_NAME,
        command: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.provider = provider
        self.command = command or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "provider": self.provider,
            "error": _sanitize_error_text(str(self)),
            "command": _redact_command(self.command),
        }


class GmailReadOnlyClient(Protocol):
    def list_messages(self, query: str, max_results: int) -> list[MessageRef]:
        ...

    def get_message_summary(self, message_id: str) -> MailSummary:
        ...


class GogGmailReadOnlyClient:
    """Read-only Gmail adapter backed by the local gog CLI."""

    def __init__(
        self,
        *,
        gog_bin: str | None = None,
        account: str | None = None,
        token_root: str | None = None,
        workspace_root: str | Path | None = None,
    ) -> None:
        self.workspace_root = Path(workspace_root) if workspace_root else WORKSPACE_ROOT
        load_env_file(self.workspace_root)
        self.calendar_source_path = self.workspace_root / "integrations" / "calendar-source.json"
        self.gog_bin = gog_bin or os.getenv("EOS_GOG_BIN") or shutil.which("gog")
        self.account = account or os.getenv("EOS_GOOGLE_ACCOUNT") or self._load_default_account()
        self.token_root = token_root or os.getenv("EOS_GOOGLE_TOKEN_PATH")

    def list_messages(self, query: str, max_results: int) -> list[MessageRef]:
        if max_results <= 0:
            return []

        command = self._run_raw(
            [
                "gmail",
                "messages",
                "search",
                query,
                "--max",
                str(max_results),
            ]
        )
        payload = _load_json_payload(command["stdout"])
        return [_message_ref(item) for item in _extract_items(payload) if _message_ref(item).message_id]

    def get_message_summary(self, message_id: str) -> MailSummary:
        command = self._run_raw(
            [
                "gmail",
                "get",
                message_id,
                "--format",
                "metadata",
                "--headers",
                ",".join(ALLOWED_HEADER_NAMES),
            ]
        )
        payload = _load_json_payload(command["stdout"])
        if not isinstance(payload, dict):
            raise GmailClientError(
                "provider_error",
                "Gmail message metadata response was not JSON object shaped.",
                command=command["command"],
            )
        return normalize_gmail_message(payload)

    def build_command_env(self) -> dict[str, str]:
        env = os.environ.copy()
        if self.token_root:
            env["XDG_CONFIG_HOME"] = str(Path(self.token_root).expanduser())
        return env

    def _run_raw(self, args: list[str]) -> dict[str, Any]:
        if not self.gog_bin:
            raise GmailClientError(
                "config_missing",
                "gog binary not found; set EOS_GOG_BIN or add gog to PATH.",
            )
        if not self.account:
            raise GmailClientError(
                "config_missing",
                "Google account missing; set EOS_GOOGLE_ACCOUNT or integrations/calendar-source.json.account.",
            )

        command = [
            self.gog_bin,
            "-a",
            self.account,
            *args,
            "--json",
            "--results-only",
            "--no-input",
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                env=self.build_command_env(),
            )
        except FileNotFoundError as exc:
            raise GmailClientError(
                "config_missing",
                "gog binary not found; set EOS_GOG_BIN or add gog to PATH.",
                command=command,
            ) from exc
        result = {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
            "command": command,
        }
        if completed.returncode != 0:
            raise GmailClientError(
                _status_from_command(result),
                _best_error(result) or "Gmail read-only command failed.",
                command=command,
            )
        return result

    def _load_default_account(self) -> str | None:
        if not self.calendar_source_path.exists():
            return None
        try:
            payload = json.loads(self.calendar_source_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        value = payload.get("account")
        return str(value) if value else None


def normalize_gmail_message(message: dict[str, Any]) -> MailSummary:
    headers = _headers_subset(message)
    payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
    return MailSummary(
        message_id=str(message.get("id") or message.get("message_id") or ""),
        thread_id=_optional_str(message.get("threadId") or message.get("thread_id")),
        sender=headers.get("From"),
        to=headers.get("To"),
        subject=headers.get("Subject"),
        date=headers.get("Date"),
        snippet=_optional_str(message.get("snippet")),
        headers_subset=headers,
        has_attachments=_has_attachments(payload),
        label_ids=tuple(str(label) for label in message.get("labelIds") or message.get("label_ids") or ()),
    )


def _message_ref(item: dict[str, Any]) -> MessageRef:
    return MessageRef(
        message_id=str(item.get("id") or item.get("message_id") or ""),
        thread_id=_optional_str(item.get("threadId") or item.get("thread_id")),
        label_ids=tuple(str(label) for label in item.get("labelIds") or item.get("label_ids") or ()),
    )


def _headers_subset(message: dict[str, Any]) -> dict[str, str]:
    payload = message.get("payload") if isinstance(message.get("payload"), dict) else {}
    raw_headers = payload.get("headers") or message.get("headers") or []
    allowed_lookup = {name.lower(): name for name in ALLOWED_HEADER_NAMES}
    selected: dict[str, str] = {}
    if isinstance(raw_headers, dict):
        iterable = [{"name": key, "value": value} for key, value in raw_headers.items()]
    else:
        iterable = raw_headers

    for header in iterable:
        if not isinstance(header, dict):
            continue
        name = str(header.get("name") or "")
        canonical = allowed_lookup.get(name.lower())
        value = header.get("value")
        if canonical and value is not None:
            selected[canonical] = str(value)
    return selected


def _has_attachments(payload: dict[str, Any]) -> bool:
    filename = payload.get("filename")
    if isinstance(filename, str) and filename.strip():
        return True
    for part in payload.get("parts") or []:
        if isinstance(part, dict) and _has_attachments(part):
            return True
    return False


def _extract_items(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("messages", "items", "results", "threads"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload]
    return []


def _load_json_payload(raw_output: str) -> Any:
    if not raw_output.strip():
        return None
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError as exc:
        raise GmailClientError("provider_error", "Gmail command returned invalid JSON.") from exc


def _status_from_command(command: dict[str, Any]) -> str:
    error_text = (_best_error(command) or "").lower()
    if command["returncode"] == EXIT_CONFIG or "oauth client credentials" in error_text:
        return "config_missing"
    if (
        command["returncode"] == EXIT_AUTH_REQUIRED
        or "no tokens stored" in error_text
        or "insufficient authentication scopes" in error_text
        or "insufficient permission" in error_text
        or "insufficient permissions" in error_text
        or "gmail api has not been used" in error_text
        or "accessnotconfigured" in error_text
    ):
        return "auth_required"
    return "provider_error"


def _best_error(command: dict[str, Any]) -> str | None:
    for value in (command.get("stderr"), command.get("stdout")):
        if value:
            return _sanitize_error_text(str(value))
    return None


def _redact_command(command: list[str]) -> list[str]:
    redacted: list[str] = []
    skip_next = False
    for part in command:
        if skip_next:
            redacted.append("<redacted>")
            skip_next = False
            continue
        redacted.append(part)
        if part in {"-a", "--account", "--access-token", "--auth-url"}:
            skip_next = True
    return redacted


def _sanitize_error_text(raw: str) -> str:
    sanitized = raw
    sanitized = re.sub(r"Bearer\s+[A-Za-z0-9._~+/=-]+", "Bearer <redacted>", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"ya29\.[A-Za-z0-9._~+/=-]+", "<redacted-token>", sanitized)
    sanitized = re.sub(r"(access[_-]?token|refresh[_-]?token|id[_-]?token|token|secret|password)=\S+", r"\1=<redacted>", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"(https?://\S*(?:token|code|auth|oauth)\S*)", "<redacted-url>", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "<redacted-account>", sanitized)
    sanitized = re.sub(r"(/[^\s:]*?(?:credentials|token|gogcli|oauth)[^\s:]*)", "<redacted-path>", sanitized, flags=re.IGNORECASE)
    return sanitized


def sanitize_gmail_error_text(raw: str) -> str:
    return _sanitize_error_text(raw)


def detect_forbidden_gmail_write_scopes(scopes: str | list[str] | tuple[str, ...] | set[str] | None) -> tuple[str, ...]:
    if scopes is None:
        return ()
    if isinstance(scopes, str):
        candidates = re.split(r"[\s,;]+", scopes)
    else:
        candidates = [str(scope) for scope in scopes]
    normalized = {scope.strip() for scope in candidates if scope and scope.strip()}
    return tuple(scope for scope in FORBIDDEN_GMAIL_WRITE_SCOPES if scope in normalized)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    rendered = str(value)
    return rendered if rendered else None


def gmail_scope_guidance() -> dict[str, Any]:
    return {
        "required_scope": READONLY_SCOPE,
        "gog_auth_hint": "gog auth add <account> --services gmail --readonly --gmail-scope=readonly",
        "write_scopes_added": False,
        "provider_contract_verified": False,
        "live_contract_verified": False,
        "live_e2e_verified": False,
        "live_contract_unverified_items": list(LIVE_CONTRACT_UNVERIFIED_ITEMS),
    }
