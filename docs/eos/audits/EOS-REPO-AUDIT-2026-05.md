# EOS Repository Audit 2026-05

Status: reconciled Phase 0 audit
Date: 2026-05
Repository: `endritmurati99/eos`
Workspace: `data/.openclaw/workspaces/personal-assistant`
Audit mode: documentation-only, no implementation

## Executive Summary

The local workspace is the EOS repository nested inside the OpenClaw deployment wrapper. EOS is a Python-based personal operations assistant with a deterministic CLI, Google Calendar reads through `gog`, Google Tasks gateway, SQLite derived/runtime state, JSON planning state, habit services, job orchestration, Telegram delivery, Vault folders, and script-style verify checks.

No tracked production Gmail module exists in `origin/main`. Gmail should therefore start with read-only shadow mode, synthetic tests, storage minimization, and audit trails before any label writes or other mailbox mutations.

## Project Structure

- Runtime code is under `src/`, with CLI routing in `src/eos_cli.py`, state logic in `src/eos_core.py`, runtime helpers in `src/runtime.py`, SQLite setup in `src/database/models.py`, jobs in `src/jobs/`, gateways in `src/gateways/`, habits in `src/habits/`, intake/dispatch in `src/intake/` and `src/dispatch/`, and Vault flows in `src/vault/`.
- Documentation currently exists in flat `docs/EOS-*.md` files and the new durable governance layer under `docs/eos/**`; Phase 0 should not refactor the flat docs.
- Local fixtures and tracked state live under `data/`; integration notes live under `integrations/`.
- Systemd scheduling artifacts are present under `ops/systemd/`.

## CLI Surface

Confirmed CLI entrypoint:

```text
python3 -m src.eos_cli
```

Confirmed commands on `origin/main`:

```text
health
tasks
habits
intake
dispatch
confirmations
energy
daily-plan
weekly-plan
run-job
cron-audit
model-audit
```

Important behavior:

- `daily-plan`, `weekly-plan`, and `run-job` default to dry-run behavior.
- `run-job --send` is rejected when combined with `--dry-run`.
- `--json-only` exists for machine-readable command output.

## Existing Calendar Integration

- Calendar reads are implemented in `src/jobs/evening_reset.py` through `_load_calendar_events` and `_load_live_calendar_events`.
- The provider path is local `gog`, using account and token configuration exposed through `TaskGateway`.
- `TARGET_CALENDAR_ROLES = ("primary", "sport")`; `integrations/calendar-source.json` maps those roles to concrete Google Calendar IDs and uses `Europe/Berlin`.
- `data/calendar.json` may be used only for dry-run or explicitly allowed stub reads.
- Calendar write is documented as future/E2E scope, not Phase 0 implementation.

## Existing Google Tasks Integration

- Google Tasks access is centralized in `src/gateways/google_tasks.py` through `TaskGateway`.
- Canonical lists are `Inbox`, `Next`, `Waiting`, and `This Week`.
- Reads filter completed, deleted, and hidden tasks.
- Create and complete methods exist, so task mutation is technically present and must stay policy-gated.
- Auth status distinguishes `success`, `config_missing`, `auth_required`, `provider_disabled`, `not_found`, and provider errors.
- Relevant env names include `EOS_GOG_BIN`, `EOS_GOOGLE_ACCOUNT`, `EOS_GOOGLE_CREDENTIALS_PATH`, `EOS_GOOGLE_TOKEN_PATH`, and `EOS_GOOGLE_TASKS_ENABLED`.

## Existing Habit Engine

- Habit operations are implemented in `src/habits/service.py` through `HabitService`.
- Habit definitions are seeded from `data/eos_state.json` and persisted in SQLite.
- Tables include `habit_definitions`, `habit_events`, `habit_daily_status`, and `habit_relapses`.
- CLI routing exists through `python3 -m src.eos_cli habits ...`.
- Tests cover habit status, logging, coaching, failure, relapse, recovery, and persistence behavior.

## Scheduler and Jobs

- Job orchestration is implemented in `src/jobs/runner.py` through `run_eos_job`.
- Supported jobs are `daily_morning`, `evening_briefing`, `weekly_sync`, `sport_prep_reminder`, `daily_hang_reminder`, `habit_checkin_morning`, and `habit_checkin_evening`.
- `src/jobs/daily_capacity.py`, `src/jobs/evening_reset.py`, and `src/jobs/weekly_plan.py` generate the main planning outputs.
- Runtime cron paths are defined in `src/runtime.py`.
- `src/audits.py` implements scheduler and model audits.

## Delivery and Idempotency

- Telegram delivery is implemented in `src/gateways/telegram.py`.
- `src/eos_cli.py` calls delivery only from `_send_job_result` after checking sendability and non-empty `output_markdown`.
- `evening_reset` uses idempotency keys like `evening_reset:<date>`, persists job runs, and updates delivery state through `mark_evening_reset_delivery`.
- Future Gmail runs need their own audit and idempotency model before any write action exists.

## State Management

SQLite:

- default path: `data/eos_v2.db`
- managed by `src/database/models.py`
- contains job runs, daily evaluations, task snapshots, habit data, confirmations, energy logs, and dispatch logs

JSON:

- `data/eos_state.json` stores planning policy, source pointers, task annotations, habits, habit log, review state, and escalation policy
- `src/eos_core.py` validates it against `data/eos_state.schema.json`

Boundary:

- SQLite is derived/runtime state.
- Google Calendar, Google Tasks, Gmail, and Vault are systems of record or target systems of record.

## Existing Policies and Documentation

Important existing docs include:

- `docs/EOS-ARCHITECTURE-v1.md`
- `docs/EOS-CAPABILITY-MAP.md`
- `docs/EOS-OPERATING-CONTRACT-v1.md`
- `docs/EOS-ACTION-CONTRACT-v1.md`
- `docs/EOS-PLANNING-POLICY-v1.md`
- `docs/EOS-SCHEDULER-POLICY-v1.md`
- `docs/EOS-TASKS-INTEGRATION-v1.md`
- `docs/EOS-CURRENT-STATE-2026-04-30.md`

Phase 0 adds `docs/eos/` as durable project memory without replacing the existing flat docs.

## Test Coverage

Current tests are script-style smoke and contract checks under `tests/verify_*.py`.

Coverage areas:

- CLI and state validation
- daily and weekly planning dry-runs
- Google Tasks degraded states
- habit tracker and habit coaching
- dispatch and intake
- Telegram gateway and run-job delivery
- TTS pipeline
- Vault brain-dump flow
- cron audit

These tests are useful, but they do not prove production readiness for Gmail, mail labeling, calendar writes, or autonomous task/calendar writes.

## Missing Contract Tests

Recommended future tests:

- Gmail synthetic corpus classifier tests
- Gmail read-only client contract tests
- Gmail CLI dry-run contract tests
- mail audit logging tests
- mail storage minimization tests
- label write rollback tests before Phase 2
- source-linked memory answer tests
- calendar intelligence source-link tests

## Config and Secrets Handling

- `src/runtime.py` loads the nearest `.env` file into process environment without overwriting already-set values.
- `TaskGateway` can set `XDG_CONFIG_HOME` from `EOS_GOOGLE_TOKEN_PATH`.
- `.gitignore` is minimal and does not explicitly ignore `.env`, credential JSON, token roots, `var/`, or future mail-derived stores.
- `data/eos_v2.db` is tracked.
- No `.env` file was found in this repo path during the Phase 0 check.
- Token or credential file contents were not inspected.

## Integration Risks

Gmail risks:

- no tracked production Gmail module exists on `origin/main`
- OAuth scope strategy is not implemented in code
- mail content is highly sensitive and should not be stored raw by default
- false positives are risky for banking, credit card, security, legal, health, spam, and phishing mail
- tracked SQLite state could accidentally capture personal mail-derived data unless storage policy and `.gitignore` are updated first

Memory risks:

- source-backed answers require stable source links
- raw content persistence could create unnecessary privacy exposure
- memory must not become a second source of truth

Scheduler and notification risks:

- future mail jobs must not send or mutate by default
- Telegram notifications can leak sensitive summaries if mail, finance, security, legal, or health content is forwarded without notification-budget rules
- send-worthy planning must continue to fail closed when source-critical live data is unavailable

## Recommended Phase Order

1. Merge a single reconciled Phase 0 foundation.
2. Review `.gitignore`, state storage, and Gmail OAuth scope strategy.
3. Implement Gmail read-only shadow mode with dry-run CLI and fake-client tests.
4. Build a synthetic mail corpus before testing on real mail.
5. Add classifier and digest behavior with confidence and reasons.
6. Add label writes only after Phase 1 validation, rollback design, and read-after-write verification.

## Concrete Next Tasks

- Treat the reconciled foundation branch as the canonical governance baseline.
- Close or rebase overlapping foundation PRs after the reconciliation PR is merged.
- Define Gmail read-only OAuth scope strategy.
- Decide where mail-derived metadata may be stored.
- Create Gmail CLI contracts before adding write-capable commands.

## Unknowns

- exact production OAuth token storage state
- whether current tracked SQLite content is intentional for all future derived state
- production status of Google Tasks write and complete flows
- production Vault mount status
- desired retention period for mail-derived classifications
- desired Gmail account or accounts for Phase 1
- final merge state of Agent 2 and Agent 3 branches after foundation reconciliation

## Audit Status

```text
AUDIT_STATUS:
- repo_understood: partial
- code_changed: no
- gmail_existing: no tracked production module found on origin/main
- calendar_read_existing: yes
- task_gateway_existing: yes
- habit_engine_existing: yes
- scheduler_existing: yes
- delivery_tracking_existing: yes
- google_tasks_write_verified: unknown
- vault_write_verified: unknown
- scheduler_risk: medium
- recommended_next_phase: merge foundation reconciliation, then rebase Agent 2 and Agent 3
```
