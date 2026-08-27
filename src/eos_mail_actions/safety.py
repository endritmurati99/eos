from __future__ import annotations

import re


SENSITIVE_EXACT_CATEGORIES = {
    "_Money/Banking",
    "_Money/Credit Card",
    "_Legal",
    "_Health",
}
SENSITIVE_PREFIXES = ("_Security/",)

SUPPRESSED_EXACT_CATEGORIES = {
    "_Money/Receipt",
    "_Security/OTP",
    "_Security/Password Reset",
    "_Risk/Spam Review",
    "_Risk/Phishing Suspected",
}
SUPPRESSED_PREFIXES = ("_Newsletter/",)

ACTION_LIST_MAPPING = {
    "reply_required": "Inbox",
    "confirm_required": "Inbox",
    "send_document": "Inbox",
    "review_invoice": "Inbox",
    "pay_invoice": "Inbox",
    "check_bank_alert": "Review",
    "review_security_alert": "Review",
    "review_legal_notice": "Review",
    "prepare_meeting": "Next",
    "schedule_followup": "Next",
    "waiting_for_reply": "Waiting",
}


def is_sensitive_category(categories: list[str]) -> bool:
    return any(
        category in SENSITIVE_EXACT_CATEGORIES
        or any(category.startswith(prefix) for prefix in SENSITIVE_PREFIXES)
        for category in categories
    )


def is_suppressed_category(categories: list[str]) -> bool:
    return any(
        category in SUPPRESSED_EXACT_CATEGORIES
        or any(category.startswith(prefix) for prefix in SUPPRESSED_PREFIXES)
        for category in categories
    )


def task_list_for_action(action_type: str, categories: list[str]) -> str:
    if is_sensitive_category(categories):
        return "Review"
    return ACTION_LIST_MAPPING.get(action_type, "Inbox")


def requires_approval_for_action(
    *,
    action_type: str,
    confidence: float,
    categories: list[str],
    risk_flags: list[str],
) -> bool:
    if is_sensitive_category(categories):
        return True
    if risk_flags:
        return True
    if action_type == "reply_required" and confidence >= 0.85:
        return False
    return True


def redact_sensitive_text(text: str) -> str:
    redacted = text
    redacted = re.sub(r"https?://\S+", "[redacted-link]", redacted)
    redacted = re.sub(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b", "[redacted-account]", redacted)
    redacted = re.sub(
        r"(?i)\b(verification|security|login|reset|one[- ]?time|otp|code)\s*(code)?\s*(is|:)?\s*[A-Z0-9-]{4,12}\b",
        "[redacted-code]",
        redacted,
    )
    redacted = re.sub(r"\b(?:\d[ -]*?){12,19}\b", "[redacted-number]", redacted)
    redacted = re.sub(r"\b\d{6,}\b", "[redacted-number]", redacted)
    redacted = re.sub(r"\b[A-Za-z0-9_-]{18,}\b", "[redacted-token]", redacted)
    return redacted
