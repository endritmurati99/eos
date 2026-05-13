#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import urllib.error

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.gateways.telegram import send_telegram_message  # noqa: E402


class FakeResponse:
    def __init__(self, payload: dict[str, object]):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")

    def close(self) -> None:
        return None


def main() -> None:
    calls = []

    def success_urlopen(request, timeout):  # noqa: ANN001
        calls.append((request, timeout))
        assert request.full_url.endswith("/bottoken/sendMessage")
        payload = json.loads(request.data.decode("utf-8"))
        assert payload["chat_id"] == "123"
        assert payload["text"] == "Hallo"
        return FakeResponse({"ok": True, "result": {"message_id": 42}})

    success = send_telegram_message(
        "Hallo",
        token="token",
        chat_id="telegram:123",
        urlopen=success_urlopen,
    )
    assert success["status"] == "success"
    assert success["delivery_status"] == "sent"
    assert success["delivery_target_configured"] is True
    assert success["delivery_target_type"] == "telegram"
    assert success["provider_delivery_refs"] == [{"kind": "telegram_message_id", "present": True}]
    assert "chat_id" not in success
    assert "123" not in json.dumps(success)
    assert len(calls) == 1

    def provider_error_urlopen(_request, timeout):  # noqa: ANN001, ARG001
        return FakeResponse({"ok": False, "description": "Bad Request: chat not found"})

    provider_error = send_telegram_message(
        "Hallo",
        token="token",
        chat_id="123",
        urlopen=provider_error_urlopen,
    )
    assert provider_error["status"] == "failed"
    assert provider_error["error_code"] == "provider_error"
    assert provider_error["delivery_target_configured"] is True
    assert "chat_id" not in provider_error
    assert "123" not in json.dumps(provider_error)

    def http_error_urlopen(_request, timeout):  # noqa: ANN001, ARG001
        raise urllib.error.HTTPError(
            url="https://api.telegram.org/test",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=FakeResponse({"description": "Unauthorized"}),
        )

    http_error = send_telegram_message(
        "Hallo",
        token="token",
        chat_id="123",
        urlopen=http_error_urlopen,
    )
    assert http_error["status"] == "failed"
    assert http_error["error_code"] == "provider_error"

    token_env_names = ["EOS_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN"]
    previous_env = {name: os.environ.pop(name, None) for name in token_env_names}
    try:
        missing = send_telegram_message("Hallo", token="", chat_id="123")
    finally:
        for name, value in previous_env.items():
            if value is not None:
                os.environ[name] = value
    assert missing["status"] == "failed"
    assert missing["error_code"] == "config_missing"
    assert missing["delivery_target_configured"] is True
    assert "chat_id" not in missing
    assert "123" not in json.dumps(missing)

    print("verify_telegram_gateway: ok")


if __name__ == "__main__":
    main()
