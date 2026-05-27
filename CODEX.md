# CODEX.md

Read `AGENTS.md` first. It is the canonical operating document for EOS.

Tool-specific notes:
- Follow the test gates in `CLAUDE.md` before claiming completion.
- Do not bypass safety, credential, or raw-client-data boundaries.
- Prefer small verified changes over broad untested edits.
- If instructions conflict, stop and ask Endrit for the one decision that blocks safe progress.

## Mandatory Skill Gates

**Superpowers** — invoke before any non-trivial task (planning, TDD, debugging, verification, review). Not optional.

**Context7** — invoke before any work touching Google APIs, gog, Telegram, or any external library. Do not rely on training-data knowledge of library behavior.

## Python Runtime

Always use: `.venv/bin/python -m src.eos_cli`

Never use bare `python3` — it lacks the venv packages EOS depends on.

## Role in EOS Work

Codex handles: code review, quick fixes, small patches, plausibility checks on architecture decisions.
For complex debugging or large refactors, prefer Claude Code (`claude-gpt` or `/data/.local/bin/claude-codex-here`).
