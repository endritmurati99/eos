# EOS Security, Secrets, and OAuth Audit

Date: 2026-05
Repository: `endritmurati99/eos`
Audit mode: metadata-only

## Executive Summary

EOS already uses sensitive integrations: Google Calendar, Google Tasks, Telegram delivery, local SQLite state, and Vault-like markdown paths. Gmail would add significantly more sensitive data. Before Gmail writes or mail-derived persistence, the repository needs a stricter storage, ignore, scope, and logging posture.

This audit did not read or print token contents, secret values, `.env` contents, or OAuth credential JSON contents.

## Current Secret Handling

Confirmed from code metadata:

- `src/runtime.py` loads the first `.env` found from the workspace upward.
- `src/gateways/google_tasks.py` reads Google-related env vars.
- `src/gateways/telegram.py` resolves Telegram token and chat ID from explicit args or env vars.
- no `.env` file was found in the repository path during the Phase 0 check.

Relevant env names visible in code:

```text
EOS_GOG_BIN
EOS_GOOGLE_ACCOUNT
EOS_GOOGLE_CREDENTIALS_PATH
EOS_GOOGLE_TOKEN_PATH
EOS_GOOGLE_TASKS_ENABLED
EOS_TELEGRAM_BOT_TOKEN
TELEGRAM_BOT_TOKEN
TELEGRAM_TOKEN
EOS_TELEGRAM_CHAT_ID
TELEGRAM_CHAT_ID
```

## OAuth Current State

Google access currently uses `gog`.

Calendar:

- calendar reads call `gog calendar events`
- `XDG_CONFIG_HOME` can be set from `EOS_GOOGLE_TOKEN_PATH`
- configured calendar source is `integrations/calendar-source.json`

Tasks:

- `TaskGateway` checks `gog auth status`, `gog auth credentials list`, and `gog auth list`
- headless auth helpers exist for Google Tasks
- services are requested through `gog auth add ... --services tasks`

Gmail:

- no Gmail OAuth scope usage was found in repo text
- no Gmail client code was found
- Gmail scopes must not be added until Phase 1 design is reviewed

## Gmail Readiness

Read-only readiness is partial.

Strengths:

- the repo already has a gateway pattern for Google APIs through `gog`
- degraded states are explicit in Google Tasks
- dry-run behavior is common in jobs
- audit and health commands exist

Gaps:

- no mail storage policy exists in code
- no Gmail OAuth scopes are configured
- no mail audit table exists
- no synthetic classifier tests exist
- `.gitignore` does not yet explicitly protect future mail state paths

## Logging Risks

Current code generally returns structured status and error text. Future mail code must be stricter than current general logging because mail can include secrets, OTPs, banking data, reset links, legal content, and private personal content.

Rules for Gmail logging:

- log message IDs and thread IDs where possible
- avoid full bodies
- avoid OTPs, reset tokens, and login links
- hash input where feasible
- store classification reason without copying sensitive snippets
- keep raw provider errors from printing sensitive payloads

## Local State Risks

Current tracked state:

- `data/eos_state.json` is tracked
- `data/eos_v2.db` is tracked
- local fixture files under `data/` are tracked

Risk:

- if future mail classifications, snippets, or sender profiles are written into tracked or poorly ignored files, personal mail data can enter git history.

Required before Gmail persistence:

- decide whether future mail-derived SQLite data lives in a tracked schema-only DB, an untracked runtime DB, or a migration-managed DB without committed personal rows
- add explicit ignore rules for raw mail exports, token roots, local runtime mail data, and temporary classification dumps

## Required Git Ignore Rules

Recommended future `.gitignore` additions before Gmail implementation:

```text
.env
.env.*
!.env.example
credentials/
tokens/
.gog/
.config/gog/
var/
logs/
data/mail/
data/gmail/
data/**/*.sqlite
data/**/*.sqlite-shm
data/**/*.sqlite-wal
*.db-shm
*.db-wal
```

Because `data/eos_v2.db` is currently tracked, changing ignore rules alone will not untrack it. That needs a separate deliberate decision.

## Minimal Scope Recommendation

Phase 1:

```text
Gmail read-only access only.
No send scope.
No delete scope.
No broad modify scope.
```

Phase 1 should support:

- bounded message listing
- metadata and headers needed for classification
- safe snippet or body excerpt handling only where policy allows it
- dry-run classification
- digest generation

Phase 2:

```text
Label modify only after policy, tests, false-positive review, and rollback design.
```

## Forbidden Early Scopes

Do not use at the start:

- send mail
- delete mail
- broad mailbox modify without constraints
- unrestricted attachment access
- unrestricted body export

## Required Mitigations Before Gmail Write

- reviewed mail policy
- reviewed action authorization policy
- synthetic classifier tests
- dry-run shadow mode reports
- audit table or audit log model
- storage minimization rules
- read-after-write verification
- rollback procedure for labels applied by EOS
- explicit denylist for delete, send, and sensitive archive actions

## Unknowns

- actual token storage encryption status
- actual `gog` token file path in production
- whether production runtime differs from local workspace
- intended Gmail account or accounts
- desired retention period for mail-derived metadata
- whether `data/eos_v2.db` should remain tracked after mail modules exist

## Security Status

```text
SECURITY_STATUS:
- secrets_in_repo_found: no by metadata search, token contents not inspected
- token_storage_understood: partial
- gmail_scopes_existing: no
- read_only_gmail_ready: partial
- write_gmail_ready: no
- blocking_risks:
  - tracked SQLite state must be reviewed before mail persistence
  - .gitignore lacks explicit env, token, runtime, and mail-data rules
  - Gmail OAuth scope strategy is not yet implemented
  - no Gmail synthetic tests or audit model exist yet
```
