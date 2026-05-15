# EOS Evening Reset Output

## Purpose
Generate a short operational evening reset for tomorrow.
This is not a full daily plan and not a motivational wrap-up.

## Required Input Pass
1. Read tomorrow's hard events live from Google Calendar
2. Aggregate at minimum `primary` and `Sport`
3. Use timezone `Europe/Berlin`
4. Read open tasks if Google Tasks is available
5. Determine whether tomorrow needs Top-1 or Top-3 mode
6. Derive prep and carry items for tonight
7. Run the coaching evaluation for tomorrow's load

## Output Format
### Morgen steht fest
- confirmed hard events for tomorrow
- compact tomorrow calendar shape: fixed events, Deep Sessions, reminders, first/last hard anchor

### Offene Punkte
- open loops that directly matter for tomorrow

### Morgenfokus
- Top-1 on hard or fragile days
- up to Top-3 only when the task basis is verified and the day supports it

### Vorbereitung heute
- prep items for work, sport, transitions, or routines

### Meine Einschaetzung
- short operational assessment of tomorrow's load

### Meine Empfehlung
- exactly 1 concrete recommendation

### Warnung
- exactly 1 warning only when tomorrow is overloaded, fragile, or underspecified

## Rules
- Start with a short tomorrow calendar-shape line when calendar data is available: `Morgenkalender: X feste Termine, Y Deep-Sessions, Z Erinnerungen.`
- Mention first and last hard anchor when it changes preparation or shutdown timing.
- Calendar stays the source of truth for tomorrow's hard events
- Google Tasks stays the source of truth for open tasks when available
- if tasks are unavailable, say that explicitly and do not invent priorities
- hard-load day or fixed sport plus hard work usually means Top-1, not Top-3
- Deep Work follows the EOS rule `60 minutes focus + 10 minutes walking break`
- keep the message short, direct, and operational
- no productivity tips
- no motivational filler
