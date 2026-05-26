# EOS Environment Unblocker Audit 2026-05

Audit date: 2026-05-04 UTC.

## Repo State

- Current directory: `/docker/openclaw-qt6t`
- Repo root: `/docker/openclaw-qt6t`
- Current user: `root`
- Current branch during checks: `agent1/p0-db-runtime-recovery`
- Origin URL: `https://github.com/endritmurati99/eos.git`
- Repo classification: EOS repo

## Dependency State

- `python3-pip` was installed locally because `python3 -m pip` was missing.
- `jsonschema` was upgraded for `python3` to satisfy `jsonschema>=4.22,<5`.
- Verification: `python3 -c "import jsonschema; print('jsonschema ok')"` succeeded.

## GitHub CLI State

- `gh` is installed.
- `gh auth status` is authenticated for `github.com`.
- `gh repo view endritmurati99/eos` succeeds.
- SSH GitHub check still fails with `Host key verification failed`.
- HTTPS origin is working and remains the active remote, so SSH is not required for local EOS work.

## Main Branch State

- Local `main` previously pointed at `44dbe0f chore: initial Solara project import`.
- `origin/main` points at `36de6cc rename: Personal Assistant -> EOS (display strings only)`.
- Backup branch created: `backup/local-main-before-eos-reset`.
- Local `main` now points at `origin/main`.

## Pytest State

- `.pytest_cache` exists and is owned by the current local user after the ownership repair command.
- `pytest.ini` is absent on the current branch.
- `python3 -m pytest --collect-only -q` reports no tests collected.
- This is expected until the pytest discovery config from the runtime gate branch lands.

## CLI Sanity

Private command output was not copied into this audit.

| Command | Exit code | Reported status | Error class |
| --- | --- | --- | --- |
| `python3 -m src.eos_cli --help` | 0 | n/a | none |
| `python3 -m src.eos_cli --json-only health` | 0 | warning | missing_or_degraded_auth |
| `python3 -m src.eos_cli --json-only cron-audit` | 0 | success | none |
| `python3 -m src.eos_cli --json-only model-audit` | 0 | success | none |

## Remaining Blockers

- SSH GitHub host key is not configured, but HTTPS GitHub operations work.
- `pytest.ini` is still missing on this branch; PR #14 owns pytest discovery.
- Health remains warning because live/provider credentials or auth are degraded or unavailable in this local environment.
