# EOS Repo Audit 2026-05

Status: Phase 0 audit
Date: 2026-05
Repository: `endritmurati99/eos`
Workspace: `data/.openclaw/workspaces/personal-assistant`
Audit mode: documentation-only, no implementation

## 1. Project Structure

- EOS is implemented in the nested workspace repo at `data/.openclaw/workspaces/personal-assistant`; the top-level `/docker/openclaw-qt6t` repo is an OpenClaw deployment wrapper, not the EOS application repo.
- Runtime code is organized under `src/`, with CLI routing in `src/eos_cli.py`, shared state logic in `src/eos_core.py`, runtime path/config helpers in `src/runtime.py`, SQLite setup in `src/database/models.py`, job orchestration in `src/jobs/`, gateways in `src/gateways/`, habits in `src/habits/`, intake in `src/intake/`, dispatch in `src/dispatch/`, and Vault flows in `src/vault/`.
- Documentation currently exists both in flat `docs/EOS-*.md` files and in this new policy/audit structure under `docs/eos/**`; Phase 0 should not refactor the existing flat docs.
- Local operational fixtures and tracked state live in `data/*.json` and `data/eos_v2.db`; integration notes live in `integrations/*.md` and `integrations/calendar-source.json`.
- Systemd scheduling artifacts are present in `ops/systemd/*.timer` and `ops/systemd/eos-job@.service`.
- No tracked production Gmail implementation was found: `git ls-files src/eos_mail` returns no tracked files. Untracked local files under `src/eos_mail/` were present during this audit, but they are outside Agent 1 ownership and are not included in this documentation-only branch.

## 2. CLI Surface

- The CLI entrypoint is `src/eos_cli.py`; `python3 -m src.eos_cli --help` lists `health`, `tasks`, `habits`, `intake`, `dispatch`, `confirmations`, `energy`, `daily-plan`, `weekly-plan`, `run-job`, `cron-audit`, and `model-audit`.
- `src/eos_cli.py` routes task commands to `TaskGateway`, habit commands to `HabitService`, daily/weekly planning to `src/jobs/daily_capacity.py` and `src/jobs/weekly_plan.py`, and job execution to `src/jobs/runner.py`.
- `src/eos_cli.py` defaults `daily-plan`, `weekly-plan`, and `run-job` to dry-run behavior via Boolean optional `--dry-run`.
- `src/eos_cli.py` rejects `run-job --send` when `--dry-run` is also set, and sends only through `_send_job_result`.
- `src/eos_cli.py` supports `--json-only`, which is important for future automation and audit-friendly callers.

## 3. Existing Calendar Integration

- Calendar reads are implemented in `src/jobs/evening_reset.py` through `_load_calendar_events` and `_load_live_calendar_events`.
- The calendar provider path is the local `gog` CLI, using account and token configuration exposed through `TaskGateway` in `src/gateways/google_tasks.py`.
- `src/jobs/evening_reset.py` defines `TARGET_CALENDAR_ROLES = ("primary", "sport")`; `integrations/calendar-source.json` maps those roles to concrete Google Calendar IDs and sets `Europe/Berlin`.
- `src/jobs/evening_reset.py` can fall back to `data/calendar.json` only for dry-run or explicitly allowed stub reads.
- `integrations/google-calendar.md` and `integrations/daily-calendar-aggregation.md` document read-only calendar posture and state that `data/calendar.json` is not the primary source.
- Calendar writes are documented as future/E2E scope in `docs/EOS-CALENDAR-WRITE-E2E-v1.md`, but this audit does not identify a production calendar-write path that should be used in Phase 0.

## 4. Existing Tasks Integration

- Google Tasks access is centralized in `src/gateways/google_tasks.py` through `TaskGateway`.
- `src/gateways/google_tasks.py` defines canonical lists `Inbox`, `Next`, `Waiting`, and `This Week`.
- `TaskGateway.get_open_tasks` filters out completed, deleted, and hidden tasks before returning normalized open tasks.
- `TaskGateway.create_task` and `TaskGateway.complete_task` exist, so task writes are technically present even though future EOS autonomy must remain policy-gated.
- `TaskGateway.get_auth_status` distinguishes `success`, `config_missing`, `auth_required`, and provider-disabled states.
- `integrations/google-tasks.md` documents the intended source-of-truth model, list semantics, read shape, create shape, complete shape, and out-of-scope delete/move/clear behavior.

## 5. Existing Habit Engine

- Habit operations are implemented in `src/habits/service.py` through `HabitService`.
- `HabitService` seeds definitions from `data/eos_state.json`, persists definitions and events through `src/database/models.py`, and exposes status, today, done, skip, add, pause, weekly-report, handle, type, failure, relapse, recovery, and pattern flows.
- Habit state tables include `habit_definitions`, `habit_events`, `habit_daily_status`, and `habit_relapses` in `src/database/models.py`.
- Habit input routing is available through `src/eos_cli.py habits ...` and through dispatch paths in `src/dispatch/router.py`.
- `tests/verify_habit_tracker.py` and `tests/verify_habit_coaching.py` cover habit status, logging, coaching, failure, relapse, recovery, and persistence behavior.

## 6. Existing Scheduler / Jobs

- Job orchestration is implemented in `src/jobs/runner.py` through `run_eos_job`.
- Supported job names in `src/jobs/runner.py` are `daily_morning`, `evening_briefing`, `weekly_sync`, `sport_prep_reminder`, `daily_hang_reminder`, `habit_checkin_morning`, and `habit_checkin_evening`.
- `src/jobs/daily_capacity.py` generates daily planning output; `src/jobs/evening_reset.py` generates evening briefing output; `src/jobs/weekly_plan.py` generates weekly planning output.
- Scheduler definitions are present in `ops/systemd/eos-*.timer` and `ops/systemd/eos-job@.service`.
- Runtime cron audit paths are resolved in `src/runtime.py` through `CRON_JOBS_PATH`, `CRON_RUNS_DIR`, and `AGENT_MODELS_PATH`.
- `src/audits.py` implements `audit_cron` and `audit_models` for scheduler and model configuration inspection.

## 7. Existing Delivery Tracking

- Telegram delivery is implemented in `src/gateways/telegram.py` through `send_telegram_message`.
- `src/eos_cli.py` calls Telegram delivery only from `_send_job_result` after checking sendable job status and non-empty `output_markdown`.
- `src/jobs/evening_reset.py` uses idempotency keys like `evening_reset:<date>`, stores generated run data in `job_runs`, and has `mark_evening_reset_delivery` for delivery status updates.
- `src/database/models.py` defines `job_runs`, `task_snapshots`, `daily_evaluations`, and `dispatch_log`, which together provide runtime and delivery history.
- `tests/verify_run_job_delivery.py` and `tests/verify_telegram_gateway.py` cover send rejection, skipped delivery, Telegram provider handling, and missing-token behavior.

## 8. Existing State Storage

- `src/database/models.py` sets the default SQLite path to `./data/eos_v2.db`, overridable by `EOS_DB_PATH`.
- SQLite tables in `src/database/models.py` include job runs, task snapshots, daily evaluations, habit definitions/events/status/relapses, confirmations, energy logs, and dispatch logs.
- `data/eos_state.json` is validated by `src/eos_core.py` against `data/eos_state.schema.json`.
- `data/eos_state.json` stores planning policy, source pointers, task annotations, habits, habit log, review state, and escalation policy.
- `data/calendar.json` and `data/tasks.json` are fixtures or transition inputs, not production systems of record.
- `src/vault/brain_dump.py` writes durable markdown notes under `vault/`, while `src/audits.py` checks required Vault folders through `audit_vault`.

## 9. Existing Tests

- Test files are script-style smoke and contract checks under `tests/verify_*.py`.
- CLI and state coverage exists in `tests/verify_eos_cli.py`, `tests/verify_eos_core.py`, and `tests/verify_eos_state.py`.
- Calendar, daily, weekly, and run-job behavior is covered by `tests/verify_daily_capacity.py`, `tests/verify_weekly_plan_dry_run.py`, `tests/verify_run_job_delivery.py`, and `tests/verify_v2_foundation.py`.
- Google Tasks degraded behavior is covered by `tests/verify_google_tasks_degraded_state.py`.
- Habit, intake, dispatch, confirmations, energy, Telegram, TTS, cron audit, and Vault brain-dump behavior are covered by their corresponding `tests/verify_*.py` files.
- These tests are useful smoke coverage, but they do not prove production readiness for Gmail, mail labeling, calendar writes, or autonomous task/calendar writes.

## 10. Config and Secrets Handling

- `src/runtime.py` loads the nearest `.env` file into process environment without overwriting already-set variables.
- `src/gateways/google_tasks.py` reads `EOS_GOG_BIN`, `EOS_GOOGLE_ACCOUNT`, `EOS_GOOGLE_CREDENTIALS_PATH`, `EOS_GOOGLE_TOKEN_PATH`, and `EOS_GOOGLE_TASKS_ENABLED`.
- `src/gateways/telegram.py` reads Telegram token and target variables such as `EOS_TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_TOKEN`, `EOS_TELEGRAM_CHAT_ID`, `TELEGRAM_CHAT_ID`, `EOS_TELEGRAM_TO`, and `TELEGRAM_TO`.
- The repo `.gitignore` currently ignores virtualenv/cache artifacts but does not explicitly ignore `.env`, credential JSON, token roots, or future mail-derived stores.
- `data/eos_v2.db` is tracked, so future Gmail-derived state must not be added to that database before retention and privacy policy are reviewed.
- Token or credential file contents were not inspected for this audit.

## 11. Gaps

- No tracked Gmail client, Gmail classifier, Gmail digest, Gmail audit, Gmail feedback, or Gmail label module exists yet. Untracked local `src/eos_mail/*` files must be reviewed separately before they are treated as repository facts.
- No Gmail OAuth scope strategy is documented in code-level contracts.
- No synthetic Gmail corpus or Gmail classifier tests exist under `tests/`.
- No mail storage minimization implementation exists yet.
- No mail audit logging schema exists yet.
- No label write rollback procedure is implemented.
- Source-linked personal memory is a policy target, but no tracked `src/eos_memory/` implementation exists.
- Calendar intelligence is partly present through daily/evening/weekly planning, but no dedicated meeting-brief or source-linked meeting intelligence module exists.

## 12. Risks

- Gmail data is highly sensitive; adding Gmail ingestion before storage, retention, audit, and OAuth policy are finalized could expose private content.
- Auto-labeling banking, credit card, legal, health, security, spam, or phishing mail too early could create false confidence or hide important messages.
- Existing task write methods in `TaskGateway` make task mutation possible, so future dispatch/autonomy work must enforce the action authorization policy.
- Calendar read fallback behavior is safe for dry-run, but send-worthy planning must continue to fail closed when live calendar data is unavailable.
- Tracked SQLite state creates a risk that future derived mail data could be accidentally committed unless storage policy and `.gitignore` are updated first.
- Telegram notifications can leak sensitive summaries if mail, finance, security, legal, or health content is forwarded without notification-budget rules.

## 13. Recommended Next Implementation Steps

1. Review and merge Phase 0 foundation docs before adding Gmail runtime code.
2. Decide future Gmail OAuth scopes and token storage without printing or committing credentials.
3. Define Gmail read-only shadow-mode CLI contracts before adding commands.
4. Create a synthetic Gmail corpus for action-required, waiting, newsletter, money, security, spam/phishing, personal, work, university, health, travel, shopping, and legal cases.
5. Design mail audit records with run ID, account alias, query window, message IDs, labels suggested, confidence, reasons, dry-run flag, and error class.
6. Decide where mail-derived metadata may be stored and explicitly avoid raw body, OTP, reset-link, account-number, and attachment persistence by default.
7. Implement Phase 1 read-only Gmail ingestion and digest generation with no Gmail mutation.
8. Add Phase 2 label writes only after shadow-mode false-positive review, rollback design, and read-after-write verification.

## Audit Status

```text
AUDIT_STATUS:
- repo_understood: medium
- code_changed: no
- gmail_existing: no tracked production module found
- calendar_read_existing: yes
- task_gateway_existing: yes
- habit_engine_existing: yes
- scheduler_existing: yes
- delivery_tracking_existing: yes
- repo_audit_confidence: high for inspected files, medium for live production readiness
- recommended_next_phase: Phase 1 Gmail Read-only Shadow Mode design
```
