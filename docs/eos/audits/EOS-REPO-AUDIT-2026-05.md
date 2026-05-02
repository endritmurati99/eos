# EOS Repository Audit

Date: 2026-05
Repository: `endritmurati99/eos`
Workspace: `data/.openclaw/workspaces/personal-assistant`
Audit mode: documentation-only, no implementation

## Executive Summary

The local workspace is the EOS repository. It contains a Python-based personal assistant with a deterministic CLI, Google Calendar read path through `gog`, Google Tasks gateway, SQLite derived state, JSON state, habit services, job orchestration, Telegram delivery, Vault folders, and verify-style tests.

No production Gmail module was found in `src/`, `tests/`, `docs/`, or `integrations/` during targeted search. Gmail should therefore start as a new read-only shadow-mode capability after policy and security review.

## Current Architecture

Key code areas:

- `src/eos_cli.py`: CLI entrypoint and command routing
- `src/runtime.py`: workspace paths, env loading, model profile constants
- `src/eos_core.py`: state validation, task ranking, capacity checks, habit version selection
- `src/database/models.py`: SQLite schema and connection setup
- `src/jobs/runner.py`: job dispatcher
- `src/jobs/daily_capacity.py`: daily planning
- `src/jobs/evening_reset.py`: evening briefing, calendar reads, task snapshots, idempotency
- `src/jobs/weekly_plan.py`: weekly planning
- `src/gateways/google_tasks.py`: Google Tasks gateway through `gog`
- `src/gateways/telegram.py`: Telegram message delivery
- `src/habits/service.py`: habit definitions, events, streaks, status, and text handling
- `src/vault/brain_dump.py`: brain dump to markdown flow

## CLI Surface

Confirmed by `python3 -m src.eos_cli --help`:

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

- `daily-plan`, `weekly-plan`, and `run-job` default to dry-run.
- `run-job --send` is rejected when combined with `--dry-run`.
- CLI output supports `--json-only`.

## Data Sources

Primary or planned systems of record:

- Google Calendar through `gog`
- Google Tasks through `TaskGateway`
- Vault markdown files
- future Gmail integration

Current local state and fixtures:

- `data/eos_state.json`: JSON primary planning and habit state
- `data/eos_state.schema.json`: JSON schema
- `data/eos_v2.db`: SQLite derived state
- `data/calendar.json`: calendar test or fallback fixture
- `data/tasks.json`: task test fixture
- `integrations/calendar-source.json`: Google Calendar source configuration

## Calendar Integration

Calendar reads are implemented in `src/jobs/evening_reset.py` and reused through job flows.

Confirmed details:

- provider path is local `gog`
- target calendar roles are `primary` and `sport`
- `integrations/calendar-source.json` contains the configured account and calendar IDs
- timezone is `Europe/Berlin`
- live calendar read can fail closed when no safe fallback is allowed

Calendar write is documented elsewhere as a target or E2E area, but it is not part of Phase 0.

## Google Tasks Integration

`src/gateways/google_tasks.py` defines `TaskGateway`.

Confirmed behavior:

- canonical lists are `Inbox`, `Next`, `Waiting`, and `This Week`
- read path filters completed, deleted, and hidden tasks
- create and complete methods exist
- auth status distinguishes `success`, `config_missing`, `auth_required`, and provider-disabled cases
- the gateway uses env names such as `EOS_GOG_BIN`, `EOS_GOOGLE_ACCOUNT`, `EOS_GOOGLE_CREDENTIALS_PATH`, `EOS_GOOGLE_TOKEN_PATH`, and `EOS_GOOGLE_TASKS_ENABLED`

Production write readiness should remain reviewed separately.

## State Management

SQLite:

- default path: `data/eos_v2.db`
- managed by `src/database/models.py`
- contains job runs, daily evaluations, task snapshots, habit definitions, habit events, daily habit status, relapses, confirmations, energy logs, and dispatch logs

JSON:

- `data/eos_state.json` stores planning policy, sources, task annotations, habit definitions, and review state
- `src/eos_core.py` validates this against `data/eos_state.schema.json`

Important boundary:

- SQLite is derived state and runtime history.
- Calendar, Tasks, Gmail, and Vault remain systems of record.

## Scheduler and Jobs

Job dispatcher:

- `src/jobs/runner.py`

Confirmed job names:

```text
daily_morning
evening_briefing
weekly_sync
sport_prep_reminder
daily_hang_reminder
habit_checkin_morning
habit_checkin_evening
```

Systemd timer definitions are in `ops/systemd/`.

Runtime cron audit paths are resolved in `src/runtime.py` against the OpenClaw runtime layout.

## Delivery and Idempotency

Telegram delivery:

- implemented by `src/gateways/telegram.py`
- called from `src/eos_cli.py` when `run-job --send` is used

Idempotency:

- `evening_reset` uses keys such as `evening_reset:<date>`
- job runs are persisted in SQLite `job_runs`
- message digests are stored for generated output
- dry-run does not send

Risk:

- idempotency coverage appears strongest around evening reset; future Gmail actions need their own audit and idempotency model.

## Existing Policies and Documentation

Existing documentation is flat under `docs/EOS-*.md`.

Important existing docs include:

- `docs/EOS-ARCHITECTURE-v1.md`
- `docs/EOS-CAPABILITY-MAP.md`
- `docs/EOS-OPERATING-CONTRACT-v1.md`
- `docs/EOS-ACTION-CONTRACT-v1.md`
- `docs/EOS-PLANNING-POLICY-v1.md`
- `docs/EOS-SCHEDULER-POLICY-v1.md`
- `docs/EOS-TASKS-INTEGRATION-v1.md`
- `docs/EOS-CURRENT-STATE-2026-04-30.md`

Phase 0 adds `docs/eos/` as durable project memory without refactoring the existing doc layout.

## Test Coverage

Verify scripts exist under `tests/`:

- CLI and state verification
- daily and weekly planning dry-runs
- Google Tasks degraded state tests
- habit tracker and habit coaching tests
- dispatch layer tests
- Telegram gateway tests
- run-job delivery tests
- TTS pipeline tests
- vault brain-dump flow tests
- cron audit tests

These are useful smoke and contract-style checks, but they do not by themselves prove production readiness for external integrations.

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

## Integration Risks

Gmail risks:

- no existing production Gmail module found
- OAuth scope strategy is not defined yet
- mail content can be sensitive and should not be stored raw by default
- false positives are risky for banking, credit card, security, legal, and health mail

Memory risks:

- source-backed answers require stable source links
- raw content persistence could create unnecessary privacy exposure
- memory must not become a second source of truth

Scheduler risks:

- future mail jobs must not send or mutate by default
- future mail jobs need idempotency and dry-run parity

## Security and Secrets Risks

Observed metadata:

- `.gitignore` is minimal and does not explicitly ignore `.env`, token roots, `var/`, or local SQLite files
- `data/eos_v2.db` is tracked
- no `.env` file was found in this repo path
- token files were not inspected
- `TaskGateway` can set `XDG_CONFIG_HOME` from `EOS_GOOGLE_TOKEN_PATH`

Risk:

- before adding Gmail, tracked or unignored local state must be reviewed so derived mail data and tokens cannot be committed accidentally.

## Recommended Phase Order

1. Finish Phase 0 docs, audits, and policies.
2. Review `.gitignore`, state storage, and OAuth scope strategy.
3. Design Phase 1 Gmail read-only shadow mode.
4. Build a synthetic mail corpus before testing on real mail.
5. Implement Gmail read-only ingestion and dry-run classification.
6. Add label writes only after Phase 1 validation.

## Concrete Next Tasks

- Review this audit and the security audit together.
- Decide storage policy for future mail tables before adding migrations.
- Define Gmail read-only OAuth scope strategy.
- Create a Gmail shadow-mode implementation plan.
- Create a Gmail synthetic test corpus.
- Create Gmail CLI contracts before adding commands.

## Unknowns

- exact production OAuth token storage state
- whether current tracked SQLite content is intentional for all future derived state
- production status of Google Tasks write and complete flows
- production Vault mount status
- desired retention period for mail-derived classifications
- desired Gmail account or accounts for Phase 1

## Audit Status

```text
AUDIT_STATUS:
- repo_understood: partial
- gmail_existing: no production module found
- google_tasks_write_verified: unknown
- vault_write_verified: unknown
- scheduler_risk: medium
- recommended_next_phase: Phase 0 security review, then Phase 1 Gmail Shadow Mode Design
```
