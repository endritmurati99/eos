from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.database.models import init_db
from src.dispatch.actions import (
    ACTION_CONFIRMATION_RESOLVE,
    ACTION_ENERGY_LOG,
    ACTION_HABIT_FAILURE,
    ACTION_HABIT_MARK_DONE,
    ACTION_HABIT_RECOVERY,
    ACTION_HABIT_RELAPSE,
    ACTION_HABIT_SKIP,
    ACTION_NOOP,
    ACTION_PENDING_CONFIRMATION,
    INTENT_TO_ACTION,
    idempotency_key,
    input_hash,
)
from src.dispatch.result import DispatchResult
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

    return DispatchResult(
        status="skipped",
        action_type=ACTION_NOOP,
        intent=intent,
        confidence=confidence,
        response_text="Das kann ich noch nicht verarbeiten. Versuch: Habit, Check-in oder Ausfall loggen.",
        response_markdown=f"Intent '{intent}' ist in Phase 3 nicht dispatched.",
        extra={"target_service": None},
    )
