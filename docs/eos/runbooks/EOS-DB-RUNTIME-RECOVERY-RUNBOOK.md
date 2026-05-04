# EOS DB Runtime Recovery Runbook

## 1. Fehlerbild

EOS scheduled jobs report:

```text
Daily Briefing failed: attempt to write a readonly database
Weekly Planning failed: attempt to write a readonly database
```

This blocks daily and weekly runtime even when commands are dry-runs, because dry-runs still write derived runtime state such as job runs, habit state, delivery state, or snapshots.

## 2. Ursache

There were three P0 causes:

- `src/runtime.py` used `WORKSPACE_ROOT.parents[2]` at import time, which crashed in a root checkout or any workspace with a different path depth.
- `data/eos_v2.db` was tracked by git even though it is runtime state.
- The active DB file could be owned by `root:root` with mode `0644`, while the runtime process writes as the OpenClaw service user.

The active deployment uses systemd `eos-job@.service`, which shells into the `openclaw` Docker service:

```text
docker compose exec -T -w /data/.openclaw/workspaces/personal-assistant openclaw ...
```

The OpenClaw application process runs as container user `node` with UID/GID `1000`. On the host, UID/GID `1000` maps to `ubuntu:ubuntu`.

Observed P0 state:

```text
data/         -> ubuntu:ubuntu, writable by node through the bind mount
data/eos_v2.db -> root:root, 0644
```

The DB file is writable by host/container root, but not by the service process user. A root-run smoke can therefore produce a false positive unless the target service user is checked explicitly.

The runtime path resolver now discovers the OpenClaw root in this order:

1. `EOS_OPENCLAW_ROOT`
2. nearest parent containing `.openclaw/`
3. nearest parent containing `data/.openclaw/`
4. `WORKSPACE_ROOT` fallback

This keeps `import src.runtime` from crashing in root and nested workspaces.

## 3. Sofortdiagnose

From the host:

```bash
pwd
whoami
id
ls -ld data || true
ls -l data/eos_v2.db || true
stat data/eos_v2.db || true
systemctl cat eos-job@.service || true
docker compose exec -T openclaw sh -lc 'ps aux | sed -n "1,80p"'
docker compose exec -T -w /data/.openclaw/workspaces/personal-assistant openclaw sh -lc \
  'runuser -u node -- test -w data/eos_v2.db && echo node_db_writable=yes || echo node_db_writable=no'
```

Run the structured doctor:

```bash
EOS_DB_PATH=/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant/data/eos_v2.db \
EOS_DB_OWNER_USER=ubuntu \
EOS_DB_OWNER_GROUP=ubuntu \
python3 scripts/eos_db_doctor.py
```

Expected live-ready DB fields:

```text
sqlite_write_probe: success
db_writable: true
parent_writable: true
```

## 4. Safe Fix

Dry-run first:

```bash
EOS_DB_PATH=/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant/data/eos_v2.db \
EOS_DB_OWNER_USER=ubuntu \
EOS_DB_OWNER_GROUP=ubuntu \
bash scripts/fix_eos_db_permissions.sh
```

Apply only after the service user mapping is confirmed:

```bash
EOS_DB_PATH=/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant/data/eos_v2.db \
EOS_DB_OWNER_USER=ubuntu \
EOS_DB_OWNER_GROUP=ubuntu \
EOS_APPLY_DB_PERMISSION_FIX=true \
bash scripts/fix_eos_db_permissions.sh
```

Expected result:

```text
host:      data/eos_v2.db -> ubuntu:ubuntu
container: data/eos_v2.db -> node:node
```

## 5. Was nicht tun

Do not:

- delete `data/eos_v2.db`
- use `chmod 777`
- run `chown -R` over the entire repo
- force root as the long-term runtime user
- touch `.env`, token, credential, Gmail, Drive, Maps, or OAuth files
- change productive systemd units without explicit approval

## 6. EOS_DB_PATH Strategie

Short term:

- keep the current default DB path if needed
- set DB ownership to the actual service user mapping
- keep `data/eos_v2.db` untracked by git

Better long term:

- move EOS runtime state to a dedicated writable state directory
- configure `EOS_DB_PATH` explicitly

For a user service:

```text
EOS_DB_PATH=$HOME/.local/state/eos/eos_v2.db
```

For a system service:

```text
EOS_DB_PATH=/var/lib/eos/eos_v2.db
User=eos
Group=eos
```

Systemd can manage the state directory:

```ini
Environment=EOS_DB_PATH=/var/lib/eos/eos_v2.db
StateDirectory=eos
```

`EOS_DB_PATH` remains the supported override and should be preferred for stable deployments. The parent directory must be writable by the service user.

## 7. Systemd/OpenClaw Hinweise

The current unit invokes Docker from systemd and relies on the container/user mapping. This is workable, but fragile when root-run commands create files that later need to be written by the `node` process.

The stable pattern is one consistent runtime identity:

- systemd owns the service lifecycle
- the container process writes runtime state as one non-root user
- host bind-mounted state is owned by the host UID/GID that maps to that container user

## 8. Smoke Tests

Run:

```bash
bash scripts/run_eos_db_smoke.sh
```

For full command output during local debugging only:

```bash
EOS_DB_SMOKE_VERBOSE=true bash scripts/run_eos_db_smoke.sh
```

Do not paste verbose output into public reports if it contains calendar/task details.

## 9. Rollback

Permission rollback is normally unnecessary. If ownership was set to the wrong user, rerun the fixer with the correct `EOS_DB_OWNER_USER` and `EOS_DB_OWNER_GROUP`.

If `EOS_DB_PATH` is changed in a future deployment:

1. stop scheduled EOS jobs,
2. copy the DB to the new state path,
3. set ownership to the runtime user,
4. run the DB doctor,
5. run daily/weekly dry-run smoke,
6. restart scheduled jobs.

## 10. Offene Risiken

- `data/eos_v2.db` was previously tracked in git. It is removed from the index in the recovery branch, but any private data already committed to history requires a separate history-rewrite decision.
- Root-run Docker exec commands can recreate root-owned DB files.
- The systemd unit currently uses `--no-dry-run --send`; dry-run recovery should be validated before scheduled sends resume.
- Google Calendar/Tasks runtime issues can still fail a job after the DB writeability blocker is fixed.

History rewrite is intentionally not part of this runbook. If the tracked DB ever contained private task, calendar, Gmail, token, or profile data, open a separate retention/security task before rewriting repository history.
