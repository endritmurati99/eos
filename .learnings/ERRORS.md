# Errors

Command failures and integration errors.

---

## [ERR-20260421-001] gog-calendar-auth

**Logged**: 2026-04-21T13:27:00Z
**Priority**: high
**Status**: pending
**Area**: config

### Summary
Google Calendar access is blocked because the gog file-keyring password is not available in the current environment.

### Error
```
read token for endrit.murati99@gmail.com: read token: no TTY available for keyring file backend password prompt; set GOG_KEYRING_PASSWORD
```

A follow-up attempt with the documented placeholder password also failed:

```
read token for endrit.murati99@gmail.com: read token: aes.KeyUnwrap(): integrity check failed.
```

### Context
- Operation attempted: inspect calendars and update tomorrow's calendar block for Endrit
- Commands attempted: `gog auth list`, `gog calendar list`
- Environment: headless OpenClaw workspace, no interactive TTY for keyring prompt
- Relevant docs indicate Google Calendar is the source of truth, but write access depends on a valid decrypted gog token

### Suggested Fix
Provide the correct `GOG_KEYRING_PASSWORD` to the OpenClaw environment or re-authenticate gog with a known password and then retry the calendar update.

### Metadata
- Reproducible: yes
- Related Files: integrations/calendar-source.json, integrations/google-calendar.md, vault/04 Knowledge/docker-compose-snippets.txt

---

## [ERR-20260421-002] gog-keyring-permissions

**Logged**: 2026-04-21T16:41:00Z
**Priority**: high
**Status**: pending
**Area**: config

### Summary
Google Calendar access is now additionally blocked by unreadable gog keyring files under `/data/.config/gogcli/keyring`.

### Error
```
read token for endrit.murati99@gmail.com: read token: open /data/.config/gogcli/keyring/token:default:endrit.murati99@gmail.com: permission denied
```

### Context
- Operation attempted: update tomorrow's schedule per Endrit's new instructions
- Command attempted: `gog auth list`
- The keyring directory entries are visible but not readable by the current process

### Suggested Fix
Adjust ownership/permissions for `/data/.config/gogcli/keyring/*` so the OpenClaw process can read the token, or re-authenticate gog under the same user that runs OpenClaw.

### Metadata
- Reproducible: yes
- Related Files: /data/.config/gogcli/keyring

---

## [ERR-20260428-001] google-tasks-provider-disabled

**Logged**: 2026-04-28T00:00:00Z
**Priority**: high
**Status**: pending
**Area**: config

### Summary
Google Tasks can fail with `403 accessNotConfigured` when the API is disabled or not ready for the configured project.

### Error
```
googleapi: Error 403: accessNotConfigured
```

### Context
- Operation: live Google Tasks read for daily planning
- Product impact before hardening: local stub tasks could be presented as real priorities
- Current code mapping: `provider_disabled`

### Suggested Fix
Enable Google Tasks API for the OAuth project used by `gog`, verify OAuth credentials and refresh token storage, then run the Google Tasks degraded-state and live-read smoke checks.

### Metadata
- Reproducible: yes
- Related Files: src/gateways/google_tasks.py, docs/EOS-TASKS-INTEGRATION-v1.md

---

## [ERR-20260501-001] eos_cli_daily_morning

**Logged**: 2026-05-01T06:01:00+02:00
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
Manual daily_morning run failed because Python dependency jsonschema is missing.

### Details
Command: python3 -m src.eos_cli --json-only run-job daily_morning --dry-run
Error: ModuleNotFoundError: No module named jsonschema
Cron job daily-briefing-morning-0600 was also disabled when Endrit asked where the daily brief was.

### Suggested Action
Install/sync Python dependencies for EOS and re-enable the daily briefing cron after verification.

---
## [ERR-20260515-001] python_binary_missing

**Logged**: 2026-05-15T07:50:00+02:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
EOS verification command failed because `python` is not available in this runtime; use `python3` explicitly.

### Error
```
/usr/bin/sh: 1: python: not found
```

### Context
- Attempted: `python -m pytest tests/eos_intake_v2 tests/verify_eos_core.py tests/verify_eos_cli.py tests/verify_eos_state.py`
- Runtime has Python under `python3`.

### Suggested Fix
Use `python3 -m pytest` for EOS verification commands in this container.

### Metadata
- Reproducible: yes
- Related Files: pytest.ini
- Tags: python, pytest, runtime

---
## [ERR-20260515-002] git_push_https_auth_missing

**Logged**: 2026-05-15T08:18:00+02:00
**Priority**: medium
**Status**: pending
**Area**: git

### Summary
Pushing EOS branch `agent/eos-ask-router-v1` to GitHub failed because HTTPS Git could not read credentials in the non-interactive OpenClaw runtime.

### Error
```
fatal: could not read Username for 'https://github.com': No such device or address
```

### Context
- Commit succeeded locally: `40e9098 feat: add EOS source-aware ask router`
- Remote: `https://github.com/endritmurati99/eos.git`
- Need configured non-interactive auth or alternate GitHub CLI/token path before push.

### Suggested Fix
Use configured GitHub auth helper/`gh-photon` credentials if valid, or set a repository remote/auth method that works non-interactively. Do not prompt for credentials in chat.

### Metadata
- Reproducible: yes
- Related Files: git remote config
- Tags: git, github, auth, eos

---
## [ERR-20260515-005] claude_code_subscription_limit_during_review

**Logged**: 2026-05-15T08:55:00+02:00
**Priority**: low
**Status**: pending
**Area**: tooling

### Summary
Claude Code review lane could not run for the EOS Daily Notes iteration because the Claude subscription quota was exhausted until reset.

### Error
```
You've hit your limit · resets 1:10pm (Europe/Berlin)
```

### Suggested Fix
Retry Claude Code review after reset, or continue only with explicit note that Claude review was blocked by quota and another review lane/test evidence was used.

### Metadata
- Reproducible: transient
- Tags: claude-code, quota, review

---
