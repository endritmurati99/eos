from __future__ import annotations

from src.eos_intake_v2.models import AskAnswer, AskIntent, SafetyDecision, SourceRequest, SourceSnapshot


def render_answer(
    *,
    intent: AskIntent,
    sources: list[SourceRequest],
    snapshots: list[SourceSnapshot],
    safety: SafetyDecision,
) -> AskAnswer:
    primary = _first_assistant_payload(snapshots)
    action = _first_action(primary)
    status = _overall_status(snapshots)
    why = _why_lines(intent, sources, snapshots)
    uncertainty = _uncertainty_lines(intent, snapshots)
    vault = _vault_payload(snapshots)
    answer = _answer_line(intent, primary, action, vault)
    next_action = _next_action_line(intent, action)
    return AskAnswer(
        status=status,
        command="ask",
        query=intent.query,
        intent=intent.intent,
        confidence=intent.confidence,
        answer=answer,
        why=why,
        next_action=next_action,
        uncertainty=uncertainty,
        sources_selected=[source.to_dict() for source in sources],
        source_status={snapshot.name: {"status": snapshot.status, "error": snapshot.error} for snapshot in snapshots},
        safety=safety.to_dict(),
        mode="read_only" if safety.status == "success" else "degraded",
    )


def _first_assistant_payload(snapshots: list[SourceSnapshot]) -> dict:
    for snapshot in snapshots:
        if snapshot.name.startswith("assistant:") and snapshot.payload:
            return snapshot.payload
    return {}


def _first_action(payload: dict) -> dict:
    actions = payload.get("actions") if isinstance(payload, dict) else None
    if isinstance(actions, list) and actions:
        first = actions[0]
        if isinstance(first, dict):
            return first
    return {}


def _overall_status(snapshots: list[SourceSnapshot]) -> str:
    statuses = {snapshot.status for snapshot in snapshots}
    if "failed" in statuses:
        return "warning"
    if statuses & {"warning", "not_implemented", "unknown"}:
        return "warning"
    return "success"


def _answer_line(intent: AskIntent, payload: dict, action: dict, vault: dict) -> str:
    if intent.intent == "next_best_action" and action.get("label"):
        return f"Jetzt ist am sinnvollsten: {action['label']}."
    if intent.intent == "mail_review":
        return "Mail ist read-only geprüft; EOS schlägt keine Gmail-Schreibaktion vor."
    if intent.intent == "meeting_lookup":
        search = intent.entities.get("search_text") or intent.query
        return f"Meeting-Lookup für '{search}' ist erkannt, aber historische Kalender/Vault-Suche ist in v1 noch nicht live verdrahtet."
    if intent.intent == "system_health":
        return _first_summary_line(payload) or "EOS-Status wurde geprüft."
    if intent.intent in {"daily_status", "journal_reflection"} and vault.get("summary_markdown"):
        return _first_summary_line(vault) or _first_summary_line(payload) or "EOS hat den Tagesstand aus der Daily Note gelesen."
    if intent.intent == "weekly_review":
        return "Wochen-/Overload-Frage erkannt; v1 nutzt vorerst Status und Tageskontext, noch keine vollständige Wochenlastanalyse."
    return _first_summary_line(payload) or "EOS hat die Frage operativ eingeordnet."


def _next_action_line(intent: AskIntent, action: dict) -> str:
    if action.get("label"):
        reason = action.get("reason")
        return f"{action['label']}" + (f" — {reason}" if reason else "")
    if intent.intent == "meeting_lookup":
        return "Als nächsten Schritt historische Kalender- und Vault-Suche implementieren, bevor EOS Meeting-Kontext behauptet."
    if intent.intent == "mail_review":
        return "Mail-Digest prüfen; Writes bleiben approval-gated."
    return "Eine kurze manuelle Prüfung machen, bevor EOS externe Aktionen ausführt."


def _why_lines(intent: AskIntent, sources: list[SourceRequest], snapshots: list[SourceSnapshot]) -> list[str]:
    lines = [f"Intent '{intent.intent}' erkannt ({intent.reason}, confidence {intent.confidence:.2f})."]
    lines.extend(f"Quelle gewählt: {source.name} — {source.reason}" for source in sources[:4])
    for snapshot in snapshots:
        if snapshot.name.startswith("assistant:"):
            lines.append(f"{snapshot.name} lieferte Status {snapshot.status}.")
        if snapshot.name == "vault_notes" and snapshot.status == "success":
            note = snapshot.payload.get("daily_note") if snapshot.payload else None
            lines.append(f"vault_notes lieferte Daily-Note-Kontext{f' aus {note}' if note else ''}.")
    return lines[:6]


def _uncertainty_lines(intent: AskIntent, snapshots: list[SourceSnapshot]) -> list[str]:
    lines = []
    for snapshot in snapshots:
        if snapshot.status in {"failed", "not_implemented", "warning", "unknown"}:
            lines.append(f"{snapshot.name}: {snapshot.error or snapshot.status}")
    if intent.confidence < 0.7:
        lines.append("Intent nur mit mittlerer Sicherheit erkannt.")
    return lines[:5]


def _first_summary_line(payload: dict) -> str:
    summary = str(payload.get("summary_markdown") or "").strip()
    if not summary:
        return ""
    for line in summary.splitlines():
        cleaned = line.strip()
        if cleaned and not cleaned.startswith("## "):
            return cleaned.removeprefix("- ").strip()
    return ""


def _vault_payload(snapshots: list[SourceSnapshot]) -> dict:
    for snapshot in snapshots:
        if snapshot.name == "vault_notes" and snapshot.payload:
            return snapshot.payload
    return {}
