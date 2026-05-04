from eos_security import scan_for_sensitive_patterns


def test_scan_reports_labels_without_raw_values() -> None:
    raw = (
        "user@example.com api_key=AIzaSyDUMMY1234567890abcdefghi "
        "client_secret=GOCSPX-dummyClientSecretValue123 telegram_chat_id=-1001234567890 "
        "OTP is 123456"
    )

    result = scan_for_sensitive_patterns(raw)

    assert result["has_sensitive"] is True
    assert result["counts"]["email_address"] == 1
    assert result["counts"]["api_key"] == 1
    assert result["counts"]["oauth_client_secret"] == 1
    assert result["counts"]["telegram_chat_id"] == 1
    assert result["counts"]["otp_code"] == 1
    assert "GOCSPX-dummyClientSecretValue123" not in str(result)
    assert "user@example.com" not in str(result)


def test_scan_detects_reset_links_and_credential_paths() -> None:
    raw = "reset=https://example.test/reset?token=abc path=/home/eos/credentials/client_secret.json"

    result = scan_for_sensitive_patterns(raw)

    assert result["counts"]["reset_link"] == 1
    assert result["counts"]["credential_path"] == 1
    assert "Class 4" in result["data_classes"]
