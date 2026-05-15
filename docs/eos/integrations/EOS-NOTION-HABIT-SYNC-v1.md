# EOS Notion Habit Sync v1

Status: proposed contract. No live Notion write enabled yet.

## Rule

EOS owns habit truth. Notion is a dashboard and planning surface.

## Databases

### 1. Habits

Properties:

- `Name` — title
- `EOS Habit ID` — rich text, unique
- `Type` — select: `build`, `reduce`, `maintain`, `recovery`
- `Status` — select: `active`, `paused`, `archived`
- `Frequency` — select: `daily`, `weekly`
- `Target Time` — text or date/time
- `Minimum Version` — multi-select or text
- `Full Version` — text
- `Replacement Actions` — multi-select/text
- `Trigger Window` — text
- `Last Synced UTC` — date

### 2. Habit Events

Properties:

- `Name` — title, generated like `2026-05-15 · Morgenroutine · done_full`
- `EOS Event ID` — rich text, unique if available
- `Habit` — relation to Habits
- `Business Date` — date
- `Status` — select: `done_full`, `done_partial`, `skipped`, `missed`, `paused`
- `Recovery Used` — checkbox
- `Failure Mode` — select/text
- `Source` — select: `telegram`, `cli`, `eos_job`, `notion_import`
- `Notes` — text
- `Created UTC` — date

### 3. Relapses

Properties:

- `Name` — title, generated like `2026-05-15 · Doomscrolling · stress`
- `Habit` — relation to Habits
- `Business Date` — date
- `Trigger` — select/text
- `Replacement Used` — select/text
- `Severity` — select: `minor`, `moderate`, `major`
- `Notes` — text
- `Created UTC` — date

### 4. Daily Habit Review

Properties:

- `Name` — title, generated like `2026-05-15 · Daily Habit Review`
- `Date` — date
- `Calendar Load` — select: `ruhig`, `mittel`, `hoch`
- `Energy` — select/text
- `Completed` — number
- `Partial` — number
- `Missed/Skipped` — number
- `Relapses` — number
- `EOS Summary` — text
- `One Improvement` — text
- `Last Synced UTC` — date

### 5. Weekly Habit Review

Properties:

- `Name` — title, generated like `2026-W20 · Weekly Habit Review`
- `Week Start` — date
- `Completion Rate` — number
- `Main Pattern` — text
- `Keep` — text
- `Change` — text
- `Add / Remove Decision` — text
- `EOS Recommendation` — text

## Templates

### Template: New Habit

Fields to fill:

- Why does this habit matter?
- Minimum version: what counts on a bad day?
- Full version: what counts on a normal day?
- Trigger/time/place.
- What breaks it?
- If `reduce`: replacement action and relapse severity scale.

### Template: Daily Check-in

Questions:

1. Which habit happened automatically today?
2. Which habit needed force?
3. Did a bad habit show up? Trigger?
4. What is the smallest adjustment for tomorrow?

### Template: Relapse Log

Questions:

1. What happened?
2. Trigger: tired, stress, boredom, procrastination, phone in bed, social pressure, hunger, frustration, unknown?
3. Replacement used or possible next time?
4. Severity: minor/moderate/major?
5. What should EOS remind you of tomorrow?

### Template: Weekly Planning — Sunday 18:00

Questions:

1. Which habit had the best completion rate?
2. Which habit failed because of schedule/load, not motivation?
3. Which bad-habit trigger repeated?
4. Keep/change/drop one thing.
5. Choose one experiment for next week.

## Sync policy

Initial version:

- Dry-run JSON only.
- No Notion write without explicit token/config and explicit approval.
- Upserts must be idempotent by `EOS Habit ID`, `EOS Event ID`, or generated deterministic key.
- Never delete Notion pages automatically in v1.
- Notion stale state must not block EOS morning/evening jobs.

Future CLI shape:

```bash
python -m src.eos_cli habits notion-export --date 2026-05-15 --dry-run
python -m src.eos_cli habits notion-export --week-start 2026-05-11 --dry-run
```
