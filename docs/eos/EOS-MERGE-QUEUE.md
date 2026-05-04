# EOS Merge Queue

Status checked on 2026-05-04 UTC with `gh pr list`, `gh pr view`, and PR diff inspection.

## Current Control Status

PR #14 is the canonical runtime-gate branch for CI, pytest discovery, privacy-safe smoke, hard/soft gate policy, and merge-queue reconciliation.

PR #6 is superseded. PR #12 content is reconciled into PR #14 and should not merge independently unless PR #14 is abandoned.

## Final Merge Order

1. PR #5 Foundation.
2. PR #1/#2 superseded close or mark.
3. PR #13 Runtime DB + path fix.
4. PR #14 Runtime gates / CI / safe smoke.
5. PR #15 local dev env doctor optional.
6. PR #16 security retention gates.
7. PR #17 Gmail integrated path, replacing #3/#4.
8. PR #8 Mail to Task Proposal.
9. PR #9 Calendar Intelligence.
10. PR #10 Habit Journal Coach.
11. PR #11 Google Platform/Maps last, after draft removal.

## Superseded PRs

| PR | Status |
| --- | --- |
| #1 | Superseded by PR #5 Foundation. Do not merge independently. |
| #2 | Superseded by PR #5 Foundation. Do not merge independently. |
| #3 | Superseded by PR #17 Gmail integrated path. Do not merge independently. |
| #4 | Superseded by PR #17 Gmail integrated path. Do not merge independently. |
| #6 | Superseded by PR #14 runtime-gates reconciliation. Do not merge independently. |
| #7 | Likely superseded by PR #13/#14/#15 runtime doctor and gate work; merge only after explicit owner review. |
| #12 | Content reconciled into PR #14. Do not merge independently unless PR #14 is abandoned. |

## PR #6/#12/#14 Decision

- PR #6 bootstraps CI and merge queue files but lacks the final privacy-safe smoke and no-tests guard behavior.
- PR #12 contributes privacy-safe smoke, pytest discovery, `.gitignore` hardening, and runtime smoke scripts.
- PR #14 is canonical because it already carries the runtime-gate policy surface and is the target for final reconciliation.

Decision: keep PR #14 as the only merge candidate for this CI/smoke/merge-queue strand, copy missing allowed PR #12 content into #14, and mark #6/#12 as superseded or held.

## Hard Gates

- Syntax or import failure.
- Real pytest failure.
- Secret scan hit.
- Raw sensitive smoke output detected in captured command output.
- Gmail write scope or Gmail write action detected.
- Code PR with zero tests collected.
- `readonly_database` after DB recovery is claimed fixed.

## Soft Gates

- Missing `gog`.
- Missing `systemctl` or systemd unavailable.
- Missing credentials.
- Provider auth required.
- Live Gmail, Maps, or Drive verification still pending.
- `readonly_database` before DB recovery is claimed fixed.

## Pytest Discovery And Zero Tests

`pytest.ini` must collect both `test_*.py` and `verify_*.py` under `tests`.

Docs-only PRs may treat pytest exit code 5 as a warning. Code/config PRs fail on exit code 5. Code paths are:

```text
src/**
tests/**
scripts/**
.github/**
```

Docs-only paths are:

```text
docs/**
README.md
AGENTS.md
```

All other changed paths fail closed for no-tests-collected handling.

## Privacy-Safe Smoke Policy

Smoke output is summary-only. It may print command name, pass/warning/fail status, exit code, error class, line counts, and detection flags.

Smoke output must not print task titles, calendar event titles, locations, Telegram IDs or targets, Google accounts, Gmail message IDs, Gmail snippets, thread IDs, raw environment values, secrets, or sensitive absolute paths.

If sensitive or secret output is detected in captured stdout/stderr, the smoke summary marks that command failed and does not print the raw output.

## Must Not Merge

- PR #1, #2, #3, #4, #6, #7, or #12 independently unless the merge queue is explicitly revised.
- PR #11 while it remains draft.
- Any PR that introduces Gmail write scopes or write actions before explicit approval.
- Any PR that prints raw smoke output from live tasks, calendar, Gmail, Telegram, credentials, environment, or sensitive local paths.
- Any PR that modifies feature modules as part of this runtime-gate reconciliation.
