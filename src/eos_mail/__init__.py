from __future__ import annotations

from src.eos_mail.audit import run_mail_audit
from src.eos_mail.auth_preflight import run_gmail_auth_preflight
from src.eos_mail.classifier import classify_mail
from src.eos_mail.digest import render_shadow_digest
from src.eos_mail.gmail_client import (
    GogGmailReadOnlyClient,
    GmailClientError,
    GmailReadOnlyClient,
    MailSummary,
    MessageRef,
)
from src.eos_mail.types import MailClassification, MailInput

__all__ = [
    "GmailClientError",
    "GmailReadOnlyClient",
    "GogGmailReadOnlyClient",
    "MailClassification",
    "MailInput",
    "MailSummary",
    "MessageRef",
    "classify_mail",
    "render_shadow_digest",
    "run_gmail_auth_preflight",
    "run_mail_audit",
]
