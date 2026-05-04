# EOS Merge Queue Audit 2026-05

Audit date: 2026-05-04 UTC.

## PR Status

| PR | Finding |
| --- | --- |
| #5 | Canonical Foundation. Merge first. |
| #1/#2 | Superseded by #5. Mark or close after owner approval. |
| #13 | Runtime DB + path fix. Required before live-ready runtime claims. |
| #14 | Canonical runtime gates / CI / privacy-safe smoke branch. |
| #6 | Superseded by #14. Do not merge independently. |
| #12 | Content reconciled into #14. Do not merge independently unless #14 is abandoned. |
| #7 | Likely superseded by #13/#14/#15. Requires explicit owner review before merge. |
| #3/#4 | Superseded by #17 integrated Gmail path. |
| #8/#9/#10 | Feature PRs held until runtime gates are stable. |
| #11 | Draft Google platform PR. Last in queue after draft removal and gate review. |

## Reconciliation Decision

PR #6 and PR #12 conflict with PR #14 on CI, smoke, tests, and queue policy. PR #14 is the canonical branch because it owns final runtime-gate policy and merge-queue documentation.

Allowed #12 content to reconcile into #14:

- privacy-safe smoke summary behavior
- `verify_*.py` pytest discovery
- no-tests-collected guard
- `.gitignore` hardening
- CLI and cron smoke wrappers under `scripts/`

Excluded #12 content:

- runtime doctor implementation and tests outside the requested ownership
- feature-module or DB permission changes

## Final Merge Order

1. PR #5 Foundation.
2. PR #1/#2 superseded close or mark.
3. PR #13 Runtime DB + path fix.
4. PR #14 Runtime gates / CI / safe smoke.
5. PR #15 local dev env doctor optional.
6. PR #16 security retention gates.
7. PR #17 Gmail integrated path, replacing #3/#4.
8. PR #8 Mail to Task Proposal.
9. PR #9 Calendar Intelligence.
10. PR #10 Habit Journal Coach.
11. PR #11 Google Platform/Maps last, after draft removal.

## Gate Audit

Hard gates:

- syntax or import failure
- real pytest failure
- secret scan hit
- raw sensitive smoke output detected
- Gmail write scope or write action detected
- code PR with zero tests collected
- post-recovery `readonly_database`

Soft gates:

- missing `gog`
- missing `systemctl`
- missing credentials
- provider auth required
- live Gmail, Maps, or Drive verification pending
- pre-recovery `readonly_database`

## Verification Policy

Required commands for this reconciliation branch:

```bash
git diff --check
python3 scripts/eos_safe_smoke_summary.py --self-test || true
bash scripts/run_eos_tests.sh || true
bash scripts/run_eos_smoke.sh || true
python3 -m pytest -q || true
```

Failures must be classified as:

```text
readonly_database
missing_gog
missing_systemctl
missing_python_alias
missing_credentials
provider_auth_required
environment_issue
real_code_failure
unknown
```

Private data in smoke output is a blocker.

## Current Verification Finding

With `verify_*.py` discovery enabled, the current runtime branch exposes existing failures outside this reconciliation scope:

```text
tests/verify_dispatch_layer.py::test_dispatch_energy_checkin
tests/verify_dispatch_layer.py::test_cli_dispatch_handle_json
tests/verify_dispatch_layer.py::test_cli_energy_today_empty
tests/verify_dispatch_layer.py::test_cli_confirmations_list_empty
tests/verify_intake_engine.py::test_supported_intents_complete
```

Classification: `real_code_failure`. This reconciliation branch must not hide these failures with `|| true` in CI or by weakening pytest discovery.
