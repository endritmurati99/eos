from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.audits import audit_cron, audit_models, audit_vault
from src.gateways.telegram import send_telegram_message
from src.gateways.google_tasks import TaskGateway
from src.habits import HabitService
from src.intake import classify_intent
from src.jobs.daily_capacity import run_daily_capacity
from src.jobs.evening_reset import BERLIN, _load_calendar_events, mark_evening_reset_delivery
from src.jobs.runner import run_eos_job
from src.jobs.weekly_plan import run_weekly_plan
from src.runtime import WORKSPACE_ROOT, load_env_file
from src.dispatch import dispatch_text
from src.confirmations import ConfirmationService
from src.energy import EnergyService, parse_energy_text
from src.database.models import init_db
from src.eos_mail.digest import digest_payload, render_shadow_digest
from src.eos_mail.gmail_client import GogGmailReadOnlyClient, gmail_scope_guidance
from src.eos_mail.ingestion import query_for_today, query_from_last, run_shadow_ingestion
from src.eos_mail.repository import InMemoryMailShadowRepository


def main(argv: list[str] | None = None) -> int:
    load_env_file()
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "health":
        result = command_health()
    elif args.command == "tasks":
        result = command_tasks(args)
    elif args.command == "habits":
        result = command_habits(args)
    elif args.command == "intake":
        result = command_intake(args)
    elif args.command == "daily-plan":
        result = run_daily_capacity(_parse_date(args.date), dry_run=args.dry_run)
    elif args.command == "weekly-plan":
        result = run_weekly_plan(_parse_date(args.week_start), dry_run=args.dry_run)
    elif args.command == "run-job":
        result = command_run_job(args)
    elif args.command == "dispatch":
        result = command_dispatch(args)
    elif args.command == "confirmations":
        result = command_confirmations(args)
    elif args.command == "energy":
        result = command_energy(args)
    elif args.command == "mail":
        result = command_mail(args)
    elif args.command == "cron-audit":
        result = audit_cron(args.jobs_path)
    elif args.command == "model-audit":
        result = audit_models(jobs_path=args.jobs_path, models_path=args.models_path)
    else:
        parser.error(f"Unknown command: {args.command}")
        return 2

    _print_result(result, json_only=args.json_only)
    return 0 if _is_successful_result(result) else 1


def command_health() -> dict[str, Any]:
    gateway = TaskGateway()
    task_auth = gateway.get_auth_status()
    task_structure = gateway.list_structure()
    task_read = gateway.readOpenTasks()
    vault = audit_vault()
    cron = audit_cron()
    models = audit_models()
    habits = _habit_health()
    calendar = _calendar_health(gateway)

    checks = {
        "calendar": calendar,
        "google_tasks": {
            "status": "success"
            if task_auth["status"] == "success"
            and task_structure["status"] == "success"
            and task_read["task_read_status"] == "success"
            else "warning",
            "auth_status": task_auth["status"],
            "structure_status": task_structure["status"],
            "read_status": task_read["task_read_status"],
            "open_task_count": task_read["open_task_count"],
            "error": task_auth.get("error") or task_structure.get("error"),
        },
        "vault": vault,
        "cron": {
            "status": cron["status"],
            "enabled_count": cron["enabled_count"],
            "issue_count": len(cron["issues"]),
            "issues": cron["issues"],
        },
        "models": {
            "status": models["status"],
            "profiles": models["model_profiles"],
            "issue_count": len(models["issues"]),
            "issues": models["issues"],
        },
        "habits": habits,
    }
    status = "success"
    if any(check.get("status") not in {"success"} for check in checks.values()):
        status = "warning"

    return {
        "status": status,
        "workspace_root": str(WORKSPACE_ROOT),
        "checks": checks,
    }


def command_tasks(args: argparse.Namespace) -> dict[str, Any]:
    gateway = TaskGateway()
    if args.task_command == "read":
        list_names = tuple(args.list_names) if args.list_names else None
        return gateway.readOpenTasks(list_names)
    if args.task_command == "create":
        return gateway.createTask(
            {
                "title": args.title,
                "notes": args.notes,
                "due": args.due,
                "listName": args.list_name,
            }
        )
    if args.task_command == "complete":
        if args.list_name:
            return gateway.completeTask({"taskId": args.ref, "listName": args.list_name})
        return gateway.completeTask(args.ref)
    return {"status": "not_found", "error": f"Unknown tasks command: {args.task_command}"}


def command_habits(args: argparse.Namespace) -> dict[str, Any]:
    service = HabitService()
    try:
        if args.habit_command == "status":
            return service.status(_parse_optional_date(args.date))
        if args.habit_command == "today":
            return service.today(_parse_optional_date(args.date))
        if args.habit_command == "done":
            return service.mark_done(
                args.habit,
                target_date=_parse_optional_date(args.date),
                mode=args.mode,
                source="cli",
                notes=args.notes,
            )
        if args.habit_command == "skip":
            return service.skip_habit(
                args.habit,
                target_date=_parse_optional_date(args.date),
                source="cli",
                notes=args.reason,
            )
        if args.habit_command == "add":
            return service.add_habit(
                name=args.name,
                target_time=args.time,
                frequency=args.frequency,
                habit_type=getattr(args, "habit_type", None),
            )
        if args.habit_command == "pause":
            return service.pause_habit(args.habit, source="cli", notes=args.reason)
        if args.habit_command == "weekly-report":
            return service.weekly_report(_parse_date(args.week_start))
        if args.habit_command == "handle":
            return service.handle_text(args.text, target_date=_parse_optional_date(args.date), source="telegram")
        if args.habit_command == "set-type":
            return service.set_habit_type(args.habit, args.type)
        if args.habit_command == "failure":
            return service.log_failure_mode(
                args.habit,
                failure_mode=args.mode,
                target_date=_parse_optional_date(args.date),
                source="cli",
                notes=args.notes,
            )
        if args.habit_command == "relapse":
            return service.log_relapse(
                args.habit,
                trigger=args.trigger,
                replacement=args.replacement,
                severity=args.severity,
                target_date=_parse_optional_date(args.date),
                source="cli",
                notes=args.notes,
            )
        if args.habit_command == "recovery":
            return service.log_recovery(
                args.habit,
                target_date=_parse_optional_date(args.date),
                source="cli",
                notes=args.notes,
            )
        if args.habit_command == "patterns":
            return service.week_patterns(_parse_optional_date(args.reference_date))
        return {"status": "not_found", "error": f"Unknown habits command: {args.habit_command}"}
    finally:
        service.close()


def command_intake(args: argparse.Namespace) -> dict[str, Any]:
    if args.intake_command == "parse":
        result = classify_intent(args.text)
        payload = result.to_dict()
        payload["status"] = "success"
        return payload
    return {"status": "not_found", "error": f"Unknown intake command: {args.intake_command}"}


def command_dispatch(args: argparse.Namespace) -> dict[str, Any]:
    if args.dispatch_command == "handle":
        result = dispatch_text(
            args.text,
            source=getattr(args, "source", "cli"),
            user_id=getattr(args, "user_id", "cli"),
        )
        return result.to_dict()
    if args.dispatch_command == "log":
        connection = init_db()
        limit = getattr(args, "limit", 20)
        rows = connection.execute(
            "SELECT * FROM dispatch_log ORDER BY timestamp_utc DESC LIMIT ?", (limit,)
        ).fetchall()
        connection.close()
        return {"status": "success", "entries": [dict(r) for r in rows]}
    return {"status": "not_found", "error": f"Unknown dispatch command: {args.dispatch_command}"}


def command_confirmations(args: argparse.Namespace) -> dict[str, Any]:
    connection = init_db()
    try:
        if args.confirmation_command == "list":
            user_id = getattr(args, "user_id", "cli")
            rows = ConfirmationService.list_pending(user_id, connection=connection)
            return {"status": "success", "confirmations": rows}
        if args.confirmation_command == "resolve":
            result = ConfirmationService.resolve_with_text(
                args.confirmation_id, args.response_text, connection=connection
            )
            return {"status": "success", "confirmation": result}
        if args.confirmation_command == "expire":
            count = ConfirmationService.expire_all(connection=connection)
            return {"status": "success", "expired_count": count}
    finally:
        connection.close()
    return {"status": "not_found", "error": f"Unknown confirmations command: {args.confirmation_command}"}


def command_energy(args: argparse.Namespace) -> dict[str, Any]:
    connection = init_db()
    try:
        if args.energy_command == "log":
            from src.energy.models import parse_energy_text
            energy_log = parse_energy_text(args.text, source="cli")
            if args.date:
                energy_log.local_date = args.date  # type: ignore[misc]
            if energy_log.energy_level is None and not any([
                energy_log.sleep_quality, energy_log.stress, energy_log.physical_fatigue,
            ]):
                return {"status": "error", "error": "Kein Wert erkannt. Beispiel: 'energie 7, schlaf 6, stress 4'"}
            result = EnergyService.log(energy_log, connection=connection)
            return {"status": "success", **result}
        if args.energy_command == "today":
            result = EnergyService.today(connection=connection)
            if result is None:
                return {"status": "no_data", "message": "Kein Check-in für heute gefunden."}
            return {"status": "success", **result}
    finally:
        connection.close()
    return {"status": "not_found", "error": f"Unknown energy command: {args.energy_command}"}


def command_mail(args: argparse.Namespace) -> dict[str, Any]:
    if not args.dry_run:
        return {
            "status": "failed",
            "error_class": "write_mode_forbidden",
            "dry_run": args.dry_run,
            "error": "Gmail shadow mode is read-only. Re-run without --no-dry-run.",
            "gmail_write_actions_added": False,
        }

    repository = InMemoryMailShadowRepository()
    client = GogGmailReadOnlyClient()
    max_results = int(args.max_results)
    query = _mail_query(args)
    audit_result = run_shadow_ingestion(
        client=client,
        query=query,
        max_results=max_results,
        dry_run=True,
        repository=repository,
    )
    audit_result["scope_guidance"] = gmail_scope_guidance()
    audit_result["gmail_write_actions_added"] = False

    if args.mail_command == "audit":
        return audit_result

    if args.mail_command == "digest":
        return {
            "status": audit_result["status"],
            "audit_run_id": audit_result["audit_run_id"],
            "started_at": audit_result["started_at"],
            "finished_at": audit_result["finished_at"],
            "dry_run": True,
            "query": query,
            "max_results": max_results,
            "messages_seen": audit_result["messages_seen"],
            "errors": audit_result["errors"],
            "scope_guidance": audit_result["scope_guidance"],
            "gmail_write_actions_added": False,
            "digest": digest_payload(repository.messages),
            "output_markdown": render_shadow_digest(repository.messages),
        }

    return {"status": "not_found", "error": f"Unknown mail command: {args.mail_command}"}


def command_run_job(args: argparse.Namespace) -> dict[str, Any]:
    if args.send and args.dry_run:
        return {
            "status": "failed",
            "job": args.job,
            "dry_run": args.dry_run,
            "delivery_status": "not_attempted",
            "error": "--send cannot be used with --dry-run. Use --no-dry-run --send.",
        }

    result = run_eos_job(
        args.job,
        target_date=_parse_optional_date(args.date),
        week_start=_parse_optional_date(args.week_start),
        dry_run=args.dry_run,
    )
    if args.send:
        result = _send_job_result(result)
    return result


def _send_job_result(result: dict[str, Any]) -> dict[str, Any]:
    if result.get("status") == "skipped":
        result["delivery_status"] = "skipped"
        return result

    status = _result_status(result)
    if status not in {"success", "partial", "green", "yellow"}:
        result["delivery_status"] = "not_attempted"
        result["delivery_result"] = {
            "status": "skipped",
            "reason": "job_status_not_sendable",
        }
        return result

    output = str(result.get("output_markdown") or "").strip()
    if not output:
        result["delivery_status"] = "not_attempted"
        result["delivery_result"] = {
            "status": "skipped",
            "reason": "output_markdown_missing",
        }
        return result

    delivery_result = send_telegram_message(output)
    result["delivery_result"] = delivery_result
    result["delivery_status"] = delivery_result.get("delivery_status", delivery_result.get("status"))

    if result.get("job") == "evening_reset" and result.get("idempotency_key"):
        mark_evening_reset_delivery(
            idempotency_key=str(result["idempotency_key"]),
            sent=delivery_result.get("status") == "success",
            delivery_status=str(result["delivery_status"]),
            error=delivery_result.get("error"),
        )

    if delivery_result.get("status") != "success":
        result["status"] = "failed"
        result["error"] = delivery_result.get("error") or "Telegram delivery failed."
    return result


def _calendar_health(gateway: TaskGateway) -> dict[str, Any]:
    result = _load_calendar_events(
        gateway=gateway,
        workspace_root=WORKSPACE_ROOT,
        target_date_berlin=datetime.now(BERLIN).date(),
        dry_run=False,
        allow_stub_calendar=False,
    )
    return {
        "status": "success" if result["calendar_read_status"] == "success" else "warning",
        "read_status": result["calendar_read_status"],
        "source": result["source"],
        "hard_event_count": len(result.get("hard_events", [])),
        "error": result.get("error"),
    }


def _habit_health() -> dict[str, Any]:
    service = HabitService()
    try:
        return service.health()
    finally:
        service.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python3 -m src.eos_cli")
    parser.add_argument("--json-only", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("health")

    tasks = subparsers.add_parser("tasks")
    task_subparsers = tasks.add_subparsers(dest="task_command", required=True)
    task_read = task_subparsers.add_parser("read")
    task_read.add_argument("--list", dest="list_names", action="append")
    task_create = task_subparsers.add_parser("create")
    task_create.add_argument("title")
    task_create.add_argument("--list-name", default="Inbox")
    task_create.add_argument("--notes")
    task_create.add_argument("--due")
    task_complete = task_subparsers.add_parser("complete")
    task_complete.add_argument("ref")
    task_complete.add_argument("--list-name")

    habits = subparsers.add_parser("habits")
    habit_subparsers = habits.add_subparsers(dest="habit_command", required=True)
    habit_status = habit_subparsers.add_parser("status")
    habit_status.add_argument("--date")
    habit_today = habit_subparsers.add_parser("today")
    habit_today.add_argument("--date")
    habit_done = habit_subparsers.add_parser("done")
    habit_done.add_argument("habit")
    habit_done.add_argument("--date")
    habit_done.add_argument("--mode", choices=("full", "partial", "minimum"), default="full")
    habit_done.add_argument("--notes")
    habit_skip = habit_subparsers.add_parser("skip")
    habit_skip.add_argument("habit")
    habit_skip.add_argument("--date")
    habit_skip.add_argument("--reason")
    habit_add = habit_subparsers.add_parser("add")
    habit_add.add_argument("--name", required=True)
    habit_add.add_argument("--time")
    habit_add.add_argument("--frequency", choices=("daily", "weekly"), default="daily")
    habit_add.add_argument(
        "--type",
        dest="habit_type",
        choices=("build", "reduce", "maintain", "recovery"),
        default=None,
    )
    habit_pause = habit_subparsers.add_parser("pause")
    habit_pause.add_argument("habit")
    habit_pause.add_argument("--reason")
    habit_weekly = habit_subparsers.add_parser("weekly-report")
    habit_weekly.add_argument("--week-start", required=True)
    habit_handle = habit_subparsers.add_parser("handle")
    habit_handle.add_argument("text")
    habit_handle.add_argument("--date")

    habit_set_type = habit_subparsers.add_parser("set-type")
    habit_set_type.add_argument("habit")
    habit_set_type.add_argument("type", choices=("build", "reduce", "maintain", "recovery"))

    habit_failure = habit_subparsers.add_parser("failure")
    habit_failure.add_argument("habit")
    habit_failure.add_argument("--mode", required=True)
    habit_failure.add_argument("--date")
    habit_failure.add_argument("--notes")

    habit_relapse = habit_subparsers.add_parser("relapse")
    habit_relapse.add_argument("habit")
    habit_relapse.add_argument("--trigger")
    habit_relapse.add_argument("--replacement")
    habit_relapse.add_argument(
        "--severity",
        choices=("minor", "moderate", "major"),
        default="moderate",
    )
    habit_relapse.add_argument("--date")
    habit_relapse.add_argument("--notes")

    habit_recovery = habit_subparsers.add_parser("recovery")
    habit_recovery.add_argument("habit")
    habit_recovery.add_argument("--date")
    habit_recovery.add_argument("--notes")

    habit_patterns = habit_subparsers.add_parser("patterns")
    habit_patterns.add_argument("--reference-date", dest="reference_date")

    intake = subparsers.add_parser("intake")
    intake_subparsers = intake.add_subparsers(dest="intake_command", required=True)
    intake_parse = intake_subparsers.add_parser("parse")
    intake_parse.add_argument("text")

    dispatch = subparsers.add_parser("dispatch")
    dispatch_subparsers = dispatch.add_subparsers(dest="dispatch_command", required=True)
    dispatch_handle = dispatch_subparsers.add_parser("handle")
    dispatch_handle.add_argument("text")
    dispatch_handle.add_argument("--user-id", dest="user_id", default="cli")
    dispatch_handle.add_argument("--source", choices=("cli", "telegram"), default="cli")
    dispatch_log_cmd = dispatch_subparsers.add_parser("log")
    dispatch_log_cmd.add_argument("--limit", type=int, default=20)

    confirmations = subparsers.add_parser("confirmations")
    conf_subparsers = confirmations.add_subparsers(dest="confirmation_command", required=True)
    conf_list = conf_subparsers.add_parser("list")
    conf_list.add_argument("--user-id", dest="user_id", default="cli")
    conf_resolve = conf_subparsers.add_parser("resolve")
    conf_resolve.add_argument("confirmation_id")
    conf_resolve.add_argument("response_text")
    conf_subparsers.add_parser("expire")

    energy = subparsers.add_parser("energy")
    energy_subparsers = energy.add_subparsers(dest="energy_command", required=True)
    energy_log_cmd = energy_subparsers.add_parser("log")
    energy_log_cmd.add_argument("text")
    energy_log_cmd.add_argument("--date")
    energy_subparsers.add_parser("today")

    mail = subparsers.add_parser("mail")
    mail_subparsers = mail.add_subparsers(dest="mail_command", required=True)
    mail_audit = mail_subparsers.add_parser("audit")
    mail_audit.add_argument("--last", default="7d")
    mail_audit.add_argument("--query")
    mail_audit.add_argument("--limit", "--max-results", dest="max_results", type=int, default=50)
    mail_audit.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)

    mail_digest = mail_subparsers.add_parser("digest")
    mail_digest.add_argument("--today", action="store_true", default=True)
    mail_digest.add_argument("--query")
    mail_digest.add_argument("--limit", "--max-results", dest="max_results", type=int, default=50)
    mail_digest.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)

    daily = subparsers.add_parser("daily-plan")
    daily.add_argument("--date", required=True)
    daily.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)

    weekly = subparsers.add_parser("weekly-plan")
    weekly.add_argument("--week-start", required=True)
    weekly.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)

    run_job = subparsers.add_parser("run-job")
    run_job.add_argument(
        "job",
        choices=(
            "daily_morning",
            "evening_briefing",
            "weekly_sync",
            "sport_prep_reminder",
            "daily_hang_reminder",
            "habit_checkin_morning",
            "habit_checkin_evening",
        ),
    )
    run_job.add_argument("--date")
    run_job.add_argument("--week-start")
    run_job.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    run_job.add_argument("--send", action="store_true")

    cron = subparsers.add_parser("cron-audit")
    cron.add_argument("--jobs-path")

    models = subparsers.add_parser("model-audit")
    models.add_argument("--jobs-path")
    models.add_argument("--models-path")
    return parser


def _print_result(result: dict[str, Any], *, json_only: bool) -> None:
    if not json_only:
        print(_summary(result))
        print("")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))


def _summary(result: dict[str, Any]) -> str:
    status = _result_status(result)
    job = result.get("job") or "EOS"
    if "output_markdown" in result:
        return f"{job}: {status}\n\n{result['output_markdown'].strip()}"
    if "checks" in result:
        checks = result["checks"]
        return (
            f"health: {status} | "
            f"calendar={checks['calendar']['status']} "
            f"tasks={checks['google_tasks']['status']} "
            f"vault={checks['vault']['status']} "
            f"cron={checks['cron']['status']} "
            f"models={checks['models']['status']} "
            f"habits={checks['habits']['status']}"
        )
    if "habits" in result and "business_date_berlin" in result:
        return f"habits: {status} | pending={result.get('pending_count', 0)}"
    if "intent" in result and "confidence" in result:
        return (
            f"intake: {status} | intent={result['intent']} "
            f"confidence={result['confidence']:.2f} "
            f"confirm={result.get('requires_confirmation', False)}"
        )
    if "issues" in result:
        return f"audit: {status} | issues={len(result['issues'])}"
    if "task_read_status" in result:
        return f"tasks: {status} | open={result.get('open_task_count', 0)}"
    return f"{job}: {status}"


def _result_status(result: dict[str, Any]) -> str:
    return str(result.get("status") or result.get("task_read_status") or result.get("auth_status") or "unknown")


def _mail_query(args: argparse.Namespace) -> str:
    if getattr(args, "query", None):
        return str(args.query)
    if getattr(args, "mail_command", None) == "digest":
        return query_for_today(datetime.now(BERLIN).date())
    return query_from_last(str(getattr(args, "last", "7d")))


def _is_successful_result(result: dict[str, Any]) -> bool:
    return _result_status(result) in {
        "success",
        "green",
        "yellow",
        "partial",
        "warning",
        "skipped",
    }


def _parse_date(raw: str) -> date:
    return date.fromisoformat(raw)


def _parse_optional_date(raw: str | None) -> date | None:
    if not raw:
        return None
    return _parse_date(raw)


if __name__ == "__main__":
    raise SystemExit(main())
