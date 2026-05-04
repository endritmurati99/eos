# EOS PR Hygiene Runbook

## Purpose

Keep the EOS queue reviewable after the P0 stabilization chain has landed.

This runbook does not authorize feature merges, Google live calls, Gmail writes, calendar writes, Drive downloads, Maps routes, or Telegram beta.

## Current Stabilization Baseline

Merged:

```text
#5 Foundation reconciliation
#13 DB runtime recovery
#19 P0 live-risk cleanup
#14 Runtime gates / CI / safe smoke
#16 Security retention / Google live-readiness gates
#17 Gmail read-only phase 1
```

Current document PR:

```text
#18 Release candidate cleanup docs
```

## Superseded PRs

Close or mark do-not-merge after #18:

```text
#1, #2, #3, #4, #6, #7, #12
```

Canonical replacements:

| Superseded | Replacement |
| --- | --- |
| #1 | #5 |
| #2 | #5 |
| #3 | #17 |
| #4 | #17 |
| #6 | #14 |
| #7 | #14 |
| #12 | #14 |

Suggested close comment:

```text
Closed as superseded by #<replacement>. Do not merge independently.
```

## Hold And Draft Rules

Keep open:

```text
#8 hold
#9 hold
#10 hold
#15 hold
```

Keep draft:

```text
#11
```

Do not promote hold or draft PRs without a separate audit and explicit owner decision.

## Merge Queue Checklist

Before merging any later PR:

```text
- Confirm it is not superseded.
- Confirm it is not draft.
- Confirm it is not hold.
- Confirm current main test collection is greater than zero.
- Run pytest, run_eos_tests.sh, and run_eos_smoke.sh.
- Confirm safe smoke prints no private raw output.
- Confirm tracked runtime data is absent.
- Confirm tracked secret hits are absent or documented false positives only.
- Confirm no Google live call is required.
- Confirm no Gmail/Calendar/Tasks/Drive/Maps write path is introduced.
```

## PR Requirements

Every later PR must state:

```text
- tests run
- test classification
- secrets policy impact
- runtime data impact
- live-readiness claim, if any
- whether feature code changed
- release queue classification
```

Unit, Contract, Synthetic, and Readiness evidence do not prove Live E2E.

## What Not To Do

Do not:

```text
- merge superseded PRs
- merge feature PRs during P0 stabilization
- remove #11 draft status before audit
- treat MERGEABLE as READY
- use Google/Gmail/Drive/Maps live providers without gates
- run Telegram personal smoke before final P0 gates
- commit runtime data, `.env`, credentials, tokens, logs, or DB files
- claim Live E2E without a real end-to-end test path
```

## Final Review Prep

For each control audit:

```bash
gh pr list --repo endritmurati99/eos --state open --limit 50
for pr in $(seq 1 19); do
  gh pr view "$pr" --repo endritmurati99/eos --json number,title,state,isDraft,mergeable,headRefName,url 2>/dev/null || true
done
```

Then update:

```text
docs/eos/EOS-RELEASE-CANDIDATE-QUEUE.md
docs/eos/audits/EOS-OPEN-PRS-AUDIT-2026-05.md
```
