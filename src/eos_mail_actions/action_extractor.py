from __future__ import annotations

import re
import unicodedata
from datetime import date

from src.eos_mail_actions.deadline_extractor import extract_deadline
from src.eos_mail_actions.safety import (
    is_sensitive_category,
    is_suppressed_category,
    requires_approval_for_action,
)
from src.eos_mail_actions.types import ActionExtraction, MailActionInput


def extract_actions(
    mail: MailActionInput,
    reference_date: date | str | None = None,
) -> list[ActionExtraction]:
    text = _mail_text(mail)
    normalized = _normalize_text(text)
    categories = mail.categories or []

    if is_suppressed_category(categories):
        return []

    deadline = extract_deadline(text, reference_date=mail.received_at or reference_date)
    actions: list[ActionExtraction] = []

    def add(action_type: str, confidence: float, reason: str) -> None:
        risk_flags = list(deadline.risk_flags)
        if is_sensitive_category(categories) and "sensitive_category" not in risk_flags:
            risk_flags.append("sensitive_category")
        requires_approval = requires_approval_for_action(
            action_type=action_type,
            confidence=confidence,
            categories=categories,
            risk_flags=risk_flags,
        )
        if deadline.requires_approval:
            requires_approval = True
        actions.append(
            ActionExtraction(
                action_type=action_type,
                confidence=confidence,
                reason=reason,
                due=deadline.due,
                requires_approval=requires_approval,
                risk_flags=risk_flags,
            )
        )

    if _is_banking_or_credit(categories):
        add("check_bank_alert", 0.88, "banking or credit card category requires review")
        return actions

    if _is_security_alert(categories):
        add("review_security_alert", 0.90, "security alert category requires review")
        return actions

    if "_Legal" in categories or _matches(normalized, ("legal notice", "contract review", "mahnung", "law office")):
        add("review_legal_notice", 0.88, "legal notice signal")
        return actions

    if "_Money/Invoice" in categories or _matches(normalized, ("invoice", "rechnung", "payment due", "amount due")):
        if _matches(normalized, ("pay", "payment due", "amount due", "zahlung", "faellig", "fallig")):
            add("pay_invoice", 0.86, "invoice payment signal")
        else:
            add("review_invoice", 0.84, "invoice review signal")
        return actions

    if _matches(normalized, ("prepare for", "prep for", "agenda", "meeting brief", "meeting prep")):
        add("prepare_meeting", 0.86, "meeting preparation signal")
        return actions

    if _matches(normalized, ("schedule follow-up", "schedule a follow-up", "follow up meeting", "next steps call")):
        add("schedule_followup", 0.84, "follow-up scheduling signal")
        return actions

    if _matches(normalized, ("waiting for reply", "waiting for a reply", "awaiting reply")) or "_EOS/Waiting For Reply" in categories:
        add("waiting_for_reply", 0.88, "waiting-for-reply signal")
        return actions

    if _matches(normalized, ("please send", "could you send", "send me", "send the document", "provide the document")):
        add("send_document", 0.88, "document request signal")
        return actions

    if _matches(normalized, ("please confirm", "can you confirm", "bitte bestaetigen", "bitte bestatigen", "rsvp")):
        add("confirm_required", 0.90, "confirmation request signal")
        return actions

    if _matches(normalized, ("please reply", "reply by", "respond by", "antwort erforderlich", "requires your response")) or "_EOS/Action Required" in categories:
        add("reply_required", 0.90, "reply request signal")
        return actions

    if "_Health" in categories and _matches(normalized, ("appointment", "termin", "confirm")):
        add("confirm_required", 0.86, "health appointment confirmation signal")

    return actions


def _mail_text(mail: MailActionInput) -> str:
    return " ".join(
        part
        for part in (mail.sender, mail.subject, mail.snippet, mail.body_excerpt)
        if part
    )


def _normalize_text(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    lowered = folded.casefold()
    return re.sub(r"\s+", " ", lowered).strip()


def _matches(normalized: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in normalized for phrase in phrases)


def _is_banking_or_credit(categories: list[str]) -> bool:
    return "_Money/Banking" in categories or "_Money/Credit Card" in categories


def _is_security_alert(categories: list[str]) -> bool:
    return any(category.startswith("_Security/") for category in categories)
