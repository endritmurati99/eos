from __future__ import annotations

from datetime import date

from src.eos_mail_actions.action_extractor import extract_actions
from src.eos_mail_actions.safety import redact_sensitive_text, task_list_for_action
from src.eos_mail_actions.types import MailActionInput, TaskProposal


TITLE_PREFIXES = {
    "reply_required": "Reply",
    "confirm_required": "Confirm",
    "send_document": "Send document",
    "review_invoice": "Review invoice",
    "pay_invoice": "Pay invoice",
    "check_bank_alert": "Review banking alert",
    "review_security_alert": "Review security alert",
    "review_legal_notice": "Review legal notice",
    "prepare_meeting": "Prepare meeting",
    "schedule_followup": "Schedule follow-up",
    "waiting_for_reply": "Waiting for reply",
}


def build_task_proposals(
    mail: MailActionInput,
    reference_date: date | str | None = None,
) -> list[TaskProposal]:
    proposals: list[TaskProposal] = []
    for action in extract_actions(mail, reference_date=reference_date):
        proposals.append(
            TaskProposal(
                source="mail",
                source_message_id=mail.message_id,
                title=_proposal_title(action.action_type, mail.subject),
                notes=_proposal_notes(mail, action.action_type),
                due=action.due,
                list_name=task_list_for_action(action.action_type, mail.categories),
                confidence=action.confidence,
                requires_approval=action.requires_approval,
                reason=action.reason,
                risk_flags=action.risk_flags,
            )
        )
    return proposals


def _proposal_title(action_type: str, subject: str) -> str:
    prefix = TITLE_PREFIXES.get(action_type, "Review")
    cleaned_subject = _clean_subject(subject)
    title = f"{prefix}: {cleaned_subject}" if cleaned_subject else prefix
    return title[:120]


def _clean_subject(subject: str) -> str:
    cleaned = subject.strip()
    for prefix in ("Re:", "RE:", "Fwd:", "FWD:", "Aw:", "AW:"):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
    return cleaned


def _proposal_notes(mail: MailActionInput, action_type: str) -> str:
    parts = [
        f"Action: {action_type}",
        f"Source mail: {mail.message_id or 'unknown'}",
        f"Thread: {mail.thread_id or 'unknown'}",
        f"Sender: {mail.sender}",
        f"Subject: {mail.subject}",
    ]
    if mail.snippet:
        parts.append(f"Snippet: {mail.snippet}")
    if mail.body_excerpt:
        parts.append(f"Excerpt: {mail.body_excerpt}")
    return redact_sensitive_text("\n".join(parts))
