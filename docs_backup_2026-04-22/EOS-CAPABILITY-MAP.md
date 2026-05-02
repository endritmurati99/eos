# EOS Capability Map

## Identity
- Agent: `personal-assistant`
- Display name: `EOS (Personal Assistant)`
- Interface: dedicated Telegram bot routed to agent `personal-assistant`
- Workspace: `/data/.openclaw/workspaces/personal-assistant`

## Current Live Capabilities
### Calendar
- Provider: Google Calendar via local `gog` CLI
- Access: Read verified and live
- Write path: not yet production-verified
- Primary use: hard events and fixed time blocks
- Relevant calendars:
  - `primary` (`endrit.murati99@gmail.com`)
  - `Sport` (`0a2994f0d433fcc6c52655f05f2266a4d3ea6fece247ea6df59ed6cb89785860@group.calendar.google.com`)
- Timezone: `Europe/Berlin`
- Write policy: disabled by default for production use until explicitly approved

### Tasks
- Current mode: manual intake via chat
- Planned mode: Google Tasks integration as primary active-task source
- Status: not yet production-ready

### Obsidian / Vault
- Architectural role: Markdown vault, not GUI app dependency
- Required integration model: filesystem-based vault path with stable folder structure
- Status: planned, not yet mounted into EOS production flow

## Internal Capability Areas
- `calendar_reader`
- `planner`
- `routine_engine`
- `task_intake`
- `obsidian_writer` (planned)
- `review_engine` (planned)

## Data Access Rules
- Google Calendar is the primary source of truth for hard events
- Google Tasks will become the primary source of truth for active tasks
- Obsidian vault will become the primary source for brain dumps, daily notes, long-term context, and linked notes
- `data/calendar.json` is test/fallback only, not primary
- `data/tasks.json` is a temporary stub only, not final production storage

## Current Constraints
- Containerized / headless environment assumptions must be respected
- GUI-first assumptions are invalid for Vault integration
- Any persistent vault path must be explicitly mounted and stable
- Write actions to external systems must stay controlled and approval-aware
