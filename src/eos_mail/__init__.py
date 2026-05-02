from __future__ import annotations

from src.eos_mail.classifier import classify_mail
from src.eos_mail.types import MailClassification, MailInput

__all__ = [
    "MailClassification",
    "MailInput",
    "classify_mail",
]
