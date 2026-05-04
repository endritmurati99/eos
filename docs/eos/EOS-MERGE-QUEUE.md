# EOS Merge Queue

Status checked on 2026-05-04 UTC with `gh pr view` and `gh pr diff --name-only`.

## Current PR Map

| PR | Branch | Status | Role | Merge guidance |
| --- | --- | --- | --- | --- |
| #5 | `agent1/foundation-reconciliation` | open, mergeable | Canonical Foundation baseline | Merge first. |
| #6 | `agent1/merge-queue-ci-bootstrap` | open, mergeable | CI/smoke/queue bootstrap | Superseded by PR #12. Do not merge independently. |
| #12 | `agent2/privacy-safe-runtime-ci` | open, mergeable | Privacy-safe runtime smoke and queue hardening | Merge after PR #13 or rebase after PR #13 if needed. |
| #13 | `agent1/p0-db-runtime-recovery` | open, mergeable | P0 readonly DB recovery tooling | Merge after Foundation and before runtime live gate. |
| #1 | `eos/global-agent-rules` | open, mergeable | Superseded Foundation draft | Close or mark superseded after #5. |
| #2 | `agent1/eos-foundation-policies` | open, mergeable | Superseded Foundation draft | Close or mark superseded after #5. |
| #7 | `agent2/runtime-cli-cron-doctor` | open, mergeable | Runtime doctor | Merge only if not replaced by #12/#13 content. |
| #4 | `agent2/gmail-classifier-synthetic-tests` | open, mergeable | Gmail classifier | Rebase after runtime gates stabilize. |
| #3 | `agent3/gmail-readonly-shadow-mode` | open, mergeable | Gmail read-only shadow mode | Rebase after #4. |
| #8 | `agent1/mail-task-proposal-engine` | open, mergeable | Mail task proposal | Hold until separate audit. |
| #9 | `agent2/calendar-intelligence-v1` | open, mergeable | Calendar intelligence | Hold until separate audit. |
| #10 | `agent3/habit-journal-coach-v1` | open, mergeable | Habit journal coach | Hold until separate audit. |
| #11 | `agent3/google-platform-readiness` | draft, mergeable | Google platform readiness | Hold until separate audit and live gates. |

## Collision Matrix

### PR #6 vs PR #12

- Shared files: `.github/workflows/eos-ci.yml`, `docs/eos/EOS-MERGE-QUEUE.md`, `scripts/run_eos_smoke.sh`, `scripts/run_eos_tests.sh`.
- Different goals: PR #6 bootstraps CI, smoke, and queue documentation. PR #12 hardens the same surface with privacy-safe summaries, pytest discovery, `.gitignore` protection, runtime diagnostics, and stricter queue policy.
- Conflict risk: high. Both PRs create or replace the same gate files, and #12 intentionally changes #6 behavior.
- Decision: Option A. PR #12 replaces PR #6 fully. PR #6 should be closed or marked superseded after owner approval.

### PR #12 vs PR #13

- Shared files: none in `gh pr diff --name-only`.
- Different goals: PR #12 owns privacy-safe CI/smoke output and queue policy. PR #13 owns DB doctor, DB permission recovery tooling, and DB recovery runbook.
- Conflict risk: low at file level, medium at gate policy level because both mention `readonly_database`.
- Recommendation: merge PR #13 before the runtime live gate, then merge or rebase PR #12 so its `readonly_database` classification aligns with `scripts/eos_db_doctor.py`.

## Required Merge Order

1. Merge PR #5 Foundation Reconciliation.
2. Close or explicitly mark PR #1 and PR #2 as superseded.
3. Merge PR #13 DB Runtime Recovery.
4. Merge PR #12 Privacy-Safe Runtime Smoke and Queue, rebased after #13 if needed.
5. Merge PR #7 Runtime Doctor only if its useful content is not already replaced by #12/#13.
6. Rebase, test, and merge PR #4 Gmail Classifier.
7. Rebase PR #3 Gmail Read-only Shadow Mode on PR #4, then test and merge.
8. Keep PR #8, #9, #10, and #11 on hold until separate audit.

## Hard Gates

- `src.eos_cli` import failure.
- Syntax or compile failure.
- Real pytest failure in a changed module.
- Secrets detected in captured or printed output.
- Gmail write scope or Gmail write action detected.
- `readonly_database` in live runtime after DB recovery is claimed fixed.
- Zero tests collected in a non-doc PR.

## Soft Gates

- Missing `gog`.
- Missing `systemctl` or systemd not running in the test environment.
- Missing Google credentials.
- Gmail live E2E unverified.
- Maps live API unverified.
- Google Drive live API unverified.

## Zero Tests Policy

Docs-only PRs may classify `pytest` exit code 5 as `docs_only_no_tests` and continue with a warning.

Any non-doc PR must fail if `pytest` exits 5. CI sets `PR_CHANGED_CODE=true/false`; local runs derive the same value from `origin/main...HEAD` when possible and fail closed when the change set is unknown.

## Privacy-Safe Smoke Policy

Smoke output must be summary-only. It may print command names, pass/warning/failed status, exit code, error class, line counts, and whether sensitive output was detected internally.

Smoke output must not print task titles, calendar event titles, locations, Telegram IDs or targets, Google accounts, Gmail IDs, Gmail snippets, thread IDs, raw environment values, secrets, or sensitive absolute paths.

## DB Recovery Gate

`readonly_database` is P0. Daily, weekly, and run-job runtime are not live-ready while the SQLite write probe fails.

After PR #13 is present, the live gate is:

```bash
python3 scripts/eos_db_doctor.py
```

The result must show at least:

```text
sqlite_write_probe: success
db_writable: true
parent_writable: true
```

If `scripts/eos_db_doctor.py` is not yet on the branch, PR #13 must merge or be rebased before any runtime live-ready claim.

## Must Not Merge

- PR #1 or PR #2 independently after PR #5.
- PR #6 independently after PR #12 is accepted.
- Any branch that introduces Gmail write scopes or Gmail write actions before explicit approval.
- Any branch that prints raw smoke output from live tasks, calendar, Gmail, Telegram, credentials, or local sensitive paths.
- Runtime feature PRs #8, #9, #10, or #11 before separate audit and gate review.
