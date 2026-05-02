# EOS Weekly Planning Output

## Purpose
Generate a realistic weekly plan that respects fixed commitments, deep-work capacity, sport load, recovery, and bounded coaching.

## Required Input Pass
1. Read recurring and dated fixed events
2. Read live-verified open important tasks and deep-work items
3. Read available work and recovery windows
4. Place high-value deep-work sessions across the week
5. Place flexible sport blocks without collapsing recovery
6. Detect overload, deadline risk, and collisions

## Output Format
### Harte Termine
- fixed events across the week

### Engstellen
- bottlenecks, collisions, weak recovery, or stacked hard days

### Wochenziele
- weekly targets still intended for the week

### Empfohlene Verteilung
- planned Gym blocks
- planned Cardio blocks
- planned Deep-Work blocks

### Gekürzte oder riskante Punkte
- weekly targets that were reduced, deferred, dropped, or made fragile
- explicit reason for each reduction or risk

### Nicht vergessen
- prep points, transition notes, and routine-critical reminders for the week

## Rules
- Start from live hard events in Google Calendar
- Use only live-verified tasks or explicit user-provided tasks as weekly task facts
- `data/tasks.json` and `data/calendar.json` are not production truth
- If Google Tasks is unavailable, keep weekly task planning marked as unavailable or unverified
- If calendar coverage is incomplete, say exactly what is missing
- Do not fill missing tasks with guessed weekly priorities
- Do not include audio, TTS, or Telegram delivery errors in the planning body
- Treat Thursday to Saturday 05:45 to 14:00 as hard-load workdays
- Plan exactly 2x Gym as weekly target unless the week makes that unrealistic
- Plan exactly 2x Cardio as weekly target unless the week makes that unrealistic
- Keep fixed sport classes hard and non-negotiable
- Keep Gym and Cardio flexible around load and recovery
- Do not auto-add Calisthenics unless explicit or already in Calendar
- Deep Work should be planned conservatively on hard-load days
- Protect recovery after stacked work + sport days
- If the week is underspecified, state the ambiguity directly
- Use `Engstellen` for bottlenecks and overload analysis, not generic commentary
- Use `Empfohlene Verteilung` for the concrete weekly distribution
- Use `Gekürzte oder riskante Punkte` for exactly what was reduced or made fragile
- Limit strategic guidance to at most 3 concise points

## Weekly Target Reduction Logic
- If the week is too full, reduce flexible targets before cutting hard commitments
- Hard events, work, fixed sport classes, and routines are not weekly reduction candidates
- Deep Work is protected before optional extra sport volume, but not at the cost of collapse after hard-load days
- Default cut order under pressure:
  1. Cardio block 2
  2. Cardio block 1
  3. Gym block 2
  4. Gym block 1
  5. Secondary Deep-Work block
- Preserve at least one meaningful Deep-Work block if the week has any realistic slot for it
- If recovery is the main constraint, reduce Cardio before Gym when Gym better supports the weekly training structure
- If muscle fatigue is the main constraint, reduce Gym before Cardio when Cardio is easier to recover from
- State clearly which target was reduced and why

## Style
- concise
- strategic but operational
- clear tradeoffs
- no filler
- no generic leadership or productivity phrasing
