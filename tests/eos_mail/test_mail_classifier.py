from __future__ import annotations

import json
from pathlib import Path
import re
import sys

import pytest

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.eos_mail import MailClassification, MailInput, classify_mail  # noqa: E402
from src.eos_mail.rules import (  # noqa: E402
    EOS_ACTION_REQUIRED,
    EOS_REVIEW_NEEDED,
    HEALTH,
    LEGAL,
    MONEY_BANKING,
    MONEY_CREDIT_CARD,
    MONEY_INVOICE,
    MONEY_RECEIPT,
    MONEY_SUBSCRIPTION,
    MONEY_TAX,
    NEWSLETTER_CATEGORIES,
    NEWSLETTER_HIGH_SIGNAL,
    NEWSLETTER_NORMAL,
    NO_ARCHIVE_CATEGORIES,
    PRIORITY_TO_CATEGORY,
    RISK_PHISHING_SUSPECTED,
    RISK_SPAM_REVIEW,
    RISK_UNKNOWN_SENDER,
    SECURITY_LOGIN_ALERT,
    SECURITY_OTP,
    SECURITY_PASSWORD_RESET,
    SECURITY_SUSPICIOUS,
)

FIXTURE_DIR = WORKSPACE_ROOT / "tests" / "eos_mail" / "fixtures" / "mail_synthetic"
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


def _synthetic_mail(
    case_id: str,
    *,
    sender: str = "sender@example.test",
    subject: str,
    snippet: str,
    body_excerpt: str | None = "Synthetic excerpt only.",
    headers: dict[str, str] | None = None,
) -> MailInput:
    return MailInput(
        message_id=f"synthetic-{case_id}",
        thread_id=f"synthetic-thread-{case_id}",
        sender=sender,
        subject=subject,
        snippet=snippet,
        body_excerpt=body_excerpt,
        headers=headers or {},
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


def test_mail_classification_rejects_out_of_range_confidence():
    with pytest.raises(ValueError):
        MailClassification([], "low", False, False, -0.01, "bad confidence")

    with pytest.raises(ValueError):
        MailClassification([], "low", False, False, 1.01, "bad confidence")


def test_classifier_confidence_is_always_bounded():
    mails = [_mail_from_case(case) for case in _load_cases()]
    mails.extend(
        [
            _synthetic_mail(
                "edge-banking-newsletter",
                sender="statements@example-bank.test",
                subject="Monthly bank statement",
                snippet="Your monthly bank statement is ready.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-bank.test>"},
            ),
            _synthetic_mail(
                "edge-unknown",
                sender="hello@new-random-sender.test",
                subject="Quick note",
                snippet="Just checking in with a vague update.",
            ),
        ]
    )

    for mail in mails:
        result = classify_mail(mail)
        assert 0.0 <= result.confidence <= 1.0, mail.message_id


def test_sensitive_categories_are_never_archive_safe():
    for case in _load_cases():
        result = classify_mail(_mail_from_case(case))
        if any(category in NO_ARCHIVE_CATEGORIES for category in result.categories):
            assert result.safe_to_archive is False, case["case_id"]


def test_required_hard_no_archive_categories_are_declared():
    hard_no_archive = {
        MONEY_BANKING,
        MONEY_CREDIT_CARD,
        MONEY_TAX,
        SECURITY_LOGIN_ALERT,
        SECURITY_PASSWORD_RESET,
        SECURITY_OTP,
        SECURITY_SUSPICIOUS,
        LEGAL,
        HEALTH,
        RISK_PHISHING_SUSPECTED,
        RISK_SPAM_REVIEW,
        RISK_UNKNOWN_SENDER,
        EOS_ACTION_REQUIRED,
        EOS_REVIEW_NEEDED,
    }

    assert hard_no_archive <= NO_ARCHIVE_CATEGORIES


def test_all_declared_no_archive_categories_block_archive():
    cases = [
        (
            MONEY_BANKING,
            _synthetic_mail(
                "no-archive-banking",
                subject="Monthly bank statement",
                snippet="Your bank statement is ready.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-bank.test>"},
            ),
        ),
        (
            MONEY_CREDIT_CARD,
            _synthetic_mail(
                "no-archive-credit-card",
                subject="Credit card alert",
                snippet="A new charge appeared on your credit card.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-card.test>"},
            ),
        ),
        (
            MONEY_INVOICE,
            _synthetic_mail(
                "no-archive-invoice",
                subject="Invoice available",
                snippet="Your invoice and amount due are ready.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-billing.test>"},
            ),
        ),
        (
            MONEY_RECEIPT,
            _synthetic_mail(
                "no-archive-receipt",
                subject="Receipt",
                snippet="Your payment received receipt is attached.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-receipts.test>"},
            ),
        ),
        (
            MONEY_TAX,
            _synthetic_mail(
                "no-archive-tax",
                subject="Tax document",
                snippet="Your year-end tax document is ready.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-tax.test>"},
            ),
        ),
        (
            MONEY_SUBSCRIPTION,
            _synthetic_mail(
                "no-archive-subscription",
                subject="Subscription renewal",
                snippet="Your membership renewal notice is ready.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-sub.test>"},
            ),
        ),
        (
            SECURITY_LOGIN_ALERT,
            _synthetic_mail(
                "no-archive-login",
                subject="Login alert",
                snippet="New login from a new device.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-security.test>"},
            ),
        ),
        (
            SECURITY_PASSWORD_RESET,
            _synthetic_mail(
                "no-archive-password-reset",
                subject="Password reset",
                snippet="A password reset was requested.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-security.test>"},
            ),
        ),
        (
            SECURITY_OTP,
            _synthetic_mail(
                "no-archive-otp",
                subject="Verification code",
                snippet="Your one-time password for 2FA is ready.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-security.test>"},
            ),
        ),
        (
            SECURITY_SUSPICIOUS,
            _synthetic_mail(
                "no-archive-suspicious",
                subject="Suspicious access",
                snippet="Suspicious login from an unrecognized device.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-security.test>"},
            ),
        ),
        (
            LEGAL,
            _synthetic_mail(
                "no-archive-legal",
                subject="Legal notice",
                snippet="Contract notice and Mahnung for review.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-legal.test>"},
            ),
        ),
        (
            HEALTH,
            _synthetic_mail(
                "no-archive-health",
                subject="Health appointment",
                snippet="Clinic appointment reminder for a patient.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-clinic.test>"},
            ),
        ),
        (
            RISK_PHISHING_SUSPECTED,
            _synthetic_mail(
                "no-archive-phishing",
                sender="security@account-verify.example.test",
                subject="Verify your account immediately",
                snippet="Suspicious login detected. Confirm your password to avoid suspension.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-risk.test>"},
            ),
        ),
        (
            RISK_SPAM_REVIEW,
            _synthetic_mail(
                "no-archive-spam",
                subject="You won",
                snippet="Claim your prize and free money today.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-spam.test>"},
            ),
        ),
        (
            RISK_UNKNOWN_SENDER,
            _synthetic_mail(
                "no-archive-unknown",
                sender="hello@unseen-sender.test",
                subject="Quick note",
                snippet="A vague update with no deterministic category.",
            ),
        ),
        (
            EOS_ACTION_REQUIRED,
            _synthetic_mail(
                "no-archive-action-required",
                subject="Monthly update",
                snippet="Please reply with confirmation.",
                headers={"List-Unsubscribe": "<mailto:unsubscribe@example-newsletter.test>"},
            ),
        ),
        (
            EOS_REVIEW_NEEDED,
            _synthetic_mail(
                "no-archive-review-needed",
                sender="hello@unseen-sender.test",
                subject="Quick note",
                snippet="A vague update with no deterministic category.",
            ),
        ),
    ]

    for expected_category, mail in cases:
        result = classify_mail(mail)
        assert expected_category in result.categories, expected_category
        assert result.safe_to_archive is False, expected_category


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


def test_newsletter_archive_requires_all_conditions():
    archive_safe = _synthetic_mail(
        "archive-safe-newsletter",
        sender="updates@example-newsletter.test",
        subject="Monthly update",
        snippet="A normal newsletter with product notes.",
        headers={"List-Unsubscribe": "<mailto:unsubscribe@example-newsletter.test>"},
    )
    archive_result = classify_mail(archive_safe)
    assert archive_result.safe_to_archive is True
    assert archive_result.confidence >= 0.95

    blocked_mails = [
        _synthetic_mail(
            "blocked-newsletter-no-header",
            subject="Monthly update",
            snippet="A normal newsletter with product notes.",
        ),
        _synthetic_mail(
            "blocked-newsletter-bank",
            subject="Monthly bank statement",
            snippet="Your monthly bank statement is ready.",
            headers={"List-Unsubscribe": "<mailto:unsubscribe@example-bank.test>"},
        ),
        _synthetic_mail(
            "blocked-newsletter-security",
            subject="Security digest and password reset",
            snippet="A password reset was requested.",
            headers={"List-Unsubscribe": "<mailto:unsubscribe@example-security.test>"},
        ),
        _synthetic_mail(
            "blocked-newsletter-legal",
            subject="Legal notice",
            snippet="Contract and Mahnung update.",
            headers={"List-Unsubscribe": "<mailto:unsubscribe@example-legal.test>"},
        ),
        _synthetic_mail(
            "blocked-newsletter-health",
            subject="Clinic newsletter",
            snippet="Patient appointment reminder.",
            headers={"List-Unsubscribe": "<mailto:unsubscribe@example-clinic.test>"},
        ),
        _synthetic_mail(
            "blocked-newsletter-phishing",
            sender="security@account-verify.example.test",
            subject="Verify your account immediately",
            snippet="Suspicious login detected.",
            headers={"List-Unsubscribe": "<mailto:unsubscribe@example-risk.test>"},
        ),
        _synthetic_mail(
            "blocked-newsletter-spam",
            subject="You won a monthly update",
            snippet="Claim your prize now.",
            headers={"List-Unsubscribe": "<mailto:unsubscribe@example-spam.test>"},
        ),
        _synthetic_mail(
            "blocked-newsletter-reply",
            subject="Monthly update",
            snippet="Please reply with feedback.",
            headers={"List-Unsubscribe": "<mailto:unsubscribe@example-newsletter.test>"},
        ),
        _synthetic_mail(
            "blocked-newsletter-high-signal",
            subject="Weekly research brief",
            snippet="Curated research and high signal operational notes.",
            headers={"List-Unsubscribe": "<mailto:unsubscribe@example-research.test>"},
        ),
    ]

    for mail in blocked_mails:
        result = classify_mail(mail)
        assert result.safe_to_archive is False, mail.message_id


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


def test_newsletter_plus_banking_statement_requires_review():
    mail = _synthetic_mail(
        "newsletter-banking-statement",
        sender="statements@example-bank.test",
        subject="Monthly bank statement",
        snippet="Your monthly bank statement is available.",
        headers={"List-Unsubscribe": "<mailto:unsubscribe@example-bank.test>"},
    )

    result = classify_mail(mail)

    assert MONEY_BANKING in result.categories
    assert EOS_REVIEW_NEEDED in result.categories
    assert result.safe_to_archive is False


def test_newsletter_plus_reply_required_is_action_required():
    mail = _synthetic_mail(
        "newsletter-reply-required",
        sender="updates@example-newsletter.test",
        subject="Monthly update",
        snippet="Bitte bestaetigen Sie diese Nachricht. Please reply by tomorrow.",
        headers={"List-Unsubscribe": "<mailto:unsubscribe@example-newsletter.test>"},
    )

    result = classify_mail(mail)

    assert EOS_ACTION_REQUIRED in result.categories
    assert result.requires_reply is True
    assert result.safe_to_archive is False


def test_high_signal_newsletter_is_important_and_not_archive_safe():
    mail = _synthetic_mail(
        "high-signal-newsletter-edge",
        sender="research@example-newsletter.test",
        subject="Weekly research brief",
        snippet="Curated research and one high signal operational digest.",
        headers={"List-Unsubscribe": "<mailto:unsubscribe@example-newsletter.test>"},
    )

    result = classify_mail(mail)

    assert NEWSLETTER_HIGH_SIGNAL in result.categories
    assert result.priority == "important"
    assert result.safe_to_archive is False


def test_phishing_with_security_language_is_critical_review():
    mail = _synthetic_mail(
        "phishing-security-language",
        sender="security@account-verify.example.test",
        subject="Verify your account immediately",
        snippet="Suspicious login detected. Confirm your password to avoid suspension.",
        headers={},
    )

    result = classify_mail(mail)

    assert RISK_PHISHING_SUSPECTED in result.categories
    assert SECURITY_SUSPICIOUS in result.categories
    assert EOS_REVIEW_NEEDED in result.categories
    assert result.priority == "critical"
    assert result.safe_to_archive is False


def test_legal_with_newsletter_header_requires_review():
    mail = _synthetic_mail(
        "legal-newsletter-header",
        sender="notices@example-legal.test",
        subject="Legal notice: contract Mahnung",
        snippet="Please review the synthetic contract notice.",
        headers={"List-Unsubscribe": "<mailto:unsubscribe@example-legal.test>"},
    )

    result = classify_mail(mail)

    assert LEGAL in result.categories
    assert EOS_REVIEW_NEEDED in result.categories
    assert result.safe_to_archive is False


def test_otp_verification_code_is_review_needed_and_reason_is_redacted():
    mail = _synthetic_mail(
        "otp-verification-code",
        sender="security@example-auth.test",
        subject="Your verification code",
        snippet="Your verification code is 123456 for this sign-in.",
        body_excerpt="Use one-time password 123456 for 2FA. Do not share it.",
    )

    result = classify_mail(mail)

    assert SECURITY_OTP in result.categories
    assert EOS_REVIEW_NEEDED in result.categories
    assert result.safe_to_archive is False
    assert "123456" not in result.reason
    assert re.search(r"\b\d{4,8}\b", result.reason) is None


def test_unknown_sender_weak_signals_require_review():
    mail = _synthetic_mail(
        "unknown-sender-weak",
        sender="hello@new-unseen-sender.test",
        subject="Quick note",
        snippet="A vague synthetic update with no known operational signal.",
    )

    result = classify_mail(mail)

    assert RISK_UNKNOWN_SENDER in result.categories
    assert EOS_REVIEW_NEEDED in result.categories
    assert result.safe_to_archive is False


def test_reason_does_not_include_sensitive_raw_values_or_links():
    mails = [
        _synthetic_mail(
            "reason-redaction-otp",
            subject="Verification code",
            snippet="Your verification code is 123456.",
            body_excerpt="Use 123456 for 2FA.",
        ),
        _synthetic_mail(
            "reason-redaction-reset-link",
            subject="Password reset",
            snippet="Reset your password using https://reset.example.test/token/secret123.",
            body_excerpt="Password reset requested.",
        ),
    ]

    for mail in mails:
        result = classify_mail(mail)
        assert "123456" not in result.reason, mail.message_id
        assert "https://" not in result.reason, mail.message_id
        assert "secret123" not in result.reason, mail.message_id
