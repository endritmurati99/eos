# HEARTBEAT.md - EOS / Personal Assistant

Default response: `HEARTBEAT_OK`.

Use heartbeats for quiet personal-operations awareness, not autonomous scheduling or task mutation.

## Allowed

- Read configured calendar/task status when the current context calls for a near-term check.
- Surface conflicts, missed hard events, urgent reminders, or a clear blocker.
- Keep the output short and operational.

## Forbidden During Heartbeat

- Do not create, update, delete, archive, send, label, or unsubscribe anything.
- Do not edit files, update docs, rewrite memory, commit, push, restart services, or change runtime config.
- Do not print secrets, tokens, private mailbox data, private runtime data, or raw personal data.
- Do not run broad mailbox/calendar sweeps or heavy tests unless Endrit explicitly requested that action.

If nothing needs attention, reply exactly `HEARTBEAT_OK`.
