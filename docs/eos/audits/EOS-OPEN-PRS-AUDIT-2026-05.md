# EOS Open PR Audit - 2026-05

Audit date: 2026-05-04.

Open PR count:

```text
17
```

Source commands:

```bash
gh pr list --repo endritmurati99/eos --state open --limit 50
for pr in $(seq 1 17); do
  gh pr view "$pr" --repo endritmurati99/eos --json number,title,state,isDraft,mergeable,headRefName,baseRefName,url 2>/dev/null || true
done
```

## Classification Summary

```text
READY_CANDIDATE: #5
NEEDS_FIX: #13, #14, #17
SUPERSEDED: #1, #2, #3, #4, #6, #12
HOLD: #7, #8, #9, #10, #15, #16
DRAFT: #11
BLOCKED: none
```

## PR Details

| PR | Title | Status | Classification | Merge allowed now | Depends on | Supersedes | Superseded by |
| --- | --- | --- | --- | --- | --- | --- | --- |
| #1 | Add EOS phase 0 docs and global agent rules | Open, mergeable | `SUPERSEDED` | No | None | None | #5 |
| #2 | Add EOS foundation policies and roadmap | Open, mergeable | `SUPERSEDED` | No | None | None | #5 |
| #3 | Implement Gmail read-only shadow mode | Open, mergeable | `SUPERSEDED` | No | None | None | #17 |
| #4 | Implement Gmail classifier synthetic test corpus | Open, mergeable | `SUPERSEDED` | No | None | None | #17 |
| #5 | Reconcile EOS foundation governance docs | Open, mergeable | `READY_CANDIDATE` | Yes, after basic docs check | None | #1, #2 | None |
| #6 | Add EOS merge queue and CI bootstrap | Open, mergeable | `SUPERSEDED` | No | None | None | #14 |
| #7 | Add EOS runtime CLI cron doctor | Open, mergeable | `HOLD` | No | #14 decision | None | None |
| #8 | Add EOS mail to task proposal engine | Open, mergeable | `HOLD` | No | #17 | None | None |
| #9 | Add EOS calendar intelligence v1 | Open, mergeable | `HOLD` | No | #14 | None | None |
| #10 | Add EOS habit journal coach v1 | Open, mergeable | `HOLD` | No | #14 | None | None |
| #11 | Add EOS Google Platform and Maps travel time readiness | Draft, mergeable | `DRAFT` | No | #14, #16, live-readiness policy | None | None |
| #12 | Harden EOS privacy-safe runtime smoke and merge queue | Open, mergeable | `SUPERSEDED` | No | None | None | #14 |
| #13 | Add EOS DB runtime recovery tooling | Open, mergeable | `NEEDS_FIX` | No | #5 preferred first | None | None |
| #14 | Reconcile EOS merge queue and runtime gates | Open, mergeable | `NEEDS_FIX` | No | #13, runtime review | #6, #12 partly | None |
| #15 | Add EOS local dev environment doctor | Open, mergeable | `HOLD` | No | #14 preferred first | None | None |
| #16 | Add EOS security retention and Google live readiness gates | Open, mergeable | `HOLD` | No | #14 | None | None |
| #17 | Integrate Gmail classifier with read-only digest | Open, mergeable | `NEEDS_FIX` | No | #14, #16 preferred first | #3, #4 | None |

## Reasons

### #1

Classification: `SUPERSEDED`.

Reason: Foundation baseline is folded into #5. Do not merge independently.

### #2

Classification: `SUPERSEDED`.

Reason: Foundation policies and roadmap are folded into #5. Do not merge independently.

### #3

Classification: `SUPERSEDED`.

Reason: Gmail read-only shadow mode is integrated into #17. Do not merge unless #17 is abandoned.

### #4

Classification: `SUPERSEDED`.

Reason: Gmail classifier synthetic corpus is integrated into #17. Do not merge unless #17 is abandoned.

### #5

Classification: `READY_CANDIDATE`.

Reason: It reconciles the foundation governance PRs and should be first in the controlled queue after a basic docs check.

### #6

Classification: `SUPERSEDED`.

Reason: Runtime merge-queue and CI bootstrap work is likely superseded by #14.

### #7

Classification: `HOLD`.

Reason: It contains runtime CLI/cron doctor content not fully represented in #14. Reassess after #14.

### #8

Classification: `HOLD`.

Reason: Mail-to-task proposal work should wait for canonical Gmail phase 1 in #17.

### #9

Classification: `HOLD`.

Reason: Calendar intelligence should wait for runtime gates.

### #10

Classification: `HOLD`.

Reason: Habit journal coach should wait for runtime gates.

### #11

Classification: `DRAFT`.

Reason: Keep as draft/hold until runtime gates, security retention gates, and Google live-readiness policy are merged.

### #12

Classification: `SUPERSEDED`.

Reason: Privacy-safe runtime CI path is covered by the #14 runtime gate reconciliation for release purposes.

### #13

Classification: `NEEDS_FIX`.

Reason: Runtime DB/path recovery is a P0 candidate and should be reviewed before merge.

### #14

Classification: `NEEDS_FIX`.

Reason: Runtime gates and CI are central to release safety and need explicit runtime review before merge.

### #15

Classification: `HOLD`.

Reason: Local development environment support is useful but optional behind runtime P0s.

### #16

Classification: `HOLD`.

Reason: Security retention and Google live readiness should follow the runtime gate baseline.

### #17

Classification: `NEEDS_FIX`.

Reason: Canonical Gmail phase 1 candidate supersedes #3/#4 but should wait for runtime/security gates and final review.

## Comment Plan

Add or confirm hygiene comments for:

```text
#1, #2, #3, #4, #6, #11
```

Do not close PRs without explicit user approval.
