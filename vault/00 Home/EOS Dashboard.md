# EOS Dashboard

Operator cockpit — real state at a glance.

**As of 2026-04-22**

---

## What Works Now

| System | State | Notes |
|--------|-------|-------|
| Telegram → EOS | ✓ Operational | Direct channel for planning and brain dumps |
| Planning policy | ✓ Specified | Daily + weekly logic defined, ready to execute manually |
| Vault structure | ✓ File-based | Folders 10–15, 90 in place; not yet live Obsidian backend |
| Google Calendar READ | ⚠ Technically verified | Blocked in production by keyring config (BLK-001, BLK-002) |
| Google Calendar WRITE | ⚠ Technically verified | E2E path spec'd; not yet enabled operationally |

---

## What Blocks Now

| Issue | Impact |
|-------|--------|
| **[BLK-001]** `GOG_KEYRING_PASSWORD` not set | Calendar read unavailable → pilot blocked |
| **[BLK-002]** Keyring file permissions | Calendar read unavailable → pilot blocked |
| **[PEND]** Google Tasks implementation (auth + v1) | Role decided via [[ADR - Tasks as Source of Truth]]; auth path and Tasks v1 still to build |

---

## Next 3 Actions

1. **Fix gog keyring** (BLK-001 + BLK-002) — unblocks calendar read, starts the pilot
2. **Run 7-day Phase 1 pilot** — daily Telegram planning with live calendar context
3. **Build Google Tasks v1** — auth + read/create/complete, per [[ADR - Tasks as Source of Truth]]

---

## Quick Navigation

→ **[[EOS Current Status]]** — Phase breakdown and system readiness  
→ **[[EOS Open Issues]]** — All blockers and pending decisions  
→ **[[MOC - Daily Operating Loop]]** — Morning/day/evening operating loop
→ **[[EOS Morning and Evening Booklet]]** — Current booklet contract and iteration notes
→ **[Daily Notes](../11%20Daily%20Notes/)** — Daily hubs  
→ **[[MOC - Architecture]]** — System overview  
→ **Decisions** — [[ADR - Calendar as Source of Truth]] · [[ADR - Tasks as Source of Truth]]  

---

## System Identity

- **Agent**: `personal-assistant` (EOS)
- **Workspace**: `/data/.openclaw/workspaces/personal-assistant`
- **Timezone**: Europe/Berlin
