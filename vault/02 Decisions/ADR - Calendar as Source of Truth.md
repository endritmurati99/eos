# ADR - Calendar as Source of Truth

## Status
Accepted

## Context

EOS needs one authoritative system for hard events and fixed time blocks.

Without a single source of truth for time, EOS will drift into contradictions such as:
- different event times in different notes
- planning based on stale or manually copied data
- scheduler jobs acting on old assumptions
- false certainty in daily and weekly planning

EOS operates across multiple layers:
- `docs/` for technical truth
- `vault/` for navigation and knowledge
- integrations for external systems
- scheduler and review logic for derived operational behavior

A clear time authority is therefore mandatory.

## Decision

Google Calendar is the single source of truth for:

- hard events
- fixed appointments
- work shifts
- fixed sport classes
- explicit time blocks that must be treated as calendar reality

EOS must treat Google Calendar as the authoritative time system.

The vault may reference calendar context.
Derived local state may cache or summarize calendar context.
Neither the vault nor local derived state may replace Google Calendar as the primary truth for hard time commitments.

## What this means operationally

### EOS may use Google Calendar to:
- read hard events
- create new hard events
- update events
- delete events, if the action contract allows it
- aggregate calendars for planning

### EOS may not:
- invent hard events from vague text
- treat Daily Notes as the primary calendar
- treat brain dumps as confirmed hard events
- override Google Calendar with local markdown notes
- silently assume that copied calendar data is still current

## Implications

### Positive
- one authoritative timeline
- cleaner daily planning
- consistent weekly planning
- scheduler jobs can rely on one real calendar source
- easier debugging when a time conflict appears

### Negative
- calendar runtime/auth issues become operationally important
- if live calendar access fails, EOS must degrade gracefully
- manual notes that conflict with the calendar must lose

## Failure behavior

If Google Calendar is unavailable:
- EOS must not pretend that hard events are known with certainty
- EOS may fall back to previously cached or user-provided context only if it is clearly marked as provisional
- EOS must distinguish between:
  - live verified calendar state
  - provisional or stale context

## Non-goals

This decision does not mean:
- every planning suggestion must become a calendar event
- the vault becomes irrelevant
- Google Calendar must hold all knowledge
- Tasks belong in the calendar by default

## Relationship to other systems

### Google Tasks
Google Tasks is intended to become the source of truth for active open tasks, not hard time.

### Vault
The vault is the source of truth for:
- brain dumps
- daily notes
- ideas
- long-term context
- operator knowledge

It may reference calendar information, but it does not replace the calendar.

### Derived state
Local databases or state files may store:
- snapshots
- job history
- review summaries
- idempotency state

They are never the primary calendar truth.

## Consequences for implementation

Technical and behavioral documents should align with this decision:

- daily planning must read real calendar context first
- weekly planning must start from real calendar structure
- scheduler jobs must perform a fresh calendar read before sending
- evening reset and review logic may summarize calendar behavior, but not replace it
- vault writeback must reference the calendar, not compete with it

## Review trigger

Revisit this ADR only if:
- Google Calendar is intentionally replaced as the time authority
- multiple calendar systems are introduced
- EOS moves to a fundamentally different time-source architecture

---

## Related

- [[ADR - Tasks as Source of Truth]]
- [[MOC - Architecture]]
- [[MOC - Scheduler]]
- [[MOC - Planning]]
- [[EOS Dashboard]]
- [[EOS Open Issues]]
