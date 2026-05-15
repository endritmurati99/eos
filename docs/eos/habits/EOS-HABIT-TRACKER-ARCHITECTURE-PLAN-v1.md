# EOS Habit Tracker Architecture Plan v1

## Decision

EOS should keep **SQLite as the local source of truth** for habits. Telegram, audio briefings, and Notion are presentation/control surfaces only.

The architecture is right in direction:

- `habit_definitions` stores the habit contract.
- `habit_events` is the append-only audit trail.
- `habit_daily_status` is the current daily projection/cache.
- `habit_relapses` stores extra detail for reduce-habits.

This is stronger than a simple streak tracker because EOS can reason about partial days, skipped days, recovery days, relapses, triggers, and replacement actions.

## Current weaknesses found by audit

### High priority

1. **Business-date consistency**
   - Habit fields are Berlin business dates, but some service defaults used host-local `date.today()`.
   - Fix: all habit defaults should use `Europe/Berlin` business date.

2. **Weekly habits need real schedule semantics**
   - The schema allowed `weekly`, but weekly habits were at risk of being treated like daily habits.
   - Fix: weekly habits without explicit schedule must not be auto-prompted or auto-missed daily.

3. **SQLite must become definitive over time**
   - Existing `data/eos_state.json` seeding is acceptable as bootstrap/migration input, but long-term runtime edits should belong to SQLite.
   - Future fix: add a one-way migration/seed mode and avoid overwriting user-edited SQLite definitions repeatedly.

4. **Event auditability is too thin for chat/audio use**
   - Telegram can duplicate messages, and users need correction/undo later.
   - Fix started: event UUID/recording metadata fields. Future: idempotency keys, supersedes/correction links, raw input hash.

### Medium priority

5. **Many-habit UX must stay selective**
   - Daily and weekly briefings must never enumerate every habit.
   - Briefings should summarize patterns, exceptions, and one next action.

6. **Reduce-habit modeling needs success signals**
   - Relapse events exist, but successful resistance/no-relapse/urge events are still missing.
   - Future: track urges resisted, trigger intensity, replacement success, duration.

7. **Notion boundary must stay strict**
   - Notion can be dashboard/mirror/template, not source of truth.
   - Sync must be idempotent, optional, and never overwrite EOS truth without explicit import flow.

## Target model before adding many habits

### Habit definition fields

Current plus planned:

- name, status, type: `build`, `maintain`, `reduce`
- frequency: `daily`, `weekly`
- timezone: default `Europe/Berlin`
- start/end dates
- schedule rule: weekdays, weekly targets, quiet days
- category/area
- salience/importance
- briefing policy: when to mention, when to stay silent
- minimum version and full version
- failure modes and replacement actions
- optional external references, e.g. Notion page id

### Event fields

Current plus planned:

- event UUID
- idempotency key
- recorded timestamp
- effective local date/time
- actor/source
- confidence
- raw input hash
- future correction/supersedes link

## UX rules

### Morning briefing

Purpose: start the day, not audit the whole habit system.

Shape:

- Today’s focus
- Fixed points
- One primary habit / minimum version
- Relevant prep check only if needed

### Evening briefing

Purpose: reflect and prepare tomorrow.

Shape:

- What happened today?
- What did not happen?
- What makes tomorrow easier?
- Short prep check, e.g. `Sporttasche gepackt?` only if sport is relevant

### Weekly review

Purpose: pattern and adjustment.

Shape:

- One strongest pattern
- One bottleneck
- One concrete change for next week
- No calendar dump, no habit dump

## Implementation phases

### Phase 1 — Foundation hardening

Status: started.

- Berlin business date defaults.
- Add metadata columns for future schedule/briefing/idempotency.
- Weekly habits without schedule do not auto-miss daily.
- Event UUID/recording metadata.
- Tests for weekly-unscheduled behavior and event metadata.

### Phase 2 — Many-habit operating layer

- Add CLI/API fields for category, salience, schedule rule, briefing policy.
- Add habit groups: morning, day, evening, reduce.
- Add notification budget: max morning nudge, max evening review, no per-habit spam.
- Rewrite visible summaries to show top exceptions only.
- Add correction/undo command.

### Phase 3 — Intelligence and dashboard

- Add reduce-habit urge/resistance events.
- Add weekly pattern confidence/sample-size guardrails.
- Add optional Notion mirror with EOS-owned IDs.
- Add dashboard views, not dashboard truth.

## Recommendation

Do not add dozens of habits directly yet.

First add habits in a curated v1 batch:

- 3–5 anchor habits
- 2–3 health/body habits
- 1–3 reduce habits

Then observe one week, improve schedule/briefing policy, and only then expand.
