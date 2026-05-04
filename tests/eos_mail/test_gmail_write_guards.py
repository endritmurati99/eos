from __future__ import annotations

import ast
from pathlib import Path

from src.eos_mail.gmail_client import (
    FORBIDDEN_GMAIL_WRITE_SCOPES,
    GOG_GMAIL_CONTRACT_COMMANDS,
    GogGmailReadOnlyClient,
    READONLY_SCOPE,
)

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def test_no_gmail_write_scopes_are_configured_for_runtime() -> None:
    env_example = (WORKSPACE_ROOT / ".env.example").read_text(encoding="utf-8")

    assert READONLY_SCOPE == "https://www.googleapis.com/auth/gmail.readonly"
    for forbidden_scope in FORBIDDEN_GMAIL_WRITE_SCOPES:
        assert forbidden_scope not in env_example


def test_gog_contract_commands_have_no_write_actions_or_scopes() -> None:
    forbidden_terms = {
        "send",
        "delete",
        "trash",
        "archive",
        "modify",
        "labels",
        "create-label",
        "mark-read",
        "mark-unread",
        *FORBIDDEN_GMAIL_WRITE_SCOPES,
    }

    for command in GOG_GMAIL_CONTRACT_COMMANDS.values():
        rendered = " ".join(command).lower().replace("list-unsubscribe", "")
        for forbidden in forbidden_terms:
            assert forbidden not in rendered


def test_readonly_client_exposes_no_write_like_methods() -> None:
    forbidden_method_names = {
        "send",
        "delete",
        "archive",
        "trash",
        "modify_label",
        "modify_labels",
        "unsubscribe",
    }

    assert forbidden_method_names.isdisjoint(set(dir(GogGmailReadOnlyClient)))


def test_eos_mail_implementation_defines_no_write_methods() -> None:
    forbidden_function_names = {
        "send",
        "delete",
        "archive",
        "trash",
        "modify_label",
        "modify_labels",
        "unsubscribe",
    }

    discovered: list[tuple[str, str]] = []
    for path in sorted((WORKSPACE_ROOT / "src" / "eos_mail").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in forbidden_function_names:
                discovered.append((str(path.relative_to(WORKSPACE_ROOT)), node.name))

    assert discovered == []
