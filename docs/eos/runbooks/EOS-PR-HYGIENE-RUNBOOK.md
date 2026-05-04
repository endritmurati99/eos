# EOS PR Hygiene Runbook

## Purpose

This runbook keeps the EOS release queue reviewable while multiple agents produce parallel PRs.

The target is a controlled queue with explicit blockers, holds, and superseded PRs.

## Active PR Limit

Keep at most four active implementation PRs at the same time.

Active implementation PRs are PRs that are not:

```text
- superseded
- draft
- explicit hold
- documentation-only support
- blocked by the current runtime gate
```

When the queue exceeds that limit, classify PRs before starting new work.

## Current Feature Freeze

Do not start new feature PRs until these are stable:

```text
#14 runtime gates / CI / safe smoke
#16 security retention and Google live readiness
#17 Gmail canonical phase 1
```

Allowed exceptions:

```text
- release coordination docs
- audit docs
- PR hygiene comments
- emergency fixes explicitly requested by the user
```

## Superseded PRs

Superseded PRs must not merge independently.

For a superseded PR:

```text
1. Confirm the superseding PR contains the useful scope.
2. Add or confirm a PR comment explaining the superseding PR.
3. Mark it as no-merge in the release queue.
4. Close only after explicit user approval.
```

Current do-not-merge superseded set:

```text
#1, #2, #3, #4, #6, #7
```

#12 is likely superseded by #14. Keep it open only if #14 is missing useful #12 content.

## Runtime Gate Rule

#14 is the current blocker until conflicts and tests are fixed.

Do not promote #16 until #14 is stable.

Do not promote #17 until #14 and #16 are stable.

Do not promote feature PRs before #14/#16/#17 are stable.

## Draft And Hold Rules

Draft PR #11 remains draft.

Use `HOLD` when a PR may remain useful but is not safe to merge now.

Use `NEEDS_FIX` when a PR is a candidate but requires rebase, conflict resolution, test repair, or audit updates before merge.

Use `READY_AFTER_GATES` only for PRs that may become candidates after #14/#16 stabilize.

## PR Requirements

Every PR must state:

```text
- tests run
- no-tests policy if tests are not relevant
- secrets policy impact
- whether feature code changed
- release queue classification
```

No PR should include secrets, tokens, `.env` contents, credential files, or runtime data.

## Merge Queue Checklist

Before merging any PR:

```text
- Confirm it is not superseded.
- Confirm it is not draft.
- Confirm it is not hold.
- Confirm it is not blocked by #14/#16/#17.
- Confirm dependencies are merged or intentionally waived.
- Confirm tests or no-tests rationale are documented.
- Confirm secrets policy is satisfied.
- Confirm no unrelated files are in the diff.
```

## Agent 5 Review Gate

Review-only Agent 5 must rerun after #14, #16, and #17 stabilize.

Do not treat the feature queue as ready until that review-only pass confirms the runtime gate, security gate, and Gmail read-only integration are coherent.

## Final Review Prep

For each control audit:

```bash
gh pr list --repo endritmurati99/eos --state open --limit 50
for pr in $(seq 1 18); do
  gh pr view "$pr" --repo endritmurati99/eos --json number,title,state,isDraft,mergeable,headRefName,url 2>/dev/null || true
done
```

Then update:

```text
docs/eos/EOS-RELEASE-CANDIDATE-QUEUE.md
docs/eos/audits/EOS-OPEN-PRS-AUDIT-2026-05.md
```

## What Not To Do

Do not:

```text
- close superseded PRs without explicit user approval
- merge superseded PRs
- merge feature PRs before #14/#16/#17 are stable
- remove #11 draft status before audit
- treat MERGEABLE as READY
- push feature fixes from release hygiene branches
- change src, tests, scripts, .github, data, credentials, tokens, or env files from PR hygiene work
```
