# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---

## [LRN-20260422-001] best_practice

**Logged**: 2026-04-22T06:34:00Z
**Priority**: high
**Status**: pending
**Area**: docs

### Summary
For recurring daily and weekly planning support, EOS should not stop at schedule playback and reminders. It should add direct analysis and evidence-based recommendations.

### Details
Endrit explicitly wants the assistant to act as a firmer planning coach, using external research on productive routines, executive habits, deep work protection, timeboxing, evening preparation, and energy-aware scheduling. Briefings should include tactical advice, not just calendar summaries.

### Suggested Action
Bake short plan analysis and one practical recommendation into daily briefings and weekly planning reminders, and periodically refresh the guidance from reliable web sources.

### Metadata
- Source: conversation
- Related Files: MEMORY.md, memory/2026-04-21.md
- Tags: planning, coaching, briefing, productivity

---

## [LRN-20260424-001] correction

**Logged**: 2026-04-24T06:28:05+02:00
**Priority**: high
**Status**: pending
**Area**: docs

### Summary
Morgenbriefings dürfen lokale Stub-Aufgaben nicht als gesicherte persönliche Aufgaben darstellen.

### Details
Ich habe Inhalte aus /data/.openclaw/workspaces/personal-assistant/data/tasks.json als reale, von Endrit bestätigte Aufgaben formuliert. Der Nutzer hat zurecht korrigiert, dass diese Aufgaben für ihn unbekannt wirken. Künftig muss ich lokale Stub- oder Testdaten klar als unbestätigt kennzeichnen oder für Nutzerbriefings ganz weglassen, wenn sie nicht verifiziert sind.

### Suggested Action
Für Briefings nur bestätigte Quellen verwenden, etwa Live-Kalender, explizit gepflegte Aufgabenquellen und Memory. Lokale Stub-Dateien erst nach Verifikation nutzen.

### Metadata
- Source: user_feedback
- Related Files: data/tasks.json, SOUL.md
- Tags: briefing, tasks, hallucination-prevention

---

## [LRN-20260428-001] best_practice

**Logged**: 2026-04-28T00:00:00Z
**Priority**: high
**Status**: applied
**Area**: grounding

### Summary
Produktive Planungsdefaults muessen live-only sein und bei Integrationsfehlern explizit degradieren.

### Details
Der bestaetigte Fehlerpfad war kein reines Modell-Halluzinieren, sondern ein Stub-Fallback nach fehlgeschlagenem Google-Tasks-Live-Read. Deshalb duerfen `data/tasks.json` und `data/calendar.json` nur noch bei ausdruecklichen Test- oder Dry-Verification-Flags als Quelle genutzt werden.

### Suggested Action
Briefings und Planungsjobs sollen `auth_required`, `config_missing`, `provider_disabled`, `provider_error` und `partial` als Datenqualitaet behandeln und fehlende Tasks nicht durch plausible Arbeit ersetzen.

### Metadata
- Source: open_beta_hardening
- Related Files: src/jobs/daily_capacity.py, src/gateways/google_tasks.py, templates/daily-output.md, templates/weekly-output.md
- Tags: grounding, google_tasks, stubs

---

## 2026-05-12 - correction
User clarified Einkaufsliste: add Handyhalterung bei Temu as an item; keep exact shopping list corrections concise.

## [LRN-20260519-001] correction

**Logged**: 2026-05-19T11:18:30+02:00
**Priority**: low
**Status**: pending
**Area**: workflow

### Summary
For the Bayern camping inquiry, the target campsite was Camping Via Claudia, not Camping Bannwaldsee.

### Details
User corrected the assistant after it researched Bannwaldsee. Future Bayern/Neuschwanstein campsite inquiry context may refer to “Via Claudia” and should not be silently mapped to other nearby campsites.

### Suggested Action
When campsite name is ambiguous or omitted, ask or check context before choosing a campsite; for “Via Claudia”, research Camping Via Claudia specifically.

### Metadata
- Source: user_feedback
- Tags: camping, bayern-trip, correction

---

## [LRN-20260519-001] correction

**Logged**: 2026-05-19T19:42:00+02:00
**Priority**: critical
**Status**: pending
**Area**: external-communications

### Summary
Do not send external emails/messages on Endrit's behalf without explicit confirmation.

### Details
After sending a Gmail reply to Via Claudia, Endrit corrected the workflow: drafts should be prepared for his confirmation only, not sent automatically.

### Suggested Action
For future Gmail/external communication requests, prepare the draft/text and ask for explicit confirmation before sending. Use drafts where appropriate; never send directly unless Endrit explicitly says to send now.

### Metadata
- Source: user_feedback
- Related Files: MEMORY.md
- Tags: gmail, external-action, confirmation-required

---
## [LRN-20260522-001] correction

**Logged**: 2026-05-22T13:48:00+02:00
**Priority**: medium
**Status**: pending
**Area**: planning

### Summary
When summarizing Endrit's work hours, exclude 14.05.2026 because it was a holiday, even if a calendar work event exists.

### Details
Endrit corrected the work-hours total: 14.05. should be removed from the calculation because it was a Feiertag.

### Suggested Action
For payroll/hour summaries, flag holiday dates and ask/verify before counting them; update the total by subtracting the affected work shift.

### Metadata
- Source: user_feedback
- Tags: eos, calendar, work-hours, payroll, holiday

---

## [LRN-20260529-001] correction

**Logged**: 2026-05-29T09:10:00Z
**Priority**: medium
**Status**: pending
**Area**: planning

### Summary
For Endrit's work-hour calculations, apply the stored standard 0:30 h break unless he explicitly says otherwise.

### Details
Endrit corrected the May 2026 running total: the baseline before Do 28.05. is 55:45 h net, not 54:45. For Fr 29.05. 06:45-15:30, the gross time is 8:45 and the stored normal break rule gives 8:15 h net. I first interpreted the day with a 1:00 h break and corrected the Telegram answer immediately after checking `MEMORY.md`.

### Suggested Action
Before answering payroll/hour totals, check the stored break rule and calculate in hours:minutes, not decimal notation. Only present a 1:00 h break alternate when the user says today's break differs.

### Metadata
- Source: correction
- Related Files: MEMORY.md, memory/2026-05-29.md
- Tags: eos, work-hours, payroll, break-rule

---
