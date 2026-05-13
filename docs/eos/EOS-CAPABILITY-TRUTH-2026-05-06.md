# EOS Capability Truth 2026-05-06

Status: usable-assistant baseline

## Live Or CLI-Usable Now

- `assistant status`: summarizes Calendar, Tasks, Habits, Vault, Cron, Models, DB, and Gmail read-only readiness.
- `assistant home`: gives the main EOS home surface with readiness, today, one next action, habits, mail, and blockers.
- `assistant heute`: produces a daily operational view from Calendar, Google Tasks, Habits, Energy, and calendar-intelligence signals.
- `assistant jetzt`: reduces the daily view to one immediate next action.
- `assistant abend`: gives a conservative evening review and tomorrow-prep view without external writes.
- `assistant mail`: uses Gmail read-only status/digest counts and may surface task-proposal counts; it does not write to Gmail.

## Confirmed Boundaries

- Gmail remains read-only. No label, archive, send, delete, unsubscribe, or compose action is part of this baseline.
- Calendar writes are not live-ready.
- Drive, Maps, and Location modules are readiness/read-only surfaces unless a live provider E2E proves otherwise.
- Vault appears as configured/missing in status only; it is not yet claimed as production memory.
- Assistant commands may include user-facing task or habit labels in local CLI output, but smoke scripts print only privacy-safe summaries.

## Degraded Or Needs Follow-Up

- DB writability must be judged for the service user, not root.
- Any DB smoke failure must stay classified instead of being hidden.
- Gmail live provider JSON shape remains unverified until real read-only E2E proves it.
- Cron configuration must remain audited after runtime job edits.

## Operator Commands

```bash
python3 -m src.eos_cli --json-only assistant home
python3 -m src.eos_cli --json-only assistant status
python3 -m src.eos_cli --json-only assistant heute --dry-run
python3 -m src.eos_cli --json-only assistant jetzt --dry-run
python3 -m src.eos_cli --json-only assistant abend --dry-run
python3 -m src.eos_cli --json-only assistant mail --limit 5 --dry-run
```

Telegram text/slash routing uses the same assistant surfaces:

```text
/eos, /start, /hilfe, /help -> assistant home
/status -> assistant status
/heute -> assistant heute
/jetzt -> assistant jetzt
/abend -> assistant abend
/mail -> assistant mail
```
