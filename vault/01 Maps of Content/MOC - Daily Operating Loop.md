# MOC - Daily Operating Loop

Purpose: one navigable map for EOS morning, day, evening, and review loops.

## Core notes

- [[EOS Morning and Evening Booklet]] — prompt contract and iteration notes
- [[EOS Dashboard]] — operator cockpit
- [[EOS Current Status]] — implementation/readiness state
- [[EOS Open Issues]] — blockers and pending decisions
- [[ADR - Calendar as Source of Truth]] — hard-time source of truth
- [[ADR - Tasks as Source of Truth]] — active-task source of truth

## Daily loop

1. **Morning** — show calendar shape, hard anchors, Deep Sessions/reminders, one focus, minimum routine.
2. **During day** — use `/ask` / `jetzt` for next best action; no external writes without approval.
3. **Tagesstand capture** — when Endrit says what happened today, write the durable summary into `11 Daily Notes/YYYY-MM-DD.md`.
4. **Evening** — preview tomorrow's calendar shape, open loops, prep/carry items, one recommendation.
5. **Review** — record what was stable, what stayed open, energy-loss driver, and tomorrow's minimum.

## Design rules

- Calendar facts come from Google Calendar or explicitly marked stub/test data.
- Task facts come from Google Tasks or explicit user input; never invent Top-3 priorities.
- Daily Notes are the handoff memory for new sessions: Tagesstand, Heute gemacht, Nächste Schritte, Aktive Projekte, Nicht weiter nutzen.
- Markdown notes are navigation and memory, not hidden automation truth.
- Wikilinks should point to stable EOS notes, ADRs, projects, and runbooks.
- Keep chat brief; put durable context here.
