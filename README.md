# EOS

EOS is a local-first personal assistant runtime for calendar-aware planning, task review, habit tracking, scheduled routines, and operational daily guidance.

## Current Status

EOS is an active personal-assistant project. The repository contains CLI commands, scheduler jobs, Telegram gateway code, verification scripts, systemd units, policy documents, and runbooks for operating a single-user assistant safely.

The system is built around clear source-of-truth boundaries. Google Calendar is the hard source for fixed time blocks, Google Tasks and the Obsidian-style vault are integration surfaces, and local SQLite/JSON state is used for derived runtime and delivery state. External integrations must be reported honestly as live-verified, dry-run-only, degraded, or disabled.

## Key Capabilities

- CLI-first interface for health checks, daily planning, weekly planning, habit handling, runtime audits, and job execution.
- Calendar-aware planning that respects hard appointments before optional work.
- Habit and routine handling with tolerant Telegram-style text commands.
- Scheduled job delivery through systemd units and idempotent runtime state.
- Privacy-safe smoke summaries that avoid printing raw private output.
- Explicit policies for Gmail, Google live readiness, action authorization, memory, and data retention.

## Architecture

```text
Calendar / Tasks / Vault / Telegram
  -> source-specific readers and gateways
  -> planning, habit, and dispatch logic
  -> runtime and delivery state
  -> CLI, Telegram, vault, and scheduled outputs
```

EOS is intentionally not a general chatbot. It is designed to answer practical planning questions such as "what is actually possible today?" and to deliver compact operational outputs instead of long advisory text.

Useful docs:

- [Deep Description](docs/EOS-DEEP-DESCRIPTION-v1.md)
- [Architecture](docs/EOS-ARCHITECTURE-v1.md)
- [Global Agent Rules](docs/eos/policies/EOS-GLOBAL-AGENT-RULES-v1.md)
- [Release Candidate Queue](docs/eos/EOS-RELEASE-CANDIDATE-QUEUE.md)
- [Merge And Live Gate Runbook](docs/eos/runbooks/EOS-MERGE-AND-LIVE-GATE-RUNBOOK.md)

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 -m src.eos_cli --help
python3 -m src.eos_cli health
```

Common commands:

```bash
python3 -m src.eos_cli daily-plan --date YYYY-MM-DD --dry-run
python3 -m src.eos_cli weekly-plan --week-start YYYY-MM-DD --dry-run
python3 -m src.eos_cli habits handle "morgenroutine erledigt"
python3 -m src.eos_cli run-job <job> --dry-run
python3 -m src.eos_cli cron-audit
python3 -m src.eos_cli model-audit
```

## Verification

Recommended local checks:

```bash
git diff --check
python3 -m pytest -q
scripts/run_eos_tests.sh
scripts/run_eos_smoke.sh
python3 -m src.eos_cli --help
```

If pytest collection is unavailable in a host environment, run the standalone verification scripts directly:

```bash
for f in tests/verify_*.py; do python3 "$f"; done
```

## Privacy And Safety

- Never commit real credentials, tokens, live `.env` files, chat IDs, raw runtime DB contents, or private assistant output.
- Gmail remains protected by policy; write scopes and real send/archive/delete/label actions require explicit authorization.
- Smoke output should be summary-only and should not leak raw provider responses.
- Runtime gates must distinguish unit-test success from live provider readiness.
- Implementation work must use a feature branch, not direct pushes to `main`.

## Roadmap

- Keep deterministic runtime gates reliable before adding more integrations.
- Continue hardening Google Tasks, Vault, Gmail read-only, and Telegram delivery paths with live-proof labels.
- Improve incident visibility and recovery around scheduler and database failures.
- Keep planning outputs compact, actionable, and tied to real source-of-truth state.
