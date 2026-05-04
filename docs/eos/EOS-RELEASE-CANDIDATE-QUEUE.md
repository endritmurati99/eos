# EOS Release Candidate Queue

## 1. Current Open PRs

Audit date: 2026-05-04.

Current open PR count:

```text
17
```

Open PRs:

| PR | Title | Branch | State | Classification |
| --- | --- | --- | --- | --- |
| #1 | Add EOS phase 0 docs and global agent rules | `eos/global-agent-rules` | Open | `SUPERSEDED` |
| #2 | Add EOS foundation policies and roadmap | `agent1/eos-foundation-policies` | Open | `SUPERSEDED` |
| #3 | Implement Gmail read-only shadow mode | `agent3/gmail-readonly-shadow-mode` | Open | `SUPERSEDED` |
| #4 | Implement Gmail classifier synthetic test corpus | `agent2/gmail-classifier-synthetic-tests` | Open | `SUPERSEDED` |
| #5 | Reconcile EOS foundation governance docs | `agent1/foundation-reconciliation` | Open | `READY_CANDIDATE` |
| #6 | Add EOS merge queue and CI bootstrap | `agent1/merge-queue-ci-bootstrap` | Open | `SUPERSEDED` |
| #7 | Add EOS runtime CLI cron doctor | `agent2/runtime-cli-cron-doctor` | Open | `HOLD` |
| #8 | Add EOS mail to task proposal engine | `agent1/mail-task-proposal-engine` | Open | `HOLD` |
| #9 | Add EOS calendar intelligence v1 | `agent2/calendar-intelligence-v1` | Open | `HOLD` |
| #10 | Add EOS habit journal coach v1 | `agent3/habit-journal-coach-v1` | Open | `HOLD` |
| #11 | Add EOS Google Platform and Maps travel time readiness | `agent3/google-platform-readiness` | Draft | `DRAFT` |
| #12 | Harden EOS privacy-safe runtime smoke and merge queue | `agent2/privacy-safe-runtime-ci` | Open | `SUPERSEDED` |
| #13 | Add EOS DB runtime recovery tooling | `agent1/p0-db-runtime-recovery` | Open | `NEEDS_FIX` |
| #14 | Reconcile EOS merge queue and runtime gates | `agent1/merge-queue-runtime-gates` | Open | `NEEDS_FIX` |
| #15 | Add EOS local dev environment doctor | `agent4/local-dev-environment-doctor` | Open | `HOLD` |
| #16 | Add EOS security retention and Google live readiness gates | `agent3/security-retention-google-live-gates` | Open | `HOLD` |
| #17 | Integrate Gmail classifier with read-only digest | `agent2/gmail-pr3-pr4-integration` | Open | `NEEDS_FIX` |

All open PRs reported `MERGEABLE` at audit time. Queue classification still controls release readiness.

## 2. Superseded PRs

Do not merge these independently:

| PR | Superseded by | Reason |
| --- | --- | --- |
| #1 | #5 | #5 reconciles the foundation/global-agent-rule baseline. |
| #2 | #5 | #5 reconciles the foundation policies and roadmap content. |
| #3 | #17 | #17 integrates Gmail read-only shadow mode into the canonical Gmail phase 1 branch. |
| #4 | #17 | #17 integrates the synthetic classifier corpus into the canonical Gmail phase 1 branch. |
| #6 | #14 | #14 is the runtime gate and merge-queue reconciliation candidate. |
| #12 | #14 | #14 owns the runtime gate path for release gating. |

#7 remains `HOLD`, not `SUPERSEDED`, because it contains runtime CLI/cron doctor work that is not fully represented in #14.

## 3. Runtime P0s

Runtime P0 queue:

1. #13 Runtime DB/path recovery.
2. #14 Runtime gates, CI, and safe smoke.
3. #16 Security retention and Google live-readiness gates after #14.

No feature PR should merge before the runtime P0 path is green.

## 4. Candidate Merge Order

1. #5 Foundation.
2. #13 Runtime DB/path fix.
3. #14 Runtime gates / CI / safe smoke.
4. #15 optional local dev env doctor.
5. #16 security retention gates.
6. #17 Gmail canonical phase 1.
7. #8 Mail to Task Proposal.
8. #9 Calendar Intelligence.
9. #10 Habit Journal Coach.
10. #11 Google Platform/Maps only after draft removal.

## 5. Hold PRs

| PR | Hold reason |
| --- | --- |
| #7 | Keep until #14 is merged, then decide whether the runtime CLI/cron doctor content should be rebased, cherry-picked, or closed. |
| #8 | Hold until #17 Gmail canonical phase 1 lands. |
| #9 | Hold until runtime gates land. |
| #10 | Hold until runtime gates land. |
| #15 | Local development support; optional after core runtime P0s. |
| #16 | Hold until runtime gates are resolved, then promote to security/live-readiness candidate. |

## 6. Draft PRs

| PR | Draft reason |
| --- | --- |
| #11 | Google Platform/Maps readiness stays draft/hold until runtime gates, security retention gates, and Google live-readiness policy are merged. |

## 7. What Not To Merge

Do not merge:

```text
#1, #2, #3, #4, #6, #12
```

Do not merge feature PRs before runtime gates:

```text
#8, #9, #10, #11
```

Do not close any superseded PR until the user explicitly authorizes closures.

## 8. Next Control Audit Checklist

Before the final release-candidate review:

```text
- Refresh open PR list with gh pr list --repo endritmurati99/eos --state open --limit 50.
- Confirm superseded PR comments exist.
- Confirm #5 has basic docs review and is still mergeable.
- Review #13 and #14 for runtime gate readiness.
- Decide whether #7 content is needed after #14.
- Promote #16 only after #14 is settled.
- Promote #17 only after runtime gates are settled.
- Keep #11 draft until policy and live-readiness gates are merged.
- Verify no feature PR bypasses runtime P0s.
```
