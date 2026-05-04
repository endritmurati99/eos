# EOS Release Candidate Queue

## 1. Current PR Status

Audit date: 2026-05-04.

Current open PR count:

```text
17
```

PR #5 has already merged and remains the completed Foundation baseline for this queue.

## 2. Release Queue Classification

| PR | Title | Branch | State | Classification |
| --- | --- | --- | --- | --- |
| #1 | Add EOS phase 0 docs and global agent rules | `eos/global-agent-rules` | Open | `SUPERSEDED` |
| #2 | Add EOS foundation policies and roadmap | `agent1/eos-foundation-policies` | Open | `SUPERSEDED` |
| #3 | Implement Gmail read-only shadow mode | `agent3/gmail-readonly-shadow-mode` | Open | `SUPERSEDED` |
| #4 | Implement Gmail classifier synthetic test corpus | `agent2/gmail-classifier-synthetic-tests` | Open | `SUPERSEDED` |
| #5 | Reconcile EOS foundation governance docs | `agent1/foundation-reconciliation` | Merged | `READY_DONE` |
| #6 | Add EOS merge queue and CI bootstrap | `agent1/merge-queue-ci-bootstrap` | Open | `SUPERSEDED` |
| #7 | Add EOS runtime CLI cron doctor | `agent2/runtime-cli-cron-doctor` | Open | `SUPERSEDED` |
| #8 | Add EOS mail to task proposal engine | `agent1/mail-task-proposal-engine` | Open | `HOLD` |
| #9 | Add EOS calendar intelligence v1 | `agent2/calendar-intelligence-v1` | Open | `HOLD` |
| #10 | Add EOS habit journal coach v1 | `agent3/habit-journal-coach-v1` | Open | `HOLD` |
| #11 | Add EOS Google Platform and Maps travel time readiness | `agent3/google-platform-readiness` | Draft | `HOLD` |
| #12 | Harden EOS privacy-safe runtime smoke and merge queue | `agent2/privacy-safe-runtime-ci` | Open | `SUPERSEDED` |
| #13 | Add EOS DB runtime recovery tooling | `agent1/p0-db-runtime-recovery` | Open | `READY` |
| #14 | Reconcile EOS merge queue and runtime gates | `agent1/merge-queue-runtime-gates` | Open | `READY` |
| #15 | Add EOS local dev environment doctor | `agent4/local-dev-environment-doctor` | Open | `HOLD` |
| #16 | Add EOS security retention and Google live readiness gates | `agent3/security-retention-google-live-gates` | Open | `READY` |
| #17 | Integrate Gmail classifier with read-only digest | `agent2/gmail-pr3-pr4-integration` | Open | `READY` |
| #18 | Add EOS release candidate PR cleanup docs | `agent4/release-candidate-cleanup` | Open | `READY` |

## 3. Active Stabilization Sequence

1. #5 Foundation: merged, complete.
2. #13 Runtime DB/path fix.
3. #14 Runtime gates / CI / safe smoke.
4. #16 Security retention/live gates.
5. #17 Gmail Phase 1 canonical integration.
6. #18 Release candidate cleanup docs.

No feature PR should bypass this stabilization sequence.

## 4. Superseded PRs

Do not merge these independently:

| PR | Superseded by | Reason |
| --- | --- | --- |
| #1 | #5 | #5 is the merged Foundation baseline. |
| #2 | #5 | #5 is the merged Foundation baseline. |
| #3 | #17 | #17 integrates Gmail read-only shadow mode into the canonical Gmail Phase 1 path. |
| #4 | #17 | #17 integrates the Gmail classifier corpus into the canonical Gmail Phase 1 path. |
| #6 | #14 | #14 owns runtime gates and CI reconciliation. |
| #7 | #14 | #14 owns the release runtime-gate path; runtime-doctor work should not merge independently. |
| #12 | #14 | #14 contains the release-gate CI workflow, pytest discovery, privacy-safe smoke, `.gitignore` hardening, and merge queue content. |

#12 still has runtime-doctor-specific files, but those are not part of the canonical release-gate strand.

## 5. Hold PRs

| PR | Hold reason |
| --- | --- |
| #8 | Hold until Gmail Phase 1 and runtime gates land. |
| #9 | Hold until runtime gates land. |
| #10 | Hold until runtime gates land. |
| #11 | Draft Google Platform/Maps work; keep last after draft removal and live-gate review. |
| #15 | Local development support; optional behind the core stabilization path. |

## 6. What Not To Do

Do not merge or close superseded PRs without explicit owner approval:

```text
#1, #2, #3, #4, #6, #7, #12
```

Do not merge held PRs before the stabilization sequence:

```text
#8, #9, #10, #11, #15
```

## 7. Next Control Checklist

Before the next release-candidate review:

```text
- Confirm superseded PR comments exist.
- Confirm #13, #14, #16, #17, and #18 are still mergeable or document blockers.
- Keep #8, #9, #10, #11, and #15 on hold.
- Do not close superseded PRs unless the owner explicitly authorizes closure.
- Verify no feature PR bypasses runtime gates.
```
