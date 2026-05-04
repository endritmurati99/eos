# EOS Merge And Live Gate Runbook

## 1. Goal

Provide the operational gate order for EOS foundation, runtime DB recovery, CI/smoke safety, and later feature PRs. This runbook does not authorize runtime feature work, DB permission changes, Gmail writes, OAuth flows, or secret handling.

## 2. Canonical Gate Branch

PR #14 is the canonical runtime-gate PR. PR #6 is superseded, and PR #12 privacy-safe runtime CI content is reconciled into PR #14.

Do not merge PR #6 or PR #12 independently unless PR #14 is abandoned and the queue is explicitly revised.

## 3. Merge Order

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

## 4. Hard Gates

- Syntax or import failure.
- Real pytest failure.
- Secret scan hit.
- Raw sensitive smoke output detected.
- Gmail write scope or write action detected.
- Code PR with zero tests collected.
- `readonly_database` after DB recovery is claimed fixed.

## 5. Soft Gates

- Missing `gog`.
- Missing `systemctl` or systemd unavailable.
- Missing credentials.
- Provider auth required.
- Gmail, Maps, or Drive live verification pending.
- `readonly_database` before DB recovery is claimed fixed.

## 6. Test Gate

Run:

```bash
git diff --check
bash scripts/run_eos_tests.sh
```

`scripts/run_eos_tests.sh` runs compile checks and pytest. Pytest exit code 5 is a warning only for docs-only PRs. It is a hard failure for code, test, script, workflow, config, or unknown changed paths.

## 7. Privacy-Safe Smoke Gate

Run:

```bash
bash scripts/run_eos_smoke.sh
```

The smoke scripts capture raw stdout/stderr into temporary files and print only summarized metadata:

```text
command name
pass/warning/fail status
exit code
error_class
stdout/stderr line counts
sensitive/secret detection flags
raw_output_printed=no
```

The summary must not include task titles, calendar event titles, locations, Telegram IDs, Google accounts, Gmail IDs, Gmail snippets, raw environment values, secrets, or sensitive absolute paths.

Set `EOS_DB_RECOVERY_FIXED=true` or `EOS_RUNTIME_LIVE_GATE=true` only after DB recovery is claimed fixed. In that mode, `readonly_database` becomes a hard failure.

## 8. Error Classes

Smoke classification must recognize:

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

Secret or sensitive output detection is treated as a hard gate and must be remediated before merge.

## 9. Rollback Notes

If a gate PR causes CI instability, revert the gate PR rather than merging feature branches around it.

If DB recovery regresses, stop live-ready claims, rerun the DB doctor from PR #13, classify failures as `readonly_database`, `environment_issue`, or `real_code_failure`, and keep scheduled runtime blocked until writeability is restored.

If smoke output leaks raw data, stop using the output in PR comments or CI summaries, rotate exposed secrets if needed, and restore summary-only smoke before continuing the queue.
