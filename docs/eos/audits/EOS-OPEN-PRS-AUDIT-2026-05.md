# EOS Open PR Audit - 2026-05

Audit date: 2026-05-04.

Current open PR count:

```text
16
```

Merged since prior queue audit:

```text
#5
#13
```

Source commands:

```bash
gh pr list --repo endritmurati99/eos --state open --limit 50
for pr in $(seq 1 18); do
  gh pr view "$pr" --repo endritmurati99/eos --json number,title,state,isDraft,mergeable,headRefName,url 2>/dev/null || true
done
```

## Classification Summary

```text
MERGED: #5, #13
BLOCKED: #14
NEEDS_FIX: #16, #18
READY_AFTER_GATES: #17
HOLD: #8, #9, #10, #11, #15
SUPERSEDED: #1, #2, #3, #4, #6, #7
SUPERSEDED_IF_COVERED_BY_14: #12
```

## PR Details

| PR | Title | Classification | Reason | Depends on | Superseded by | Should merge now |
| --- | --- | --- | --- | --- | --- | --- |
| #1 | Add EOS phase 0 docs and global agent rules | `SUPERSEDED` | #5 is merged and contains the foundation baseline. | None | #5 | No |
| #2 | Add EOS foundation policies and roadmap | `SUPERSEDED` | #5 is merged and contains the foundation policy/roadmap baseline. | None | #5 | No |
| #3 | Implement Gmail read-only shadow mode | `SUPERSEDED` | #17 is the canonical Gmail phase 1 integration branch. | None | #17 | No |
| #4 | Implement Gmail classifier synthetic test corpus | `SUPERSEDED` | #17 integrates the classifier and synthetic corpus. | None | #17 | No |
| #5 | Reconcile EOS foundation governance docs | `MERGED` | Foundation reconciliation already landed. | None | None | No, already merged |
| #6 | Add EOS merge queue and CI bootstrap | `SUPERSEDED` | #14 owns the runtime-gate and merge-queue reconciliation path. | None | #14 | No |
| #7 | Add EOS runtime CLI cron doctor | `SUPERSEDED` | Current queue treats #14 as the runtime gate path. | None | #14 | No |
| #8 | Add EOS mail to task proposal engine | `HOLD` | Feature work waits for Gmail canonical phase 1. | #17 | None | No |
| #9 | Add EOS calendar intelligence v1 | `HOLD` | Feature work waits for runtime/security gate stability. | #14, #16 | None | No |
| #10 | Add EOS habit journal coach v1 | `HOLD` | Feature work waits for runtime/security gate stability. | #14, #16 | None | No |
| #11 | Add EOS Google Platform and Maps travel time readiness | `HOLD` | Draft PR; requires runtime, security, and live-readiness audit. | #14, #16, separate audit | None | No |
| #12 | Harden EOS privacy-safe runtime smoke and merge queue | `SUPERSEDED_IF_COVERED_BY_14` | Likely replaced by #14; keep open only if #14 lacks #12 content. | #14 comparison | #14 if covered | No |
| #13 | Add EOS DB runtime recovery tooling | `MERGED` | Runtime DB recovery tooling already landed. | None | None | No, already merged |
| #14 | Reconcile EOS merge queue and runtime gates | `BLOCKED` | Current release blocker; GitHub reports conflicts and tests must be green before merge. | Conflict resolution, test pass | None | No |
| #15 | Add EOS local dev environment doctor | `HOLD` | Useful local support, but not part of the runtime gate path. | #14 preferred first | None | No |
| #16 | Add EOS security retention and Google live readiness gates | `NEEDS_FIX` | Must be rebased/fixed after #14; currently conflicting. | #14 | None | No |
| #17 | Integrate Gmail classifier with read-only digest | `READY_AFTER_GATES` | Candidate after #14/#16 stabilize; do not merge before gates. | #14, #16 | None | No |
| #18 | Add EOS release candidate PR cleanup docs | `NEEDS_FIX` | Queue docs were stale and must reflect #14/#16/#17 blockers. | This docs update | None | No until this correction is reviewed |

## Control Notes

PR #14 is the active release blocker. PR #16 waits on #14. PR #17 waits on #14 and #16. Feature PRs remain hold. Superseded PRs must not merge independently.

Review-only Agent 5 should rerun after #14, #16, and #17 stabilize.
