from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.database.models import init_db
from src.dispatch.actions import (
    ACTION_ASSISTANT_RESPONSE,
    ACTION_CALENDAR_PROPOSAL,
    ACTION_CONFIRMATION_RESOLVE,
    ACTION_ENERGY_LOG,
    ACTION_HABIT_FAILURE,
    ACTION_HABIT_MARK_DONE,
    ACTION_HABIT_RECOVERY,
    ACTION_HABIT_RELAPSE,
    ACTION_HABIT_SKIP,
    ACTION_HABIT_STATUS,
    ACTION_NOOP,
    ACTION_PENDING_CONFIRMATION,
    ACTION_TASK_PROPOSAL,
    INTENT_TO_ACTION,
    idempotency_key,
    input_hash,
)
from src.dispatch.result import DispatchResult
from src.eos_assistant import run_assistant_command
from src.intake.confidence import CONFIDENCE_MEDIUM
from src.intake.intent_router import classify_intent

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _berlin_date() -> str:
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Berlin")
    except Exception:
        import pytz
        tz = pytz.timezone("Europe/Berlin")
    return datetime.now(tz).date().isoformat()


def _write_dispatch_log(
    connection: Any,
    *,
    source: str,
    raw_text: str,
    intent: str,
    confidence: float,
    action_type: str,
    target_service: str | None,
    result_status: str,
    idempotency_key_val: str | None,
    error: str | None,
) -> None:
    connection.execute(
        """
        INSERT INTO dispatch_log
            (timestamp_utc, source, input_hash, intent, confidence,
             action_type, target_service, result_status, idempotency_key, error_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            _now_utc(),
            source,
            input_hash(raw_text),
            intent,
            confidence,
            action_type,
            target_service,
            result_status,
            idempotency_key_val,
            json.dumps({"error": error}) if error else None,
        ),
    )
    connection.commit()


def _already_dispatched(connection: Any, ikey: str) -> bool:
    row = connection.execute(
        "SELECT id FROM dispatch_log WHERE idempotency_key = ? AND result_status = 'ok' LIMIT 1",
        (ikey,),
    ).fetchone()
    return row is not None


def dispatch_text(
    raw_text: str,
    *,
    source: str = "cli",
    user_id: str = "cli",
    db_path: str | None = None,
) -> DispatchResult:
    from src.confirmations.service import ConfirmationService
    from src.energy.service import EnergyService
    from src.habits.service import HabitService

    connection = init_db(db_path)
    today = _berlin_date()

    intake = classify_intent(raw_text)
    intent = intake.intent
    confidence = intake.confidence
    entities = intake.entities

    open_confirmations = ConfirmationService.list_pending(user_id, connection=connection)
    if open_confirmations and intent not in ("confirm_response", "habit_relapse", "habit_recovery", "habit_failure"):
        if confidence < CONFIDENCE_MEDIUM or intake.requires_confirmation:
            resolved = ConfirmationService.resolve_with_text(
                open_confirmations[0]["id"], raw_text, connection=connection
            )
            merged_entities = {**json.loads(open_confirmations[0].get("parsed_entities_json") or "{}"), **entities}
            original_intent = open_confirmations[0]["parsed_intent"]
            intake_override = intake.__class__(
                intent=original_intent,
                confidence=0.92,
                entities=merged_entities,
                requires_confirmation=False,
                confirmation_question=None,
                ambiguity=None,
                raw_input=raw_text,
                normalized_input=intake.normalized_input,
                matched_keywords=intake.matched_keywords,
            )
            result = _dispatch_intake(
                intake_override,
                source=source,
                user_id=user_id,
                today=today,
                connection=connection,
                action_type_override=ACTION_CONFIRMATION_RESOLVE,
            )
            _write_dispatch_log(
                connection,
                source=source,
                raw_text=raw_text,
                intent=original_intent,
                confidence=0.92,
                action_type=ACTION_CONFIRMATION_RESOLVE,
                target_service=result.extra.get("target_service"),
                result_status=result.status,
                idempotency_key_val=None,
                error=result.error,
            )
            connection.close()
            return result

    result = _dispatch_intake(
        intake,
        source=source,
        user_id=user_id,
        today=today,
        connection=connection,
        action_type_override=None,
    )
    _write_dispatch_log(
        connection,
        source=source,
        raw_text=raw_text,
        intent=intent,
        confidence=confidence,
        action_type=result.action_type,
        target_service=result.extra.get("target_service"),
        result_status=result.status,
        idempotency_key_val=result.extra.get("idempotency_key"),
        error=result.error,
    )
    connection.close()
    return result


def _dispatch_intake(
    intake: Any,
    *,
    source: str,
    user_id: str,
    today: str,
    connection: Any,
    action_type_override: str | None,
) -> DispatchResult:
    from src.confirmations.service import ConfirmationService
    from src.energy.service import EnergyService
    from src.habits.service import HabitService

    intent = intake.intent
    confidence = intake.confidence
    entities = intake.entities

    if intent == "unknown" or confidence < CONFIDENCE_MEDIUM:
        if intent == "unknown" or intake.requires_confirmation:
            conf = ConfirmationService.create(intake, user_id=user_id, source=source, connection=connection)
            question = intake.confirmation_question or "Was meinst du genau?"
            return DispatchResult(
                status="pending",
                action_type=ACTION_PENDING_CONFIRMATION,
                intent=intent,
                confidence=confidence,
                response_text=question,
                response_markdown=f"**Rückfrage:** {question}",
                confirmation_id=conf["id"],
                extra={"target_service": "ConfirmationService"},
            )
        return DispatchResult(
            status="skipped",
            action_type=ACTION_NOOP,
            intent=intent,
            confidence=confidence,
            response_text="Ich verstehe das nicht eindeutig. Meinst du Habit, Check-in oder etwas anderes?",
            response_markdown="Eingabe nicht erkannt.",
            extra={"target_service": None},
        )

    if intake.requires_confirmation and confidence < 0.85:
        conf = ConfirmationService.create(intake, user_id=user_id, source=source, connection=connection)
        question = intake.confirmation_question or "Bitte bestätige deine Eingabe."
        return DispatchResult(
            status="pending",
            action_type=ACTION_PENDING_CONFIRMATION,
            intent=intent,
            confidence=confidence,
            response_text=question,
            response_markdown=f"**Rückfrage:** {question}",
            confirmation_id=conf["id"],
            extra={"target_service": "ConfirmationService"},
        )

    from datetime import date as date_cls
    target_date = date_cls.fromisoformat(today)

    if intent == "habit_status":
        service = HabitService(workspace_root=WORKSPACE_ROOT)
        status_payload = service.today(target_date)
        service.close()
        response_markdown = _render_habit_status_markdown(status_payload)
        return DispatchResult(
            status="ok",
            action_type=ACTION_HABIT_STATUS,
            intent=intent,
            confidence=confidence,
            response_text=response_markdown,
            response_markdown=response_markdown,
            extra={
                "target_service": "HabitService",
                "habit_status": {
                    "status": status_payload.get("status"),
                    "business_date_berlin": status_payload.get("business_date_berlin"),
                    "active_count": status_payload.get("active_count", 0),
                    "pending_count": status_payload.get("pending_count", 0),
                },
                "external_writes_performed": False,
            },
        )

    if intent == "habit_log":
        completion = entities.get("completion", "done_full")
        scope = entities.get("scope", "unknown")
        habit_hint = entities.get("habit_hint")

        if scope == "unknown" or (scope == "specific" and not habit_hint):
            conf = ConfirmationService.create(intake, user_id=user_id, source=source, connection=connection)
            question = intake.confirmation_question or "Welche Habit meinst du?"
            return DispatchResult(
                status="pending",
                action_type=ACTION_PENDING_CONFIRMATION,
                intent=intent,
                confidence=confidence,
                response_text=question,
                response_markdown=f"**Rückfrage:** {question}",
                confirmation_id=conf["id"],
                extra={"target_service": "ConfirmationService"},
            )

        service = HabitService(workspace_root=WORKSPACE_ROOT)
        if scope == "all_today":
            results = []
            today_habits = service.today()
            habit_ids = [h["id"] for h in today_habits.get("habits", [])]
            for hid in habit_ids:
                ikey = idempotency_key(ACTION_HABIT_MARK_DONE, hid, target_date)
                if ikey and _already_dispatched(connection, ikey):
                    continue
                if completion == "skipped":
                    service.skip_habit(hid, target_date=target_date)
                else:
                    service.mark_done(hid, target_date=target_date, mode="full" if completion == "done_full" else "partial")
                results.append(hid)
            service.close()
            names = ", ".join(results) if results else "keine"
            return DispatchResult(
                status="ok",
                action_type=ACTION_HABIT_MARK_DONE,
                intent=intent,
                confidence=confidence,
                response_text=f"✓ Habits markiert: {names}.",
                response_markdown=f"**✓ Habits markiert:** {names}",
                extra={"target_service": "HabitService", "habit_ids": results},
            )
        else:
            ikey = idempotency_key(ACTION_HABIT_MARK_DONE, habit_hint, target_date)
            if ikey and _already_dispatched(connection, ikey):
                service.close()
                return DispatchResult(
                    status="skipped",
                    action_type=ACTION_HABIT_MARK_DONE,
                    intent=intent,
                    confidence=confidence,
                    response_text=f"ℹ️ {habit_hint} wurde heute bereits markiert.",
                    response_markdown=f"Already logged: {habit_hint}",
                    habit_id=habit_hint,
                    extra={"target_service": "HabitService", "idempotency_key": ikey},
                )
            if completion == "skipped":
                res = service.skip_habit(habit_hint, target_date=target_date)
            else:
                res = service.mark_done(habit_hint, target_date=target_date, mode="full" if completion == "done_full" else "partial")
            service.close()
            if res.get("status") == "not_found":
                return DispatchResult(
                    status="error",
                    action_type=ACTION_HABIT_MARK_DONE,
                    intent=intent,
                    confidence=confidence,
                    response_text=f"Habit '{habit_hint}' nicht gefunden.",
                    response_markdown=f"Habit not found: {habit_hint}",
                    habit_id=habit_hint,
                    error=f"habit_not_found:{habit_hint}",
                    extra={"target_service": "HabitService"},
                )
            display = res.get("habit", {}).get("name", habit_hint)
            verb = "erledigt" if completion == "done_full" else ("übersprungen" if completion == "skipped" else "teilweise erledigt")
            return DispatchResult(
                status="ok",
                action_type=ACTION_HABIT_MARK_DONE if completion != "skipped" else ACTION_HABIT_SKIP,
                intent=intent,
                confidence=confidence,
                response_text=f"✓ {display} {verb}.",
                response_markdown=f"**✓ {display}** {verb}",
                habit_id=res.get("habit", {}).get("id", habit_hint),
                extra={"target_service": "HabitService", "idempotency_key": ikey},
            )

    if intent == "habit_relapse":
        habit_hint = entities.get("habit_hint")
        if not habit_hint:
            conf = ConfirmationService.create(intake, user_id=user_id, source=source, connection=connection)
            return DispatchResult(
                status="pending",
                action_type=ACTION_PENDING_CONFIRMATION,
                intent=intent,
                confidence=confidence,
                response_text="Bei welcher Habit hattest du den Rückfall?",
                response_markdown="**Rückfrage:** Bei welcher Habit hattest du den Rückfall?",
                confirmation_id=conf["id"],
                extra={"target_service": "ConfirmationService"},
            )
        service = HabitService(workspace_root=WORKSPACE_ROOT)
        res = service.log_relapse(
            habit_hint,
            trigger=entities.get("trigger"),
            replacement=entities.get("replacement"),
            severity=entities.get("severity", "moderate"),
            target_date=target_date,
        )
        service.close()
        if res.get("status") in ("not_found", "config_missing"):
            return DispatchResult(
                status="error",
                action_type=ACTION_HABIT_RELAPSE,
                intent=intent,
                confidence=confidence,
                response_text=f"Konnte Rückfall nicht speichern: {res.get('status')}",
                response_markdown=f"Error: {res.get('status')}",
                habit_id=habit_hint,
                error=res.get("status"),
                extra={"target_service": "HabitService"},
            )
        return DispatchResult(
            status="ok",
            action_type=ACTION_HABIT_RELAPSE,
            intent=intent,
            confidence=confidence,
            response_text=f"📝 Rückfall für '{habit_hint}' gespeichert.",
            response_markdown=f"**📝 Rückfall gespeichert:** {habit_hint}",
            habit_id=habit_hint,
            extra={"target_service": "HabitService"},
        )

    if intent == "habit_recovery":
        habit_hint = entities.get("habit_hint")
        if not habit_hint:
            conf = ConfirmationService.create(intake, user_id=user_id, source=source, connection=connection)
            return DispatchResult(
                status="pending",
                action_type=ACTION_PENDING_CONFIRMATION,
                intent=intent,
                confidence=confidence,
                response_text="Für welche Habit war das der Recovery-Reset?",
                response_markdown="**Rückfrage:** Für welche Habit war das der Recovery-Reset?",
                confirmation_id=conf["id"],
                extra={"target_service": "ConfirmationService"},
            )
        service = HabitService(workspace_root=WORKSPACE_ROOT)
        res = service.log_recovery(habit_hint, target_date=target_date)
        service.close()
        ikey = idempotency_key(ACTION_HABIT_RECOVERY, habit_hint, target_date)
        return DispatchResult(
            status="ok",
            action_type=ACTION_HABIT_RECOVERY,
            intent=intent,
            confidence=confidence,
            response_text=f"✓ Recovery für '{habit_hint}' gespeichert. Streak geschützt.",
            response_markdown=f"**✓ Recovery:** {habit_hint} — Streak geschützt",
            habit_id=habit_hint,
            extra={"target_service": "HabitService", "idempotency_key": ikey},
        )

    if intent == "habit_failure":
        habit_hint = entities.get("habit_hint")
        if not habit_hint:
            conf = ConfirmationService.create(intake, user_id=user_id, source=source, connection=connection)
            return DispatchResult(
                status="pending",
                action_type=ACTION_PENDING_CONFIRMATION,
                intent=intent,
                confidence=confidence,
                response_text="Welche Habit ist heute ausgefallen?",
                response_markdown="**Rückfrage:** Welche Habit ist heute ausgefallen?",
                confirmation_id=conf["id"],
                extra={"target_service": "ConfirmationService"},
            )
        service = HabitService(workspace_root=WORKSPACE_ROOT)
        failure_mode = entities.get("failure_mode", "unbekannt")
        ikey = idempotency_key(ACTION_HABIT_FAILURE, habit_hint, target_date)
        if ikey and _already_dispatched(connection, ikey):
            service.close()
            return DispatchResult(
                status="skipped",
                action_type=ACTION_HABIT_FAILURE,
                intent=intent,
                confidence=confidence,
                response_text=f"ℹ️ {habit_hint} wurde heute bereits als ausgefallen geloggt.",
                response_markdown=f"Already logged failure: {habit_hint}",
                habit_id=habit_hint,
                extra={"target_service": "HabitService", "idempotency_key": ikey},
            )
        res = service.log_failure_mode(habit_hint, failure_mode=failure_mode, target_date=target_date)
        service.close()
        return DispatchResult(
            status="ok",
            action_type=ACTION_HABIT_FAILURE,
            intent=intent,
            confidence=confidence,
            response_text=f"📝 Ausfall für '{habit_hint}' gespeichert (Grund: {failure_mode}).",
            response_markdown=f"**📝 Ausfall:** {habit_hint} — Grund: {failure_mode}",
            habit_id=habit_hint,
            extra={"target_service": "HabitService", "idempotency_key": ikey},
        )

    if intent == "daily_checkin":
        from src.energy.models import parse_energy_text, EnergyLog
        from src.energy.service import EnergyService

        if entities:
            energy_log = EnergyLog(
                local_date=today,
                energy_level=entities.get("energy_level"),
                sleep_quality=entities.get("sleep_quality"),
                physical_fatigue=entities.get("physical_fatigue"),
                mental_load=entities.get("mental_load"),
                stress=entities.get("stress"),
                motivation=entities.get("motivation"),
                soreness=entities.get("soreness"),
                source=source,
            )
        else:
            energy_log = parse_energy_text(intake.raw_input, source=source)

        if energy_log.energy_level is None and not any([
            energy_log.sleep_quality, energy_log.stress, energy_log.physical_fatigue,
            energy_log.mental_load, energy_log.motivation,
        ]):
            conf = ConfirmationService.create(intake, user_id=user_id, source=source, connection=connection)
            return DispatchResult(
                status="pending",
                action_type=ACTION_PENDING_CONFIRMATION,
                intent=intent,
                confidence=confidence,
                response_text="Kein Wert erkannt. Beispiel: 'energie 7, schlaf 6, stress 4'",
                response_markdown="**Rückfrage:** Bitte gib Werte an, z.B. 'energie 7, schlaf 6'",
                confirmation_id=conf["id"],
                extra={"target_service": "ConfirmationService"},
            )

        result = EnergyService.log(energy_log, connection=connection)
        e = result.get("energy_level", "?")
        s = result.get("stress")
        parts = [f"Energie {e}/10"]
        if s:
            parts.append(f"Stress {s}/10")
        summary = ", ".join(parts)
        return DispatchResult(
            status="ok",
            action_type=ACTION_ENERGY_LOG,
            intent=intent,
            confidence=confidence,
            response_text=f"📊 Check-in gespeichert. {summary}.",
            response_markdown=f"**📊 Energy Check-in:** {summary}",
            energy_log_id=result.get("id"),
            extra={"target_service": "EnergyService"},
        )

    if intent == "task_capture":
        proposal_text = _clean_task_proposal_text(str(entities.get("raw_text") or intake.raw_input or ""))
        response_markdown = (
            f"**Aufgaben-Vorschlag:** {proposal_text}\n"
            "Nicht in Google Tasks angelegt. Für einen echten Write brauche ich eine separate, explizite Freigabe."
        )
        return DispatchResult(
            status="ok",
            action_type=ACTION_TASK_PROPOSAL,
            intent=intent,
            confidence=confidence,
            response_text=response_markdown,
            response_markdown=response_markdown,
            extra={
                "target_service": "TaskProposal",
                "proposal": {"kind": "task", "title": proposal_text},
                "actions": [
                    {
                        "label": f"Aufgabe anlegen: {proposal_text}",
                        "requires_confirmation": True,
                        "write_performed": False,
                    }
                ],
                "external_writes_performed": False,
                "google_tasks_write_performed": False,
                "write_policy": "proposal_only",
            },
        )

    if intent == "calendar_proposal_request":
        proposal_text = _clean_calendar_proposal_text(str(entities.get("raw_text") or intake.raw_input or ""))
        response_markdown = (
            f"**Kalender-Vorschlag:** {proposal_text}\n"
            "Noch nichts eingetragen. Ich kann als nächsten Schritt freie Slots prüfen und danach erst mit expliziter Freigabe handeln."
        )
        return DispatchResult(
            status="ok",
            action_type=ACTION_CALENDAR_PROPOSAL,
            intent=intent,
            confidence=confidence,
            response_text=response_markdown,
            response_markdown=response_markdown,
            extra={
                "target_service": "CalendarProposal",
                "proposal": {"kind": "calendar", "request": proposal_text},
                "actions": [
                    {
                        "label": "Freie Slots prüfen",
                        "requires_confirmation": True,
                        "write_performed": False,
                    }
                ],
                "external_writes_performed": False,
                "calendar_external_writes_performed": False,
                "write_policy": "proposal_only",
            },
        )

    if intent in {"assistant_command", "plan_request", "review_request"}:
        command = entities.get("assistant_command")
        if not command and intent == "plan_request":
            command = "heute"
        if not command and intent == "review_request":
            command = "abend"
        payload = run_assistant_command(str(command or "status"), dry_run=True)
        result_status = "ok" if payload.get("status") in {"success", "warning"} else "error"
        response_markdown = _render_assistant_dispatch_markdown(payload)
        return DispatchResult(
            status=result_status,
            action_type=ACTION_ASSISTANT_RESPONSE,
            intent=intent,
            confidence=confidence,
            response_text=response_markdown,
            response_markdown=response_markdown,
            error=None if result_status == "ok" else "assistant_command_failed",
            extra={
                "target_service": "AssistantService",
                "assistant_command": payload.get("command") or command,
                "assistant": payload,
            },
        )

    return DispatchResult(
        status="skipped",
        action_type=ACTION_NOOP,
        intent=intent,
        confidence=confidence,
        response_text="Das kann ich noch nicht verarbeiten. Versuch: Habit, Check-in oder Ausfall loggen.",
        response_markdown=f"Intent '{intent}' ist in Phase 3 nicht dispatched.",
        extra={"target_service": None},
    )


def _render_habit_status_markdown(status_payload: dict[str, Any]) -> str:
    habits = status_payload.get("habits") or []
    active_count = int(status_payload.get("active_count") or 0)
    pending = [habit for habit in habits if habit.get("pending")]
    finished = [habit for habit in habits if not habit.get("pending")]

    if not habits:
        return "Heute sind keine aktiven Habits konfiguriert."

    lines = [f"**Habit-Status:** {len(pending)} offen von {active_count} aktiven Habits."]
    if pending:
        lines.append("Offen: " + ", ".join(_habit_display_name(habit) for habit in pending[:5]))
    if finished:
        lines.append("Erledigt/abgeschlossen: " + ", ".join(_habit_display_name(habit) for habit in finished[:5]))
    return "\n".join(lines)


def _habit_display_name(habit: dict[str, Any]) -> str:
    return str(habit.get("name") or habit.get("id") or "Habit")


def _clean_task_proposal_text(raw_text: str) -> str:
    cleaned = " ".join(raw_text.strip().split())
    lowered = cleaned.lower()
    prefixes = (
        "merken:",
        "notiere:",
        "todo:",
        "to do:",
        "to-do:",
        "neue aufgabe:",
        "neuer task:",
        "erinnere mich daran",
        "erinner mich daran",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip(" :-")
            break
    return cleaned or "Aufgabe ohne Titel"


def _clean_calendar_proposal_text(raw_text: str) -> str:
    cleaned = " ".join(raw_text.strip().split())
    lowered = cleaned.lower()
    prefixes = (
        "trag in den kalender",
        "trage in den kalender",
        "schreib in kalender",
        "in kalender schreiben",
        "kalender vorschlag:",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip(" :-")
            break
    return cleaned or "Kalenderwunsch ohne Details"


def _render_assistant_dispatch_markdown(payload: dict[str, Any]) -> str:
    summary = str(payload.get("summary_markdown") or "").strip()
    actions = payload.get("actions") or []
    cards = payload.get("cards") or []
    lines: list[str] = []
    if summary:
        lines.append(summary)
    if actions:
        first = actions[0]
        label = first.get("label")
        reason = first.get("reason")
        if label:
            lines.append("")
            lines.append(f"Jetzt: {label}")
        if reason:
            lines.append(f"Warum: {reason}")
    if cards:
        blockers = next((card for card in cards if card.get("title") == "Blocker"), None)
        if blockers and blockers.get("items"):
            lines.append("")
            lines.append("Offen:")
            for item in blockers["items"][:3]:
                lines.append(f"- {item}")
    return "\n".join(lines).strip() or "EOS hat gerade keine sichtbare Antwort erzeugt."
