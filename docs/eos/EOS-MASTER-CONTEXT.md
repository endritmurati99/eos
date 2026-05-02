# EOS Master Context

Status: Phase 0 baseline
Date: 2026-05
Repository: `endritmurati99/eos`
Workspace: `data/.openclaw/workspaces/personal-assistant`

## Purpose

EOS is a personal operations system for one person. It is designed to read real operational sources, structure them, and turn them into small, concrete planning decisions.

EOS should help with:

- realistic daily and weekly planning
- protection of focus time
- important mail detection
- structured follow-ups
- meeting preparation
- habit and journal review
- reminders with low notification load
- source-backed personal memory
- controlled, low-risk automation

## Non-Goals

EOS is not:

- a general chatbot
- a general knowledge assistant
- a marketing assistant
- a generic writing assistant
- a therapy system
- an autonomous agent without limits
- a broad data collector without policy boundaries
- a second source of truth for systems that already have one

## Current Confirmed Capabilities

The current codebase contains:

- dedicated `personal-assistant` workspace
- deterministic CLI at `python3 -m src.eos_cli`
- Google Calendar read path through `gog`
- hard calendar aggregation for at least `primary` and `sport`
- Google Tasks gateway through `src/gateways/google_tasks.py`
- daily and weekly planning jobs
- habit engine with SQLite events
- job orchestration through `src/jobs/runner.py`
- Telegram delivery path through `src/gateways/telegram.py`
- cron and model audits
- Vault folder audit and brain-dump file flow

Current CLI surface:

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

## Architecture Principle

EOS must separate source-of-truth systems from derived state and runtime state.

System of Record:

- Google Calendar for hard events
- Google Tasks for active tasks
- Gmail for mail
- Vault markdown files for durable notes and personal context

Derived State:

- SQLite classifications
- daily evaluations
- habit metrics
- summaries
- meeting contexts
- source-linked memory indexes

Runtime and Delivery State:

- job runs
- idempotency keys
- delivery events
- audit logs
- dry-run outputs

EOS must not create contradictory truth systems. If a source is primary, EOS may cache or summarize it, but must not silently replace it.

## Quality Principles

- Prefer deterministic CLI contracts before background automation.
- Prefer dry-run output before writes.
- Keep every classification explainable with confidence and reason.
- Keep source IDs and source links attached to derived summaries.
- Fail closed when source-critical live data is missing.
- Add tests before expanding integration scope or autonomy.

## Security Principles

- Do not print, store, or commit secrets.
- Start every new external integration in read-only mode.
- Treat mail, finance, security, legal, health, and account-recovery data as sensitive.
- Store metadata and provenance before raw content.
- Require approval for destructive, external, sensitive, or irreversible actions.
- Keep action logs sufficient for review and rollback.

## Strategic Modules

Future modules should be added only after Phase 0 policies are in place.

```text
src/eos_mail/
  gmail_client.py
  models.py
  rules.py
  classifier.py
  digest.py
  audit.py
  feedback.py

src/eos_memory/
  indexer.py
  retriever.py
  source_links.py
  summarizer.py

src/eos_calendar_intelligence/
  meeting_brief.py
  conflict_detector.py
  prep_engine.py
  rescheduler.py

src/eos_journal/
  morning_prompt.py
  evening_review.py
  quote_provider.py
  mood_energy.py

src/eos_notifications/
  budget.py
  routing.py
  escalation.py
```

These paths are target architecture, not confirmed implementation.

## Phase Roadmap

1. Phase 0: Context, audit, and policies
2. Phase 1: Gmail read-only shadow mode
3. Phase 2: Safe auto-labeling
4. Phase 3: Mail to task and calendar suggestions
5. Phase 4: Meeting intelligence
6. Phase 5: Personal memory
7. Phase 6: Habit and journal coach
8. Phase 7: Controlled autopilot

Phase 1 must not start until the Phase 0 repository audit, policy foundation, and security audit have been reviewed.

## Engineering Rules

- No big-bang implementation.
- Start with dry-run behavior before writes.
- Start with read-only access before reversible actions.
- Do not store sensitive data unless needed for a defined feature.
- Store source IDs and links before storing raw content.
- Every external action must be auditable.
- Every classification must include confidence and reason.
- Unsafe or low-confidence classifications go to review.
- Banking, credit card, security, legal, and health signals are conservative by default.
- Memory answers require source links.
- Autonomy requires policy, tests, dry-runs, and rollback.

## Policy Foundation Status

```text
POLICY_STATUS:
- master_context_created: yes
- roadmap_created: yes
- mail_policy_created: yes
- action_policy_created: yes
- memory_policy_created: yes
- calendar_policy_created: yes
- habit_journal_policy_created: yes
- notification_budget_created: yes
- implementation_started: no runtime implementation
```
