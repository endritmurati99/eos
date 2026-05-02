# EOS Brain Dump Intake

## Goal
Convert raw user input into vault-first EOS artifacts.

## Required Primary Output
- exactly one `brain_dump_note`

## Allowed Supporting Outputs
- `daily_note_link`
- `project_note_link`
- `idea_note_link`
- `task_candidate`
- `calendar_candidate`

## Intake Rules
- create the raw inbox note first
- preserve the raw dump before any restructuring
- add a short summary only after raw capture exists
- add exactly one link entry in the corresponding daily note
- route to project or idea only when the routing rule is justified
- prefer links over duplicated copied text
- preserve uncertainty explicitly
- do not invent dates, durations, owners, or commitment
- handoff markers document candidates only; they do not mutate external systems
- archive only after the dump has been fully triaged

## Routing Hints
### `project_note_link`
Use when all or most apply:
- explicit commitment or active ownership
- concrete outcome
- active work is already happening
- a real next step exists without invention

### `idea_note_link`
Use when all or most apply:
- speculative or exploratory
- commitment is unclear
- direction is still open
- next step is optional experiment or open question

## Handoff Marker Hints
### `task_candidate`
Actionable item that should later be handled by the task system after review.

### `calendar_candidate`
Time-bound or schedule-relevant item that may later require calendar review.

## Normalization Rules
- keep one source note per brain dump even when multiple themes appear
- keep raw phrasing when uncertainty matters
- keep optional items optional
- keep possible project and idea links separate
- keep handoff markers separate from vault routing links
