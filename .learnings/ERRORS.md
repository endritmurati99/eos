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
## [ERR-20260511-001] gog-remote-auth-step2

**Logged**: 2026-05-11T20:39:00+02:00
**Priority**: medium
**Status**: pending
**Area**: config

### Summary
`gog auth add --remote --step 2` failed with “manual auth state missing” after a prior step 1 had been run.

### Error
```
manual auth state missing; run remote step 1 again
```

### Context
- Attempted to finish Gmail OAuth expansion to include send scope.
- Avoid logging the provided OAuth callback URL/code because it is sensitive.

### Suggested Fix
Run remote step 1 again and have the user authorize the fresh URL, then immediately run step 2 with the returned callback URL.

### Metadata
- Reproducible: unknown
- Related Files: TOOLS.md

---
## [ERR-20260513-001] python_requests_missing

**Logged**: 2026-05-13T10:20:32+02:00
**Priority**: low
**Status**: pending
**Area**: tooling

### Summary
Attempted quick web retrieval with Python `requests`, but the module is not installed in this workspace/runtime.

### Details
For lightweight web checks, prefer browser tool or stdlib `urllib.request` instead of assuming `requests` is available. Also quote heredocs when logging content that contains backticks.

### Suggested Action
Use Python stdlib or browser automation for ad-hoc web retrieval unless dependencies are verified first; use `<<'EOF'` for literal learning-log entries.

### Metadata
- Source: error
- Tags: python, web-research, dependencies

---
## [ERR-20260513-002] browser_start_namespace

**Logged**: 2026-05-13T10:21:48+02:00
**Priority**: low
**Status**: pending
**Area**: tooling

### Summary
OpenClaw browser start failed in this container because Chromium could not create the required namespace.

### Error
```
Failed to move to new namespace ... Operation not permitted
Hint: If running in a container or as root, try setting browser.noSandbox: true.
```

### Suggested Action
For quick web research in this runtime, use `curl`/stdlib retrieval or configure the browser with noSandbox if browser automation is required.

### Metadata
- Source: browser tool failure
- Tags: browser, chromium, sandbox, web-research

---
## [ERR-20260515-003] codex_direct_duplicate_sandbox_flag

**Logged**: 2026-05-15T08:20:00+02:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
`codex-direct exec` failed when an explicit `--sandbox read-only` flag was added because the wrapper already injects a sandbox mode.

### Error
```
error: the argument '--sandbox <SANDBOX_MODE>' cannot be used multiple times
```

### Context
- Attempted to run a read-only Codex review lane for EOS morning/evening/Second-Brain brainstorming.
- `/data/.local/bin/codex-direct` already supplies sandbox configuration.

### Suggested Fix
When using `codex-direct`, do not add a second `--sandbox` flag. Use the wrapper defaults or call raw `codex exec` if a specific sandbox mode is needed.

### Metadata
- Reproducible: yes
- Tags: codex, wrapper, sandbox

---
## [ERR-20260515-004] codex_unsupported_subscription_model

**Logged**: 2026-05-15T08:25:00+02:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
Codex review lane failed when explicitly requesting `openai-codex/gpt-5.2-codex`; the ChatGPT-account Codex CLI did not support that model id.

### Error
```
The 'openai-codex/gpt-5.2-codex' model is not supported when using Codex with a ChatGPT account.
```

### Suggested Fix
For Codex CLI subscription runs, prefer the configured default model or a verified subscription model id instead of forcing `openai-codex/gpt-5.2-codex`.

### Metadata
- Reproducible: yes
- Tags: codex, model, subscription

---

## [ERR-20260515-habits-list-command] eos_cli_command

**Logged**: 2026-05-15T11:58:17+02:00
**Priority**: low
**Status**: resolved
**Area**: cli

### Summary
Tried non-existent EOS command `habits list`; current CLI uses `habits status` for listing configured habits.

### Error
```text
python3 -m src.eos_cli habits: error: argument habit_command: invalid choice: 'list'
```

### Context
While checking Habit Tracker state for Endrit. Re-ran with `.venv/bin/python -m src.eos_cli --json-only habits status`, which succeeded.

### Suggested Fix
Use `habits status` in future Habit Tracker audits unless a `habits list` alias is intentionally added.

### Metadata
- Reproducible: yes
- Related Files: src/eos_cli.py

---

## [ERR-20260515-unquoted-heredoc-backticks] shell_logging

**Logged**: 2026-05-15T11:59:00+02:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
A markdown learning entry was appended with an unquoted heredoc, so shell backticks inside the entry were executed.

### Error
```text
/usr/bin/sh: 1: habits: not found
/usr/bin/python3: Error while finding module specification for 'src.eos_cli'
```

### Context
The entry was repaired immediately using Python file editing. No secrets were involved; the executed substitutions were harmless command-name strings.

### Suggested Fix
When appending markdown containing backticks through shell, use a quoted heredoc delimiter (`<<'EOF'`) or write via Python.

### Metadata
- Reproducible: yes
- Related Files: .learnings/ERRORS.md

---
## [ERR-20260515-001] gog_tasks_insufficient_scope

**Logged**: 2026-05-15T14:15:00+02:00
**Priority**: high
**Status**: pending
**Area**: integration

### Summary
Google Tasks write/read request failed because the current gog OAuth grant lacks Tasks scope.

### Error
```
gog tasks lists list --account endrit.murati99@gmail.com --json
Google API error (403 insufficientPermissions): Request had insufficient authentication scopes.
```

### Context
- User asked to update an existing Google Task named Einkauf with a shopping list.
- `gog auth list` showed the account currently authorized only for `forms` in this session.
- Fallback `python3 -m src.eos_cli tasks read` also failed because local dependency `jsonschema` is missing.

### Suggested Fix
Reauthorize gog for Google Tasks service and/or fix local Python deps for `src.eos_cli`.

### Metadata
- Reproducible: yes
- Related Files: TOOLS.md, .learnings/ERRORS.md

---

## [ERR-20260517-001] Image/web search provider failures during Bayern Trip planning

**Logged**: 2026-05-17T14:40:00+02:00
**Priority**: medium
**Context**: User asked for per-screenshot OCR/analysis and internet template research for a Notion Bayern trip planner.
**What failed**: Parallel image analysis calls timed out or hit provider quota/API-key errors; two web_search calls timed out.
**Impact**: Need fallback to prior successful combined image analysis, local OCR if available, and retry web research with narrower/fewer queries or direct fetches.
**No secrets logged**: yes

## [ERR-20260517-002] Notion connection unavailable in local environment

**Logged**: 2026-05-17T14:45:00+02:00
**Priority**: medium
**Context**: User asked to establish Notion connection and create a Bayern Trip planning template.
**What failed/blocked**: No NOTION-related environment keys were present; browser attach/start for possible logged-in Notion access timed out. No Notion CLI/client package available.
**Fallback used**: Created importable Markdown/CSV/JSON template and a Node Notion API script that can create the page once NOTION_TOKEN and NOTION_PARENT_PAGE_ID are supplied.
**No secrets logged**: yes

## [ERR-20260517-003] Notion URL page-id parsing failed for slugged URLs

**Logged**: 2026-05-17T16:58:00+02:00
**Priority**: low
**Context**: Verifying newly created Notion dashboard subpages.
**What failed**: Parser used final URL path segment as raw ID, but Notion URLs include a title slug before the 32-character page ID.
**Fix**: Extract the trailing 32 hex characters from the path segment instead of removing dashes from the whole slug.
**No secrets logged**: yes

## [ERR-20260517-004] Notion child page blocks cannot be archived through /blocks endpoint

**Logged**: 2026-05-17T17:08:00+02:00
**Priority**: medium
**Context**: Cleaning duplicate Bayern Trip Notion dashboard blocks.
**What failed**: PATCH /v1/blocks/:id with archived=true fails for child_page blocks because they are pages and must be patched via /v1/pages/:page_id.
**Fix**: In cleanup logic, route child_page to PATCH /pages/:id, child_database to PATCH /databases/:id where supported, and normal blocks to PATCH /blocks/:id.
**No secrets logged**: yes

## [ERR-20260517-005] Notion link_to_page cannot target inline databases

**Logged**: 2026-05-17T18:05:00+02:00
**Priority**: medium
**Context**: Rebuilding Bayern Trip dashboard with inline databases so users see participant lists directly on section pages.
**What failed**: link_to_page with database_id failed for inline databases: Notion requires a collection_view_page/database page target.
**Fix**: Do not link inline databases from dashboard. Link the containing section pages instead; inline databases appear inside those pages.
**No secrets logged**: yes

## [ERR-20260518-001] notion_update_schema_mismatch

**Logged**: 2026-05-18T19:57:00+02:00
**Priority**: medium
**Status**: resolved
**Area**: integration

### Summary
Bayern Trip Notion update script failed because the script used a non-existent database property `Notizen` for a database that uses a different note property name.

### Details
Notion API returned `400 validation_error Notizen is not a property that exists.` while upserting rows. The fix is to inspect/align with the actual database schemas before writing rows.

### Suggested Action
For future Notion update scripts, fetch database schemas or reuse existing script property names before creating/updating records.

### Metadata
- Source: error
- Related Files: data/bayern_trip/update_from_whatsapp_2026-05-18.mjs
- Tags: notion, schema, bayern-trip

---

## [ERR-20260518-002] eos_cli_without_venv

**Logged**: 2026-05-18T22:22:00+02:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
Running `python3 -m src.eos_cli ...` failed because the system Python lacked `jsonschema`.

### Details
The EOS CLI should be run via `.venv/bin/python` in this workspace, as documented by existing cron jobs.

### Suggested Action
Use `EOS_DB_PATH=data/eos_v2.db .venv/bin/python -m src.eos_cli ...` for EOS CLI commands.

### Metadata
- Source: error
- Tags: eos-cli, python, venv

---

## [ERR-20260518-003] pdf_tool_unavailable

**Logged**: 2026-05-18T22:29:00+02:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
PDF analysis tool failed due unavailable/invalid provider credentials and disabled extraction fallback.

### Details
While analyzing Via Claudia booking PDFs, the PDF tool failed across Anthropic, Gemini, OpenAI, and Codex routes. Fallback should use local text extraction tools such as `pdftotext` when available.

### Suggested Action
Use local extraction first for small text PDFs, then model analysis only if necessary.

### Metadata
- Source: error
- Related Files: data/bayern_trip/email_attachments/BB-054075.pdf, data/bayern_trip/email_attachments/OR-031088.pdf
- Tags: pdf, extraction, tooling

---

## [ERR-20260519-001] python_requests_missing

**Logged**: 2026-05-19T10:58:30+02:00
**Priority**: low
**Status**: pending
**Area**: tooling

### Summary
A quick Python web-scraping helper failed because the `requests` module is not installed in this workspace/runtime.

### Details
Command used `import requests` to fetch camping website pages and extract snippets; runtime raised `ModuleNotFoundError: No module named 'requests'`.

### Suggested Action
Use Python stdlib `urllib.request` for quick fetch scripts unless dependency availability is verified, or use `web_fetch` for simple extraction.

### Metadata
- Source: error
- Tags: python, dependencies, web-fetch

---

## [ERR-20260519-002] browser_start_timeout

**Logged**: 2026-05-19T10:59:30+02:00
**Priority**: low
**Status**: pending
**Area**: tooling

### Summary
OpenClaw browser start timed out while trying to inspect a campsite online booking flow.

### Details
`browser(action=start)` returned: timed out; suggested restarting OpenClaw gateway. Continued with `web_fetch` and direct website content instead of browser automation.

### Suggested Action
For future booking-flow checks, first run browser status/start early or use non-browser fetch/search if only public text is required.

### Metadata
- Source: error
- Tags: browser, timeout, web-research

---

## [ERR-20260519-003] pdf_tool_unavailable

**Logged**: 2026-05-19T11:00:30+02:00
**Priority**: low
**Status**: pending
**Area**: tooling

### Summary
The PDF analysis tool failed for a public campsite price-list PDF due provider/API/document-extract limitations.

### Details
Anthropic had insufficient credit, Gemini API key invalid, and OpenAI/Codex PDF extraction unavailable without document-extract plugin.

### Suggested Action
Use local utilities such as `pdftotext`/`python` fallback for public PDFs when the model PDF tool is unavailable.

### Metadata
- Source: error
- Tags: pdf, api, fallback

---

## [ERR-20260519-001] pdf_tool_provider_failures

**Logged**: 2026-05-19T19:45:00+02:00
**Priority**: medium
**Status**: pending
**Area**: integrations

### Summary
OpenClaw pdf tool could not process a local Via Claudia PDF due provider/config issues.

### Details
Attempting to analyze `artifacts/via-claudia/BB-054075.pdf` failed: Anthropic credit balance too low, Gemini API key invalid, and OpenAI/Codex PDF extraction disabled. Fallback via local `pdftotext` worked.

### Suggested Action
For small text PDFs, try `pdftotext` before model PDF analysis when provider PDF extraction is unavailable.

### Metadata
- Source: tool_failure
- Tags: pdf, gog, fallback

---

## [ERR-20260528-001] skill_path_tilde_resolution

**Logged**: 2026-05-28T00:01:40Z
**Priority**: low
**Status**: pending
**Area**: tooling

### Summary
Reading a skill path with `~` failed because the shell home in this OpenClaw runtime did not resolve to the expected `/data/.openclaw` location.

### Error
```
sed: can't read /data/.openclaw/agents/personal-assistant/agent/codex-home/home/.openclaw/skills/self-improving-agent/SKILL.md: No such file or directory
```

### Context
- Attempted to read `~/.openclaw/skills/self-improving-agent/SKILL.md`.
- Retried with `/data/.openclaw/skills/self-improving-agent/SKILL.md`, which succeeded.

### Suggested Fix
When a provided skill path contains `~`, verify the actual absolute OpenClaw path before concluding the skill is unavailable.

### Metadata
- Reproducible: unknown
- Related Files: AGENTS.md
- See Also: ERR-20260518-002

---

## [ERR-20260528-002] pytest_habit_weekly_review_denominator

**Logged**: 2026-05-28T00:04:00Z
**Priority**: medium
**Status**: pending
**Area**: tests

### Summary
The repository test suite fails in the habit weekly-review denominator test.

### Error
```
tests/verify_habit_coaching.py::test_weekly_review_denominator_includes_backfilled_statuses_before_creation
AssertionError: backfilled days plus current creation day: expected 3, got 5
```

### Context
- Full command: `EOS_DB_PATH=data/eos_v2.db .venv/bin/python -m pytest`
- Result: 236 passed, 1 failed.
- Targeted rerun of the failing test reproduced the failure.
- Current task changed docs/memory only, so this appears to be a pre-existing habit-coaching logic or test expectation issue.

### Suggested Fix
Inspect `HabitService.weekly_review` trackable-day denominator handling for statuses backfilled before habit creation.

### Metadata
- Reproducible: yes
- Related Files: tests/verify_habit_coaching.py
- Tags: pytest, habits, weekly-review

---

## [ERR-20260528-003] git_push_gh_config_not_used

**Logged**: 2026-05-28T00:07:00Z
**Priority**: medium
**Status**: pending
**Area**: tooling

### Summary
`GH_CONFIG_DIR=/data/.openclaw/gh-main-eos git push` failed because plain git did not automatically use the GitHub CLI auth file, and `gh` is not installed in this runtime.

### Error
```
fatal: could not read Username for 'https://github.com': No such device or address
/bin/bash: line 1: gh: command not found
```

### Context
- Remote is `https://github.com/endritmurati99/eos.git`.
- `/data/.openclaw/gh-main-eos/hosts.yml` contains GitHub auth, but only file names/redacted config were inspected.
- Push needs either an installed `gh` with `gh auth setup-git` or a git credential helper that reads the existing config without printing secrets.

### Suggested Fix
Install/restore `gh` in this runtime or document the safe credential-helper fallback for EOS pushes.

### Metadata
- Reproducible: yes
- Related Files: AGENTS.md
- Tags: git, github, push, auth

---

## [ERR-20260529-001] rg_unavailable

**Logged**: 2026-05-29T09:10:00Z
**Priority**: low
**Status**: pending
**Area**: tooling

### Summary
`rg` is not installed in this OpenClaw runtime.

### Error
```
/bin/bash: line 1: rg: command not found
```

### Context
- Attempted to search `MEMORY.md` for Google/OAuth/workflow context.
- Retried with `grep`, which worked.

### Suggested Fix
Use `grep` as the local fallback in this workspace unless `ripgrep` is installed later.

### Metadata
- Reproducible: yes
- Related Files: MEMORY.md
- Tags: tooling, search

---
