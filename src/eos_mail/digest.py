from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from src.eos_mail.gmail_client import MailSummary
from src.eos_mail.rules import (
    EOS_ACTION_REQUIRED,
    EOS_REVIEW_NEEDED,
    MONEY_BANKING,
    MONEY_CREDIT_CARD,
    MONEY_INVOICE,
    MONEY_RECEIPT,
    MONEY_SUBSCRIPTION,
    MONEY_TAX,
    NEWSLETTER_HIGH_SIGNAL,
    NEWSLETTER_LOW_SIGNAL,
    NEWSLETTER_NORMAL,
    NEWSLETTER_UNSUBSCRIBE_CANDIDATE,
    RISK_PHISHING_SUSPECTED,
    RISK_UNKNOWN_SENDER,
    SECURITY_CATEGORIES,
)

try:
    from src.eos_mail.classifier import classify_mail as _classify_mail
    from src.eos_mail.types import MailClassification, MailInput
except ImportError:  # pragma: no cover - exercised by strict fallback tests via monkeypatch
    _classify_mail = None
    MailClassification = Any  # type: ignore[misc, assignment]
    MailInput = None  # type: ignore[assignment]

CLASSIFIER_UNAVAILABLE = "classifier_unavailable"
DIGEST_BUCKETS = (
    "critical",
    "action_required",
    "review_needed",
    "finance",
    "security",
    "newsletter_high_signal",
    "newsletter_normal",
    "newsletter_low_signal",
    "unknown",
)

DigestBuckets = dict[str, list[MailSummary]]


def bucket_messages(messages: list[MailSummary]) -> DigestBuckets:
    buckets: DigestBuckets = defaultdict(list)
    for message in messages:
        for bucket in _buckets_for_message(message):
            buckets[bucket].append(message)
    for key in DIGEST_BUCKETS:
        buckets.setdefault(key, [])
    return dict(buckets)


def digest_payload(messages: list[MailSummary]) -> dict[str, Any]:
    buckets, classifications, issues = _digest_components(messages)
    return {
        "status": "partial" if issues else "success",
        "issue": issues[0] if issues else None,
        "issues": issues,
        "classifier_enabled": CLASSIFIER_UNAVAILABLE not in issues,
        "total_messages_scanned": len(messages),
        "groups": {
            key: [message.to_dict() for message in value]
            for key, value in buckets.items()
        },
        "counts": {key: len(value) for key, value in buckets.items()},
        "classifications": classifications,
    }


def render_shadow_digest(messages: list[MailSummary]) -> str:
    payload = digest_payload(messages)
    counts = payload["counts"]
    lines = [
        "# Gmail Shadow Digest",
        "",
        f"Status: {payload['status']}",
        f"Total messages scanned: {payload['total_messages_scanned']}",
        f"Critical: {counts['critical']}",
        f"Action required: {counts['action_required']}",
        f"Review needed: {counts['review_needed']}",
        f"Finance: {counts['finance']}",
        f"Security: {counts['security']}",
        f"Newsletter high signal: {counts['newsletter_high_signal']}",
        f"Newsletter normal: {counts['newsletter_normal']}",
        f"Newsletter low signal: {counts['newsletter_low_signal']}",
        f"Unknown: {counts['unknown']}",
    ]
    if payload["issue"]:
        lines.append(f"Issue: {payload['issue']}")
    return "\n".join(lines).strip() + "\n"


def _digest_components(messages: list[MailSummary]) -> tuple[DigestBuckets, dict[str, Any], list[str]]:
    buckets: DigestBuckets = defaultdict(list)
    classifications: dict[str, Any] = {}
    issues: list[str] = []
    classifier = _classifier()

    for message in messages:
        if classifier is None:
            if CLASSIFIER_UNAVAILABLE not in issues:
                issues.append(CLASSIFIER_UNAVAILABLE)
            message_buckets = _metadata_buckets_for_message(message)
        else:
            classification = classifier(_mail_input_from_summary(message))
            classifications[message.message_id] = classification.to_dict()
            message_buckets = _buckets_for_classification(classification)
        for bucket in message_buckets:
            buckets[bucket].append(message)

    for key in DIGEST_BUCKETS:
        buckets.setdefault(key, [])
    return dict(buckets), classifications, issues


def _classifier() -> Callable[[Any], Any] | None:
    return _classify_mail


def _mail_input_from_summary(message: MailSummary) -> Any:
    if MailInput is None:
        raise RuntimeError("classifier MailInput is unavailable")
    headers = dict(message.headers_subset)
    if message.sender:
        headers.setdefault("From", message.sender)
    if message.subject:
        headers.setdefault("Subject", message.subject)
    return MailInput(
        message_id=message.message_id,
        thread_id=message.thread_id,
        sender=message.sender or "",
        subject=message.subject or "",
        snippet=message.snippet or "",
        body_excerpt=None,
        headers=headers,
    )


def _buckets_for_message(message: MailSummary) -> tuple[str, ...]:
    classifier = _classifier()
    if classifier is None:
        return _metadata_buckets_for_message(message)
    return _buckets_for_classification(classifier(_mail_input_from_summary(message)))


def _buckets_for_classification(classification: Any) -> tuple[str, ...]:
    categories = set(classification.categories)
    buckets: list[str] = []
    if classification.priority == "critical":
        buckets.append("critical")
    if classification.requires_reply or EOS_ACTION_REQUIRED in categories:
        buckets.append("action_required")
    if EOS_REVIEW_NEEDED in categories:
        buckets.append("review_needed")
    if categories & {
        MONEY_BANKING,
        MONEY_CREDIT_CARD,
        MONEY_INVOICE,
        MONEY_RECEIPT,
        MONEY_SUBSCRIPTION,
        MONEY_TAX,
    }:
        buckets.append("finance")
    if categories & SECURITY_CATEGORIES or RISK_PHISHING_SUSPECTED in categories:
        buckets.append("security")
    if NEWSLETTER_HIGH_SIGNAL in categories:
        buckets.append("newsletter_high_signal")
    if NEWSLETTER_NORMAL in categories:
        buckets.append("newsletter_normal")
    if categories & {NEWSLETTER_LOW_SIGNAL, NEWSLETTER_UNSUBSCRIBE_CANDIDATE}:
        buckets.append("newsletter_low_signal")
    if RISK_UNKNOWN_SENDER in categories:
        buckets.append("unknown")
    if not buckets:
        buckets.append("unknown")
    return tuple(dict.fromkeys(buckets))


def _metadata_buckets_for_message(message: MailSummary) -> tuple[str, ...]:
    haystack = " ".join(
        part.lower()
        for part in (
            message.sender or "",
            message.subject or "",
            message.snippet or "",
            " ".join(message.label_ids),
        )
    )
    buckets: list[str] = []
    if _looks_finance_or_security(haystack):
        if _looks_security(haystack):
            buckets.extend(("critical", "review_needed", "security"))
        else:
            buckets.extend(("review_needed", "finance"))
    if message.headers_subset.get("List-Unsubscribe") or "category_promotions" in haystack:
        buckets.append("newsletter_normal")
    if _looks_important(haystack):
        buckets.append("action_required")
    if message.has_attachments:
        buckets.append("review_needed")
    if not buckets:
        buckets.append("unknown")
    return tuple(dict.fromkeys(buckets))


def _looks_finance_or_security(text: str) -> bool:
    markers = (
        "bank",
        "credit card",
        "kreditkarte",
        "invoice",
        "rechnung",
        "receipt",
        "paypal",
        "stripe",
        "tax",
        "security",
        "login",
        "password",
        "passwort",
        "otp",
        "verification",
        "suspicious",
    )
    return any(marker in text for marker in markers)


def _looks_security(text: str) -> bool:
    markers = (
        "security",
        "login",
        "password",
        "passwort",
        "otp",
        "verification",
        "suspicious",
    )
    return any(marker in text for marker in markers)


def _looks_important(text: str) -> bool:
    markers = (
        "urgent",
        "wichtig",
        "deadline",
        "action required",
        "antwort",
        "reply",
        "due",
        "termin",
    )
    return any(marker in text for marker in markers)
