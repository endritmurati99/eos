# EOS Google Tasks Integration

## Goal
Use Google Tasks as the real active-task source for EOS.

## Target Path
Use direct Google Tasks API access with OAuth 2.0 user consent and refresh-token persistence.
Reason: headless-safe architecture, no forced proxy dependency, and aligned with the EOS production target.

## Optional Bridge Path
A Maton-based gateway path may be used as a temporary bridge if it is explicitly accepted and configured.
It is a bridge option, not the normative EOS target architecture.

## Scope v1
- `list_structure`
- `task_read`
- `task_create`
- `task_complete`

## List Structure v1
- `Inbox` = default capture, untriaged
- `Next` = directly executable
- `Waiting` = blocked by another person or an external dependency
- `This Week` = relevant this week, but not a calendar event

## Task Read Shape
- Default read = open tasks from all four lists
- Read order = `Inbox`, `Next`, `Waiting`, `This Week`
- Explicit list request = read only that list
- Explicit `taskId` = resolve exactly that task
- Title-based read = only when the title is unique across open tasks
- Ambiguous title = exactly one short clarification

## Task Create Shape
- Required field: `title`
- Optional fields: `notes`, `due`, explicit target list
- Without explicit target list, EOS creates the task in `Inbox`
- New tasks start with `status = needsAction`
- EOS does not auto-triage or auto-move newly created tasks

## Task Complete Shape
- Resolve by `taskId` first, otherwise by unique title across open tasks
- Completion happens in place via `status = completed`
- EOS does not delete, move, or clear tasks as part of completion
- Completed tasks disappear from the default open-task read

## EOS Policy
- Google Tasks is the source of truth for active and open tasks
- `This Week` is a real Google Tasks list, not a derived view
- Default task reads exclude `completed`, `deleted`, and `hidden` items
- EOS does not mix task operations with Calendar or Vault side effects in this layer

## Out of Scope v1
- delete tasks
- move tasks
- clear completed tasks
- rename-list refactors
- Scheduler coupling
- Calendar coupling
- Vault coupling

## Blocking Requirement
Direct production use still requires a headless-safe OAuth 2.0 setup with stable refresh-token storage.
