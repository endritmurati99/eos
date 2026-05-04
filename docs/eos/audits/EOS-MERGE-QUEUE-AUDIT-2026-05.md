# EOS Merge Queue Audit 2026-05

Audit date: 2026-05-04 UTC.

## PR Status

| PR | Title | Status | Mergeability | Finding |
| --- | --- | --- | --- | --- |
| #5 | Reconcile EOS foundation governance docs | open | mergeable | Canonical Foundation base. Merge first. |
| #6 | Add EOS merge queue and CI bootstrap | open | mergeable | Superseded by #12. Do not merge independently. |
| #12 | Harden EOS privacy-safe runtime smoke and merge queue | open | mergeable | Preferred CI/smoke hardening branch. |
| #13 | Add EOS DB runtime recovery tooling | open | mergeable | P0 DB recovery branch. Required before runtime live gate. |
| #1 | Add EOS phase 0 docs and global agent rules | open | mergeable | Superseded by #5. |
| #2 | Add EOS foundation policies and roadmap | open | mergeable | Superseded by #5. |

## Collision Matrix

### PR #6 vs PR #12

- Shared files: `.github/workflows/eos-ci.yml`, `docs/eos/EOS-MERGE-QUEUE.md`, `scripts/run_eos_smoke.sh`, `scripts/run_eos_tests.sh`.
- Different goals: #6 creates bootstrap CI and smoke. #12 hardens the same files with privacy-safe smoke, stricter pytest behavior, discovery config, gitignore hardening, and updated queue policy.
- Conflict risk: high.
- Recommendation: choose Option A. PR #12 replaces PR #6; close or mark #6 superseded after owner approval.

### PR #12 vs PR #13

- Shared files: none reported by `gh pr diff --name-only`.
- Different goals: #12 is runtime smoke and CI safety. #13 is DB writeability diagnosis and recovery.
- Conflict risk: low file conflict, medium policy dependency.
- Recommendation: PR #13 must be merged or rebased into the live-gate base before runtime live readiness is claimed. PR #12 should keep `readonly_database` classification aligned with the DB doctor.

## Recommended Merge Order

1. PR #5 Foundation.
2. Mark or close PR #1/#2 as superseded.
3. PR #13 DB Runtime Recovery.
4. PR #12 Privacy-Safe Runtime Smoke and Queue.
5. PR #7 Runtime Doctor only if not replaced by #12/#13.
6. PR #4 Gmail Classifier.
7. PR #3 Gmail Read-only after rebase on #4.
8. PR #8/#9/#10/#11 only after separate audit.

This is better than merging #6 before #12 because #12 intentionally replaces #6 gate behavior and removes the main smoke-gating weakness from the bootstrap branch.

## Gate Audit

Hard gates defined:

- `src.eos_cli` import failure.
- Syntax or compile failure.
- Real pytest failure in a changed module.
- Secret output.
- Gmail write scope or action.
- Post-recovery `readonly_database`.
- Zero tests collected in non-doc PRs.

Soft gates defined:

- Missing `gog`.
- Missing `systemctl`.
- Missing Google credentials.
- Gmail live E2E unverified.
- Maps live API unverified.
- Google Drive live API unverified.

## Unresolved Blockers

- PR #13 must land before the DB recovery gate can be executed from `main`.
- PR #6 remains open until explicitly closed or marked superseded.
- PR #1/#2 remain open until explicitly closed or marked superseded.
- PR #8/#9/#10/#11 need separate audits before merge.
- Runtime is not live-ready if `python3 scripts/eos_db_doctor.py` does not report `sqlite_write_probe: success`, `db_writable: true`, and `parent_writable: true`.
- Current full pytest discovery exposes existing Runtime/Dispatch/Intake failures that are outside this reconciliation branch:
  `tests/verify_dispatch_layer.py::test_dispatch_energy_checkin`,
  `tests/verify_dispatch_layer.py::test_cli_dispatch_handle_json`,
  `tests/verify_dispatch_layer.py::test_cli_energy_today_empty`,
  `tests/verify_dispatch_layer.py::test_cli_confirmations_list_empty`,
  and `tests/verify_intake_engine.py::test_supported_intents_complete`.
- In shallow local clones such as `/docker/eos-agent1-runtime-gates`, `src.runtime` can raise `IndexError: 2` while resolving `WORKSPACE_ROOT.parents[2]`; classify that local result as `environment_issue` unless reproduced in the normal OpenClaw workspace path or GitHub Actions path.

## Verification Policy

Required commands for this reconciliation branch:

```bash
git diff --check
bash scripts/run_eos_tests.sh || true
bash scripts/run_eos_smoke.sh || true
python3 -m pytest -q || true
```

Failures must be classified as one of:

- `docs_only_no_tests`
- `code_no_tests_collected`
- `readonly_database`
- `missing_dependency`
- `environment_issue`
- `real_code_failure`
