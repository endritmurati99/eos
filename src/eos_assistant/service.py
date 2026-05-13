from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable

from src.audits import audit_cron, audit_models, audit_vault
from src.database.models import init_db
from src.energy import EnergyService
from src.eos_calendar_intelligence import (
    CalendarEventInput,
    detect_calendar_conflicts,
    suggest_prep_windows,
)
from src.eos_mail.auth_preflight import run_gmail_auth_preflight
from src.eos_mail.digest import digest_payload
from src.eos_mail.gmail_client import GogGmailReadOnlyClient
from src.eos_mail.ingestion import query_for_today, run_shadow_ingestion
from src.eos_mail.repository import InMemoryMailShadowRepository
from src.eos_mail_actions import MailActionInput, build_task_proposals
from src.eos_notifications import should_notify
from src.gateways.google_tasks import CANONICAL_LISTS, TaskGateway
from src.habits import HabitService
from src.jobs.daily_capacity import run_daily_capacity
from src.jobs.evening_reset import BERLIN, _load_calendar_events
from src.runtime import WORKSPACE_ROOT

try:
    from scripts.eos_db_doctor import run_doctor as run_db_doctor
except Exception:  # pragma: no cover - import fallback for packaged contexts.
    run_db_doctor = None  # type: ignore[assignment]


ASSISTANT_COMMANDS = ("home", "status", "heute", "jetzt", "abend", "mail")
COMMAND_ALIASES = {
    "eos": "home",
    "start": "home",
    "hilfe": "home",
    "help": "home",
    "today": "heute",
    "now": "jetzt",
    "evening": "abend",
    "emails": "mail",
    "inbox": "mail",
    "health": "status",
}


def normalize_assistant_command(command: str) -> str:
    normalized = (command or "").strip().lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    if normalized.startswith("/"):
        normalized = normalized[1:].split()[0].split("@", 1)[0]
    normalized = COMMAND_ALIASES.get(normalized, normalized)
    if normalized not in ASSISTANT_COMMANDS:
        return "status"
    return normalized


def run_assistant_command(
    command: str,
    *,
    target_date: date | None = None,
    dry_run: bool = True,
    max_results: int = 20,
    workspace_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(workspace_root) if workspace_root is not None else WORKSPACE_ROOT
    normalized = normalize_assistant_command(command)
    if normalized == "home":
        return build_home(target_date=target_date, dry_run=dry_run, max_results=max_results, workspace_root=root)
    if normalized == "status":
        return build_status(workspace_root=root)
    if normalized == "heute":
        return build_heute(target_date=target_date, dry_run=dry_run, workspace_root=root)
    if normalized == "jetzt":
        return build_jetzt(target_date=target_date, dry_run=dry_run, workspace_root=root)
    if normalized == "abend":
        return build_abend(target_date=target_date, dry_run=dry_run, workspace_root=root)
    if normalized == "mail":
        return build_mail(target_date=target_date, max_results=max_results)
    return _response(
        command=normalized,
        status="failed",
        mode="degraded",
        summary_markdown="EOS kennt diesen Assistant-Befehl nicht.",
        cards=[],
        actions=[],
        source_status={},
    )


def build_home(
    *,
    target_date: date | None = None,
    dry_run: bool = True,
    max_results: int = 0,
    workspace_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    status_payload = build_status(workspace_root=workspace_root)
    today_payload = build_heute(target_date=target_date, dry_run=dry_run, workspace_root=workspace_root)
    mail_payload = build_mail(target_date=target_date, max_results=max_results)
    primary_action = (today_payload.get("actions") or [_action("Kurz sortieren", False, "Keine sichere Aktion aus Live-Daten ableitbar.")])[0]
    today_sources = today_payload.get("source_status", {})
    status_sources = status_payload.get("source_status", {})
    mail_sources = mail_payload.get("source_status", {})
    blocker_lines = _home_blockers(status_sources, mail_sources)
    status = "success" if (
        status_payload.get("status") == "success"
        and today_payload.get("status") == "success"
        and mail_payload.get("status") == "success"
    ) else "warning"
    cards = [
        _card("Status", status_payload.get("status", "warning"), [
            f"Modus: {status_payload.get('mode')}",
            f"Blocker: {len(blocker_lines)}",
        ]),
        _card("Heute", today_payload.get("status", "warning"), [
            str(today_payload.get("summary_markdown") or "Heute ist noch nicht verfuegbar."),
        ]),
        _card("Jetzt", today_payload.get("status", "warning"), [
            primary_action["label"],
            primary_action["reason"],
        ]),
        _card("Habits & Mail", mail_payload.get("status", "warning"), [
            f"Offene Habits: {today_sources.get('habits', {}).get('pending_count', 0)}",
            "Mail: read-only",
            f"Gmail Live-Vertrag: {mail_sources.get('mail', {}).get('live_contract_verified', False)}",
        ]),
        _card("Blocker", "success" if not blocker_lines else "warning", blocker_lines or ["Keine harten Blocker aus Status erkannt."]),
    ]
    summary = (
        "EOS Home\n\n"
        f"Jetzt: {primary_action['label']}\n"
        f"Status: {status_payload.get('mode', 'unknown')}\n"
        f"Offene Habits: {today_sources.get('habits', {}).get('pending_count', 0)}\n"
        "Mail: read-only"
    )
    return _response(
        command="home",
        status=status,
        mode="live" if status == "success" else "degraded",
        summary_markdown=summary,
        cards=cards,
        actions=[primary_action],
        source_status={
            "status": status_sources,
            "today": today_sources,
            "mail": mail_sources.get("mail", {}),
        },
        contains_private_user_data=True,
        gmail_write_actions_added=False,
    )


def build_status(*, workspace_root: Path = WORKSPACE_ROOT) -> dict[str, Any]:
    checks = _collect_status_checks(workspace_root=workspace_root)
    degraded = [name for name, check in checks.items() if check.get("status") != "success"]
    status = "success" if not degraded else "warning"
    mode = "live" if not degraded else "degraded"
    headline = "EOS ist live nutzbar." if not degraded else "EOS ist nutzbar, aber nicht komplett sauber."
    details = ", ".join(degraded) if degraded else "alle Kernquellen gruen"
    cards = [
        _card("Quellen", status, [
            f"Kalender: {checks['calendar'].get('status')}",
            f"Tasks: {checks['tasks'].get('status')} ({checks['tasks'].get('open_task_count', 0)} offen)",
            f"Habits: {checks['habits'].get('status')}",
        ]),
        _card("Betrieb", status, [
            f"Cron: {checks['cron'].get('status')}",
            f"Modelle: {checks['models'].get('status')}",
            f"DB: {checks['db'].get('status')}",
            f"Vault: {checks['vault'].get('status')}",
        ]),
        _card("Mail", checks["mail"].get("status", "warning"), [
            "Gmail bleibt read-only.",
            f"Live-Vertrag verifiziert: {checks['mail'].get('live_contract_verified', False)}",
        ]),
    ]
    actions = []
    if checks["vault"].get("status") != "success":
        actions.append(_action("Vault-Struktur vervollstaendigen", True, "Vault ist noch nicht als Produktionsspeicher bereit."))
    if checks["cron"].get("issue_count", 0):
        actions.append(_action("Cron-Warnungen pruefen", True, "Mindestens ein geplanter Job ist nicht sauber konfiguriert."))
    if checks["db"].get("status") not in {"success", "warning"}:
        actions.append(_action("DB-Rechte pruefen", True, "SQLite ist fuer den Zielnutzer nicht eindeutig schreibbar."))
    return _response(
        command="status",
        status=status,
        mode=mode,
        summary_markdown=f"{headline}\n\nDegraded: {details}.",
        cards=cards,
        actions=actions,
        source_status=checks,
    )


def build_heute(
    *,
    target_date: date | None = None,
    dry_run: bool = True,
    workspace_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    day = target_date or datetime.now(BERLIN).date()
    daily = _safe_call(
        "daily_capacity",
        lambda: run_daily_capacity(day, dry_run=dry_run, workspace_root=workspace_root),
    )
    if daily["status"] == "failed":
        return _response(
            command="heute",
            status="warning",
            mode="degraded",
            summary_markdown="Heute kann nicht voll geplant werden, weil die Tagesplanung fehlgeschlagen ist.",
            cards=[_card("Tagesplanung", "failed", [daily.get("error") or "unbekannter Fehler"])],
            actions=[_action("Health prüfen", False, "Erst die Datenquellen stabilisieren.")],
            source_status={"daily_capacity": _source_from_result(daily)},
        )

    calendar = _calendar_intelligence_for_date(day, workspace_root=workspace_root)
    energy = _energy_today()
    top_tasks = daily.get("top_tasks") or []
    ranked_tasks = daily.get("ranked_tasks") or []
    visible_tasks = top_tasks or ranked_tasks[:3]
    habit_status = daily.get("habit_status") or {}
    pending_habits = [habit for habit in habit_status.get("habits", []) if habit.get("pending")]
    actions = _actions_for_today(visible_tasks, pending_habits, daily, calendar)
    status = "success" if daily.get("status") in {"green", "success"} else "warning"
    mode = "live" if daily.get("calendar_read_status") == "success" and daily.get("task_read_status") == "success" else "degraded"
    summary = (
        f"Heute ({day.isoformat()}): Kalender {daily.get('calendar_read_status')}, "
        f"Tasks {daily.get('task_read_status')}, {len(pending_habits)} Habit(s) offen."
    )
    cards = [
        _card("Fokus", status, [daily.get("recommendation") or "Keine Empfehlung verfuegbar."]),
        _card("Top-Aktionen", "success" if actions else "warning", [action["label"] for action in actions[:3]] or ["Erst Aufgaben triagieren."]),
        _card("Kalender-Intelligenz", calendar.get("status", "warning"), calendar.get("lines", [])),
        _card("Energie", "success" if energy else "warning", [_energy_line(energy)]),
    ]
    return _response(
        command="heute",
        status=status,
        mode=mode,
        summary_markdown=summary,
        cards=cards,
        actions=actions,
        source_status={
            "calendar": {"status": daily.get("calendar_read_status"), "intelligence": calendar.get("status")},
            "tasks": {"status": daily.get("task_read_status"), "visible_task_count": len(visible_tasks)},
            "habits": {"status": habit_status.get("status", "unknown"), "pending_count": len(pending_habits)},
            "energy": {"status": "success" if energy else "no_data"},
        },
        contains_private_user_data=True,
    )


def build_jetzt(
    *,
    target_date: date | None = None,
    dry_run: bool = True,
    workspace_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    today = build_heute(target_date=target_date, dry_run=dry_run, workspace_root=workspace_root)
    primary = (today.get("actions") or [_action("Kurz sortieren", False, "Keine sichere Aktion aus Live-Daten ableitbar.")])[0]
    status = "success" if today.get("status") == "success" else "warning"
    return _response(
        command="jetzt",
        status=status,
        mode=today.get("mode", "degraded"),
        summary_markdown=f"Jetzt: {primary['label']}\n\nWarum: {primary['reason']}",
        cards=[_card("Naechste Aktion", status, [primary["label"], primary["reason"]])],
        actions=[primary],
        source_status=today.get("source_status", {}),
        contains_private_user_data=True,
    )


def build_abend(
    *,
    target_date: date | None = None,
    dry_run: bool = True,
    workspace_root: Path = WORKSPACE_ROOT,
) -> dict[str, Any]:
    today = target_date or datetime.now(BERLIN).date()
    tomorrow = today + timedelta(days=1)
    tomorrow_plan = _safe_call(
        "tomorrow_capacity",
        lambda: run_daily_capacity(tomorrow, dry_run=dry_run, workspace_root=workspace_root),
    )
    habit_status = _habit_today(today, workspace_root=workspace_root)
    pending = [habit for habit in habit_status.get("habits", []) if habit.get("pending")]
    energy = _energy_today()
    notification = should_notify("evening_review", "normal", 0, {"active": False}, "normal")
    calendar = _calendar_intelligence_for_date(tomorrow, workspace_root=workspace_root)
    actions = []
    if pending:
        actions.append(_action("Offene Habits beantworten", True, f"{len(pending)} Habit(s) sind noch offen."))
    tomorrow_tasks = (tomorrow_plan.get("top_tasks") or tomorrow_plan.get("ranked_tasks") or [])[:3]
    if tomorrow_tasks:
        actions.append(_action(f"Morgen zuerst: {tomorrow_tasks[0].get('title')}", False, "Beste sichtbare Aufgabe fuer morgen."))
    if not actions:
        actions.append(_action("Kurzer Tagesabschluss", False, "Keine harte offene Aktion erkannt."))
    status = "success" if tomorrow_plan.get("status") in {"green", "success", "yellow"} else "warning"
    cards = [
        _card("Heute abschliessen", "success" if not pending else "warning", [f"Offen: {len(pending)} Habit(s)"]),
        _card("Morgen vorbereiten", status, [tomorrow_plan.get("recommendation") or "Keine Morgenempfehlung verfuegbar."]),
        _card("Kalender morgen", calendar.get("status", "warning"), calendar.get("lines", [])),
        _card("Push-Budget", "success", [f"Abendreview erlaubt: {notification['notification_allowed']} ({notification['reason']})"]),
        _card("Energie", "success" if energy else "warning", [_energy_line(energy)]),
    ]
    return _response(
        command="abend",
        status=status,
        mode="live" if tomorrow_plan.get("calendar_read_status") == "success" and tomorrow_plan.get("task_read_status") == "success" else "degraded",
        summary_markdown=f"Abend: {len(pending)} Habit(s) offen. Morgen ist vorbereitet mit Status {tomorrow_plan.get('status', 'unknown')}.",
        cards=cards,
        actions=actions,
        source_status={
            "tomorrow_calendar": {"status": tomorrow_plan.get("calendar_read_status"), "intelligence": calendar.get("status")},
            "tomorrow_tasks": {"status": tomorrow_plan.get("task_read_status"), "visible_task_count": len(tomorrow_tasks)},
            "habits": {"status": habit_status.get("status", "unknown"), "pending_count": len(pending)},
            "notifications": {"status": "success", "reason": notification["reason"]},
        },
        contains_private_user_data=True,
    )


def build_mail(
    *,
    target_date: date | None = None,
    max_results: int = 20,
) -> dict[str, Any]:
    day = target_date or datetime.now(BERLIN).date()
    auth = _safe_call("gmail_auth", run_gmail_auth_preflight)
    cards = [
        _card("Gmail Auth", auth.get("status", "warning"), [
            "Read-only bleibt erzwungen.",
            f"Write-Scopes erkannt: {auth.get('write_scopes_detected', False)}",
            f"Live-Vertrag verifiziert: {auth.get('live_contract_verified', False)}",
        ])
    ]
    actions = []
    digest_counts: dict[str, int] = {}
    proposal_count = 0
    audit_status = "skipped"
    if max_results > 0 and auth.get("provider_command_available") and auth.get("account_configured"):
        repository = InMemoryMailShadowRepository()
        client = GogGmailReadOnlyClient()
        audit = _safe_call(
            "gmail_digest",
            lambda: run_shadow_ingestion(
                client=client,
                query=query_for_today(day),
                max_results=max_results,
                dry_run=True,
                repository=repository,
            ),
        )
        audit_status = audit.get("status", "failed")
        if audit_status != "failed":
            digest = digest_payload(repository.messages)
            digest_counts = dict(digest.get("counts", {}))
            proposal_count = _count_mail_task_proposals(repository.messages)
            cards.append(_card("Digest", audit_status, [
                f"Gescannte Nachrichten: {digest.get('total_messages_scanned', 0)}",
                f"Wichtig: {digest_counts.get('likely_important', 0)}",
                f"Review: {digest_counts.get('review_needed', 0)}",
                f"Task-Vorschlaege: {proposal_count}",
            ]))
            if proposal_count:
                actions.append(_action("Mail-Task-Vorschlaege pruefen", True, f"{proposal_count} Vorschlag/Vorschlaege, keine automatische Anlage."))
        else:
            cards.append(_card("Digest", "warning", [audit.get("error") or "Gmail-Digest nicht verfuegbar."]))
    else:
        cards.append(_card("Digest", "warning", ["Gmail-Digest uebersprungen, weil Auth/Provider nicht bereit ist."]))
    status = "success" if auth.get("status") == "success" and audit_status in {"success", "skipped"} else "warning"
    return _response(
        command="mail",
        status=status,
        mode="read_only",
        summary_markdown="Mail ist im Read-only-Modus. EOS hat keine Gmail-Schreibaktion ausgefuehrt.",
        cards=cards,
        actions=actions,
        source_status={
            "mail": {
                "status": auth.get("status", "warning"),
                "audit_status": audit_status,
                "live_contract_verified": auth.get("live_contract_verified", False),
                "live_contract_unverified_items": auth.get("live_contract_unverified_items", []),
                "digest_counts": digest_counts,
                "task_proposal_count": proposal_count,
            }
        },
        contains_private_user_data=False,
        gmail_write_actions_added=False,
    )


def _collect_status_checks(*, workspace_root: Path) -> dict[str, dict[str, Any]]:
    gateway = TaskGateway()
    task_auth = _safe_call("tasks_auth", gateway.get_auth_status)
    task_structure = _safe_call("tasks_structure", gateway.list_structure)
    task_read = _safe_call("tasks_read", gateway.readOpenTasks)
    calendar = _calendar_health(gateway, workspace_root=workspace_root)
    vault = _safe_call("vault", audit_vault)
    cron = _safe_call("cron", audit_cron)
    models = _safe_call("models", audit_models)
    habits = _habit_health(workspace_root=workspace_root)
    mail = _safe_call("mail_auth", run_gmail_auth_preflight)
    db = _db_status(workspace_root=workspace_root)
    task_status = "success" if (
        task_auth.get("status") == "success"
        and task_structure.get("status") == "success"
        and task_read.get("task_read_status") == "success"
    ) else "warning"
    return {
        "calendar": calendar,
        "tasks": {
            "status": task_status,
            "auth_status": task_auth.get("status"),
            "structure_status": task_structure.get("status"),
            "read_status": task_read.get("task_read_status"),
            "open_task_count": task_read.get("open_task_count", 0),
        },
        "habits": habits,
        "vault": {
            "status": vault.get("status", "warning"),
            "missing_dir_count": len(vault.get("missing_dirs", [])),
        },
        "cron": {
            "status": cron.get("status", "warning"),
            "enabled_count": cron.get("enabled_count", 0),
            "issue_count": len(cron.get("issues", [])),
            "issue_codes": [issue.get("code") for issue in cron.get("issues", [])],
        },
        "models": {
            "status": models.get("status", "warning"),
            "issue_count": len(models.get("issues", [])),
        },
        "mail": {
            "status": mail.get("status", "warning"),
            "readonly_scope_configured": mail.get("readonly_scope_configured"),
            "write_scopes_detected": mail.get("write_scopes_detected", False),
            "live_contract_verified": mail.get("live_contract_verified", False),
        },
        "db": db,
    }


def _calendar_health(gateway: TaskGateway, *, workspace_root: Path) -> dict[str, Any]:
    result = _safe_call(
        "calendar",
        lambda: _load_calendar_events(
            gateway=gateway,
            workspace_root=workspace_root,
            target_date_berlin=datetime.now(BERLIN).date(),
            dry_run=False,
            allow_stub_calendar=False,
        ),
    )
    return {
        "status": "success" if result.get("calendar_read_status") == "success" else "warning",
        "read_status": result.get("calendar_read_status", result.get("status")),
        "source": result.get("source"),
        "hard_event_count": len(result.get("hard_events", [])),
    }


def _db_status(*, workspace_root: Path) -> dict[str, Any]:
    if run_db_doctor is None:
        return {"status": "warning", "issue_codes": ["db_doctor_unavailable"], "sqlite_write_probe": "not_available"}
    result = _safe_call(
        "db_doctor",
        lambda: run_db_doctor(workspace_root=workspace_root, sqlite_probe=False),
    )
    return {
        "status": result.get("status", "warning"),
        "issue_codes": [issue.get("code") for issue in result.get("issues", [])],
        "sqlite_write_probe": result.get("sqlite_write_probe", "skipped"),
        "db_writable": result.get("db_writable"),
        "parent_writable": result.get("parent_writable"),
    }


def _habit_health(*, workspace_root: Path) -> dict[str, Any]:
    service = HabitService(workspace_root=workspace_root)
    try:
        return service.health()
    finally:
        service.close()


def _habit_today(day: date, *, workspace_root: Path) -> dict[str, Any]:
    service = HabitService(workspace_root=workspace_root)
    try:
        return service.today(day)
    finally:
        service.close()


def _energy_today() -> dict[str, Any] | None:
    connection = init_db()
    try:
        return EnergyService.today(connection=connection)
    finally:
        connection.close()


def _calendar_intelligence_for_date(day: date, *, workspace_root: Path) -> dict[str, Any]:
    gateway = TaskGateway()
    result = _safe_call(
        "calendar_intelligence",
        lambda: _load_calendar_events(
            gateway=gateway,
            workspace_root=workspace_root,
            target_date_berlin=day,
            dry_run=True,
            allow_stub_calendar=False,
        ),
    )
    events = _calendar_inputs_from_events(day, result.get("hard_events", []))
    if not events:
        return {
            "status": "warning" if result.get("calendar_read_status") != "success" else "success",
            "lines": ["Keine auswertbaren Kalenderzeiten fuer Konflikte/Prep-Fenster."],
        }
    conflicts = detect_calendar_conflicts(events)
    prep = suggest_prep_windows(events)
    lines = [
        f"Risiko: {conflicts.risk_level}",
        f"Konflikte: {len(conflicts.issues)}",
        f"Prep-Fenster: {len(prep)}",
    ]
    if conflicts.suggestions:
        lines.append(conflicts.suggestions[0])
    return {"status": "success" if conflicts.risk_level == "low" else "warning", "lines": lines}


def _calendar_inputs_from_events(day: date, events: list[dict[str, Any]]) -> list[CalendarEventInput]:
    result: list[CalendarEventInput] = []
    for index, event in enumerate(events):
        start_display = str(event.get("start_display") or "")
        end_display = str(event.get("end_display") or "")
        if not _looks_like_time(start_display) or not _looks_like_time(end_display):
            continue
        start_dt = datetime.combine(day, time.fromisoformat(start_display), tzinfo=BERLIN)
        end_dt = datetime.combine(day, time.fromisoformat(end_display), tzinfo=BERLIN)
        if end_dt <= start_dt:
            continue
        result.append(
            CalendarEventInput(
                event_id=str(event.get("id") or f"calendar-{day.isoformat()}-{index}"),
                title=str(event.get("title") or "Termin"),
                start=start_dt.isoformat(),
                end=end_dt.isoformat(),
                location=None,
                description=None,
                attendees=[],
                calendar_role=None,
            )
        )
    return result


def _actions_for_today(
    tasks: list[dict[str, Any]],
    pending_habits: list[dict[str, Any]],
    daily: dict[str, Any],
    calendar: dict[str, Any],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if tasks:
        first = tasks[0]
        actions.append(_action(f"Starte: {first.get('title')}", False, "Beste sichtbare Aufgabe aus Tasks/Planung."))
    if pending_habits:
        habit = pending_habits[0]
        actions.append(_action(f"Habit offen: {habit.get('name')}", True, "Schreib erledigt, partial oder skip."))
    if daily.get("triage_required"):
        actions.append(_action("Tasks triagieren", False, "Prioritaeten, Energie und Schaetzungen fehlen noch."))
    if calendar.get("status") == "warning":
        actions.append(_action("Kalenderpuffer pruefen", False, "Calendar Intelligence sieht moegliche Engstellen."))
    if not actions:
        actions.append(_action("Kurzer Fokusblock", False, "Keine dringende offene Aktion erkannt."))
    return actions


def _home_blockers(status_sources: dict[str, Any], mail_sources: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    db = status_sources.get("db", {})
    vault = status_sources.get("vault", {})
    mail = mail_sources.get("mail", {})
    if db.get("status") not in {"success", "warning"}:
        blockers.append("DB: Schreibbarkeit fuer Runtime-Nutzer pruefen.")
    if vault.get("status") != "success":
        blockers.append("Vault: Struktur/Produktionspfad fehlt noch.")
    if mail and not mail.get("live_contract_verified", False):
        blockers.append("Gmail: read-only bleibt, Live-Vertrag noch unbewiesen.")
    return blockers


def _count_mail_task_proposals(messages: list[Any]) -> int:
    count = 0
    for message in messages:
        mail = MailActionInput(
            message_id=message.message_id,
            thread_id=message.thread_id,
            sender=message.sender or "",
            subject=message.subject or "",
            snippet=message.snippet or "",
            body_excerpt=None,
            categories=list(message.label_ids),
            received_at=message.date,
        )
        count += len(build_task_proposals(mail))
    return count


def _response(
    *,
    command: str,
    status: str,
    mode: str,
    summary_markdown: str,
    cards: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    source_status: dict[str, Any],
    contains_private_user_data: bool = False,
    gmail_write_actions_added: bool = False,
) -> dict[str, Any]:
    return {
        "status": status,
        "command": command,
        "mode": mode,
        "summary_markdown": summary_markdown,
        "cards": cards,
        "actions": actions,
        "source_status": source_status,
        "privacy": {
            "contains_private_user_data": contains_private_user_data,
            "raw_provider_output_included": False,
            "external_writes_performed": False,
            "gmail_write_actions_added": gmail_write_actions_added,
            "requires_approval_for_writes": True,
        },
    }


def _card(title: str, status: str, items: list[str]) -> dict[str, Any]:
    return {"title": title, "status": status, "items": [str(item) for item in items if item is not None]}


def _action(label: str, requires_confirmation: bool, reason: str) -> dict[str, Any]:
    return {
        "label": label,
        "requires_confirmation": requires_confirmation,
        "reason": reason,
    }


def _source_from_result(result: dict[str, Any]) -> dict[str, Any]:
    return {"status": result.get("status", "failed"), "error_class": result.get("error_class")}


def _safe_call(name: str, fn: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - assistant surfaces should degrade instead of crashing.
        return {
            "status": "failed",
            "error_class": type(exc).__name__,
            "error": f"{name} failed: {exc}",
        }


def _energy_line(energy: dict[str, Any] | None) -> str:
    if not energy:
        return "Kein Energy-Check-in fuer heute."
    parts = []
    if energy.get("energy_level") is not None:
        parts.append(f"Energie {energy['energy_level']}/10")
    if energy.get("sleep_quality") is not None:
        parts.append(f"Schlaf {energy['sleep_quality']}/10")
    if energy.get("stress") is not None:
        parts.append(f"Stress {energy['stress']}/10")
    return ", ".join(parts) if parts else "Check-in ohne numerische Werte."


def _looks_like_time(value: str) -> bool:
    if len(value) != 5 or value[2] != ":":
        return False
    try:
        time.fromisoformat(value)
    except ValueError:
        return False
    return True
