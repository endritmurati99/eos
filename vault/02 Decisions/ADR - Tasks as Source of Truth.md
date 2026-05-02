# ADR - Tasks as Source of Truth

## Status
Accepted

## Context

EOS needs one authoritative system for active open tasks.

Without a single source of truth for tasks, EOS will drift into problems such as:
- tasks living partly in chat, partly in notes, partly in local files
- duplicate tasks across systems
- planning based on stale task lists
- reviews that cannot tell what is truly still open

EOS already distinguishes between:
- hard time commitments
- open work
- knowledge and context
- derived operational state

Tasks therefore need their own dedicated authority.

## Decision

Google Tasks is the intended single source of truth for active open tasks.

Google Tasks should hold the live list of active operational work, especially:
- new actionable items
- short-term next actions
- waiting items
- current-week commitments

EOS may accept tasks from chat as capture input.
EOS may reference tasks in vault notes.
Neither chat capture nor vault notes may replace Google Tasks as the primary long-term source of truth for active open tasks.

## Minimal scope for Tasks v1

The first production-capable task layer should stay minimal:

- read open tasks
- create new tasks
- complete tasks
- map tasks to a small fixed list structure

Recommended lists:
- Inbox
- Next
- Waiting
- This Week

## What this means operationally

### EOS may use Google Tasks to:
- read the current open task set
- add a new task
- mark a task complete
- use tasks in daily planning
- use tasks in weekly planning
- use tasks in evening reset and reviews

### EOS may not:
- invent persistent tasks from vague context
- treat vault notes as the definitive active task list
- silently maintain competing local task systems
- auto-reschedule or bulk-rewrite tasks without an explicit contract
- pretend that chat capture is a sufficient long-term task system

## Implications

### Positive
- one authoritative list of active work
- cleaner daily and weekly planning
- easier task review and completion tracking
- better separation between planning, knowledge, and execution

### Negative
- Google Tasks auth/runtime becomes operationally important
- tasks must degrade gracefully if the integration is unavailable
- capture workflows need a disciplined routing path into the real task system

## Failure behavior

If Google Tasks is unavailable:
- EOS must not pretend that live task data is available
- EOS may temporarily fall back to chat-provided tasks
- EOS must clearly mark that fallback as provisional
- EOS must continue planning with reduced confidence instead of silently hallucinating a full task state

## Non-goals

This decision does not mean:
- every thought becomes a task
- the vault should stop storing context
- all project context belongs in Google Tasks
- Tasks must model full project management complexity

## Relationship to other systems

### Google Calendar
Calendar remains the source of truth for hard events and fixed time blocks.

### Vault
Vault remains the source of truth for:
- brain dumps
- daily notes
- ideas
- project context
- operator knowledge

The vault may reference tasks, but it does not become the active task system.

### Derived state
Local state stores may keep:
- snapshots
- review data
- idempotency metadata
- summaries

They are not allowed to become the primary active task source.

## Consequences for implementation

Technical and behavioral documents should align with this decision:

- daily planning should prefer live task data over ad hoc copied lists
- weekly planning should use the real open task set
- evening reset should look at unresolved tasks
- reviews should use task history and snapshots only as derived analytical state
- brain-dump routing should move actionable items into Google Tasks, not leave them floating in notes indefinitely

## Review trigger

Revisit this ADR only if:
- Google Tasks is intentionally replaced
- EOS adopts a different authoritative task system
- the operational scope of tasks changes fundamentally

---

## Related

- [[ADR - Calendar as Source of Truth]]
- [[MOC - Tasks]]
- [[MOC - Planning]]
- [[MOC - Vault]]
- [[EOS Dashboard]]
- [[EOS Open Issues]]
