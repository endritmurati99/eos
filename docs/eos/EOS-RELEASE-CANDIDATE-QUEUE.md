# EOS Release Candidate Queue

Audit date: 2026-05-04.

## 1. Current State

Merged core PRs:

```text
#5 Foundation reconciliation
#13 DB runtime recovery
#19 P0 live-risk cleanup before Telegram smoke
#14 Runtime gates / CI / safe smoke
#16 Security retention / Google live gates
#17 Gmail read-only phase 1 integration
```

Current open PR count before merging this document PR:

```text
13
```

Open PRs:

| PR | Title | Branch | State | Classification |
| --- | --- | --- | --- | --- |
| #1 | Add EOS phase 0 docs and global agent rules | `eos/global-agent-rules` | Open, conflicting | `SUPERSEDED` |
| #2 | Add EOS foundation policies and roadmap | `agent1/eos-foundation-policies` | Open, conflicting | `SUPERSEDED` |
| #3 | Implement Gmail read-only shadow mode | `agent3/gmail-readonly-shadow-mode` | Open | `SUPERSEDED` |
| #4 | Implement Gmail classifier synthetic test corpus | `agent2/gmail-classifier-synthetic-tests` | Open | `SUPERSEDED` |
| #6 | Add EOS merge queue and CI bootstrap | `agent1/merge-queue-ci-bootstrap` | Open | `SUPERSEDED` |
| #7 | Add EOS runtime CLI cron doctor | `agent2/runtime-cli-cron-doctor` | Open | `SUPERSEDED` |
| #8 | Add EOS mail to task proposal engine | `agent1/mail-task-proposal-engine` | Open | `HOLD` |
| #9 | Add EOS calendar intelligence v1 | `agent2/calendar-intelligence-v1` | Open | `HOLD` |
| #10 | Add EOS habit journal coach v1 | `agent3/habit-journal-coach-v1` | Open | `HOLD` |
| #11 | Add EOS Google Platform and Maps travel time readiness | `agent3/google-platform-readiness` | Draft | `HOLD_DRAFT` |
| #12 | Harden EOS privacy-safe runtime smoke and merge queue | `agent2/privacy-safe-runtime-ci` | Open, conflicting | `SUPERSEDED` |
| #15 | Add EOS local dev environment doctor | `agent4/local-dev-environment-doctor` | Open | `HOLD` |
| #18 | Add EOS release candidate PR cleanup docs | `agent4/release-candidate-cleanup` | Open | `READY_AFTER_DOC_REFRESH` |

GitHub mergeability alone is not release verification.

## 2. Superseded PRs

Do not merge these independently:

| PR | Superseded by | Reason |
| --- | --- | --- |
| #1 | #5 | #5 is merged and contains the foundation/global-agent-rule baseline. |
| #2 | #5 | #5 is merged and contains the foundation policy/roadmap baseline. |
| #3 | #17 | #17 is merged and contains the canonical Gmail read-only phase 1 path. |
| #4 | #17 | #17 is merged and contains the classifier and synthetic corpus. |
| #6 | #14 | #14 is merged and owns runtime gates, CI, safe smoke, and queue reconciliation. |
| #7 | #14 | #14 is merged and owns the runtime gate path. |
| #12 | #14 | #14 is merged and contains the privacy-safe smoke and merge-queue hardening path. |

The current cleanup instruction authorizes closing #1, #2, #3, #4, #6, #7, and #12 as superseded after #18 merges.

## 3. Candidate Merge Order

1. #18 Release candidate cleanup docs.
2. Hold #15 until owner decides whether local-dev tooling is still needed.
3. Hold #8, #9, and #10 until separate feature audits.
4. Keep #11 draft until separate Google Platform/Maps audit.

No feature PR should merge as part of this P0 stabilization pass.

## 4. Hold PRs

| PR | Hold reason |
| --- | --- |
| #8 | Feature PR; waits for separate mail-to-task audit after Gmail read-only base is merged. |
| #9 | Feature PR; waits for separate calendar-intelligence audit. |
| #10 | Feature PR; waits for separate habit-journal audit. |
| #11 | Draft; Google Platform/Maps live readiness is not approved by P0 stabilization. |
| #15 | Local development support; optional and outside the P0 runtime merge chain. |

## 5. What Not To Merge

Do not merge superseded PRs:

```text
#1, #2, #3, #4, #6, #7, #12
```

Do not merge feature or draft PRs during this P0 pass:

```text
#8, #9, #10, #11, #15
```

## 6. Next Control Checklist

Before any later feature queue review:

```text
- Confirm #18 is merged.
- Confirm superseded PRs are closed or clearly marked do-not-merge.
- Confirm #8/#9/#10/#11/#15 remain hold or draft.
- Rerun tests and safe smoke on current main.
- Do not claim Live E2E readiness without a real end-to-end provider path.
```
