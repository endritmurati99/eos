# EOS — Plan

## Current State
- Dedicated agent routing via Telegram account `personal-assistant`
- Dedicated workspace at `/data/.openclaw/workspaces/personal-assistant`
- Current hard-event primary source: Google Calendar via `gog`
- `data/calendar.json` retained only as explicit test/dry-verification artifact, not as primary source
- `data/tasks.json` retained only as explicit test fixture; production defaults are live-only and must degrade honestly
- Local-first TTS pipeline is available through Piper-compatible runtime configuration
- Planning persona defined in `SOUL.md`

## Architecture Principle
EOS is currently isolated by routing and workspace, not by strict permissions.
That means EOS has its own inbox/bot and workspace, but not yet a hard least-privilege security boundary.

## Planning Scope v1
EOS should be able to:
1. Accept a brain dump
2. Classify items into `event`, `task`, `deep_work_block`, `routine`, `brain_dump`, `planning_request`
3. Create a daily plan
4. Create a weekly plan
5. Derive preparation and carry items
6. Detect overload
7. Route content into the correct system without mixing roles

Not in v1:
- Journal analysis beyond structured daily notes
- Autonomous folder proliferation
- Broad knowledge work outside the planning stack

## System Roles
- Google Calendar = time system of record for hard events and planned time blocks
- Google Tasks = operational system of record for active/open tasks
- Obsidian = durable system for brain dumps, daily notes, linked notes, ideas, and history

Obsidian is not a backup for Google Tasks.
Do not create new folders for each idea.
Use a stable vault structure instead.

## Daily Planning Rules
1. Read today's events
2. Read open important tasks
3. Determine available focus windows
4. Set at most 1 to 2 deep-work blocks
5. Determine top 3 tasks
6. Name carry and preparation points
7. Output a realistic execution order

### Daily Output Format
- Tagesstruktur
- Top-3
- Deep-Work-Block
- Sport
- Vorbereitung
- Warnung bei Überladung

## Object Model Rules
Do not model work, gym, courses, deep work, and brain dumps as the same thing.

### `event`
Fixed event or hard block in Google Calendar.
Examples: work, appointments, fixed sport classes.

### `task`
Concrete active task in Google Tasks without fixed time.
Examples: next actions, waiting items, this-week tasks.

### `deep_work_block`
Generic planned focus block in Calendar.
It represents reserved concentration time, not necessarily the detailed content label.

### `routine`
Contextual checklist, not a normal task.
Examples: morning routine, evening routine, BJJ bag, gym bag, workday carry list.

### `brain_dump`
Raw material that belongs in Obsidian Inbox or Daily Notes, then may be partially extracted into tasks/events.

### `planning_request`
Explicit request to generate a plan, not an executable task.

## Sport and Weekly Targets
### Fixed sports classes
Treat as `event` from Google Calendar.

### Flexible weekly targets
Plan these as flexible blocks around hard events:
- 2x Gym
- 2x Cardio
- Deep Work as generic blocks

### Routines
Morning Routine:
- Yoga Mobility
- Infrarot
- Kokosöl
- danach Skin Care

Evening Routine:
- Yoga Mobility
- Infrarot
- Kokosöl
- danach Skin Care

### Prep examples
BJJ routine:
- Gi oder No-Gi
- Wasser
- Handtuch
- Tape
- Mundschutz
- Abfahrtszeit
- Duschzeug

Gym routine:
- Kleidung
- Schuhe
- Wasser
- Kopfhörer
- Handtuch
- Snack

Workday routine:
- Laptop
- Ladekabel
- Essen
- Unterlagen
- Schlüssel

## Planning Schema
### Weekly logic
1. Read hard calendar events first
2. Block workdays
3. Trust fixed sport classes from Calendar
4. Plan 2x Gym
5. Plan 2x Cardio
6. Plan generic Deep-Work blocks
7. Account for morning and evening routines
8. Surface overload explicitly

### Daily logic
1. Read today's hard events
2. Read open tasks from Google Tasks
3. Detect free windows
4. Set only realistic blocks
5. Name Top-3 tasks
6. Add routines and carry points
7. Warn on overload

### Daily output
- harte Termine
- Top-3 Aufgaben
- Deep-Work-Block
- Sportblock
- was nicht vergessen werden darf
- Warnung bei Überladung

## Roadmap
### Phase 1 - Local Planner
- Keep local JSON as source of truth
- Generate daily and weekly plans
- Add task priorities, durations, due dates, and status schema
- Add reminder generation rules
- Add classification logic for the five planning object types

### Phase 2 - Real System Integration
- Google Calendar via `gog` as the primary time source
- Google Tasks as the primary active-task source
- Obsidian as the primary brain-dump and daily-note source
- Read-first verification before broader writes

### Phase 3 - Trusted Operational Assistant
- Conflict detection
- Deadline risk flags
- Agenda prep
- Scheduled reminder workflows
- Optional write-back to Google systems

## Current Blockers
- `gog` CLI is not installed on this host
- Google OAuth for Calendar is not configured
- `MATON_API_KEY` is missing for the installed Google Tasks connector
- Google Tasks connector currently depends on Maton-managed OAuth
- Google Tasks architecture is not yet finally decided

## Inputs Confirmed From Endrit
1. Fixed sports classes and preferred training structure were provided:
   - Monday 16:30 to 17:30 Kickboxen at HSP TU Dortmund
   - Tuesday 17:45 to 19:15 BJJ
   - Wednesday from 17:00 preferred Calisthenics outdoors
   - Thursday Kickboxen, with optional Calisthenics afterwards
   - Friday to Sunday Gym should be planned flexibly
   - Hiking and Padel are occasional or biweekly options, not fixed weekly events
2. Typical work blocks were partially provided:
   - Thursday 05:45 to 14:00
   - Saturday 06:00 to 13:30
   - general pattern still needs tighter confirmation
3. Real deep-work categories were provided:
   - Bachelor thesis
   - Web app work
   - AI/OpenClaw learning and systems building
   - AI-supported business building
4. Repeating routines were confirmed as necessary and were encoded for BJJ, gym, workday, and kickboxing/calisthenics prep
5. Gym should be treated as a flexibly planned block
6. Brain dumps should both structure information and fill the planning system

## Remaining Ambiguities
- Exact Thursday kickboxing time still needs explicit confirmation in case it differs from Monday
- Wednesday calisthenics duration is still approximate
- Thursday to Saturday work pattern may need refinement if Friday has a typical block too
- Preferred wake/sleep boundaries for daily planning are still not fully defined

## Obsidian Vault Structure
- `10 Inbox`
- `11 Daily Notes`
- `12 Projects`
- `13 Areas`
- `14 Knowledge`
- `15 Ideas`
- `90 Archive`

## Brain Dump Processing Target
1. Store raw brain dump in Obsidian Inbox
2. Extract concrete tasks into Google Tasks
3. Extract fixed events or planned blocks into Calendar only when appropriate
4. Link relevant content into Daily Notes or project/idea notes

## Immediate Next Step
Close Phase 1 as the current implementation target and run a 7-day real-life pilot with:
- Telegram as the entry point
- Google Calendar live read for hard events
- manual tasks via chat
- Daily Planning
- Weekly Planning
- overload detection

## Phase 1 Success Criteria
- usable for 7 consecutive real days
- no calendar hallucinations
- overload is called out clearly
- daily plans stay short and operational
- weekly plans respect work, fixed sport, and recovery

## After the 7-Day Pilot
If Phase 1 is stable, proceed in this order:
1. Google Tasks integration
2. Obsidian vault integration
3. review and light automation
