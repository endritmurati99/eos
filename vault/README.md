# EOS Vault

Human navigation, knowledge, and operations layer for EOS.

This vault does not replace the technical specifications in `docs/`.
It sits next to `docs/` inside the same workspace and serves a different role:

- `docs/` = technical source of truth
- `vault/` = human navigation, status, decisions, runbooks, and working context

## Start here

- [[EOS Dashboard]]
- [[EOS Current Status]]
- [[EOS Open Issues]]
- [01 Maps of Content/](01%20Maps%20of%20Content/)
- [02 Decisions/](02%20Decisions/) — [[ADR - Calendar as Source of Truth]], [[ADR - Tasks as Source of Truth]]

## What belongs here

This vault is for:

- navigation
- operator context
- current system status
- open issues
- decisions and ADRs
- runbooks
- daily notes
- weekly reviews
- brain dumps
- project notes
- idea notes

This vault is not the place for canonical technical contracts or implementation truth.
Those stay in `docs/`.

## Workspace model

Workspace root:

`/data/.openclaw/workspaces/personal-assistant`

Within that root:

- `docs/` contains canonical technical specifications
- `vault/` contains the human-facing operational layer
- `templates/` contains reusable output and intake templates
- `integrations/` contains technical integration notes and artifacts

## Folder structure

### Navigation
- `00 Home/` → dashboard, status, open issues
- `01 Maps of Content/` → navigation by topic
- `02 Decisions/` → Architecture Decision Records (binding source-of-truth decisions)

### Working knowledge
- `10 Inbox/` → raw brain dumps
- `11 Daily Notes/` → daily context and history
- `12 Projects/` → active committed projects
- `13 Areas/` → stable areas of responsibility
- `14 Knowledge/` → operator knowledge and reference material
- `15 Ideas/` → exploratory ideas
- `90 Archive/` → closed or archived content

## Note types & naming

| Type | Path | Format |
|------|------|--------|
| `brain_dump_note` | `10 Inbox/YYYY-MM-DD-HHmm-brain-dump.md` | Raw capture, later triaged |
| `daily_note` | `11 Daily Notes/YYYY-MM-DD.md` | Daily hub: context, tasks, projects, log |
| `project_note` | `12 Projects/<slug>.md` | Active committed project |
| `idea_note` | `15 Ideas/<slug>.md` | Exploratory or uncommitted idea |

Linking standard:
- Wikilinks are allowed in `vault/`
- Relative Markdown links are preferred when linking into `docs/`
- No YAML frontmatter required

## Systems of record

| System | Primary role | Current state |
|--------|--------------|---------------|
| Google Calendar | Hard events and fixed time blocks — formalized in [[ADR - Calendar as Source of Truth]] | Technically verified, but runtime path still blocked until keyring issue is fixed |
| Google Tasks | Active open tasks — formalized in [[ADR - Tasks as Source of Truth]] | Target system, not yet live as the primary task backend |
| Obsidian Vault | Brain dumps, daily notes, ideas, context | File structure exists, live persistent backend and writeback still pending |

## How to read this vault

Use this vault to:
- understand the system
- see the current state
- track open issues
- navigate to the right technical specification
- operate EOS day to day

Use `docs/` to:
- define behavior
- define contracts
- define architecture
- define technical rollout and tests

Do not treat workflow descriptions in this file as proof that the automation is already live.

## Workflow maturity levels

### Live now
- Manual planning via Telegram
- Manual task intake via chat
- Brain dump capture into the vault structure
- Human navigation through dashboard, status, issues, and MOCs

### Defined, but not yet fully live
- Google Tasks as the primary task system
- Scheduler-based reminders and briefings
- Evening Reset and Weekly Review automation
- Vault writeback from EOS into daily notes and linked notes

## Target workflows

These are target workflows, not guaranteed-live automation paths.

### Brain dump intake
1. Capture in Telegram
2. Store in `10 Inbox/`
3. Triage into one of:
   - task
   - fixed event
   - idea
   - project
   - reference note
4. Link the result into the current daily note
5. Archive the processed raw dump

Reference:
- [MOC - Vault.md](01%20Maps%20of%20Content/MOC%20-%20Vault.md)
- [docs/EOS-VAULT-v1.md](../docs/EOS-VAULT-v1.md)

### Daily planning
1. Read current calendar context
2. Read current task context
3. Generate a daily plan
4. Log results in the evening

### Project tracking
- Use one active `project_note` per committed project
- Link related daily notes, dumps, and specs
- Archive when closed

### Idea exploration
- Capture in `15 Ideas/`
- Promote to `12 Projects/` only when committed
- Archive if rejected

## Operator knowledge

For debugging, troubleshooting, and runtime operations:

- [14 Knowledge/README-RUNTIME-FIX.txt](14%20Knowledge/README-RUNTIME-FIX.txt)
- [MOC - Runtime.md](01%20Maps%20of%20Content/MOC%20-%20Runtime.md)
- [00 Home/EOS Open Issues.md](00%20Home/EOS%20Open%20Issues.md)

## Related

- [Technical Specifications Index](../docs/INDEX.md)
- [SOUL.md](../SOUL.md)
- [PLAN.md](../PLAN.md)
- [MEMORY.md](../MEMORY.md)

## Workspace root

This entire workspace is the vault root:

`/data/.openclaw/workspaces/personal-assistant`

The two-layer structure is:

- `docs/` — technical canonical specifications
- `vault/` — human navigation and knowledge layer

Both are peers in the same workspace root and are cross-linkable.