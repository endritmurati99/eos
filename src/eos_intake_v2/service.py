from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Callable

from src.eos_assistant import run_assistant_command
from src.eos_intake_v2.context_builder import build_context
from src.eos_intake_v2.intent_router import route_ask_intent
from src.eos_intake_v2.response_renderer import render_answer
from src.eos_intake_v2.safety_gate import check_ask_safety
from src.eos_intake_v2.source_selector import select_sources


def route_query(query: str) -> dict[str, Any]:
    intent = route_ask_intent(query)
    sources = select_sources(intent)
    safety = check_ask_safety(intent, sources)
    return {
        "status": "success" if intent.intent != "unknown" else "warning",
        "command": "intake route",
        "query": query,
        "intent": intent.to_dict(),
        "sources_selected": [source.to_dict() for source in sources],
        "safety": safety.to_dict(),
    }


def ask(
    query: str,
    *,
    target_date: date | None = None,
    workspace_root: str | Path | None = None,
    assistant_runner: Callable[..., dict] = run_assistant_command,
) -> dict[str, Any]:
    intent = route_ask_intent(query)
    sources = select_sources(intent)
    safety = check_ask_safety(intent, sources)
    snapshots = build_context(
        intent,
        sources,
        target_date=target_date,
        workspace_root=workspace_root,
        assistant_runner=assistant_runner,
    )
    return render_answer(intent=intent, sources=sources, snapshots=snapshots, safety=safety).to_dict()
