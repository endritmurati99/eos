# EOS Open PR Audit - 2026-05

Audit date: 2026-05-04.

## Source Commands

```bash
gh pr list --repo endritmurati99/eos --state open --limit 50
for pr in $(seq 1 18); do
  gh pr view "$pr" --repo endritmurati99/eos --json number,title,state,isDraft,mergeable,headRefName,url 2>/dev/null || true
done
gh pr diff 12 --repo endritmurati99/eos --name-only
gh pr diff 14 --repo endritmurati99/eos --name-only
```

## Open PR Count

```text
17
```

PR #5 is merged and is no longer in the open PR list.

## Classification Summary

```text
READY: #5 (merged), #13, #14, #16, #17, #18
SUPERSEDED: #1, #2, #3, #4, #6, #7, #12
HOLD: #8, #9, #10, #11, #15
```

No superseded PR is authorized for closure in this pass.

## PR Details

| PR | Title | Status | Classification | Merge guidance |
| --- | --- | --- | --- | --- |
| #1 | Add EOS phase 0 docs and global agent rules | Open | `SUPERSEDED` | Do not merge independently; superseded by #5. |
| #2 | Add EOS foundation policies and roadmap | Open | `SUPERSEDED` | Do not merge independently; superseded by #5. |
| #3 | Implement Gmail read-only shadow mode | Open | `SUPERSEDED` | Do not merge independently; superseded by #17. |
| #4 | Implement Gmail classifier synthetic test corpus | Open | `SUPERSEDED` | Do not merge independently; superseded by #17. |
| #5 | Reconcile EOS foundation governance docs | Merged | `READY_DONE` | Completed Foundation baseline. |
| #6 | Add EOS merge queue and CI bootstrap | Open | `SUPERSEDED` | Do not merge independently; superseded by #14. |
| #7 | Add EOS runtime CLI cron doctor | Open | `SUPERSEDED` | Do not merge independently; release-gate path superseded by #14. |
| #8 | Add EOS mail to task proposal engine | Open | `HOLD` | Hold behind runtime gates and Gmail Phase 1. |
| #9 | Add EOS calendar intelligence v1 | Open | `HOLD` | Hold behind runtime gates. |
| #10 | Add EOS habit journal coach v1 | Open | `HOLD` | Hold behind runtime gates. |
| #11 | Add EOS Google Platform and Maps travel time readiness | Draft | `HOLD` | Keep last after draft removal and live-gate review. |
| #12 | Harden EOS privacy-safe runtime smoke and merge queue | Open | `SUPERSEDED` | Do not merge independently; release-gate content is covered by #14. |
| #13 | Add EOS DB runtime recovery tooling | Open | `READY` | Canonical Runtime DB/path fix candidate. |
| #14 | Reconcile EOS merge queue and runtime gates | Open | `READY` | Canonical runtime gates, CI, and safe smoke candidate. |
| #15 | Add EOS local dev environment doctor | Open | `HOLD` | Optional local-dev support after core stabilization. |
| #16 | Add EOS security retention and Google live readiness gates | Open | `READY` | Canonical security retention/live-gate candidate. |
| #17 | Integrate Gmail classifier with read-only digest | Open | `READY` | Canonical Gmail Phase 1 integration replacing #3/#4. |
| #18 | Add EOS release candidate PR cleanup docs | Open | `READY` | Release candidate cleanup docs and PR hygiene status. |

## PR #12 vs PR #14 Result

PR #14 contains the release-gate content required from #12:

```text
- pytest.ini with verify_*.py discovery
- privacy-safe smoke scripts
- readonly_database classification
- final merge queue
- CI workflow
- .gitignore hardening
```

PR #12 has additional runtime-doctor-specific files:

```text
scripts/eos_runtime_doctor.py
tests/verify_runtime_doctor.py
docs/eos/audits/EOS-RUNTIME-CLI-CRON-AUDIT-2026-05.md
docs/eos/audits/EOS-RUNTIME-PRIVACY-SMOKE-AUDIT-2026-05.md
docs/eos/runbooks/EOS-RUNTIME-CLI-CRON-TESTING-RUNBOOK.md
```

Decision: #12 is superseded for the release-gate queue by #14. The runtime-doctor-only content is not a reason to merge #12 independently in the release candidate path.

## Superseded Comment Status

Comments were added for:

```text
#1, #2, #3, #4, #6, #7, #12
```

No PRs were closed.

## Next Step

Keep the open PR set reduced by treating only #13, #14, #16, #17, and #18 as active READY candidates after merged #5. Hold #8, #9, #10, #11, and #15 until the stabilization path is settled.
