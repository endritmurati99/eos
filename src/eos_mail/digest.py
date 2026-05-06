from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.eos_mail.gmail_client import MailSummary

DigestBuckets = dict[str, list[MailSummary]]


def bucket_messages(messages: list[MailSummary]) -> DigestBuckets:
    buckets: DigestBuckets = defaultdict(list)
    for message in messages:
        bucket = _bucket_for_message(message)
        buckets[bucket].append(message)
    for key in (
        "likely_important",
        "likely_newsletters",
        "likely_finance_security",
        "review_needed",
        "unknown",
    ):
        buckets.setdefault(key, [])
    return dict(buckets)


def digest_payload(messages: list[MailSummary]) -> dict[str, Any]:
    buckets = bucket_messages(messages)
    return {
        "total_messages_scanned": len(messages),
        "groups": {
            key: [message.to_dict() for message in value]
            for key, value in buckets.items()
        },
        "counts": {key: len(value) for key, value in buckets.items()},
    }


def render_shadow_digest(messages: list[MailSummary]) -> str:
    payload = digest_payload(messages)
    counts = payload["counts"]
    lines = [
        "# Gmail Shadow Digest",
        "",
        f"Total messages scanned: {payload['total_messages_scanned']}",
        f"Likely important: {counts['likely_important']}",
        f"Likely newsletters: {counts['likely_newsletters']}",
        f"Likely finance/security: {counts['likely_finance_security']}",
        f"Review needed: {counts['review_needed']}",
        f"Unknown: {counts['unknown']}",
    ]
    return "\n".join(lines).strip() + "\n"


def _bucket_for_message(message: MailSummary) -> str:
    haystack = " ".join(
        part.lower()
        for part in (
            message.sender or "",
            message.subject or "",
            message.snippet or "",
            " ".join(message.label_ids),
        )
    )
    if _looks_finance_or_security(haystack):
        return "likely_finance_security"
    if message.headers_subset.get("List-Unsubscribe") or "category_promotions" in haystack:
        return "likely_newsletters"
    if _looks_important(haystack):
        return "likely_important"
    if message.has_attachments:
        return "review_needed"
    return "unknown"


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
