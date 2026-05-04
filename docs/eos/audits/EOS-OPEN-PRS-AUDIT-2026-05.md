# EOS Open PR Audit - 2026-05

Audit date: 2026-05-04.

## Current Open PRs

Current open PR count before merging #18:

```text
13
```

Merged stabilization PRs:

```text
#5, #13, #19, #14, #16, #17
```

Source commands:

```bash
gh pr list --repo endritmurati99/eos --state open --limit 50
for pr in $(seq 1 19); do
  gh pr view "$pr" --repo endritmurati99/eos --json number,title,state,isDraft,mergeable,headRefName,url 2>/dev/null || true
done
```

## Classification Summary

```text
MERGED: #5, #13, #19, #14, #16, #17
READY_AFTER_DOC_REFRESH: #18
HOLD: #8, #9, #10, #15
HOLD_DRAFT: #11
SUPERSEDED: #1, #2, #3, #4, #6, #7, #12
```

## PR Details

| PR | Title | Classification | Reason | Superseded by | Should merge now |
| --- | --- | --- | --- | --- | --- |
| #1 | Add EOS phase 0 docs and global agent rules | `SUPERSEDED` | #5 is merged and contains the foundation baseline. | #5 | No |
| #2 | Add EOS foundation policies and roadmap | `SUPERSEDED` | #5 is merged and contains the foundation policy/roadmap baseline. | #5 | No |
| #3 | Implement Gmail read-only shadow mode | `SUPERSEDED` | #17 is merged as canonical Gmail phase 1. | #17 | No |
| #4 | Implement Gmail classifier synthetic test corpus | `SUPERSEDED` | #17 is merged and contains classifier plus synthetic corpus. | #17 | No |
| #5 | Reconcile EOS foundation governance docs | `MERGED` | Foundation reconciliation landed. | None | No |
| #6 | Add EOS merge queue and CI bootstrap | `SUPERSEDED` | #14 is merged and owns runtime gates, CI, and queue reconciliation. | #14 | No |
| #7 | Add EOS runtime CLI cron doctor | `SUPERSEDED` | #14 is merged and owns runtime gate smoke/doctor coverage. | #14 | No |
| #8 | Add EOS mail to task proposal engine | `HOLD` | Feature PR; requires separate audit after P0 stabilization. | None | No |
| #9 | Add EOS calendar intelligence v1 | `HOLD` | Feature PR; requires separate audit. | None | No |
| #10 | Add EOS habit journal coach v1 | `HOLD` | Feature PR; requires separate audit. | None | No |
| #11 | Add EOS Google Platform and Maps travel time readiness | `HOLD_DRAFT` | Draft and requires separate Google live-readiness audit. | None | No |
| #12 | Harden EOS privacy-safe runtime smoke and merge queue | `SUPERSEDED` | #14 is merged and covers privacy-safe smoke plus queue hardening. | #14 | No |
| #13 | Add EOS DB runtime recovery tooling | `MERGED` | Runtime DB recovery tooling landed. | None | No |
| #14 | Reconcile EOS merge queue and runtime gates | `MERGED` | Runtime gates, CI, pytest discovery, and safe smoke landed. | None | No |
| #15 | Add EOS local dev environment doctor | `HOLD` | Optional local support; outside P0 merge chain. | None | No |
| #16 | Add EOS security retention and Google live readiness gates | `MERGED` | Security retention and live-readiness gates landed. | None | No |
| #17 | Integrate Gmail classifier with read-only digest | `MERGED` | Gmail read-only integration landed. | None | No |
| #18 | Add EOS release candidate PR cleanup docs | `READY_AFTER_DOC_REFRESH` | This PR refreshes queue and audit docs after #14/#16/#17. | None | Yes, after tests |
| #19 | Fix P0 live risk blockers before Telegram smoke | `MERGED` | Runtime data cleanup and Google Tasks default false landed. | None | No |

## Control Notes

#18 is the only remaining P0 stabilization merge candidate.

Feature PRs #8, #9, and #10 remain hold. #11 remains draft. #15 remains optional hold.

Superseded PRs #1, #2, #3, #4, #6, #7, and #12 should be closed or marked do-not-merge after #18.

Live E2E is not proven by this audit.
