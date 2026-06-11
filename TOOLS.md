# TOOLS.md - EOS Tool Reference

## EOS CLI

Working directory: `/data/.openclaw/workspaces/eos`

```bash
python3 -m src.eos_cli health
python3 -m src.eos_cli habits status
python3 -m src.eos_cli habits handle "<message>"
python3 -m src.eos_cli dispatch handle "<message>"
python3 -m src.eos_cli energy today
python3 -m src.eos_cli daily-plan --date YYYY-MM-DD --dry-run
python3 -m src.eos_cli weekly-plan --week-start YYYY-MM-DD --dry-run
python3 -m src.eos_cli run-job daily_morning --no-dry-run
python3 -m src.eos_cli run-job evening_briefing --no-dry-run
python3 -m src.eos_cli run-job weekly_sync --no-dry-run
python3 -m src.eos_cli run-job habit_checkin_evening --no-dry-run
python3 -m src.eos_cli cron-audit
python3 -m src.eos_cli model-audit
```

## Google Calendar (gog)

```bash
gog auth status
gog calendar list --tz Europe/Berlin
gog calendar events --calendar primary --date YYYY-MM-DD
gog calendar events --calendar Sport --date YYYY-MM-DD
gog calendar create --calendar primary --title "..." --start "..." --end "..."
```

Status: auth broken (keyring permission error — ERR-20260421-001). Stub mode active.

## Google Tasks

```bash
gog tasks list
gog tasks create --title "..."
gog tasks complete --id "..."
```

Status: 403 accessNotConfigured (ERR-20260428-001). Tasks API not enabled in Google Cloud project.

## Database

- Path: `data/eos_v2.db`
- Schema: `data/eos_state.schema.json`
- State: `data/eos_state.json`

## Telegram Delivery

- Bot account: `eos`
- User chat ID: `<telegram-chat-id>`
- Delivery via OpenClaw announce: `delivery.mode = "announce", to = "telegram:<telegram-chat-id>"`

## Skills Available

| Skill | Path | Trigger |
|-------|------|---------|
| self-improving-agent | `/data/.openclaw/skills/self-improving-agent/` | `/self-improvement` or auto at 02:00 |
| graphify | `/data/.openclaw/skills/graphify/` | `/graphify` |
| hhmail | `/data/.openclaw/skills/hhmail/` | `/hhmail` |
| model-switch | `/data/.openclaw/skills/model-switch/` | `/model-switch` |

## Web Tools

- Web search: DuckDuckGo (enabled, max 5 results, 15min cache)
- Web fetch: enabled (max 50k chars, readability mode on)
- Browser: Chromium headless (available for JS-heavy pages)

## Vault Structure

```
vault/
  10 Inbox/      — unprocessed inputs
  12 Projects/   — active projects
  13 Areas/
    Wandern/     — hiking context
    Fitness/     — training context
    Uni/         — university context
    Work/        — work context
  15 Ideas/      — ideas for later
```
