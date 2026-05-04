from eos_security import redact_text


def test_api_keys_are_masked() -> None:
    raw = "maps api_key=AIzaSyDUMMY1234567890abcdefghi"
    redacted = redact_text(raw)

    assert "AIzaSyDUMMY1234567890abcdefghi" not in redacted
    assert "[REDACTED:api_key]" in redacted


def test_oauth_client_secret_is_masked() -> None:
    raw = "client_secret=GOCSPX-dummyClientSecretValue123"
    redacted = redact_text(raw)

    assert "GOCSPX-dummyClientSecretValue123" not in redacted
    assert "[REDACTED:oauth_client_secret]" in redacted


def test_telegram_ids_are_masked() -> None:
    raw = "telegram_chat_id=-1001234567890"
    redacted = redact_text(raw)

    assert "-1001234567890" not in redacted
    assert "[REDACTED:telegram_chat_id]" in redacted


def test_otp_like_code_is_masked() -> None:
    raw = "Your OTP is 123456"
    redacted = redact_text(raw)

    assert "123456" not in redacted
    assert "[REDACTED:otp_code]" in redacted


def test_reset_links_are_masked() -> None:
    raw = "https://accounts.example.test/reset-password?token=abc123456789"
    redacted = redact_text(raw)

    assert "abc123456789" not in redacted
    assert "[REDACTED:reset_link]" in redacted


def test_email_addresses_are_masked() -> None:
    raw = "send to user@example.com"
    redacted = redact_text(raw)

    assert "user@example.com" not in redacted
    assert "[REDACTED:email_address]" in redacted


def test_absolute_credential_paths_are_masked() -> None:
    raw = "path=/home/eos/credentials/client_secret.json"
    redacted = redact_text(raw)

    assert "/home/eos/credentials/client_secret.json" not in redacted
    assert "[REDACTED:credential_path]" in redacted
