# EOS PR Hygiene Runbook

## Purpose

This runbook keeps the EOS release queue reviewable when multiple agents are producing parallel PRs.

The target is a controlled queue, not maximum open PR volume.

## Active PR Limit

Keep at most four active implementation PRs at the same time.

Active implementation PRs are PRs that are not:

```text
- superseded
- draft
- explicit hold
- documentation-only support PRs
```

When the queue exceeds that limit, classify PRs before starting new work.

## Superseded PRs

For a superseded PR:

```text
1. Confirm the superseding PR contains the useful scope.
2. Add a PR comment explaining the superseding PR.
3. Mark it as no-merge in the release queue.
4. Close only after explicit user approval.
```

Use direct comments such as:

```text
Release cleanup: superseded by PR #5. Do not merge independently.
```

## Runtime Gate Rule

Do not merge feature PRs before runtime gates.

Runtime P0 order:

```text
1. Foundation reconciliation.
2. Runtime DB/path recovery.
3. Runtime gates / CI / safe smoke.
4. Security retention and live-readiness gates.
```

Feature PRs that must wait include:

```text
- Gmail-dependent mail actions
- calendar intelligence
- habit journal coach
- Google Platform / Maps
```

## Draft And Hold Rules

Draft stays draft until audit.

Use `HOLD` when a PR may remain useful but is not safe to merge now.

Use `DRAFT` when the author explicitly marked the PR draft or the branch still needs policy, runtime, or live-readiness confirmation.

Use `NEEDS_FIX` when a PR is a candidate but requires review, update, or runtime validation before merge.

## New Branch Freeze

Do not start new feature branches until P0 runtime is green.

Allowed exceptions:

```text
- release coordination docs
- audit docs
- PR hygiene comments
- emergency fixes explicitly requested by the user
```

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
- Confirm it is not listed as SUPERSEDED.
- Confirm it is not DRAFT.
- Confirm it is not HOLD.
- Confirm dependencies are merged or intentionally waived.
- Confirm tests or no-tests rationale are documented.
- Confirm secrets policy is satisfied.
- Confirm no unrelated files are in the diff.
```

## Final Review Prep

For each control audit:

```bash
gh pr list --repo endritmurati99/eos --state open --limit 50
for pr in $(seq 1 17); do
  gh pr view "$pr" --repo endritmurati99/eos --json number,title,state,isDraft,mergeable,headRefName,baseRefName,url 2>/dev/null || true
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
- merge feature PRs before runtime gates
- treat MERGEABLE as READY
- push feature fixes from release hygiene branches
- change src, tests, scripts, .github, data, credentials, tokens, or env files from PR hygiene work
```
