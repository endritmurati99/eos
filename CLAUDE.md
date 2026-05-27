# CLAUDE.md

Read `AGENTS.md` first. It is the canonical operating document for EOS.

## What EOS Is

EOS is a personal planning & scheduling assistant — not a general coding tool.
Stay in scope: calendar, tasks, habits, daily/weekly plans, preparation reminders.
Do not add features, integrations, or abstractions beyond what was explicitly requested.

## Mandatory Skill Gates

**Superpowers** — invoke before any non-trivial coding task (debugging, refactors, test writing, architecture decisions). Not optional.

**Context7** — invoke BEFORE touching any external API, framework, or library integration:
- Google Calendar / Google Tasks (via `gog`)
- Gmail, Drive, Maps APIs
- Telegram gateway
- Any new Python dependency

Never assume training-data docs are current. Fetch before writing a single line.

## Test Gates

Before claiming implementation complete:
```bash
cd /data/.openclaw/workspaces/personal-assistant
.venv/bin/python -m src.eos_cli health
bash scripts/run_eos_smoke.sh
.venv/bin/python -m pytest
```

## Python Runtime

Always use the project venv:
```bash
.venv/bin/python -m src.eos_cli <command>
```
Never use bare `python3` — it lacks venv packages.

## Code Discipline

- Never modify `.env` with real credentials.
- Never add Gmail write scopes or send/delete/archive real emails unless explicitly asked.
- Never push to `main` directly — use feature branches.
- End implementation reports with: BRANCH, COMMITS, FILES_CHANGED, TESTS_RUN, TEST_RESULT, OPEN_RISKS, NEXT_RECOMMENDED_STEP.
