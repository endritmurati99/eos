# EOS DB Runtime Audit 2026-05

## Executive Summary

EOS daily and weekly scheduled jobs failed with:

```text
attempt to write a readonly database
```

The immediate blocker is runtime ownership mismatch on SQLite derived state. The DB file is owned by `root:root` with mode `0644`, while the long-running OpenClaw process inside the container runs as user `node` UID/GID `1000`. On the host bind mount, that maps to `ubuntu:ubuntu`.

Recommended immediate fix: set the DB file and existing SQLite sidecars to `ubuntu:ubuntu` on the host so the container service user sees them as `node:node`.

## Current DB Path

```text
/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant/data/eos_v2.db
```

EOS also supports:

```text
EOS_DB_PATH
```

The default application DB path remains:

```text
data/eos_v2.db
```

## Ownership Before Fix

Observed:

```text
data/          ubuntu:ubuntu 0755
data/eos_v2.db root:root     0644
```

Host shell user:

```text
root
```

OpenClaw app process:

```text
container user node, uid=1000, gid=1000
```

Host UID/GID mapping:

```text
1000 -> ubuntu:ubuntu
```

## Schreibbarkeit

`root` can write the DB file, but the service process user cannot. This explains why manual root probes can succeed while OpenClaw-triggered EOS jobs fail.

Pre-fix check:

```text
runuser -u node -- test -w data/eos_v2.db -> no
node_sqlite_write_probe -> OperationalError: attempt to write a readonly database
```

Post-fix check:

```text
runuser -u node -- test -w data/eos_v2.db -> yes
node_sqlite_write_probe -> success
```

## Service User

Systemd unit:

```text
eos-job@.service
```

Invocation:

```text
docker compose exec -T -w /data/.openclaw/workspaces/personal-assistant openclaw ...
```

The relevant write user for runtime state is the container `node` process, mapped to host `ubuntu`.

## SQLite Write Probe

The DB doctor performs a probe with:

```text
CREATE TABLE IF NOT EXISTS eos_db_write_probe
INSERT
DELETE
DROP TABLE
```

The probe is intentionally small and removes the probe table after the write test.

## Daily Dry-Run Ergebnis

Post-fix status:

```text
container node daily-plan dry-run -> exit_code=0
readonly_db error -> no
```

Only status, exit code, and error class should be reported publicly. Do not paste full calendar/task payloads if they contain personal data.

## Weekly Dry-Run Ergebnis

Post-fix status:

```text
container node weekly-plan dry-run -> exit_code=0
readonly_db error -> no
```

Only status, exit code, and error class should be reported publicly.

## Run-Job Dry-Run Ergebnis

Post-fix status:

```text
container node run-job daily_morning dry-run -> exit_code=0
container node run-job weekly_sync dry-run -> exit_code=0
readonly_db error -> no
```

## Empfohlener Fix

Immediate host-side ownership repair:

```bash
EOS_DB_PATH=/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant/data/eos_v2.db \
EOS_DB_OWNER_USER=ubuntu \
EOS_DB_OWNER_GROUP=ubuntu \
EOS_APPLY_DB_PERMISSION_FIX=true \
bash scripts/fix_eos_db_permissions.sh
```

This changes only:

```text
data/
data/eos_v2.db
data/eos_v2.db-wal, if present
data/eos_v2.db-shm, if present
data/eos_v2.db-journal, if present
```

It does not use `chmod 777` and does not recursively chown the repository.

## Angewendeter Fix

Applied on 2026-05-03:

```text
data/eos_v2.db root:root 0644 -> ubuntu:ubuntu 0644
```

No `chmod 777` was used. No recursive repo `chown` was used. No DB file was deleted.

## Verbleibende Risiken

- Root-run maintenance commands can recreate root-owned SQLite files.
- The DB is currently under the repository worktree, which can mix runtime state with git state.
- Long-term reliability requires `EOS_DB_PATH` to point to a dedicated runtime state location.
- Google Calendar/Tasks/auth issues may still surface after the DB blocker is removed.
