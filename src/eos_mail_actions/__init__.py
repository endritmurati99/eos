from src.eos_mail_actions.action_extractor import extract_actions
from src.eos_mail_actions.deadline_extractor import extract_deadline
from src.eos_mail_actions.task_proposal import build_task_proposals
from src.eos_mail_actions.types import (
    ActionExtraction,
    DeadlineExtraction,
    MailActionInput,
    TaskProposal,
)

__all__ = [
    "ActionExtraction",
    "DeadlineExtraction",
    "MailActionInput",
    "TaskProposal",
    "build_task_proposals",
    "extract_actions",
    "extract_deadline",
]
