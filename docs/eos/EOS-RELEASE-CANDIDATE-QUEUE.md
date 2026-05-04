# EOS Release Candidate Queue

## 1. Current Open PRs

Audit date: 2026-05-04.

Current open PR count:

```text
16
```

Merged since the previous queue audit:

```text
#5 Reconcile EOS foundation governance docs
#13 Add EOS DB runtime recovery tooling
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
| #11 | Add EOS Google Platform and Maps travel time readiness | `agent3/google-platform-readiness` | Draft | `HOLD` |
| #12 | Harden EOS privacy-safe runtime smoke and merge queue | `agent2/privacy-safe-runtime-ci` | Open, conflicting | `SUPERSEDED_IF_COVERED_BY_14` |
| #14 | Reconcile EOS merge queue and runtime gates | `agent1/merge-queue-runtime-gates` | Open, conflicting | `BLOCKED` |
| #15 | Add EOS local dev environment doctor | `agent4/local-dev-environment-doctor` | Open | `HOLD` |
| #16 | Add EOS security retention and Google live readiness gates | `agent3/security-retention-google-live-gates` | Open, conflicting | `NEEDS_FIX` |
| #17 | Integrate Gmail classifier with read-only digest | `agent2/gmail-pr3-pr4-integration` | Open | `READY_AFTER_GATES` |
| #18 | Add EOS release candidate PR cleanup docs | `agent4/release-candidate-cleanup` | Open | `NEEDS_FIX` |

Queue classification controls release readiness. GitHub mergeability alone is not enough.

## 2. Superseded PRs

Do not merge these independently:

| PR | Superseded by | Reason |
| --- | --- | --- |
| #1 | #5 | #5 is merged and contains the foundation/global-agent-rule baseline. |
| #2 | #5 | #5 is merged and contains the foundation policy/roadmap baseline. |
| #3 | #17 | #17 is the canonical Gmail phase 1 integration branch. |
| #4 | #17 | #17 integrates the Gmail classifier and synthetic corpus. |
| #6 | #14 | #14 is the runtime gate and merge-queue reconciliation candidate. |
| #7 | #14 | #14 is the runtime gate path; do not merge #7 independently. |
| #12 | #14, if fully covered | Keep #12 only if #14 is missing useful privacy-safe smoke or merge-queue content. |

Do not close superseded PRs without explicit user approval.

## 3. Runtime Gate Blockers

Current release blocker:

```text
#14 until conflicts are resolved and tests are green
```

Dependent stabilization queue:

```text
#16 needs rebase/fix after #14
#17 waits for #14 and #16
#18 needs this queue/audit correction before it can be treated as current
```

No new feature PRs should start until #14, #16, and #17 are stable.

## 4. Candidate Merge Order

1. #14 Runtime gates / CI / safe smoke after conflict resolution and tests.
2. #16 Security retention and Google live-readiness gates after #14.
3. #17 Gmail canonical phase 1 after #14/#16.
4. #18 Release queue docs after this correction is pushed and reviewed.
5. #15 optional local dev environment doctor.
6. #8 Mail to Task Proposal.
7. #9 Calendar Intelligence.
8. #10 Habit Journal Coach.
9. #11 Google Platform/Maps only after draft removal and separate audit.

## 5. Hold PRs

| PR | Hold reason |
| --- | --- |
| #8 | Hold until #17 Gmail canonical phase 1 lands. |
| #9 | Hold until runtime gates and security/live-readiness gates are stable. |
| #10 | Hold until runtime gates and security/live-readiness gates are stable. |
| #11 | Draft; hold until runtime gates, security retention gates, and Google live-readiness policy are merged. |
| #15 | Local development support; optional after the runtime gate path is stable. |

## 6. What Not To Merge

Do not merge superseded PRs:

```text
#1, #2, #3, #4, #6, #7
```

Do not merge #12 unless #14 is missing required content:

```text
#12
```

Do not merge feature PRs before #14/#16/#17 are stable:

```text
#8, #9, #10, #11
```

## 7. Next Control Audit Checklist

Before the next release-candidate review:

```text
- Refresh open PR list.
- Confirm #14 conflict resolution and test status.
- Confirm #16 is rebased after #14.
- Confirm #17 remains read-only and waits for #14/#16.
- Confirm #8/#9/#10/#11/#15 remain hold.
- Confirm superseded comments exist for #1/#2/#3/#4/#6/#7/#12.
- Rerun review-only Agent 5 after #14/#16/#17 stabilize.
```
