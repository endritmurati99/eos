# EOS Merge And Live Gate Runbook

## 1. Ziel

Provide a safe merge order for EOS foundation, CI/smoke, privacy-safe runtime gates, and P0 DB recovery. This runbook does not authorize runtime feature work, Gmail writes, OAuth changes, DB permission changes, or secret handling.

## 2. Current PR Map

| PR | Status | Role |
| --- | --- | --- |
| #5 | open, mergeable | Canonical Foundation Reconciliation. |
| #6 | open, mergeable | CI bootstrap, superseded by #12. |
| #12 | open, mergeable | Privacy-safe runtime smoke and queue hardening. |
| #13 | open, mergeable | P0 DB runtime recovery tooling. |
| #7 | open, mergeable | Runtime doctor, merge only if not replaced by #12/#13. |
| #4 | open, mergeable | Gmail classifier. |
| #3 | open, mergeable | Gmail read-only shadow mode after #4. |
| #8/#9/#10 | open, mergeable | Feature PRs on hold pending audit. |
| #11 | draft, mergeable | Google platform readiness on hold pending audit. |

## 3. Superseded PRs

PR #1 and PR #2 are superseded by PR #5 and must not merge independently.

PR #6 is superseded by PR #12. Close or mark #6 superseded after owner approval.

## 4. Merge Order

1. Merge PR #5.
2. Close or mark PR #1/#2 superseded.
3. Merge PR #13.
4. Merge PR #12 after #13, rebasing if needed.
5. Merge PR #7 only if it contains runtime doctor content not already covered by #12/#13.
6. Rebase and merge PR #4.
7. Rebase PR #3 on #4, then merge if read-only gates pass.
8. Audit PR #8/#9/#10/#11 separately before any merge.

## 5. Hard Gates

- `src.eos_cli` import failure.
- Syntax or compile failure.
- Real pytest failure in a changed module.
- Secret value detected in output.
- Gmail write scope or Gmail write action detected.
- `readonly_database` after DB recovery is claimed fixed.
- Zero tests collected in a non-doc PR.

## 6. Soft Gates

- Missing `gog`.
- Missing `systemctl` or systemd unavailable.
- Missing Google credentials.
- Gmail live E2E unverified.
- Maps live API unverified.
- Google Drive live API unverified.

## 7. DB Recovery Gate

`readonly_database` is P0. Daily, weekly, and run-job paths are not live-ready until SQLite writeability is proven for the runtime user.

Run after PR #13 is available:

```bash
python3 scripts/eos_db_doctor.py
```

Minimum required result:

```text
sqlite_write_probe: success
db_writable: true
parent_writable: true
```

If the DB doctor file is missing, merge or rebase PR #13 before runtime live gate evaluation.

## 8. Privacy-Safe Smoke Gate

Run:

```bash
bash scripts/run_eos_smoke.sh
```

The smoke script must print only safe summaries: command name, status, exit code, error class, line counts, and detection flags. It must not print raw task, calendar, Gmail, Telegram, credential, environment, or sensitive path data.

Set `EOS_DB_RECOVERY_FIXED=true` or `EOS_RUNTIME_LIVE_GATE=true` only after DB recovery is claimed fixed. In that mode, `readonly_database` is a hard failure.

## 9. Gmail Read-only Gate

Gmail branches must remain read-only until explicit write approval. Block merge if any new code path adds Gmail write scopes or actions such as modify, send, compose, label mutation, delete, trash, archive, or mailbox-wide write behavior.

Read-only shadow mode must be rebased after the classifier PR and must run tests plus privacy-safe smoke before merge.

## 10. Google Platform Gate

Google credentials, Gmail live E2E, Maps live API, and Drive live API can remain soft gates only while the branch is not claiming live-ready Google Platform behavior.

Any PR claiming live readiness for Gmail, Maps, Drive, or broader Google Workspace must include a separate audit and must pass the DB recovery gate first.

## 11. What Must Not Merge

- PR #1 or #2 independently after #5.
- PR #6 independently after #12 is accepted.
- Any PR with raw smoke output in CI logs.
- Any PR with Gmail write scope or write action before explicit approval.
- Any PR that treats post-recovery `readonly_database` as a soft warning.
- PR #8/#9/#10/#11 before separate audit.

## 12. Rollback Notes

If a gate PR causes CI instability, revert the gate PR rather than merging feature branches around it.

If DB recovery regresses, stop live-ready claims, rerun the DB doctor from PR #13, classify failures as `readonly_database`, `missing_dependency`, `environment_issue`, or `real_code_failure`, and keep scheduled daily/weekly/run-job runtime blocked until writeability is restored.

If smoke output leaks raw data, stop using the output in PR comments or CI summaries, rotate any exposed secret if needed, and restore summary-only smoke before continuing the queue.
