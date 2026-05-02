# EOS Daily Calendar Aggregation

## Goal
Read hard events live from Google Calendar for daily planning.

## Required calendars
At minimum aggregate:
- `primary` (`endrit.murati99@gmail.com`)
- `Sport` (`0a2994f0d433fcc6c52655f05f2266a4d3ea6fece247ea6df59ed6cb89785860@group.calendar.google.com`)

## Timezone
- Always use `Europe/Berlin`
- Daily boundaries are local-day boundaries in `Europe/Berlin`

## Aggregation Logic
1. Query each relevant calendar separately for `today 00:00` to `tomorrow 00:00` in `Europe/Berlin`
2. Normalize all returned events to local Berlin time
3. Merge into one ordered list by start time
4. Preserve source calendar for traceability
5. Treat the merged result as the hard-event set for the day
6. Ignore `data/calendar.json` as a primary source

## Minimum command shape
```bash
TZ=Europe/Berlin gog calendar events <calendarId> --from YYYY-MM-DDT00:00:00+02:00 --to YYYY-MM-DDT00:00:00+02:00 --json --no-input
```

## Output use
The merged live event list feeds:
- Harte Termine heute
- free-window detection
- overload detection
- sport/preparation reminders
