from __future__ import annotations

from src.eos_mail.rules import (
    EOS_ACTION_REQUIRED,
    EOS_REVIEW_NEEDED,
    HEALTH,
    KEYWORDS,
    LEGAL,
    MONEY_BANKING,
    MONEY_CREDIT_CARD,
    MONEY_INVOICE,
    MONEY_RECEIPT,
    MONEY_SUBSCRIPTION,
    MONEY_TAX,
    NEWSLETTER_CATEGORIES,
    NEWSLETTER_HIGH_SIGNAL,
    NEWSLETTER_LOW_SIGNAL,
    NEWSLETTER_NORMAL,
    NEWSLETTER_UNSUBSCRIBE_CANDIDATE,
    NO_ARCHIVE_CATEGORIES,
    PERSONAL,
    PRIORITY_TO_CATEGORY,
    RISK_PHISHING_SUSPECTED,
    RISK_SPAM_REVIEW,
    RISK_UNKNOWN_SENDER,
    SECURITY_CATEGORIES,
    SECURITY_LOGIN_ALERT,
    SECURITY_OTP,
    SECURITY_PASSWORD_RESET,
    SECURITY_SUSPICIOUS,
    SHOPPING,
    TRAVEL,
    UNIVERSITY,
    WORK,
    has_list_unsubscribe,
    matches_any,
    normalize_headers,
    normalize_text,
    sender_domain,
)
from src.eos_mail.types import MailClassification, MailInput


def classify_mail(mail: MailInput) -> MailClassification:
    headers = normalize_headers(mail.headers)
    text = normalize_text(mail.sender, mail.subject, mail.snippet, mail.body_excerpt)
    sender = normalize_text(mail.sender)
    domain = sender_domain(mail.sender)
    list_unsubscribe = has_list_unsubscribe(headers)

    categories: list[str] = []
    risk_flags: list[str] = []
    reasons: list[str] = []
    evidence_scores: list[float] = []

    def add_category(category: str, reason: str, confidence: float) -> None:
        if category not in categories:
            categories.append(category)
        if reason not in reasons:
            reasons.append(reason)
        evidence_scores.append(confidence)

    def add_risk_flag(flag: str) -> None:
        if flag not in risk_flags:
            risk_flags.append(flag)

    if matches_any(text, KEYWORDS["phishing"]) or "account-verify" in domain:
        add_category(RISK_PHISHING_SUSPECTED, "phishing pattern matched", 0.96)
        add_category(SECURITY_SUSPICIOUS, "suspicious security language", 0.94)
        add_risk_flag("phishing_suspected")

    if matches_any(text, KEYWORDS["spam"]):
        add_category(RISK_SPAM_REVIEW, "spam pattern matched", 0.88)
        add_risk_flag("spam_review")

    if matches_any(text, KEYWORDS["security_password_reset"]):
        add_category(SECURITY_PASSWORD_RESET, "password reset signal", 0.96)
        add_risk_flag("security_sensitive")

    if matches_any(text, KEYWORDS["security_otp"]):
        add_category(SECURITY_OTP, "verification code signal", 0.96)
        add_risk_flag("security_sensitive")

    if matches_any(text, KEYWORDS["security_login_alert"]):
        add_category(SECURITY_LOGIN_ALERT, "login alert signal", 0.95)
        add_risk_flag("security_sensitive")

    if matches_any(text, KEYWORDS["security_suspicious"]):
        add_category(SECURITY_SUSPICIOUS, "suspicious access signal", 0.92)
        add_risk_flag("security_sensitive")

    if matches_any(text, KEYWORDS["banking"]):
        add_category(MONEY_BANKING, "banking keyword matched", 0.90)
        add_risk_flag("sensitive_banking")

    if matches_any(text, KEYWORDS["credit_card"]):
        add_category(MONEY_CREDIT_CARD, "credit card keyword matched", 0.91)
        add_risk_flag("sensitive_credit_card")

    if matches_any(text, KEYWORDS["tax"]):
        add_category(MONEY_TAX, "tax keyword matched", 0.90)
        add_risk_flag("sensitive_tax")

    if matches_any(text, KEYWORDS["invoice"]):
        add_category(MONEY_INVOICE, "invoice keyword matched", 0.90)

    if matches_any(text, KEYWORDS["receipt"]):
        add_category(MONEY_RECEIPT, "receipt keyword matched", 0.88)

    if matches_any(text, KEYWORDS["subscription"]):
        add_category(MONEY_SUBSCRIPTION, "subscription keyword matched", 0.87)

    if list_unsubscribe or matches_any(text, KEYWORDS["newsletter_normal"]):
        newsletter_confidence = 0.97 if list_unsubscribe else 0.72
        if matches_any(text, KEYWORDS["newsletter_high_signal"]):
            add_category(NEWSLETTER_HIGH_SIGNAL, "high-signal newsletter signal", newsletter_confidence)
        elif matches_any(text, KEYWORDS["newsletter_unsubscribe_candidate"]):
            add_category(
                NEWSLETTER_UNSUBSCRIBE_CANDIDATE,
                "unsubscribe candidate newsletter signal",
                newsletter_confidence,
            )
        elif matches_any(text, KEYWORDS["newsletter_low_signal"]):
            add_category(NEWSLETTER_LOW_SIGNAL, "low-signal newsletter signal", newsletter_confidence)
        else:
            add_category(NEWSLETTER_NORMAL, "newsletter header or keyword matched", newsletter_confidence)

    if matches_any(text, KEYWORDS["university"]) or "university" in domain or ".edu" in domain:
        add_category(UNIVERSITY, "university signal", 0.89)

    if matches_any(text, KEYWORDS["work"]) or "example-company" in domain:
        add_category(WORK, "work signal", 0.88)

    if matches_any(text, KEYWORDS["personal"]) or "example-personal" in domain:
        add_category(PERSONAL, "personal signal", 0.86)

    if matches_any(text, KEYWORDS["travel"]) or "travel" in domain:
        add_category(TRAVEL, "travel booking signal", 0.90)

    if matches_any(text, KEYWORDS["shopping"]) or "shop" in domain:
        add_category(SHOPPING, "shopping delivery signal", 0.88)

    if matches_any(text, KEYWORDS["health"]) or "clinic" in domain:
        add_category(HEALTH, "health appointment signal", 0.90)
        add_risk_flag("health_sensitive")

    if matches_any(text, KEYWORDS["legal"]) or "legal" in domain:
        add_category(LEGAL, "legal signal", 0.90)
        add_risk_flag("legal_sensitive")

    requires_reply = bool(matches_any(text, KEYWORDS["reply_required"]))
    if requires_reply:
        add_category(EOS_ACTION_REQUIRED, "reply or action cue matched", 0.88)

    content_categories = [
        category
        for category in categories
        if not category.startswith("_Priority/") and category not in {EOS_ACTION_REQUIRED, EOS_REVIEW_NEEDED}
    ]
    if not content_categories:
        add_category(RISK_UNKNOWN_SENDER, "no deterministic category matched", 0.45)
        add_risk_flag("unknown_sender")

    priority = _priority_for(categories, requires_reply, text)
    categories.insert(0, PRIORITY_TO_CATEGORY[priority])

    confidence = _bounded_confidence(max(evidence_scores) if evidence_scores else 0.45)
    if _needs_review(categories, risk_flags, confidence):
        if EOS_REVIEW_NEEDED not in categories:
            categories.append(EOS_REVIEW_NEEDED)

    safe_to_archive = _safe_to_archive(
        categories=categories,
        confidence=confidence,
        list_unsubscribe=list_unsubscribe,
        requires_reply=requires_reply,
        risk_flags=risk_flags,
    )

    reason = "; ".join(reasons[:4]) if reasons else "no deterministic category matched"
    return MailClassification(
        categories=categories,
        priority=priority,
        requires_reply=requires_reply,
        safe_to_archive=safe_to_archive,
        confidence=confidence,
        reason=reason,
        risk_flags=risk_flags,
    )


def _priority_for(categories: list[str], requires_reply: bool, text: str) -> str:
    if RISK_PHISHING_SUSPECTED in categories or any(category in SECURITY_CATEGORIES for category in categories):
        return "critical"
    if MONEY_CREDIT_CARD in categories and ("alert" in text or "new charge" in text):
        return "critical"
    if RISK_SPAM_REVIEW in categories or RISK_UNKNOWN_SENDER in categories:
        return "low"
    if requires_reply:
        return "important"
    if any(category in categories for category in (MONEY_BANKING, MONEY_INVOICE, MONEY_TAX, UNIVERSITY, LEGAL, TRAVEL, HEALTH)):
        return "important"
    if NEWSLETTER_HIGH_SIGNAL in categories:
        return "important"
    return "low"


def _bounded_confidence(raw_confidence: float) -> float:
    return round(min(1.0, max(0.0, raw_confidence)), 2)


def _needs_review(categories: list[str], risk_flags: list[str], confidence: float) -> bool:
    if confidence < 0.80:
        return True
    if any(flag in risk_flags for flag in ("phishing_suspected", "spam_review", "unknown_sender")):
        return True
    if any(category in categories for category in SECURITY_CATEGORIES):
        return True
    if any(category in categories for category in (MONEY_BANKING, MONEY_CREDIT_CARD, MONEY_TAX, LEGAL, HEALTH)):
        return True
    return False


def _safe_to_archive(
    *,
    categories: list[str],
    confidence: float,
    list_unsubscribe: bool,
    requires_reply: bool,
    risk_flags: list[str],
) -> bool:
    if not any(category in NEWSLETTER_CATEGORIES for category in categories):
        return False
    if NEWSLETTER_HIGH_SIGNAL in categories:
        return False
    if any(category in NO_ARCHIVE_CATEGORIES for category in categories):
        return False
    if requires_reply or risk_flags:
        return False
    return list_unsubscribe and confidence >= 0.95
