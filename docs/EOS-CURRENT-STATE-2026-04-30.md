# EOS – Current State & Architecture

**Stand:** 2026-04-30
**Agent:** `personal-assistant` (Display-Name: *EOS*)
**Workspace:** `/data/.openclaw/workspaces/personal-assistant`
**Scope dieser Datei:** Vollständige, ehrliche Bestandsaufnahme — *was EOS heute wirklich kann*, nicht das Zielbild.

---

## 1. Identität & Rolle

| Feld | Wert |
|---|---|
| Agent-ID | `personal-assistant` |
| Display-Name | `EOS` |
| Vibe | Fokussiert, strukturiert, minimal, scheduling-aware, ruhig, direkt |
| Emoji | 📅 |
| Interface | Dedizierter Telegram-Bot, geroutet auf `personal-assistant` |
| Heartbeat | Alle 30 min, Ziel `telegram` (account `personal-assistant`, chat `6526468834`), `lightContext: true` |
| Zeitzone | `Europe/Berlin` (operativ verbindlich) |

**Was EOS *nicht* ist:**
- Kein generischer Produktivitäts-Coach
- Kein Research-/Guru-Persona
- Keine Black-Box-Scoring-Maschine
- Nicht für Fitness/Health-Coaching (das macht Solara)

---

## 2. Verzeichnisstruktur

```
personal-assistant/
├── AGENTS.md          – Workspace-Verhaltensregeln, Heartbeat-Policy
├── IDENTITY.md        – Wer bin ich
├── HEARTBEAT.md       – proaktive Checkliste (30-min-Polls)
├── MEMORY.md          – Langzeitgedächtnis (nur Main-Session)
├── PLAN.md / SOUL.md / TOOLS.md / USER.md
├── requirements.txt
├── data/
│   ├── eos_state.json + eos_state.schema.json   ← Single Source für Policy/Habits/Annotations
│   ├── eos_v2.db                                 ← SQLite Derived State
│   ├── calendar.json   (Test-/Fallback-Stub)
│   ├── tasks.json      (Test-Fixture)
│   ├── routines.json
│   ├── profile.json
│   └── planning-schema.json
├── docs/              – 30+ Spezifikationsdokumente (v1)
├── integrations/      – calendar-source.json, google-tasks.md, ...
├── memory/            – tägliche YYYY-MM-DD.md Notizen
├── ops/systemd/       – 8 Timer + ein Job@-Service-Template
├── src/               – Python-Code (siehe §3)
├── templates/         – Output-Templates (evening-reset, weekly-output, daily-note, ...)
├── tests/             – verify_*.py Skripte (Smoke-/E2E-Verifikation)
├── var/               – Runtime-State, Logs, idempotency
└── vault/             – Brain-Dump-Vault (Markdown)
```

---

## 3. Code-Module (`src/`)

| Modul | Rolle | Status |
|---|---|---|
| `eos_core.py` | Schema-Validierung, Task-Ranking, Capacity-Check, Habit-Version-Selektion | Stabil |
| `eos_cli.py` | Deterministische CLI: `health`, `tasks`, `habits`, `daily-plan`, `weekly-plan`, `run-job`, `cron-audit`, `model-audit` | Stabil |
| `runtime.py` | `WORKSPACE_ROOT`, `load_env_file()`, gemeinsame Pfade | Stabil |
| `audits.py` | `audit_cron`, `audit_models`, `audit_vault` | Stabil |
| `database/models.py` | SQLite Schema (`eos_v2.db`): habit_definitions, habit_events, daily_evaluations, delivery_log, … | Stabil |
| `habits/service.py` | `HabitService`: definitions, status, log_event, streaks, aliases, today/heute | Stabil |
| `jobs/runner.py` | `run_eos_job` Dispatcher (dry-run + send) | Stabil |
| `jobs/daily_capacity.py` | `daily_capacity` Job (early-day Briefing) | Stabil |
| `jobs/evening_reset.py` | `evening_briefing` Job (Abendanker) | Stabil |
| `jobs/weekly_plan.py` | `weekly_sync` Job (Sonntags-Wochenanker) | Stabil |
| `gateways/google_tasks.py` | `TaskGateway`: OAuth2, list-structure, readOpenTasks, create, complete | Live (degraded states explizit) |
| `gateways/telegram.py` | `send_telegram_message` | Stabil |
| `gateways/tts_local.py` + `tts_pipeline.py` + `tts_provider.py` | Lokale Piper-WAV Generierung (TTS) | Funktioniert, Delivery getrennt |
| `vault/brain_dump.py` | Brain-Dump → Inbox-Markdown | Funktional, nicht prod-mounted |

---

## 4. Systems of Record

| System | Rolle | Status |
|---|---|---|
| **Google Calendar** (via `gog` CLI) | Harte Termine, fixe Zeitblöcke | **Live-Read bestätigt** (`primary` + `Sport` aggregiert) |
| **Google Tasks** (OAuth2) | Aktive offene Aufgaben | Live-Read gehärtet, Create/Complete verfügbar – Provider-Setup noch nicht fully prod-verifiziert |
| **Obsidian Vault** (Markdown-Filesystem) | Brain Dumps, Daily Notes, Wissen | Geplant, nicht produktiv gemountet |
| **SQLite `eos_v2.db`** | *Nur* Derived State: Habit-Events, Daily-Evaluations, Delivery-Log, Idempotenz | Stabil, **nicht** Primärquelle |
| `data/calendar.json` | Test-/Fallback-Stub | Nur für Dry-Run-Verifikation |
| `data/tasks.json` | Test-Fixture | Nicht produktiv |

**Architekturregel:** Keine Mehrfachwahrheiten. Calendar / Tasks / Vault / SQLite haben **strikt getrennte Rollen**.

---

## 5. Coaching Engine v1 (deterministisch)

Datei: `docs/EOS-COACHING-ENGINE-v1.md`

**Output pro Tag:**
- `TrafficLightStatus` ∈ {`green`, `yellow`, `red`}
- `reasons[]` (endliche Menge)
- kurze `assessment`
- **genau eine** `recommendation`
- optional **eine** `warning`

**Endliche Reasons:**
`hard_shift_plus_fixed_sport`, `too_many_heavy_blocks`, `fragmented_capacity`, `insufficient_recovery`, `prep_risk`, `poor_distribution`, `missing_task_basis`

**Endliche Recommendation-Keys (nach Priorität):**
1. `protect_recovery`
2. `cut_extra_block`
3. `pick_top1`
4. `use_single_focus_block`
5. `skip_deep_work`
6. `prepare_tonight`

**Harte EOS-Regeln:**
- **Belastungstage:** Do–Sa = harte Belastungstage (frühe Schicht, konservative Zusatzplanung)
- **Deep Work:** 60 min Fokus + 10 min Spaziergang. Max. 1 zusätzlicher Block. Harter Arbeitstag + fixer Sport ⇒ meist *kein* echter Deep-Work-Block.
- **Sport:** Fixer Kalender-Kurs = harter Block. Gym/Cardio = flexibel. Calisthenics nicht automatisch on top.
- **Ton:** Genau eine Empfehlung, keine Predigt, kein Research-Framing, nicht moralisierend.

---

## 6. Habit-System

**State:** Definitionen leben in `data/eos_state.json`, Events laufen in SQLite (`eos_v2.db` → `habit_events`).
**Service:** `src/habits/service.py` (`HabitService`).

### Aktive Habits (aus `eos_state.json`)

| ID | Name | Frequenz | Target-Time | Minimum-Version | Full-Version |
|---|---|---|---|---|---|
| `habit-morning-routine` | Morgenroutine | daily | 07:00 | Yoga Mobility, Skin Care | + Infrarot, Kokosoel |
| `habit-evening-routine` | Abendroutine | daily | 21:30 | Yoga Mobility, Skin Care | + Infrarot, Kokosoel |
| `habit-pullup-bar-hang` | Hängenlassen an der Klimmzugstange | daily | 21:00 | short_hang, 1 Reflexionsfrage | full hang + 3 Reflexionsfragen |

### Event-Typen
`done_full`, `done_partial`, `skipped`, `missed`, `paused` — finale Statuse: `{done_full, done_partial, skipped, missed}`.

### Telegram-Eingabe
Tolerante Free-Text-Routing über `python3 -m src.eos_cli habits handle "<text>"`. Beispiele:
- `morgenroutine erledigt`
- `abendroutine partial`
- `klimmzug skip heute, zu muede`
- `habit status`, `habits heute`

Bei Mehrdeutigkeit → CLI gibt `ambiguous` zurück, EOS fragt zurück statt zu raten.

### Collision-Policy
Bei Konflikt mit Kalender oder Task ⇒ `preserve_minimum_version` (lieber kurze Version durchziehen als Habit komplett kippen).

---

## 7. Scheduler – Jobs & Timer

### Drei normative Jobs (siehe `EOS-SCHEDULER-JOBS-v1.md`)

| Job | Trigger | Zielzeitraum | Output |
|---|---|---|---|
| `evening_briefing` | täglich **20:30** Berlin | morgen 00:00 → übermorgen 00:00 | Harte Termine morgen, Top-3, Deep-Work-Vorschlag, Sport, Vorbereitung, Warnung |
| `sport_prep_reminder` | täglich **08:30** Berlin | morgen | Pro qualifizierten Sport-Termin: definierte Kurz-Checkliste |
| `weekly_sync` | Sonntag **18:00** Berlin | kommende Woche Mo–Mo | Rückblick 7d, Muster, harte Termine, Verteilung, gekürzte Ziele, 1 Empfehlung |

**Idempotenz-Keys:**
- `evening_briefing:<target_date_berlin>`
- `sport_prep_reminder:<target_date_berlin>`
- `weekly_sync:<week_start_date_berlin>`

Nur `sent` blockiert weiteren Send. `skipped`/`failed`/`sending` blockieren keinen späteren Retry.

### systemd-Timer (`ops/systemd/`)

```
eos-daily-morning.timer            → daily_capacity / morning briefing
eos-daily-hang-reminder.timer      → klimmzugstange Reminder
eos-evening-briefing.timer         → 20:30 evening_briefing
eos-habit-checkin-morning.timer    → Morgen-Habit-Check
eos-habit-checkin-evening.timer    → Abend-Habit-Check
eos-sport-prep-reminder.timer      → 08:30 sport_prep_reminder
eos-weekly-sync.timer              → So 18:00 weekly_sync
eos-job@.service                   → Job-Service-Template (parametrisiert)
```

### Job-Regeln (für *alle* Jobs)
- Triggerbewertung in `Europe/Berlin`
- Vor jedem Send frischer Live-Calendar-Read
- Mindestens `primary` + `Sport` aggregieren
- Keine Sends ohne persistenten State
- Genau **eine** Nachricht pro Job-Ausführung
- Keine spekulativen Inhalte
- Dry-Run durchläuft dieselbe Fachlogik, sendet aber nicht

### Partial Degradation
- Tasks fehlen ⇒ Job läuft, markiert `missing_task_basis` explizit
- `daily_evaluations` fehlen ⇒ Mustererkennung fällt auf Calendar+Task-Snapshots zurück
- Calendar fehlt ⇒ **fail-closed**, kein Send

---

## 8. State & Persistenz

### `data/eos_state.json` (Primary State, JSON-Schema-validiert)
- `schema_version`, `timezone`
- `sources` (Calendar/Tasks/Routines/Profile-Pointer)
- `energy_profile` (4 Default-Tagesfenster: morning_ramp / deep_work_peak / afternoon_execution / evening_low_load)
- `planning_policy`:
  - `wake_window` 06:00–22:00, `buffer_ratio` 0.2
  - `collision_order` (10-stufig: hard events → work → fixed sport → min routine → deep work → urgent → manual → gym → cardio → full routine)
  - `deep_work` (45 min minimum, 60+10 default, 1 preferred / 2 max pro Tag)
  - `behavior_rules` (z.B. "Habits sind keine Tasks", "Missing priority = untriaged, nicht raten")
- `task_annotations` (priority, energy_required, estimated_minutes, triage_status)
- `habits` + `habit_log`
- `review_state` (last_daily_review_date, last_weekly_review_date, open_review_questions)
- `escalation_policy` (overdue_tasks, deferred_tasks, missing_task_metadata)

### `data/eos_v2.db` (SQLite – Derived State)
Tabellen u.a.:
- `habit_definitions` (gemirrort aus eos_state.json)
- `habit_events` (alle Habit-Logs mit Timestamp)
- `daily_evaluations` (Coaching-Engine Output pro Tag)
- `delivery_log` (Idempotenz für Telegram-Sends)

**Regel:** SQLite ist *nur* Derived State. Niemals neue Primärwahrheiten.

---

## 9. CLI (`python3 -m src.eos_cli ...`)

| Befehl | Zweck |
|---|---|
| `health` | Calendar + Google Tasks + Vault + Cron + Models + Habits Status |
| `tasks read|create|complete` | Google-Tasks-Operationen |
| `habits handle "<text>"` | Tolerantes Free-Text-Routing für Habit-Events |
| `habits status` / `habits heute` | Heutiger Habit-Stand |
| `daily-plan --date YYYY-MM-DD --dry-run` | Tagesplan |
| `weekly-plan --week-start YYYY-MM-DD --dry-run` | Wochenplan |
| `run-job <job> --dry-run` | Einzelnen Job ausführen |
| `cron-audit` | Cron-Konfiguration prüfen |
| `model-audit` | Modell-Konfiguration prüfen |

---

## 10. Templates (Output-Format)

Alle Telegram-/Vault-Outputs nutzen Templates aus `templates/`:
- `daily-output.md`
- `evening-reset-output.md`
- `weekly-output.md`
- `weekly-review-output.md`
- `daily-note.md` (für Vault)
- `brain-dump-intake.md` / `brain-dump-note.md`
- `idea-note.md` / `project-note.md` / `manual-task-intake.md`

---

## 11. Tests / Verify-Suite (`tests/`)

Smoke-/E2E-Verifikation, kein klassischer pytest-Lauf:
- `verify_eos_core.py` / `verify_eos_state.py` / `verify_eos_cli.py`
- `verify_daily_capacity.py` / `verify_weekly_plan_dry_run.py`
- `verify_habit_tracker.py`
- `verify_brain_dump_vault_flow.py`
- `verify_google_tasks_degraded_state.py`
- `verify_telegram_gateway.py` / `verify_tts_pipeline.py`
- `verify_cron_audit.py` / `verify_v2_foundation.py`
- `verify_run_job_delivery.py`

---

## 12. Was *bestätigt* ist (eingefrorene Basis)

- ✅ Eigener Agent `personal-assistant` mit dediziertem Workspace
- ✅ Eigener Telegram-Bot, eigenes Routing
- ✅ Google Calendar Live-Read (`primary` + `Sport` aggregiert)
- ✅ Operative Zeitzone `Europe/Berlin`
- ✅ Daily Planning Policy v1 + Weekly Planning Policy v1
- ✅ Coaching Engine v1 (Ampel + 1 Empfehlung)
- ✅ Habit Engine (3 aktive Habits, Event-Logging, Streaks, Aliase)
- ✅ Drei Scheduler-Jobs: `evening_briefing` (20:30), `sport_prep_reminder` (08:30), `weekly_sync` (So 18:00)
- ✅ systemd-Timer (8 Timer + Service-Template)
- ✅ JSON-Schema-validierter State + SQLite Derived State
- ✅ Idempotenz pro Job + Zielperiode
- ✅ Heartbeat alle 30 min
- ✅ Vault-Strategie als **Markdown-Filesystem** (kein GUI-Obsidian-Zwang)

---

## 13. Was *offen* ist (Phase 2+)

- 🟡 **Google Tasks** voll produktiv und headless-fähig (OAuth2 + Refresh-Token sauber durchziehen)
- 🟡 **Obsidian Vault** als echten persistenten Mount-Pfad ins Live-System einbinden
- 🟡 **Calendar Write** (aktuell nur Read; Schreiben bewusst deaktiviert)
- 🟡 **Skill-/Tool-Sichtbarkeit** für EOS minimalisieren (Hardening)
- 🟡 **Live-E2E** für Tasks und Vault ergänzen
- 🟡 **Reverse Proxy / Firewall / Fail2Ban / Token-Validierung** (Hardening-Zielbild)

---

## 14. Bewusste Nicht-Ziele

| Was | Warum |
|---|---|
| Multi-Agent-„Zoo" öffentlicher Agenten | Ein sichtbarer Hauptagent, interne Fähigkeiten, keine Fragmentierung |
| Service Account für persönlichen Zugriff | OAuth2 + Refresh-Token ist der saubere Standardpfad |
| GUI-Obsidian-App auf VPS | Markdown-Vault als Filesystem, headless-fähig |
| Redis/Postgres-Pflicht | OpenClaw/QMD Memory + SQLite reichen |
| LLM-Halluzination von Terminen/Tasks | Engine arbeitet *nur* mit bestätigten Datenquellen |
| Generische Produktivitäts-Sprüche | EOS gibt **eine** konkrete Empfehlung, keine Predigt |
| Autonomes Umplanen ohne Approval | Schreibaktionen sind approval-aware |

---

## 15. Kurzurteil (Stand 2026-04-30)

EOS ist als **Telegram-gesteuerter persönlicher Planungsagent** belastbar:
- Live Google Calendar Read funktioniert produktiv
- Coaching-Engine liefert deterministische, kurze Empfehlungen (Ampel + 1 Action)
- Habit-Tracker existiert mit SQLite-Eventlog, drei aktiven Habits, Streaks, Telegram-Eingabe
- Drei Scheduler-Jobs senden idempotent über systemd-Timer
- State sauber getrennt: JSON (Primary Policy) + SQLite (Derived) + Templates (Output)

**Was fehlt für den nächsten Sprung:**
- Google Tasks voll produktiv (statt Stub-Fallback)
- Obsidian-Vault produktiv gemountet
- Intelligenter Habit-Hintergrund-Loop (proaktive Reminder, Adaptive Re-Schedules, Streak-Recovery-Nudges)
- Echter „intelligenter Kalenderassistent" der nicht nur empfiehlt, sondern auch *vorschlägt-und-schreibt* (mit Approval-Loop)
- Mustererkennung über Wochen hinweg (nicht nur 7-Tage-Rückblick)

---

## 16. Datei-Referenzen

- Spec: [EOS-V2-TECHNICAL-SPEC.md](EOS-V2-TECHNICAL-SPEC.md)
- Architektur v1: [EOS-ARCHITECTURE-v1.md](EOS-ARCHITECTURE-v1.md)
- Capability-Map: [EOS-CAPABILITY-MAP.md](EOS-CAPABILITY-MAP.md)
- Coaching-Engine: [EOS-COACHING-ENGINE-v1.md](EOS-COACHING-ENGINE-v1.md)
- Review-Engine: [EOS-REVIEW-ENGINE-v1.md](EOS-REVIEW-ENGINE-v1.md)
- Scheduler-Jobs: [EOS-SCHEDULER-JOBS-v1.md](EOS-SCHEDULER-JOBS-v1.md)
- Scheduler-Policy: [EOS-SCHEDULER-POLICY-v1.md](EOS-SCHEDULER-POLICY-v1.md)
- Scheduler-Idempotenz: [EOS-SCHEDULER-STATE-IDEMPOTENCY-v1.md](EOS-SCHEDULER-STATE-IDEMPOTENCY-v1.md)
- Habit-Tracker-Draft: [HABIT-TRACKER-DRAFT.md](HABIT-TRACKER-DRAFT.md)
- Vault-Spec: [EOS-VAULT-v1.md](EOS-VAULT-v1.md)
- Operating-Contract: [EOS-OPERATING-CONTRACT-v1.md](EOS-OPERATING-CONTRACT-v1.md)
- Action-Contract: [EOS-ACTION-CONTRACT-v1.md](EOS-ACTION-CONTRACT-v1.md)
- Calendar-Write-E2E: [EOS-CALENDAR-WRITE-E2E-v1.md](EOS-CALENDAR-WRITE-E2E-v1.md)
- Tasks-Integration: [EOS-TASKS-INTEGRATION-v1.md](EOS-TASKS-INTEGRATION-v1.md)
