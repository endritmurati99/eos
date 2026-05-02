# EOS Integration & Rollout Plan

## Goal
Take EOS from current Phase-1 planning pilot to a production-grade headless personal operations agent.

## Phase 1, Already in Progress
- Dedicated Telegram bot and routing
- Dedicated agent/workspace
- Google Calendar live read verified
- Daily Planning and Weekly Planning policy defined
- Manual tasks via chat

## Phase 2, Google Tasks
### Objective
Use Google Tasks as the primary active-task source.

### Requirements
- headless-safe auth flow
- stable refresh-token storage
- clear list structure
  - Inbox
  - Next
  - Waiting
  - This Week
- no Maton dependency in the final production path unless explicitly accepted

### Readiness checks
- live read works
- live write works
- no duplicate task truth between chat and Google Tasks
- `403 accessNotConfigured` and disabled-API states are reported as `provider_disabled`
- daily and weekly planning never backfill failed live reads from `data/tasks.json`

### Current hardening rule
Production defaults are live-only. Local task/calendar JSON files are allowed only for explicit test or dry-verification paths and must be named as such in output.

## Phase 2b, Local-first Audio
### Objective
Generate briefing audio without coupling text generation to delivery success.

### Readiness checks
- local Piper-compatible synthesis can create a WAV artifact
- provider failure returns structured metadata
- Telegram or audio delivery errors are logged outside the user-facing briefing body

## Phase 3, Obsidian Vault
### Objective
Use a mounted Markdown vault as EOS long-term context store.

### Required architecture
- host path mounted into the runtime explicitly
- vault treated as filesystem, not app/plugin runtime
- stable structure:
  - `10 Inbox`
  - `11 Daily Notes`
  - `12 Projects`
  - `13 Areas`
  - `14 Knowledge`
  - `15 Ideas`
  - `90 Archive`

### Suggested mount model
- host path example: `/home/user/openclaw/vault`
- runtime path example: `/app/vault` or another explicit mounted path
- exact path must match the real deployment, not tutorial defaults

### Readiness checks
- EOS can read vault files
- EOS can create/update markdown safely
- links remain stable
- no folder inflation

## Phase 4, Review and History
- daily notes updates
- 7-day review
- overload trend detection
- open-loop detection

## Phase 5, Light Automation
- morning briefing
- evening wrap-up
- prep reminders
- context-aware nudges only when useful

## Operational Hardening
- keep external writes approval-aware
- keep only necessary ports open
- prefer stable mounted storage over ad-hoc local JSON in container paths
- prefer reproducible deployment paths over tutorial assumptions

## Critical Corrections vs Generic Tutorials
- Obsidian is a markdown vault, not a required GUI app
- container isolation means every persistent path must be explicitly mounted
- Google integrations must use headless-safe auth and token persistence
- current live Google Calendar path is `gog`, not a hypothetical `google-calendar-v3` skill
- OpenClaw memory is already available; do not add Redis/Postgres just to replace working memory unless there is a clear operational reason

## Live E2E Readiness Paths
1. Telegram -> Google Calendar -> Daily Plan
2. Telegram -> Weekly aggregation -> Weekly Plan
3. Telegram -> Google Tasks -> task capture and prioritization
4. Telegram -> Obsidian vault -> brain dump and daily note write
