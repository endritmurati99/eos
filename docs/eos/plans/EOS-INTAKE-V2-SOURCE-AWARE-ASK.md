# EOS Intake v2 — Source-Aware Ask Router

Status: initial implementation plan and v1 baseline

## Goal

EOS should accept normal user questions and route them through a controlled operational pipeline:

```text
free text question
→ intent routing
→ source selection
→ read-only context snapshot
→ safety gate
→ short source-aware answer
→ next action
```

This is not a general chatbot. It is a deterministic ask router with explicit sources and uncertainty.

## v1 Scope

Allowed:

- CLI `ask "..."`
- CLI `intake route "..."`
- deterministic intent routing
- deterministic source selection
- existing read-only/dry-run assistant surfaces as context
- answer contract: Antwort / Warum / Nächste Aktion / Unsicherheit
- synthetic tests

Not allowed in v1:

- new external APIs
- Gmail writes
- Calendar writes
- Google Tasks writes
- Drive content ingestion
- autonomous actions
- claiming meeting context without implemented historical search

## Initial Intents

- `daily_status`
- `next_best_action`
- `open_loops`
- `mail_review`
- `meeting_lookup`
- `weekly_review`
- `journal_reflection`
- `system_health`

Future intents can include `meeting_brief`, `calendar_conflict`, `task_review`, and `habit_checkin` once the data surfaces are stronger.

## Design Principle

The user should not need slash commands for normal use. Slash commands remain debug/fallback. The primary user experience is free text.
