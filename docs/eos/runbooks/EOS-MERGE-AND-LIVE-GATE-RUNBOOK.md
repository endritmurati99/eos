# EOS Merge And Live Gate Runbook

## 1. Goal

Provide the operational gate order for EOS foundation, runtime DB recovery, CI/smoke safety, and later feature PRs. This runbook does not authorize runtime feature work, DB permission changes, Gmail writes, OAuth flows, or secret handling.

## 2. Current PR Map

PR #5 and PR #13 are merged. They are the current foundation and runtime DB recovery baseline.

PR #14 is the canonical runtime-gate PR. PR #6 is superseded, and PR #12 privacy-safe runtime CI content is reconciled into PR #14.

Next after PR #14:

- PR #16 security retention and Google live readiness gates.
- PR #17 integrated Gmail read-only path, replacing #3/#4.
- PR #18 release candidate cleanup docs.

Held:

- PR #8 Mail to Task Proposal.
- PR #9 Calendar Intelligence.
- PR #10 Habit Journal Coach.
- PR #11 Google Platform/Maps. Draft.
- PR #15 Local dev environment doctor.

## 3. Superseded PRs

PR #1/#2 are superseded by PR #5.

PR #3/#4 are superseded by PR #17.

PR #6/#7/#12 are superseded by PR #13/#14 runtime recovery, doctor, CI, and privacy-safe smoke work.

Do not merge superseded PRs independently unless the queue is explicitly revised.

## 4. Merge Order

1. PR #5 Foundation. Merged.
2. PR #13 Runtime DB + path fix. Merged.
3. PR #14 Runtime gates / CI / safe smoke.
4. PR #16 Security retention and Google live readiness gates.
5. PR #17 Gmail integrated read-only path.
6. PR #18 Release candidate cleanup docs.

Hold PR #8, #9, #10, #11, and #15 until separate audit or explicit owner decision after PR #14.

## 5. Hard Gates

- Syntax or import failure.
- Real pytest failure.
- Secret scan hit.
- Raw sensitive smoke output detected.
- Gmail write scope or write action detected.
- Code PR with zero tests collected.
- `readonly_database` after DB recovery is claimed fixed.

## 6. Soft Gates

- Missing `gog`.
- Missing `systemctl` or systemd unavailable.
- Missing credentials.
- Provider auth required.
- Gmail, Maps, or Drive live verification pending.
- `readonly_database` before DB recovery is claimed fixed.

## 7. DB Recovery Gate

Daily, weekly, and run-job flows are not live-ready while SQLite write probes fail.

The DB doctor from PR #13 must show:

```text
sqlite_write_probe: success
db_writable: true
parent_writable: true
```

After DB recovery is claimed fixed, `readonly_database` is a hard gate for PR #14 and later runtime-gated work.

## 8. Test Gate

Run:

```bash
git diff --check
bash scripts/run_eos_tests.sh
```

`scripts/run_eos_tests.sh` runs compile checks and pytest. Pytest exit code 5 is a warning only for docs-only PRs. It is a hard failure for code, test, script, workflow, config, or unknown changed paths.

## 9. Privacy-Safe Smoke Gate

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

## 10. Gmail Read-Only Gate

Gmail work must remain read-only until explicit owner approval for write scopes or write actions.

PR #17 is the only current Gmail merge candidate. PR #3 and PR #4 are superseded and must not merge independently.

## 11. Google Platform Gate

Google credentials, Gmail live E2E, Maps live API, and Drive live API gaps are soft gates until a PR claims live readiness. No gate script may require secrets for CI.

PR #11 remains draft and held until separate review.

## 12. What Must Not Merge

- Superseded PR #1, #2, #3, #4, #6, #7, or #12 independently.
- Held PR #8, #9, #10, #11, or #15 before separate audit or explicit owner decision.
- PR #11 while it remains draft.
- Any PR that prints private raw smoke output.
- Any PR that introduces Gmail write scopes or write actions before explicit approval.

## 13. Error Classes

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

## 14. Rollback Notes

If a gate PR causes CI instability, revert the gate PR rather than merging feature branches around it.

If DB recovery regresses, stop live-ready claims, rerun the DB doctor from PR #13, classify failures as `readonly_database`, `environment_issue`, or `real_code_failure`, and keep scheduled runtime blocked until writeability is restored.

If smoke output leaks raw data, stop using the output in PR comments or CI summaries, rotate exposed secrets if needed, and restore summary-only smoke before continuing the queue.
