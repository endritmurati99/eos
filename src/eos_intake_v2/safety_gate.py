from __future__ import annotations

from src.eos_intake_v2.models import AskIntent, SafetyDecision, SourceRequest


def check_ask_safety(intent: AskIntent, sources: list[SourceRequest]) -> SafetyDecision:
    return SafetyDecision(
        status="success",
        external_writes_allowed=False,
        external_writes_performed=False,
        requires_confirmation_for_writes=True,
        reason="ask_router_v1_is_read_only; selected sources are read-only snapshots or existing dry-run assistant surfaces",
    )
