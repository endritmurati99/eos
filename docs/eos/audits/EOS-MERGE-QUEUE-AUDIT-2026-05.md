# EOS Merge Queue Audit 2026-05

Audit date: 2026-05-04 UTC.

## PR Status

| PR | Finding |
| --- | --- |
| #5 | Merged. Canonical Foundation baseline. |
| #1/#2 | Superseded by #5. Mark or close after owner approval. |
| #13 | Merged. Runtime DB + path fix baseline for live-ready runtime claims. |
| #14 | Open. Canonical runtime gates / CI / privacy-safe smoke branch. Must merge next. |
| #16 | Open. Security retention and Google live readiness gates. Queue after #14. |
| #17 | Open. Integrated Gmail read-only path replacing #3/#4. Queue after #16. |
| #18 | Open. Release candidate cleanup docs. Queue after #17. |
| #6 | Superseded by #14. Do not merge independently. |
| #12 | Content reconciled into #14. Do not merge independently unless #14 is abandoned. |
| #7 | Superseded by #13/#14 runtime doctor and gate work. Requires explicit owner review before any revival. |
| #3/#4 | Superseded by #17 integrated Gmail path. |
| #8/#9/#10 | Feature PRs held until separate audit after runtime gates are stable. |
| #11 | Draft Google platform PR. Hold until draft removal and separate gate review. |
| #15 | Local dev environment doctor. Hold until explicit owner decision after #14. |

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

1. PR #5 Foundation. Merged.
2. PR #13 Runtime DB + path fix. Merged.
3. PR #14 Runtime gates / CI / safe smoke.
4. PR #16 Security retention and Google live readiness gates.
5. PR #17 Gmail integrated read-only path, replacing #3/#4.
6. PR #18 Release candidate PR cleanup docs.

Held until separate audit or explicit owner decision:

- PR #8 Mail to Task Proposal.
- PR #9 Calendar Intelligence.
- PR #10 Habit Journal Coach.
- PR #11 Google Platform/Maps. Draft.
- PR #15 Local dev environment doctor.

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

With `verify_*.py` discovery enabled, the previous runtime-gate audit exposed these existing failures:

```text
tests/verify_dispatch_layer.py::test_dispatch_energy_checkin
tests/verify_dispatch_layer.py::test_cli_dispatch_handle_json
tests/verify_dispatch_layer.py::test_cli_energy_today_empty
tests/verify_dispatch_layer.py::test_cli_confirmations_list_empty
tests/verify_intake_engine.py::test_supported_intents_complete
```

Resolution in PR #14: update stale `verify_*.py` expectations for current runtime behavior without changing feature modules. CI must run the full suite without `|| true`, and any remaining failures must be reported as `real_code_failure`.
