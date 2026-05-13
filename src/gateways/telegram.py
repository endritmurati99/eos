from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

from src.runtime import CRON_JOBS_PATH, load_json

UrlOpen = Callable[..., Any]

TELEGRAM_API_ROOT = "https://api.telegram.org"
MAX_TELEGRAM_TEXT = 3900


def send_telegram_message(
    text: str,
    *,
    token: str | None = None,
    chat_id: str | None = None,
    timeout_seconds: int = 20,
    jobs_path: str | Path | None = None,
    urlopen: UrlOpen | None = None,
) -> dict[str, Any]:
    resolved_token = _resolve_token(token)
    resolved_chat_id = _resolve_chat_id(chat_id, jobs_path=jobs_path)
    clean_text = text.strip()

    if not clean_text:
        return _failure("input_empty", "No Telegram message text was provided.")
    if not resolved_token:
        return _failure(
            "config_missing",
            "Telegram bot token is not configured.",
            delivery_target_configured=bool(resolved_chat_id),
            delivery_target_type="telegram" if resolved_chat_id else None,
        )
    if not resolved_chat_id:
        return _failure(
            "config_missing",
            "Telegram chat target is not configured.",
            delivery_target_configured=False,
            delivery_target_type="telegram",
        )

    opener = urlopen or _system_urlopen
    messages = _split_message(clean_text)
    provider_refs = []

    for index, message in enumerate(messages, start=1):
        payload = {
            "chat_id": resolved_chat_id,
            "text": message,
            "disable_web_page_preview": True,
        }
        result = _post_message(
            token=resolved_token,
            payload=payload,
            timeout_seconds=timeout_seconds,
            urlopen=opener,
        )
        if result["status"] != "success":
            result["message_count"] = len(messages)
            result["delivered_count"] = index - 1
            result["provider_delivery_refs"] = provider_refs
            result["delivery_target_configured"] = True
            result["delivery_target_type"] = "telegram"
            return result
        provider_refs.append(_public_provider_ref(result.get("provider_delivery_ref")))

    return {
        "status": "success",
        "provider": "telegram",
        "delivery_status": "sent",
        "delivery_target_configured": True,
        "delivery_target_type": "telegram",
        "message_count": len(messages),
        "provider_delivery_refs": provider_refs,
    }


def _post_message(
    *,
    token: str,
    payload: dict[str, Any],
    timeout_seconds: int,
    urlopen: UrlOpen,
) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{TELEGRAM_API_ROOT}/bot{token}/sendMessage",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        return _failure("provider_error", f"Telegram HTTP {exc.code}: {_safe_error(error_body)}")
    except OSError as exc:
        return _failure("transport_error", str(exc))

    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        return _failure("provider_error", "Telegram returned invalid JSON.")

    if body.get("ok") is not True:
        description = str(body.get("description") or "Telegram send failed.")
        return _failure("provider_error", description)

    message = body.get("result") or {}
    return {
        "status": "success",
        "provider": "telegram",
        "delivery_status": "sent",
        "provider_delivery_ref": str(message.get("message_id") or ""),
    }


def _system_urlopen(request: urllib.request.Request, *, timeout: int) -> Any:
    return urllib.request.urlopen(request, timeout=timeout, context=_ssl_context())


def _ssl_context() -> ssl.SSLContext:
    cafile = _resolve_ca_file()
    if cafile is not None:
        return ssl.create_default_context(cafile=str(cafile))
    return ssl.create_default_context()


def _resolve_ca_file() -> Path | None:
    for raw in (
        os.getenv("SSL_CERT_FILE"),
        ssl.get_default_verify_paths().cafile,
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
        "/etc/ssl/cert.pem",
    ):
        if not raw:
            continue
        path = Path(raw)
        if path.is_file():
            return path
    return None


def _resolve_token(token: str | None) -> str | None:
    return _clean_optional(
        token
        or os.getenv("EOS_TELEGRAM_BOT_TOKEN")
        or os.getenv("TELEGRAM_BOT_TOKEN")
        or os.getenv("TELEGRAM_TOKEN")
    )


def _resolve_chat_id(chat_id: str | None, *, jobs_path: str | Path | None) -> str | None:
    configured = _clean_optional(
        chat_id
        or os.getenv("EOS_TELEGRAM_CHAT_ID")
        or os.getenv("TELEGRAM_CHAT_ID")
        or os.getenv("EOS_TELEGRAM_TO")
        or os.getenv("TELEGRAM_TO")
    )
    if configured:
        return _strip_telegram_prefix(configured)

    payload = load_json(Path(jobs_path) if jobs_path is not None else CRON_JOBS_PATH, {"jobs": []})
    for job in payload.get("jobs", []):
        delivery = job.get("delivery") or {}
        target = _clean_optional(delivery.get("to"))
        if target and str(delivery.get("channel") or "").lower() == "telegram":
            return _strip_telegram_prefix(target)
    return None


def _strip_telegram_prefix(value: str) -> str:
    if value.startswith("telegram:"):
        return value.removeprefix("telegram:")
    return value


def _split_message(text: str) -> list[str]:
    if len(text) <= MAX_TELEGRAM_TEXT:
        return [text]

    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= MAX_TELEGRAM_TEXT:
            chunks.append(remaining)
            break
        split_at = remaining.rfind("\n\n", 0, MAX_TELEGRAM_TEXT)
        if split_at < MAX_TELEGRAM_TEXT // 2:
            split_at = remaining.rfind("\n", 0, MAX_TELEGRAM_TEXT)
        if split_at < MAX_TELEGRAM_TEXT // 2:
            split_at = MAX_TELEGRAM_TEXT
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    return [chunk for chunk in chunks if chunk]


def _clean_optional(value: Any) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _safe_error(raw: str) -> str:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw[:500]
    return str(payload.get("description") or payload)[:500]


def _public_provider_ref(value: Any) -> dict[str, Any]:
    return {
        "kind": "telegram_message_id",
        "present": bool(str(value or "").strip()),
    }


def _failure(code: str, error: str, **extra: Any) -> dict[str, Any]:
    payload = {
        "status": "failed",
        "provider": "telegram",
        "delivery_status": "failed",
        "error_code": code,
        "error": error,
    }
    payload.update({key: value for key, value in extra.items() if value is not None})
    return payload
