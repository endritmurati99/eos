# Eos Upgrade Phase 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore Eos to a stable, well-structured agent with green test suite, reliable evening briefing, working habit backfill, template-clean identity files, and a clean decision on workspace promotion.

**Architecture:** Eos is a Python CLI app living at `/data/.openclaw/workspaces/personal-assistant` (branch `agent/eos-usable-assistant-v1`, GitHub remote `endritmurati99/eos`). SQLite source-of-truth (`data/eos_v2.db`), event-log/projection model for habits, `gog` CLI as Google Workspace gateway, Telegram as control surface. Cron-driven daily/evening/weekly jobs. Phase 1 (Google OAuth restore) completed today 2026-05-31 ~17:00 Berlin.

**Tech Stack:** Python 3 (venv at `.venv/`), pytest, sqlite3, subprocess→`gog`, OpenClaw cron (`/data/.openclaw/cron/jobs.json`).

**Source audits this plan is built on:**
- Claude Code lane audit (Trio member 1): code/architecture/reliability/tests/habits/cron/integrations
- Codex lane audit (Trio member 2): identity files, workspace structure, worktree state, cron coverage, GitHub hygiene

---

## File Structure

Files this plan creates or modifies:

**Code (`src/`):**
- Modify: `src/habits/service.py` — fix weekly-review denominator
- Modify: `src/jobs/runner.py` — wrap `run_evening_reset` in `partial`-envelope
- Modify: `src/jobs/evening_reset.py` — guard `json.loads`, add `subprocess` timeout
- Modify: `src/audits.py` — fix model provider-prefix handling
- Modify: `src/eos_cli.py` — add `habits backfill` subcommand
- Modify: `src/dispatch/router.py` — wire backfill to Telegram (optional)

**Tests (`tests/`):**
- Modify: `tests/verify_habit_coaching.py` — already has the failing test
- Create: `tests/eos_audits/test_audit_models_prefix.py`
- Create: `tests/eos_jobs/test_evening_briefing_degrades.py`
- Create: `tests/eos_jobs/test_gog_timeout.py`
- Create: `tests/eos_habits/test_backfill_command.py`

**Identity files (workspace root):**
- Rewrite: `IDENTITY.md` (YAML format per template)
- Modify: `SOUL.md` (add Domains + Tone sections)
- Modify: `AGENTS.md` (trim toward template baseline, keep mandates)
- Clean: `TOOLS.md` (strip template scaffolding lines 31-71, add Laptop Compute section)

**Git/worktree:**
- Cherry-pick `0181edd` into current branch
- Prune `/data/.openclaw/worktrees/personal-assistant-eos-p0-stabilization/`
- Delete branch `agent/eos-p0-stabilization`
- Commit dirty `DREAMS.md`, decide on `GIT_STANDARD.json`

**Optional workspace promotion (Phase E, gated):**
- Create: `/data/.openclaw/agents/eos/`
- Move: `/data/.openclaw/workspaces/personal-assistant/` → `/data/.openclaw/workspaces/eos/`
- Update: 7 entries in `/data/.openclaw/cron/jobs.json` (`sessionTarget` strings)

---

## Phase A — Foundation Cleanup

**Goal:** Clean git state, recover unmerged stabilization commit, prune stale worktree. No code risk.

### Task A1: Cherry-pick unmerged stabilization commit

**Files:**
- Modify: working tree of `agent/eos-usable-assistant-v1` via cherry-pick

- [ ] **Step 1: Inspect what's in 0181edd**

```bash
cd /data/.openclaw/workspaces/personal-assistant
git show --stat 0181edd
```

Expected: list of files touched by the stabilization commit.

- [ ] **Step 2: Stash dirty files first**

```bash
git stash push -m "phase-a-temp" -- DREAMS.md
```

Expected: `Saved working directory and index state`.

- [ ] **Step 3: Cherry-pick the commit**

```bash
git cherry-pick 0181edd
```

Expected: clean cherry-pick OR conflicts. If conflicts → resolve manually, then `git cherry-pick --continue`.

- [ ] **Step 4: Run full pytest to confirm cherry-pick didn't break anything**

```bash
.venv/bin/python -m pytest -x --ignore=tests/verify_habit_coaching.py 2>&1 | tail -20
```

Expected: passes (the one known failing test is excluded for this gate; we fix it in Phase B).

- [ ] **Step 5: Pop the stash back**

```bash
git stash pop
```

Expected: `DREAMS.md` is back as modified.

### Task A2: Prune stale worktree and branch

**Files:**
- Delete: `/data/.openclaw/worktrees/personal-assistant-eos-p0-stabilization/`
- Delete: branch `agent/eos-p0-stabilization`

- [ ] **Step 1: Verify worktree still references the merged commit**

```bash
git -C /data/.openclaw/workspaces/personal-assistant worktree list | grep eos-p0
```

Expected: shows the worktree.

- [ ] **Step 2: Remove the worktree**

```bash
git -C /data/.openclaw/workspaces/personal-assistant worktree remove /data/.openclaw/worktrees/personal-assistant-eos-p0-stabilization
```

Expected: clean removal. If "contains modified or untracked files" → inspect first, then `--force` only after manual review.

- [ ] **Step 3: Delete the branch**

```bash
git -C /data/.openclaw/workspaces/personal-assistant branch -D agent/eos-p0-stabilization
```

Expected: `Deleted branch agent/eos-p0-stabilization (was 0181edd)`.

### Task A3: Handle dirty `DREAMS.md` and untracked `GIT_STANDARD.json`

- [ ] **Step 1: Inspect DREAMS.md diff**

```bash
git -C /data/.openclaw/workspaces/personal-assistant diff DREAMS.md | head -50
```

Decide: is this content that belongs in repo? If yes → commit. If no → discard.

- [ ] **Step 2: Inspect GIT_STANDARD.json**

```bash
cat /data/.openclaw/workspaces/personal-assistant/GIT_STANDARD.json
```

Decide: add to repo, add to `.gitignore`, or `trash`.

- [ ] **Step 3: Commit decisions**

```bash
cd /data/.openclaw/workspaces/personal-assistant
git add DREAMS.md GIT_STANDARD.json   # or just DREAMS.md
git commit -m "chore: foundation cleanup — recover stabilization, dreams update"
```

---

## Phase B — Reliability Fixes (TDD)

**Goal:** Green test suite. Evening briefing degrades like daily_morning. Subprocess calls have timeouts. Audit models stops flooding false positives.

### Task B1: Fix the failing weekly-review denominator test

**Files:**
- Modify: `src/habits/service.py:587-598`
- Test: `tests/verify_habit_coaching.py::test_weekly_review_denominator_includes_backfilled_statuses_before_creation`

- [ ] **Step 1: Run only the failing test to confirm current state**

```bash
.venv/bin/python -m pytest tests/verify_habit_coaching.py::test_weekly_review_denominator_includes_backfilled_statuses_before_creation -v
```

Expected: FAIL (expects 3, gets 5).

- [ ] **Step 2: Read the test and the denominator code**

Read `tests/verify_habit_coaching.py` lines 395-414 and `src/habits/service.py` lines 587-598 to understand the contract.

- [ ] **Step 3: Apply the fix per Claude Code audit**

The denominator counts every scheduled in-week day, but it should count only `min(latest_trackable_day, max(first_trackable_day, today))` worth of days. Apply this clamp inside the loop or before the count.

- [ ] **Step 4: Re-run the test**

```bash
.venv/bin/python -m pytest tests/verify_habit_coaching.py::test_weekly_review_denominator_includes_backfilled_statuses_before_creation -v
```

Expected: PASS.

- [ ] **Step 5: Run full test suite to verify no regression**

```bash
.venv/bin/python -m pytest 2>&1 | tail -5
```

Expected: all green.

- [ ] **Step 6: Commit**

```bash
git add src/habits/service.py
git commit -m "fix(habits): clamp weekly-review denominator to trackable days"
```

### Task B2: Add subprocess timeout to gog calls in evening_reset

**Files:**
- Modify: `src/jobs/evening_reset.py:283` (and any other unguarded `subprocess.run` against `gog_bin`)
- Create: `tests/eos_jobs/test_gog_timeout.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/eos_jobs/test_gog_timeout.py
import subprocess
from unittest.mock import patch
from src.jobs import evening_reset


def test_gog_call_returns_provider_error_on_timeout():
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="gog", timeout=60)):
        result = evening_reset._load_calendar_events(
            target_date_berlin=__import__("datetime").date(2026, 5, 31),
        )
    assert result["calendar_read_status"] == "provider_error"
    assert "timeout" in (result.get("error") or "").lower()
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/eos_jobs/test_gog_timeout.py -v
```

Expected: FAIL (no timeout handling).

- [ ] **Step 3: Add timeout and exception handler in evening_reset.py**

In `_load_calendar_events` (and similar gog-calling helpers): wrap `subprocess.run(...)` with `timeout=60` and try/except `subprocess.TimeoutExpired` → return `{"calendar_read_status": "provider_error", "error": "gog timeout"}`.

- [ ] **Step 4: Re-run test**

```bash
.venv/bin/python -m pytest tests/eos_jobs/test_gog_timeout.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/eos_jobs/test_gog_timeout.py src/jobs/evening_reset.py
git commit -m "feat(jobs): timeout gog subprocess calls in evening_reset"
```

### Task B3: Guard `json.loads` and degrade evening_briefing like daily_morning

**Files:**
- Modify: `src/jobs/evening_reset.py` (lines 189, 298, 331, 581)
- Modify: `src/jobs/runner.py:42-44` (wrap `run_evening_reset` in `partial`-envelope)
- Create: `tests/eos_jobs/test_evening_briefing_degrades.py`

- [ ] **Step 1: Write failing test**

```python
# tests/eos_jobs/test_evening_briefing_degrades.py
import json
from unittest.mock import patch
from src.jobs import runner


def test_evening_briefing_returns_partial_when_calendar_fails():
    bad_stdout = "this is not json"
    with patch("subprocess.run") as m:
        m.return_value.stdout = bad_stdout
        m.return_value.returncode = 0
        result = runner.run_job("evening_briefing", dry_run=True)
    assert result["status"] in ("partial", "success")
    assert "crash" not in str(result).lower()
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/eos_jobs/test_evening_briefing_degrades.py -v
```

Expected: FAIL (crashes with JSONDecodeError).

- [ ] **Step 3: Wrap json.loads + runner call**

In `evening_reset.py`, each unguarded `json.loads(...)` → `try/except json.JSONDecodeError` returning a status field. In `runner.py:42-44`, mirror the `partial`-envelope pattern from `daily_morning` (lines 26-40).

- [ ] **Step 4: Re-run test + smoke check the real command**

```bash
.venv/bin/python -m pytest tests/eos_jobs/test_evening_briefing_degrades.py -v
EOS_DB_PATH=data/eos_v2.db .venv/bin/python -m src.eos_cli run-job evening_briefing --dry-run 2>&1 | tail -5
```

Expected: test PASS, smoke succeeds.

- [ ] **Step 5: Commit**

```bash
git add tests/eos_jobs/test_evening_briefing_degrades.py src/jobs/evening_reset.py src/jobs/runner.py
git commit -m "fix(jobs): evening_briefing degrades like daily_morning"
```

### Task B4: Fix `audit_models` provider-prefix handling

**Files:**
- Modify: `src/audits.py:88-120`
- Create: `tests/eos_audits/test_audit_models_prefix.py`

- [ ] **Step 1: Write failing test**

```python
# tests/eos_audits/test_audit_models_prefix.py
from src import audits


def test_audit_does_not_false_positive_on_codex_gpt55(monkeypatch):
    monkeypatch.setattr(audits, "_load_available_models", lambda: {"gpt-5.5", "claude-opus-4-7"})
    issues = audits._audit_job_models([{"id": "x", "name": "x", "model": "codex/gpt-5.5"}])
    assert issues == []
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/eos_audits/test_audit_models_prefix.py -v
```

Expected: FAIL (current code treats `codex/gpt-5.5` as missing).

- [ ] **Step 3: Apply the fix**

In `_audit_job_models` (or wherever the comparison happens): normalize by `model_id.split("/", 1)[-1]` before checking availability. Keep prefixed-forms working.

- [ ] **Step 4: Re-run + run `eos_cli health` to verify dramatically fewer false positives**

```bash
.venv/bin/python -m pytest tests/eos_audits/test_audit_models_prefix.py -v
EOS_DB_PATH=data/eos_v2.db .venv/bin/python -m src.eos_cli health 2>&1 | grep -c job_model_missing
```

Expected: test PASS, false-positive count drops from 17 to 0.

- [ ] **Step 5: Commit**

```bash
git add tests/eos_audits/test_audit_models_prefix.py src/audits.py
git commit -m "fix(audits): strip provider prefix before model availability check"
```

---

## Phase C — Habit Backfill Command

**Goal:** First-class CLI command to backfill habit statuses for a date range. Resolves the 29.05+30.05 backlog and any future outage gap.

### Task C1: TDD the `habits backfill` CLI command

**Files:**
- Modify: `src/eos_cli.py` (extend `habits` subparser)
- Modify: `src/habits/service.py` (add `backfill_range` method if needed)
- Create: `tests/eos_habits/test_backfill_command.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/eos_habits/test_backfill_command.py
import datetime as dt
from src.habits.service import HabitService


def test_backfill_marks_all_pending_days_in_range(tmp_path):
    db_path = tmp_path / "test.db"
    svc = HabitService(db_path=str(db_path))
    svc.add_habit(id="morgenroutine", title="Morgenroutine", schedule="daily")
    summary = svc.backfill_range(
        habit_id="morgenroutine",
        since=dt.date(2026, 5, 29),
        until=dt.date(2026, 5, 30),
        mark="missed",
    )
    assert summary["filled"] == 2
    assert summary["skipped"] == 0
```

- [ ] **Step 2: Run to confirm failure**

```bash
.venv/bin/python -m pytest tests/eos_habits/test_backfill_command.py -v
```

Expected: FAIL (`backfill_range` does not exist).

- [ ] **Step 3: Implement `HabitService.backfill_range`**

Iterate dates from `since` to `until` inclusive, skip days that are not `scheduled & pending` for the habit, call `mark_done` (or `mark_status`) with `mark` (one of `missed`, `skip`, `done`), accumulate filled/skipped counts, return summary.

- [ ] **Step 4: Run service test**

```bash
.venv/bin/python -m pytest tests/eos_habits/test_backfill_command.py -v
```

Expected: PASS.

- [ ] **Step 5: Wire CLI**

Extend `src/eos_cli.py`'s `habits` subparser with `backfill --habit ID --since YYYY-MM-DD --until YYYY-MM-DD --mark missed|skip|done`. Default `--until=today_berlin`. Output JSON summary.

- [ ] **Step 6: Smoke-test CLI**

```bash
EOS_DB_PATH=data/eos_v2.db .venv/bin/python -m src.eos_cli habits backfill --habit morgenroutine --since 2026-05-29 --until 2026-05-30 --mark missed --dry-run
```

Expected: prints intended actions, exits 0.

- [ ] **Step 7: Real run for the 29.05/30.05 backlog (3 habits × 2 days)**

```bash
EOS_DB_PATH=data/eos_v2.db .venv/bin/python -m src.eos_cli habits backfill --habit morgenroutine --since 2026-05-29 --until 2026-05-30 --mark missed
EOS_DB_PATH=data/eos_v2.db .venv/bin/python -m src.eos_cli habits backfill --habit klimmzugstange --since 2026-05-29 --until 2026-05-30 --mark missed
EOS_DB_PATH=data/eos_v2.db .venv/bin/python -m src.eos_cli habits backfill --habit abendroutine --since 2026-05-29 --until 2026-05-30 --mark missed
```

Expected: each prints `filled: 2`.

- [ ] **Step 8: Verify via habits status**

```bash
EOS_DB_PATH=data/eos_v2.db .venv/bin/python -m src.eos_cli habits status
```

Expected: 29.05 and 30.05 no longer `pending`.

- [ ] **Step 9: Commit**

```bash
git add tests/eos_habits/test_backfill_command.py src/habits/service.py src/eos_cli.py
git commit -m "feat(habits): backfill --since/--until CLI command"
```

### Task C2: (optional) Wire backfill to Telegram dispatcher

Skipped unless Endrit explicitly asks — current CLI path is enough to unblock the backlog. Document in `MEMORY.md` as future enhancement.

---

## Phase D — Identity Files Cleanup + KI-Chat Review

**Goal:** Identity files match the AGENT_FACTORY templates. Photon and Eos both document the new Laptop Compute / KI-Chat-Review capability. KI-Chats on Endrit's laptop sanity-check the changes.

### Task D1: Rewrite `IDENTITY.md` to YAML format

**Files:**
- Rewrite: `/data/.openclaw/workspaces/personal-assistant/IDENTITY.md`

- [ ] **Step 1: Read template**

```bash
cat /data/.openclaw/workspaces/photon/agent-factory/templates/IDENTITY.md.tmpl
```

- [ ] **Step 2: Write new IDENTITY.md matching template (YAML keys: name, creature, vibe, emoji)**

- [ ] **Step 3: Commit**

```bash
git add IDENTITY.md && git commit -m "chore(identity): IDENTITY.md template alignment"
```

### Task D2: Add Domains + Tone sections to SOUL.md

**Files:**
- Modify: `/data/.openclaw/workspaces/personal-assistant/SOUL.md`

- [ ] **Step 1: Read template**

```bash
cat /data/.openclaw/workspaces/photon/agent-factory/templates/SOUL.md.tmpl
```

- [ ] **Step 2: Insert `## Standard Domains` and `## Tone` sections preserving existing Eos-specific Phase-1 content**

- [ ] **Step 3: Commit**

```bash
git add SOUL.md && git commit -m "chore(identity): SOUL.md add Domains and Tone sections"
```

### Task D3: Clean TOOLS.md (strip template scaffolding + add Laptop Compute section)

**Files:**
- Modify: `/data/.openclaw/workspaces/personal-assistant/TOOLS.md`

- [ ] **Step 1: Delete lines 31-71 (template scaffolding remnants)**

- [ ] **Step 2: Add `## Laptop Compute & KI-Chat Review — 2026-05-31` section mirroring Photon's TOOLS.md addition (node `endrit-laptop-wsl`, browser via `target: node, profile: user`, KI-Chat-Review-Gate rules)**

- [ ] **Step 3: Commit**

```bash
git add TOOLS.md && git commit -m "chore(tools): strip template scaffolding, add Laptop Compute section"
```

### Task D4: Trim AGENTS.md toward template baseline

**Files:**
- Modify: `/data/.openclaw/workspaces/personal-assistant/AGENTS.md`

- [ ] **Step 1: Diff against template to find redundant boilerplate**

```bash
diff /data/.openclaw/workspaces/photon/agent-factory/templates/AGENTS.md.tmpl AGENTS.md | head -100
```

- [ ] **Step 2: Move EOS-specific runtime CLI commands (lines 136-158) to TOOLS.md if not already there; remove from AGENTS.md**

- [ ] **Step 3: Keep mandates (Universal Second Brain, GitHub Auto-Push, Context7 Gate) — these are policy, not bloat**

- [ ] **Step 4: Add Laptop Compute / KI-Chat-Review reference to mandates section**

- [ ] **Step 5: Commit**

```bash
git add AGENTS.md && git commit -m "chore(agents): trim AGENTS.md, move runtime to TOOLS.md, add KI-Chat-Review mandate"
```

### Task D5: Update Photon's AGENTS.md with KI-Chat-Review-Gate

**Files:**
- Modify: `/data/.openclaw/workspaces/photon/AGENTS.md`

- [ ] **Step 1: Add a `## KI-Chat-Review-Gate` section pointing to Photon's TOOLS.md Laptop Compute section, listing when KI-Chat-Review is mandatory (Agent-MD-Writing, Architecture-Entscheidungen, Post-Push-Code-Review, neue Agent-Erstellung)**

- [ ] **Step 2: Commit (note: photon workspace, not personal-assistant)**

```bash
git -C /data/.openclaw/workspaces/photon add AGENTS.md
# photon is not a git repo at workspace level — confirm; if so, just save the file
```

### Task D6: KI-Chat-Review of Eos identity diffs

**Files:**
- Read-only consultation via browser on `endrit-laptop-wsl`

- [ ] **Step 1: Stage the post-D4 identity diff**

```bash
cd /data/.openclaw/workspaces/personal-assistant
git diff HEAD~4..HEAD -- IDENTITY.md SOUL.md AGENTS.md TOOLS.md > /tmp/eos-identity-diff.txt
```

- [ ] **Step 2: Photon opens Claude.ai in laptop browser**

Use `mcp__openclaw__browser` with `target: "node"`, `node: "endrit-laptop-wsl"`, `profile: "user"`, navigate to `https://claude.ai/new`.

- [ ] **Step 3: Paste the diff with prompt**

> "Hier sind die Eos identity files (Agent für Calendar/Tasks-Planung) nach Cleanup. Review: konsistenz, fehlende Mandates, AGENT_FACTORY-Template-Drift, bloat, redundanz."

- [ ] **Step 4: Capture Claude.ai response, decide what to integrate**

Save the response (or screenshot) to `second-brain/30-runs/2026-05-31-eos-identity-claude-review.md`.

- [ ] **Step 5: Apply concrete fixes if any → commit as `chore(identity): apply Claude.ai review feedback`**

---

## Phase E — Workspace Promotion Decision

**Goal:** Decide promote vs stay-tenant. Codex lane recommended promote. This phase is GATED on Endrit's explicit go-ahead because it has cross-system blast radius (cron rewrites, file paths, Second Brain root path).

### Task E1: Explicit gate-check with Endrit

- [ ] **Step 1: Photon presents the trade-off and the Codex-lane recommendation in chat, asks decision**

If Endrit says "stay tenant" → Phase E ends with a memory note explaining the decision.

If Endrit says "promote" → continue with E2.

### Task E2: Promote Eos (only if E1 says promote)

**Files:**
- Create: `/data/.openclaw/agents/eos/{config.json,SOUL.md,IDENTITY.md,USER.md,AGENTS.md,TOOLS.md}` per AGENT_FACTORY.md
- Move: `/data/.openclaw/workspaces/personal-assistant/` → `/data/.openclaw/workspaces/eos/`
- Modify: 7 cron entries in `/data/.openclaw/cron/jobs.json` (`sessionTarget`)
- Modify: any path references in scripts/docs

- [ ] **Step 1: Snapshot current state to backup**

```bash
cp -a /data/.openclaw/workspaces/personal-assistant /data/.openclaw/backups/personal-assistant-pre-eos-promote-$(date +%Y%m%d-%H%M%S)
```

- [ ] **Step 2: Create `agents/eos/` registration**

Follow AGENT_FACTORY.md Phase-by-phase. Reuse identity files.

- [ ] **Step 3: Move workspace dir**

```bash
mv /data/.openclaw/workspaces/personal-assistant /data/.openclaw/workspaces/eos
```

- [ ] **Step 4: Rewrite cron sessionTargets**

```bash
sed -i 's|agent:personal-assistant:|agent:eos:|g' /data/.openclaw/cron/jobs.json
```

- [ ] **Step 5: Smoke test 1 cron job manually**

```bash
EOS_DB_PATH=data/eos_v2.db .venv/bin/python -m src.eos_cli run-job daily_morning --dry-run
```

- [ ] **Step 6: Health check + commit**

---

## Phase F — Push + Account Review + Memory

**Goal:** Push all branches, KI-Chats review the GitHub state, memory + Second Brain reflect the work.

### Task F1: Push to GitHub

- [ ] **Step 1: Push branch**

```bash
cd /data/.openclaw/workspaces/personal-assistant   # or workspaces/eos if Phase E ran
GH_CONFIG_DIR=/data/.openclaw/gh-main-eos git push
```

- [ ] **Step 2: Verify on GitHub**

```bash
GH_CONFIG_DIR=/data/.openclaw/gh-main-eos gh -R endritmurati99/eos browse --no-browser
```

### Task F2: KI-Chat Review of GitHub state

- [ ] **Step 1: Build commit-range URL** (`https://github.com/endritmurati99/eos/compare/...HEAD`)

- [ ] **Step 2: Photon opens Claude.ai (laptop browser) and pastes the URL with prompt**

> "Review diesen Stand. Was wäre das nächste was du fixen würdest?"

- [ ] **Step 3: Capture response, file as `second-brain/30-runs/2026-05-31-eos-github-review-claude.md`**

- [ ] **Step 4: ChatGPT same flow for cross-validation**

### Task F3: Memory + Second Brain

- [ ] **Step 1: Write `personal-assistant/memory/2026-05-31.md` (or `eos/memory/...` post-promote)** — covering Phase 1 OAuth restore, Phase 2 fixes, key decisions.

- [ ] **Step 2: Write `personal-assistant/vault/11 Daily Notes/2026-05-31.md` end-of-day section** — what shipped, what stayed open.

- [ ] **Step 3: Write Photon's `second-brain/30-runs/2026-05-31-eos-upgrade-phase-2.md`** — full structured run log per AGENTS.md mandate.

- [ ] **Step 4: Update Photon's `MEMORY.md`** with the durable facts: Google OAuth restored 2026-05-31, Eos audit done, Phase-1 Trio workflow validated.

- [ ] **Step 5: Push Second Brain**

```bash
git -C /data/.openclaw/workspaces/photon/second-brain add -A
git -C /data/.openclaw/workspaces/photon/second-brain commit -m "session: 2026-05-31 eos upgrade phase 2"
GH_CONFIG_DIR=/data/.openclaw/gh-main-photon git -C /data/.openclaw/workspaces/photon/second-brain push
```

---

## Self-Review Notes

- **Spec coverage:** All 5 Top-Fixes from Claude Code lane are covered (B1-B4 + C1). All 5 Recommended Actions from Codex lane are covered (A1+A2 for worktree, D1-D5 for identity, F1-F2 for GitHub, E for workspace promotion, F3 for memory). Phase A handles the dirty git state. Phase D adds the Laptop Compute capability requested by Endrit on 2026-05-31.
- **No placeholders:** every step has concrete commands or code. Where the actual edit is non-trivial (denominator fix, evening_briefing wrap), the audit reports cited give exact line refs.
- **Type consistency:** `backfill_range`/`mark_status`/`mark_done` are referenced consistently. `_load_calendar_events` and `runner.run_job` match Claude-Code-lane audit.
- **Tests-first ordering:** B1 fixes the only currently-failing test before any new test is added. B2/B3/B4/C1 all write failing test first.

---

## Open Decisions Endrit Must Make Before Execution

1. **Phase E gate**: promote Eos to own workspace + agent registration, or stay tenant under `personal-assistant`?
2. **Phase A3 `GIT_STANDARD.json`**: commit, gitignore, or trash?
3. **Cron schedule reconciliation** (out of scope of this plan but related): is the live `06:00`/`20:00` schedule correct, or should it move to documented `07:00`/`22:00`? Decide before Phase B sign-off if relevant.
4. **Phase C2 Telegram wiring**: yes or skip for now?

These are decisions, not blockers — the plan can execute Phases A-D and F1+F3 even with Phase E unresolved.
