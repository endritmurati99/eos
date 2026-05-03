# EOS Merge Queue

## Current PR State

As of the Phase 0 merge queue bootstrap, the active EOS pull requests are:

| PR | Branch | Role | Merge guidance |
| --- | --- | --- | --- |
| #5 | `agent1/foundation-reconciliation` | Canonical Foundation Reconciliation | Merge first. |
| #4 | `agent2/gmail-classifier-synthetic-tests` | Gmail classifier and synthetic test corpus | Rebase after Foundation lands, then test and merge. |
| #3 | `agent3/gmail-readonly-shadow-mode` | Gmail read-only runtime and CLI dry-run | Rebase after Agent 2 lands, then test and merge. |
| #1 | `eos/global-agent-rules` | Superseded Foundation draft | Do not merge independently. |
| #2 | `agent1/eos-foundation-policies` | Superseded Foundation draft | Do not merge independently. |

No visible GitHub status checks were available when this queue was documented. Local validation remains required before every merge.

## Why PR #5 Goes First

PR #5 is the canonical Foundation baseline because it reconciles the overlapping Phase 0 documentation from PR #1 and PR #2. It preserves the required Security/Secrets Audit, global agent rules, `AGENTS.md` guidance, docs index entrypoints, roadmap, repo audit, and EOS policy set.

Merging PR #1 and PR #2 independently would reintroduce overlapping `docs/eos/**` content and can create contradictory governance text. Treat both as superseded unless the owner explicitly asks to close them.

## Merge Order

1. Merge PR #5.
2. Merge this CI bootstrap PR after PR #5, or rebase it if Foundation changes touch the same docs path.
3. Leave PR #1 and PR #2 open but superseded, or close them only with owner approval.
4. Rebase Agent 2 on `main`, run tests, and merge PR #4.
5. Rebase Agent 3 on `main`, run tests plus CLI smoke checks, and merge PR #3.
6. Run a final integration pass on `main`.

## Agent 2 Rebase

After PR #5 and the CI bootstrap are merged:

```bash
git fetch origin
git checkout agent2/gmail-classifier-synthetic-tests
git rebase origin/main
bash scripts/run_eos_tests.sh
```

Agent 2 must not change Gmail API clients, OAuth scopes, CLI routing, real Gmail data, secrets, or write actions.

## Agent 3 Rebase

After PR #4 is merged:

```bash
git fetch origin
git checkout agent3/gmail-readonly-shadow-mode
git rebase origin/main
bash scripts/run_eos_tests.sh
bash scripts/run_eos_smoke.sh
```

Agent 3 remains read-only and dry-run only. No Gmail label, archive, delete, send, unsubscribe, or broad mailbox modify behavior may be introduced in Round 1.

## Test Requirement

Before merging any implementation PR:

```bash
bash scripts/run_eos_tests.sh
bash scripts/run_eos_smoke.sh
git diff --check
```

If a check fails, report whether the cause is a code defect, missing secrets, missing local dependency, package/dependency conflict, or environment issue. Do not mark a PR as merge-ready when tests are clearly red because of a code defect.

## Blockers

- PR #5 is not merged.
- PR #1 or PR #2 is merged independently after PR #5.
- Agent 2 or Agent 3 cannot rebase cleanly on `main`.
- Any branch introduces Gmail write scopes or real Gmail write actions.
- Tests fail because of a code defect rather than no tests collected, missing secrets, or a degraded local integration.
- New tracked changes appear under `.env*`, `data/**`, credentials, tokens, `src/**`, or `tests/**` outside the explicit PR ownership.
