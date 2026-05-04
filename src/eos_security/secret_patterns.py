"""Regex patterns for local-only secret and sensitive-data detection."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class SensitivePattern:
    label: str
    pattern: re.Pattern[str]
    data_class: str


def _compile(value: str) -> re.Pattern[str]:
    return re.compile(value, re.IGNORECASE)


SENSITIVE_PATTERNS: tuple[SensitivePattern, ...] = (
    SensitivePattern(
        label="reset_link",
        pattern=_compile(r"https?://[^\s\"'<>)]*(?:reset|recover|recovery|password|verify)[^\s\"'<>)]*"),
        data_class="Class 3",
    ),
    SensitivePattern(
        label="oauth_client_secret",
        pattern=_compile(
            r"\b(?:oauth[_-]?)?client[_-]?secret\b\s*[:=]\s*[\"']?[A-Za-z0-9._~+/=-]{12,}[\"']?"
            r"|\bGOCSPX-[A-Za-z0-9_-]{16,}\b"
        ),
        data_class="Class 4",
    ),
    SensitivePattern(
        label="api_key",
        pattern=_compile(
            r"\bAIza[0-9A-Za-z_-]{20,}\b"
            r"|\b(?:api[_-]?key|google[_-]?api[_-]?key|maps[_-]?api[_-]?key)\b\s*[:=]\s*[\"']?[A-Za-z0-9._-]{16,}[\"']?"
        ),
        data_class="Class 4",
    ),
    SensitivePattern(
        label="token",
        pattern=_compile(
            r"\b(?:access[_-]?token|refresh[_-]?token|id[_-]?token|auth[_-]?token|bearer[_-]?token|secret)\b"
            r"\s*[:=]\s*[\"']?[A-Za-z0-9._~+/=-]{16,}[\"']?"
            r"|\bAuthorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]{16,}\b"
        ),
        data_class="Class 4",
    ),
    SensitivePattern(
        label="telegram_chat_id",
        pattern=_compile(r"\b(?:telegram[_-]?)?(?:chat[_-]?id|user[_-]?id)\b\s*[:=]\s*[\"']?-?\d{6,20}[\"']?"),
        data_class="Class 2",
    ),
    SensitivePattern(
        label="otp_code",
        pattern=_compile(
            r"\b(?:otp|one[-\s]?time(?:\s+(?:password|code))?|verification\s+code|2fa\s+code|mfa\s+code|auth\s+code)\b"
            r"\s*(?:is|=|:)?\s*[\"']?\d{6,8}\b"
        ),
        data_class="Class 3",
    ),
    SensitivePattern(
        label="credential_path",
        pattern=_compile(
            r"(?:~|/)[^\s\"'`<>]*(?:credentials|tokens|client_secret|oauth|\.gog|\.config/gog)[^\s\"'`<>]*"
            r"|[A-Za-z]:\\[^\s\"'`<>]*(?:credentials|tokens|client_secret|oauth)[^\s\"'`<>]*"
        ),
        data_class="Class 4",
    ),
    SensitivePattern(
        label="gmail_message_id",
        pattern=_compile(r"\b(?:gmail[_-]?message[_-]?id|gmail[_-]?msg[_-]?id)\b\s*[:=]\s*[\"']?[A-Za-z0-9_-]{8,80}[\"']?"),
        data_class="Class 2",
    ),
    SensitivePattern(
        label="email_address",
        pattern=_compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b"),
        data_class="Class 2",
    ),
)


CLASS_4_LABELS = frozenset({"api_key", "credential_path", "oauth_client_secret", "token"})
CLASS_3_LABELS = frozenset({"otp_code", "reset_link"})
