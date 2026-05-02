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
