from __future__ import annotations

import re
from src.eos_intake_v2.models import AskIntent


def route_ask_intent(query: str) -> AskIntent:
    text = _normalize(query)
    if not text:
        return AskIntent("unknown", 0.0, "empty_query", query)

    meeting_entity = _extract_meeting_entity(query)
    if _has_any(text, ("meeting", "termin", "sync", "call", "besprechung")) and _has_any(text, ("was war", "nochmal", "kontext", "brief", "vorbereiten", "mit ")):
        return AskIntent("meeting_lookup", 0.88, "meeting_lookup_keywords", query, {"search_text": meeting_entity or query})

    if _has_any(text, ("antworten", "antwort", "reply", "mails", "mail", "email", "postfach", "inbox")):
        return AskIntent("mail_review", 0.9, "mail_review_keywords", query)

    if _has_any(text, ("jetzt", "gerade", "naechste aktion", "nächste aktion", "next action", "was soll ich machen", "was kann ich machen")):
        return AskIntent("next_best_action", 0.92, "next_action_keywords", query)

    if _has_any(text, ("offen", "open loops", "offene schleifen", "haengt", "hängt", "todo", "to do", "tasks")):
        return AskIntent("open_loops", 0.84, "open_loop_keywords", query)

    if _has_any(text, ("ueberladen", "überladen", "zu viel", "overload", "woche", "weekly", "diese woche")):
        return AskIntent("weekly_review", 0.82, "weekly_review_keywords", query)

    if _has_any(text, ("status", "health", "bereit", "readiness", "laeuft eos", "läuft eos", "system")):
        return AskIntent("system_health", 0.86, "system_health_keywords", query)

    if _has_any(text, ("review", "abend", "rueckblick", "rückblick", "morgen wichtig", "was lief")):
        return AskIntent("journal_reflection", 0.78, "review_keywords", query)

    if _has_any(text, ("heute", "tag", "wichtig", "realistisch", "machbar", "fokusblock", "fokus")):
        return AskIntent("daily_status", 0.86, "daily_status_keywords", query)

    return AskIntent("daily_status", 0.55, "fallback_daily_status", query)


def _normalize(value: str) -> str:
    return " ".join((value or "").strip().lower().split())


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def _extract_meeting_entity(query: str) -> str | None:
    match = re.search(r"\b(?:mit|with)\s+([^?.,;!]+)", query, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None
