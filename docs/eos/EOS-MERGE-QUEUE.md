# EOS Merge Queue

## Current Control Status

Control status: `FIX_BEFORE_LIVE`.

The runtime now has a P0 blocker that must be resolved before Gmail, Maps, Drive, or broader Google Workspace work is treated as live-ready:

```text
attempt to write a readonly database
```

Observed DB state:

```text
data/eos_v2.db root:root -rw-r--r--
```

This branch does not change DB permissions. Agent 1 owns DB Runtime Recovery. Until that lands, smoke/CI must classify the condition as `readonly_database` and must not print raw runtime output.

## Active Pull Requests

| PR | Branch | Role | Merge guidance |
| --- | --- | --- | --- |
| #5 | `agent1/foundation-reconciliation` | Canonical Foundation Reconciliation | Merge after DB Runtime Recovery is understood and reconciled. |
| #6 | `agent1/merge-queue-ci-bootstrap` | Merge Queue + CI Bootstrap | Rebase or supersede with privacy-safe smoke changes before merge. |
| #7 | `agent2/runtime-cli-cron-doctor` | Runtime CLI/Cron Doctor | Rebase or supersede with redaction and DB error classification before merge. |
| #4 | `agent2/gmail-classifier-synthetic-tests` | Gmail classifier and synthetic corpus | Rebase after Foundation and runtime/CI stabilization, then test and merge. |
| #3 | `agent3/gmail-readonly-shadow-mode` | Gmail read-only shadow mode | Rebase after PR #4 and resolve `src/eos_mail/__init__.py` exports. |
| #8 | `agent1/mail-task-proposal-engine` | Mail to Task Proposal | `HOLD_UNTIL_AUDITED`. |
| #9 | `agent2/calendar-intelligence-v1` | Calendar Intelligence | `HOLD_UNTIL_AUDITED`. |
| #10 | `agent3/habit-journal-coach-v1` | Habit Journal Coach | `HOLD_UNTIL_AUDITED`. |
| #1 | `eos/global-agent-rules` | Superseded Foundation draft | Do not merge independently. |
| #2 | `agent1/eos-foundation-policies` | Superseded Foundation draft | Do not merge independently. |

## Required Merge Order

0. Agent 1 DB Runtime Recovery: diagnose/fix the readonly DB runtime state or document the accepted runtime DB path.
1. Merge PR #5 Foundation Reconciliation.
2. Close or explicitly mark PR #1 and PR #2 as superseded.
3. Merge PR #6 only after privacy-safe smoke output and pytest discovery are present, or supersede it with this privacy-safe CI branch.
4. Merge PR #7 only after redaction and `readonly_database` classification are present, or supersede it with this privacy-safe CI branch.
5. Rebase and test PR #4 Gmail Classifier.
6. Rebase and test PR #3 Gmail Read-only Shadow Mode after PR #4, resolving `src/eos_mail/__init__.py` by exporting both classifier and read-only runtime groups.
7. Keep PR #8 on `HOLD_UNTIL_AUDITED`.
8. Keep PR #9 on `HOLD_UNTIL_AUDITED`.
9. Keep PR #10 on `HOLD_UNTIL_AUDITED`.
10. Start Google Workspace/Maps/Drive readiness only after runtime, DB, and privacy-safe smoke are stable.

## Test Requirement

Before merging any implementation PR:

```bash
git diff --check
python3 -m pytest -q
bash scripts/run_eos_smoke.sh
```

Smoke output must be safe to paste into CI logs. It may include command names, pass/warning/failed status, exit codes, error classes, and line counts. It must not include task titles, calendar event titles, locations, Telegram IDs or targets, Google account emails, Gmail IDs/snippets/thread IDs, raw env values, or sensitive absolute paths.

## Blocking Conditions

- `readonly_database` is unclassified or treated as a generic code failure.
- Smoke scripts print raw CLI, calendar, task, Gmail, Telegram, or environment output.
- Tests are skipped with `|| true` or pytest discovery misses `verify_*.py`.
- Any branch introduces Gmail/Drive/Maps write behavior before runtime recovery.
- New tracked changes appear under `.env*`, credentials, tokens, or live `data/**` paths without explicit owner approval.
