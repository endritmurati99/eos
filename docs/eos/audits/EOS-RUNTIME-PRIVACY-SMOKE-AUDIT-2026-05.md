# EOS Runtime Privacy Smoke Audit 2026-05

## Status

Control status: `FIX_BEFORE_LIVE`.

The new P0 runtime blocker is:

```text
attempt to write a readonly database
```

Observed state:

```text
data/eos_v2.db root:root -rw-r--r--
```

This audit does not change DB ownership, mode, contents, or runtime permissions. Agent 1 owns DB Runtime Recovery. This branch only makes the condition visible as the explicit `readonly_database` error class.

## Raw Output Leakage Risk

The previous CLI/Cron smoke scripts could print raw JSON and dry-run output. That output may include:

- task titles
- calendar event titles
- locations
- Telegram chat IDs or delivery targets
- Google account emails
- Gmail message IDs, thread IDs, or snippets
- raw environment values
- sensitive local paths

These values are not safe for CI logs or public PR comments.

## Masked Smoke Strategy

`scripts/eos_safe_smoke_summary.py` is the single summary layer for smoke output. Smoke scripts capture stdout/stderr internally and print only:

- command name
- pass/warning/failed status
- exit code
- error class
- stdout/stderr line counts
- whether sensitive output was detected internally
- `raw_output_printed=no`

Known environment/runtime classes are warnings:

- `readonly_database`
- `missing_gog`
- `missing_systemctl`
- `missing_python_alias`
- `missing_secrets`
- `provider_auth_required`
- `environment_issue`

Unknown non-zero exits and tracebacks that are not otherwise classified remain `failed`.

When `EOS_DB_PATH` is not already set, smoke scripts use a temporary DB path so they do not mutate tracked `data/eos_v2.db`. If an operator explicitly points `EOS_DB_PATH` at the affected runtime DB, the readonly failure remains classified as `readonly_database` without printing raw output.

## Pytest Discovery Status

`origin/main` contains many `tests/verify_*.py` files. Default pytest discovery misses them. This branch adds:

```ini
[pytest]
testpaths = tests
python_files = test_*.py verify_*.py
```

Real tests must run without `|| true`.

Local validation after enabling discovery:

- `python3 -m pytest tests/verify_runtime_doctor.py -q`: 9 passed.
- `python3 -m pytest -q`: 61 passed, 5 failed.

The five global failures are existing Runtime/Intent test failures exposed by discovery, not changes in the privacy-safe smoke layer:

- `tests/verify_dispatch_layer.py::test_dispatch_energy_checkin`
- `tests/verify_dispatch_layer.py::test_cli_dispatch_handle_json`
- `tests/verify_dispatch_layer.py::test_cli_energy_today_empty`
- `tests/verify_dispatch_layer.py::test_cli_confirmations_list_empty`
- `tests/verify_intake_engine.py::test_supported_intents_complete`

They are classified as code/test drift requiring the Runtime/Dispatch/Intake owner. This branch does not change `src/` code to fix them.

## Gitignore Hardening

`.gitignore` now covers env files, credential/token folders, gog config, runtime logs/state, Google workspace data folders, SQLite sidecars, token files, secret files, and OAuth credential JSON patterns.

`data/eos_v2.db` remains tracked. Removing, replacing, or changing permissions on that DB is a separate retention and recovery decision owned by Agent 1.

## Remaining Risks

- The readonly DB condition still blocks reliable runtime dry-runs until Agent 1 resolves DB ownership/path policy.
- Safe smoke scripts can detect sensitive raw output internally, but classification coverage must be maintained as new CLI commands are added.
- Google Workspace/Maps/Drive readiness remains blocked until runtime recovery and privacy-safe smoke are merged.
- PR #8, PR #9, and PR #10 remain `HOLD_UNTIL_AUDITED`.
