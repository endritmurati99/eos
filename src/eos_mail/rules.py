from __future__ import annotations

import re
import unicodedata

EOS_ACTION_REQUIRED = "_EOS/Action Required"
EOS_REVIEW_NEEDED = "_EOS/Review Needed"

PRIORITY_CRITICAL = "_Priority/Critical"
PRIORITY_IMPORTANT = "_Priority/Important"
PRIORITY_LOW = "_Priority/Low"

MONEY_BANKING = "_Money/Banking"
MONEY_CREDIT_CARD = "_Money/Credit Card"
MONEY_INVOICE = "_Money/Invoice"
MONEY_RECEIPT = "_Money/Receipt"
MONEY_TAX = "_Money/Tax"
MONEY_SUBSCRIPTION = "_Money/Subscription"

SECURITY_LOGIN_ALERT = "_Security/Login Alert"
SECURITY_PASSWORD_RESET = "_Security/Password Reset"
SECURITY_OTP = "_Security/OTP"
SECURITY_SUSPICIOUS = "_Security/Suspicious"

NEWSLETTER_HIGH_SIGNAL = "_Newsletter/High Signal"
NEWSLETTER_NORMAL = "_Newsletter/Normal"
NEWSLETTER_LOW_SIGNAL = "_Newsletter/Low Signal"
NEWSLETTER_UNSUBSCRIBE_CANDIDATE = "_Newsletter/Unsubscribe Candidate"

RISK_SPAM_REVIEW = "_Risk/Spam Review"
RISK_PHISHING_SUSPECTED = "_Risk/Phishing Suspected"
RISK_UNKNOWN_SENDER = "_Risk/Unknown Sender"

PERSONAL = "_Personal"
WORK = "_Work"
UNIVERSITY = "_University"
HEALTH = "_Health"
TRAVEL = "_Travel"
SHOPPING = "_Shopping"
LEGAL = "_Legal"

PRIORITY_TO_CATEGORY = {
    "critical": PRIORITY_CRITICAL,
    "important": PRIORITY_IMPORTANT,
    "low": PRIORITY_LOW,
}

SECURITY_CATEGORIES = {
    SECURITY_LOGIN_ALERT,
    SECURITY_PASSWORD_RESET,
    SECURITY_OTP,
    SECURITY_SUSPICIOUS,
}

RISK_CATEGORIES = {
    RISK_SPAM_REVIEW,
    RISK_PHISHING_SUSPECTED,
    RISK_UNKNOWN_SENDER,
}

NEWSLETTER_CATEGORIES = {
    NEWSLETTER_HIGH_SIGNAL,
    NEWSLETTER_NORMAL,
    NEWSLETTER_LOW_SIGNAL,
    NEWSLETTER_UNSUBSCRIBE_CANDIDATE,
}

NO_ARCHIVE_CATEGORIES = {
    EOS_ACTION_REQUIRED,
    EOS_REVIEW_NEEDED,
    MONEY_BANKING,
    MONEY_CREDIT_CARD,
    MONEY_INVOICE,
    MONEY_RECEIPT,
    MONEY_TAX,
    MONEY_SUBSCRIPTION,
    *SECURITY_CATEGORIES,
    *RISK_CATEGORIES,
    LEGAL,
    HEALTH,
}

RULE_GROUPS = (
    "newsletter_header",
    "newsletter_signal_quality",
    "invoice",
    "receipt",
    "banking",
    "credit_card",
    "tax",
    "subscription",
    "security_login_alert",
    "security_password_reset",
    "security_otp",
    "phishing_suspected",
    "spam_review",
    "reply_required",
    "work_context",
    "university_context",
    "travel_booking",
    "shopping_delivery",
    "health_appointment",
    "legal_context",
    "unknown_sender",
)

KEYWORDS: dict[str, tuple[str, ...]] = {
    "newsletter_high_signal": (
        "research brief",
        "policy digest",
        "security digest",
        "high signal",
        "curated research",
        "weekly research",
    ),
    "newsletter_low_signal": (
        "daily deals",
        "limited time",
        "coupon",
        "promo",
        "sale",
        "sponsored",
        "clearance",
    ),
    "newsletter_unsubscribe_candidate": (
        "you are receiving this newsletter",
        "unsubscribe at any time",
        "manage email preferences",
        "marketing update",
    ),
    "newsletter_normal": (
        "newsletter",
        "weekly digest",
        "roundup",
        "monthly update",
        "community update",
    ),
    "banking": (
        "bank account",
        "account statement",
        "bank statement",
        "monthly statement",
        "monthly bank statement",
        "balance notice",
        "direct debit",
        "wire transfer",
        "deposit notice",
    ),
    "credit_card": (
        "credit card",
        "kreditkarte",
        "card alert",
        "card transaction",
        "new charge",
        "charge alert",
        "card statement",
    ),
    "invoice": (
        "invoice",
        "rechnung",
        "zahlung faellig",
        "zahlungsaufforderung",
        "bill is ready",
        "payment due",
        "amount due",
    ),
    "receipt": (
        "receipt",
        "beleg",
        "zahlungsbeleg",
        "zahlung erhalten",
        "payment received",
        "purchase confirmation",
        "order receipt",
    ),
    "tax": (
        "tax document",
        "tax filing",
        "tax notice",
        "steuer",
        "year-end tax",
    ),
    "subscription": (
        "subscription",
        "membership renewal",
        "plan renews",
        "renewal notice",
        "trial ends",
    ),
    "security_login_alert": (
        "login alert",
        "anmeldewarnung",
        "new sign-in",
        "new signin",
        "new login",
        "new device",
        "account access",
    ),
    "security_password_reset": (
        "password reset",
        "reset your password",
        "passwort zuruecksetzen",
        "passwort zurucksetzen",
        "change your password",
    ),
    "security_otp": (
        "one-time code",
        "one time code",
        "one-time password",
        "one time password",
        "verification code",
        "verifizierungscode",
        "bestaetigungscode",
        "security code",
        "two-factor code",
        "2fa",
        "2fa code",
        "otp",
    ),
    "security_suspicious": (
        "suspicious",
        "unusual activity",
        "unrecognized device",
        "suspicious access",
    ),
    "phishing": (
        "verify immediately",
        "verify your account immediately",
        "account suspended",
        "mailbox will be closed",
        "confirm your password",
        "avoid suspension",
        "urgent account verification",
        "security hold",
    ),
    "spam": (
        "you won",
        "winner",
        "lottery",
        "free money",
        "guaranteed income",
        "crypto giveaway",
        "claim your prize",
    ),
    "reply_required": (
        "please reply",
        "bitte antworten",
        "bitte bestaetigen",
        "bitte bestatigen",
        "antwort erforderlich",
        "reply by",
        "respond by",
        "can you confirm",
        "please confirm",
        "requires your response",
        "please review",
        "action required",
        "approval needed",
        "rsvp",
        "deadline",
        "send me",
        "could you send",
    ),
    "work": (
        "project",
        "client",
        "team",
        "manager",
        "quarterly",
        "standup",
        "workstream",
        "meeting",
    ),
    "university": (
        "university",
        "campus",
        "registrar",
        "course",
        "seminar",
        "exam",
        "assignment",
        "student office",
    ),
    "personal": (
        "dinner",
        "family",
        "friend",
        "birthday",
        "coffee",
        "weekend",
    ),
    "travel": (
        "flight",
        "hotel",
        "booking confirmation",
        "reservation",
        "itinerary",
        "boarding",
    ),
    "shopping": (
        "package",
        "delivery",
        "tracking",
        "shipped",
        "order update",
        "out for delivery",
    ),
    "health": (
        "clinic",
        "doctor",
        "appointment reminder",
        "patient",
        "lab result",
        "health appointment",
    ),
    "legal": (
        "legal notice",
        "contract",
        "contract review",
        "attorney",
        "law office",
        "court",
        "mahnung",
        "terms notice",
        "sign the agreement",
    ),
}


def normalize_text(*parts: str | None) -> str:
    raw = " ".join(part for part in parts if part)
    folded = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    lowered = folded.casefold()
    return re.sub(r"\s+", " ", lowered).strip()


def normalize_headers(headers: dict[str, str] | None) -> dict[str, str]:
    return {str(key).casefold(): str(value) for key, value in (headers or {}).items()}


def has_list_unsubscribe(headers: dict[str, str] | None) -> bool:
    normalized = normalize_headers(headers)
    return bool(normalized.get("list-unsubscribe", "").strip())


def matches_any(text: str, keywords: tuple[str, ...]) -> tuple[str, ...]:
    matches: list[str] = []
    for keyword in keywords:
        pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
        if re.search(pattern, text):
            matches.append(keyword)
    return tuple(matches)


def sender_domain(sender: str) -> str:
    match = re.search(r"@([^>\s]+)", sender or "")
    if not match:
        return ""
    return match.group(1).strip().casefold()
