# EOS Habit Tracker Research — 2026-05-15

Status: research + product direction. No external habit app adopted yet.

## Decision

EOS should keep habit control internally.

- Source of truth: EOS SQLite + `data/eos_state.json` habit definitions.
- Chat/Telegram: capture surface for done, skip, relapse, recovery, notes.
- Notion: optional mirror/dashboard/template layer, not primary storage.
- External habit apps: inspiration or optional future import/export, not runtime dependency.

Reason: Endrit wants EOS to analyze the day, build good habits, detect bad habits, and coach behavior. That requires raw events, triggers, recovery, calendar/task context, and daily reflections in one local model. A third-party tracker can show streaks, but it cannot reliably own EOS coaching logic.

## GitHub scan

| Project | Stars checked | Useful idea | Fit for EOS | Risk / reason not to adopt directly |
|---|---:|---|---|---|
| `iSoron/uhabits` / Loop Habit Tracker | ~9.9k | Habit score, flexible schedules, offline-first privacy, CSV/SQLite export, reminders/widgets | Very strong design reference | Android app, GPL-3.0; do not copy code into EOS. Use concepts only. |
| `HabitRPG/habitica` | ~13.9k | Positive/negative habits, rewards, penalties, gamification | Good inspiration for bad-habit tracking and immediate feedback | Heavy product/server/game model; too much for EOS. |
| `oppiliappan/dijo` | ~2.9k | Scriptable terminal habit tracker, automation hooks | Useful for EOS CLI/event hooks | Separate Rust TUI; no need to adopt. |
| `daya0576/beaverhabits` | ~1.8k | Self-hosted Python tracker, simple API, no-goals philosophy, local JSON/SQLite | Best candidate for optional visual companion or API bridge | Would add another app and auth/storage surface; EOS should still own truth. |
| `xpavle00/Habo` | ~1.3k | Privacy-first mobile tracker, E2EE/self-host option | Good mobile UX reference | Flutter app; sync layer not needed now. |
| `FriesI23/mhabit` | ~1.4k | Micro-habits and charting | Good UX/reference for tiny habits | Mobile app, not EOS-integrated. |

## Five tips to take over

1. **Keep local event history, not only current streaks.**
   Store every done/partial/skip/miss/relapse/recovery event with date, source, note, and context. EOS already has `habit_events`, `habit_daily_status`, and `habit_relapses`; this should remain the core.

2. **Use habit strength, not brittle streak worship.**
   Loop's best lesson: one missed day should not erase identity/progress. EOS should keep current streaks, but coaching should rely more on 7/14/28-day completion rate, recovery usage, and pattern signals.

3. **Model bad habits as `reduce` habits with triggers and replacements.**
   Habitica's positive/negative distinction is useful, but EOS should keep it clinical: trigger → relapse severity → replacement action → next experiment. No shame loop.

4. **Make logging one-tap / one-message.**
   Dijo and Loop win because capture is fast. EOS needs Telegram/CLI shortcuts like `wasser done`, `doomscroll relapse müde`, `abendroutine recovery`, plus a Notion/mobile dashboard later.

5. **Separate coaching truth from presentation.**
   Beaver/Habo/Loop all care about data ownership. EOS should own the truth locally and export to Notion/CSV/Beaver-style APIs only as views. If Notion is down or stale, EOS still works.

## Current EOS baseline

Already implemented:

- Habit definitions seeded from `data/eos_state.json`.
- SQLite persistence.
- `build`, `reduce`, `maintain`, `recovery` habit types.
- Failure modes.
- Relapses with trigger/replacement/severity.
- Recovery events that protect streaks.
- Deterministic weekly pattern detection.
- CLI commands under `python -m src.eos_cli habits ...`.

Current active habits:

- Morgenroutine — build.
- Abendroutine — build.
- Haengenlassen an der Klimmzugstange — build/reflection habit.

Gap: this is technically capable but not yet productized as Endrit's daily habit cockpit.

## Proposed EOS habit architecture

### 1. Internal source of truth

Use these layers:

- `habit_definitions`: identity, type, target time, schedule, minimum/full version, aliases.
- `habit_events`: raw event log.
- `habit_daily_status`: per-day final status snapshot.
- `habit_relapses`: bad-habit incidents with trigger, replacement, severity.
- future `habit_context_snapshots`: daily calendar load, sleep/energy, location/sport signal, notable notes.

### 2. Daily EOS analysis

Morning:

- show today's habits by time and minimum version.
- detect calendar load and recommend minimum/full versions.
- include one behavior experiment, not many.

Evening:

- ask for unresolved habit statuses.
- ask one day-analysis question.
- record relapses/failures without turning them into tasks.
- create a short daily habit summary.

Weekly Sunday 18:00:

- review 7-day completion rates.
- identify the strongest pattern, not every pattern.
- choose max 1 new habit and max 1 bad-habit intervention.
- update Notion/dashboard export if enabled.

### 3. Bad habits / reduce habits

Add explicit reduce habits, for example:

```json
{
  "id": "habit-reduce-doomscrolling-night",
  "name": "Abendliches Doomscrolling reduzieren",
  "status": "active",
  "frequency": "daily",
  "target_time": "21:30",
  "type": "reduce",
  "failure_modes": ["muede", "stress", "langeweile", "aufschieben", "handy_im_bett"],
  "replacement_actions": ["handy_laden_ausserhalb_bett", "2_minuten_reflexion", "buch_aufschlagen", "abendroutine_starten"],
  "trigger_window": {"start": "21:30", "end": "23:30"},
  "recovery_rule": {"fallback": "handy_weglegen_und_einen_satz_notieren"}
}
```

Do not add this silently to production state yet; first confirm the actual bad habits Endrit wants tracked.

## Notion stance

Notion is useful for visibility, not control.

Good uses:

- habit dashboard with weekly status.
- daily review database.
- templates for adding a habit, logging relapse, weekly planning.
- human-readable archive.

Bad uses:

- primary event log.
- source of truth for EOS coaching.
- live dependency for morning/evening briefing.

Recommended sync mode: one-way EOS → Notion initially. Later, Notion → EOS only for explicit habit definition edits after validation.

## Near-term implementation plan

1. Add a durable habit product spec and Notion template contract. ✅ this document + integration spec.
2. Add `habits daily-summary` command for a target date.
3. Add `habits weekly-review` command that renders Sunday review text from `week_patterns()`.
4. Add Telegram-friendly parser shortcuts for done/skip/relapse/recovery.
5. Add optional Notion exporter interface with dry-run JSON first.
6. Only then decide whether BeaverHabits should be deployed as an optional visual UI.

## Recommendation

Do not replace EOS with a GitHub habit tracker.

Use Loop/Habitica/Beaver ideas, keep EOS as the controller, and make Notion a mirror/template layer. This keeps the system local, auditable, and coachable.
