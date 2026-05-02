from __future__ import annotations

import json
from pathlib import Path
import sys

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.eos_mail import MailInput, classify_mail  # noqa: E402
from src.eos_mail.rules import (  # noqa: E402
    EOS_REVIEW_NEEDED,
    NEWSLETTER_CATEGORIES,
    NEWSLETTER_NORMAL,
    NO_ARCHIVE_CATEGORIES,
    PRIORITY_TO_CATEGORY,
)

FIXTURE_DIR = WORKSPACE_ROOT / "tests" / "fixtures" / "mail_synthetic"
EXPECTED_CASE_COUNT = 25


def _load_cases() -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        cases.append(json.loads(path.read_text(encoding="utf-8")))
    return cases


def _mail_from_case(case: dict[str, object]) -> MailInput:
    mail = case["mail"]
    assert isinstance(mail, dict)
    return MailInput(
        message_id=mail["message_id"],  # type: ignore[arg-type]
        thread_id=mail["thread_id"],  # type: ignore[arg-type]
        sender=str(mail["sender"]),
        subject=str(mail["subject"]),
        snippet=str(mail["snippet"]),
        body_excerpt=mail.get("body_excerpt"),  # type: ignore[arg-type]
        headers=dict(mail.get("headers", {})),
    )


def test_synthetic_corpus_is_complete():
    cases = _load_cases()
    case_ids = {str(case["case_id"]) for case in cases}

    assert len(cases) == EXPECTED_CASE_COUNT
    assert len(case_ids) == EXPECTED_CASE_COUNT
    assert case_ids == {
        "newsletter_high_signal",
        "newsletter_normal",
        "newsletter_low_signal",
        "newsletter_unsubscribe_candidate",
        "banking_info",
        "credit_card_alert",
        "invoice",
        "receipt",
        "tax",
        "subscription",
        "security_login_alert",
        "security_password_reset",
        "security_otp",
        "phishing_suspected",
        "spam_review",
        "unknown_sender",
        "personal_reply_required",
        "work_reply_required",
        "university_important",
        "calendar_related",
        "task_related",
        "legal",
        "shopping_delivery",
        "travel_booking",
        "health_appointment",
    }


def test_classifier_matches_synthetic_expectations():
    for case in _load_cases():
        expected = case["expected"]
        assert isinstance(expected, dict)

        result = classify_mail(_mail_from_case(case))
        case_id = case["case_id"]

        assert result.priority == expected["priority"], case_id
        assert PRIORITY_TO_CATEGORY[result.priority] in result.categories, case_id
        assert result.requires_reply is expected["requires_reply"], case_id
        assert result.safe_to_archive is expected["safe_to_archive"], case_id
        assert result.confidence >= expected["min_confidence"], case_id

        for category in expected["categories_include"]:
            assert category in result.categories, f"{case_id}: missing category {category}"
        for risk_flag in expected["risk_flags_include"]:
            assert risk_flag in result.risk_flags, f"{case_id}: missing risk flag {risk_flag}"

        payload = result.to_dict()
        json.dumps(payload)
        assert isinstance(payload["categories"], list), case_id
        assert isinstance(payload["risk_flags"], list), case_id
        assert payload["reason"], case_id


def test_sensitive_categories_are_never_archive_safe():
    for case in _load_cases():
        result = classify_mail(_mail_from_case(case))
        if any(category in NO_ARCHIVE_CATEGORIES for category in result.categories):
            assert result.safe_to_archive is False, case["case_id"]


def test_safe_newsletter_requires_list_unsubscribe_and_no_risky_signals():
    safe_newsletter = MailInput(
        message_id="synthetic-safe-newsletter",
        thread_id="synthetic-thread-safe-newsletter",
        sender="updates@example-newsletter.test",
        subject="Monthly update",
        snippet="A normal newsletter with product notes.",
        body_excerpt="Synthetic update only.",
        headers={"List-Unsubscribe": "<mailto:unsubscribe@example-newsletter.test>"},
    )
    result = classify_mail(safe_newsletter)

    assert NEWSLETTER_NORMAL in result.categories
    assert result.safe_to_archive is True
    assert result.requires_reply is False
    assert result.risk_flags == []
    assert result.confidence >= 0.95

    missing_header = MailInput(
        message_id="synthetic-newsletter-no-header",
        thread_id="synthetic-thread-newsletter-no-header",
        sender="updates@example-newsletter.test",
        subject="Monthly update",
        snippet="A normal newsletter with product notes.",
        body_excerpt="Synthetic update only.",
        headers={},
    )
    result_without_header = classify_mail(missing_header)

    assert any(category in NEWSLETTER_CATEGORIES for category in result_without_header.categories)
    assert result_without_header.safe_to_archive is False
    assert EOS_REVIEW_NEEDED in result_without_header.categories


def test_newsletter_with_reply_or_security_signal_is_not_archive_safe():
    reply_newsletter = MailInput(
        message_id="synthetic-reply-newsletter",
        thread_id="synthetic-thread-reply-newsletter",
        sender="updates@example-newsletter.test",
        subject="Monthly update",
        snippet="Please reply with feedback on this newsletter.",
        body_excerpt="Synthetic update only.",
        headers={"List-Unsubscribe": "<mailto:unsubscribe@example-newsletter.test>"},
    )
    reply_result = classify_mail(reply_newsletter)

    assert reply_result.requires_reply is True
    assert reply_result.safe_to_archive is False

    security_newsletter = MailInput(
        message_id="synthetic-security-newsletter",
        thread_id="synthetic-thread-security-newsletter",
        sender="updates@example-newsletter.test",
        subject="Monthly update and password reset notice",
        snippet="A password reset was requested.",
        body_excerpt="No reset link is included.",
        headers={"List-Unsubscribe": "<mailto:unsubscribe@example-newsletter.test>"},
    )
    security_result = classify_mail(security_newsletter)

    assert security_result.safe_to_archive is False
    assert EOS_REVIEW_NEEDED in security_result.categories
