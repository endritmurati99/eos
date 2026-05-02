# EOS Manual Task Intake

## Purpose
Until Google Tasks is integrated, EOS accepts active tasks manually through chat.

## Input Format
Use this structure when asking EOS for daily planning:

```text
Plane mir heute den Tag.

Offene Aufgaben:
- ...
- ...
- ...

Optional:
- besondere Priorität: ...
- was ich nicht vergessen darf: ...
- Energie heute: niedrig | mittel | hoch
- verfügbar für Deep Work: ...
```

## Parsing Rules
- Treat each bullet under `Offene Aufgaben` as a manual active task
- If no priorities are given, EOS ranks tasks by urgency, importance, and fit to available windows
- If no energy level is given, assume `mittel`
- If no deep-work availability is given, infer from live hard events in Google Calendar
- Manual tasks are temporary planning inputs unless explicitly written into a system later

## Output Contract
Daily Planning must always return exactly these sections:
- Harte Termine heute
- Top-3 Aufgaben
- Deep-Work-Block
- Sportblock
- Nicht vergessen
- Warnung bei Überladung
