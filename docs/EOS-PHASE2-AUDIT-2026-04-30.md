# EOS Phase 2 — Repository Audit & Risk Analysis

**Stand:** 2026-04-30
**Vor:** Implementierung Phase 1 (Intake Engine)
**Verbindlich:** Diese Datei sperrt den Schutzkontext, bevor Code geschrieben wird.

---

## 1. Bestandsaufnahme

### 1.1 Bestehende `src/`-Module

| Pfad | Rolle | Schutzstatus |
|---|---|---|
| `src/runtime.py` | `WORKSPACE_ROOT`, `load_env_file()`, gemeinsame Pfade | **Nicht ändern**, nur erweitern wenn nötig |
| `src/eos_core.py` | Schema-Validierung, Task-Ranking, Capacity-Check | **Nicht ändern** |
| `src/eos_cli.py` | CLI-Dispatcher | **Erweitern** (neuer Subcommand `intake`), bestehende Commands intakt lassen |
| `src/audits.py` | `audit_cron`, `audit_models`, `audit_vault` | **Nicht ändern** |
| `src/database/__init__.py` + `models.py` | SQLite Schema (`eos_v2.db`) | **Nicht ändern** in Phase 1 (Tabellen kommen erst Phase 2+) |
| `src/habits/__init__.py` + `service.py` | `HabitService` mit `handle_text` | **Nicht ändern**; Intake-Engine **delegiert** an `HabitService.handle_text` |
| `src/jobs/runner.py` + `daily_capacity.py` + `evening_reset.py` + `weekly_plan.py` | Scheduler-Jobs | **Nicht ändern** in Phase 1 |
| `src/gateways/google_tasks.py` (`TaskGateway`) | Google-Tasks-API: read/create/complete/auth | **Nicht ändern** |
| `src/gateways/telegram.py` (`send_telegram_message`) | Telegram-Send | **Nicht ändern** |
| `src/gateways/tts_*.py` | Lokale TTS-Pipeline | **Nicht ändern** |
| `src/vault/brain_dump.py` | `capture_brain_dump`, `archive_brain_dump` | **Nicht ändern** in Phase 1 |

### 1.2 Bestehende CLI-Kommandos (alle müssen weiter funktionieren)

```
python3 -m src.eos_cli health
python3 -m src.eos_cli tasks read|create|complete
python3 -m src.eos_cli habits status|today|done|skip|add|pause|weekly-report|handle
python3 -m src.eos_cli daily-plan --date YYYY-MM-DD --dry-run
python3 -m src.eos_cli weekly-plan --week-start YYYY-MM-DD --dry-run
python3 -m src.eos_cli run-job <job> --dry-run [--send]
python3 -m src.eos_cli cron-audit [--jobs-path]
python3 -m src.eos_cli model-audit [--jobs-path] [--models-path]
```

### 1.3 Bestehende Verify-Tests

```
tests/verify_brain_dump_vault_flow.py
tests/verify_cron_audit.py
tests/verify_daily_capacity.py
tests/verify_eos_cli.py
tests/verify_eos_core.py
tests/verify_eos_state.py
tests/verify_google_tasks_degraded_state.py
tests/verify_habit_tracker.py
tests/verify_run_job_delivery.py
tests/verify_telegram_gateway.py
tests/verify_tts_pipeline.py
tests/verify_v2_foundation.py
tests/verify_weekly_plan_dry_run.py
```

Alle müssen nach Phase-1-Änderungen weiter grün laufen.

### 1.4 Bestehende SQLite-Tabellen (`data/eos_v2.db`)

| Tabelle | Rolle |
|---|---|
| `job_runs` | Idempotenz pro Job |
| `daily_evaluations` | Coaching-Engine-Output pro Tag |
| `task_snapshots` | Task-Snapshots für Idempotenz |
| `habit_definitions` | Habit-Stammdaten (gemirrort aus `eos_state.json`) |
| `habit_events` | Alle Habit-Events |
| `habit_daily_status` | Finalstatus pro Habit/Tag |
| `sqlite_sequence` | SQLite-Intern |

**Phase-1-Regel:** Keine Schema-Änderung. Intake-Engine ist **stateless** und schreibt **nichts** in SQLite. Persistenz erst Phase 2 (Habit Engine v3) und Phase 3 (Energy Layer).

### 1.5 `data/eos_state.json` Struktur

Versionsschema 1, Top-Level-Keys:
- `schema_version`, `created_at_utc`, `updated_at_utc`, `timezone`
- `sources`, `energy_profile`, `planning_policy`
- `task_annotations`, `habits`, `habit_log`, `review_state`, `escalation_policy`

**Phase-1-Regel:** Keine Schema-Änderung. Intake liest nur `habits` (für Resolution durch `HabitService`) und nichts sonst.

### 1.6 Bestehende systemd-Timer

```
eos-daily-hang-reminder.timer
eos-daily-morning.timer
eos-evening-briefing.timer
eos-habit-checkin-evening.timer
eos-habit-checkin-morning.timer
eos-job@.service
eos-sport-prep-reminder.timer
eos-weekly-sync.timer
```

**Phase-1-Regel:** Keine Timer-Änderung. Phase 1 ist CLI-only.

### 1.7 Bestehende Templates

```
templates/{daily-output, evening-reset-output, weekly-output, weekly-review-output,
          daily-note, brain-dump-intake, brain-dump-note, idea-note, project-note,
          manual-task-intake, README}.md
```

**Phase-1-Regel:** Keine Template-Änderung in Phase 1.

### 1.8 Verfügbare Gateway-Funktionen

| Gateway | Public Methods |
|---|---|
| `TaskGateway` | `get_auth_status`, `prepare_headless_auth`, `finalize_headless_auth`, `get_open_tasks`, `list_structure`, `ensure_canonical_lists`, `readOpenTasks`, `get_canonical_open_tasks`, `createTask`, `create_task`, `completeTask`, `complete_task` |
| `telegram.send_telegram_message` | Send Markdown-Text an konfigurierten Chat |
| `vault.brain_dump.capture_brain_dump` | Brain-Dump-Note anlegen |
| `vault.brain_dump.archive_brain_dump` | Brain-Dump archivieren |

### 1.9 Habit-Resolution-API (für Intake wichtig)

`HabitService` bietet:
- `resolve_habit(query)` → returns `{status: success|ambiguous|not_found, habit?, candidates?}`
- `handle_text(text, target_date, source)` → existierender tolerant-Parser
- `mark_done`, `skip_habit`, `pause_habit`, `add_habit`, `today`, `status`, `weekly_report`

**Wichtig:** Der bestehende `handle_text` ist der heutige Intake. Phase 1 baut die **Engine darüber** — ersetzt sie aber nicht in Phase 1.

---

## 2. Geplante Änderungen

### 2.1 Neu (additiv, isoliert)

```
src/intake/__init__.py             ← Public-API Re-Export
src/intake/models.py               ← Datenklassen (Intent, Confidence, IntakeResult)
src/intake/normalizer.py           ← Text-Normalisierung (lowercase, trim, umlaut-fold)
src/intake/confidence.py           ← Confidence-Gates (HIGH/MEDIUM/LOW Schwellen)
src/intake/intent_router.py        ← Klassifikation Text → Intent + Confidence
tests/verify_intake_engine.py      ← Verify-Test für Intake-Engine
```

### 2.2 Erweitert (rückwärtskompatibel)

| Datei | Änderung |
|---|---|
| `src/eos_cli.py` | Neuer Subparser `intake parse "<text>"`. Bestehende Commands unverändert. |

### 2.3 Nicht angefasst (Phase 1)

- Alle bestehenden Module außer `eos_cli.py`
- `data/eos_state.json` Schema
- `data/eos_v2.db` Schema
- systemd-Timer
- Templates
- Bestehende verify_*.py Tests

---

## 3. Risikoanalyse

| Risiko | Wahrscheinlichkeit | Schweregrad | Gegenmaßnahme |
|---|---|---|---|
| `eos_cli.py` Erweiterung bricht bestehende Commands | niedrig | hoch | Subparser ergänzen, keinen bestehenden Branch ändern; `verify_eos_cli.py` muss grün bleiben |
| Intake-Engine schreibt fälschlich in SQLite | nicht möglich | hoch | Intake-Engine ist **stateless** by design — keine `import sqlite3`, keine `HabitService` außer für Resolution-Lookup ohne Mutation |
| Intake schreibt automatisch Habit-Events | nicht möglich | hoch | Intake gibt **nur** `IntakeResult` zurück. Keine Mutation in Phase 1. |
| Intake delegiert an `handle_text` und löst Mutation aus | mittel | hoch | Phase 1 ruft `handle_text` **nicht** auf. Intake klassifiziert nur. Aktion folgt erst Phase 2. |
| LLM-Halluzination | nicht möglich | hoch | Phase 1 ist **rein deterministisch**, keine LLM-Calls |
| Confidence falsch kalibriert | mittel | mittel | Verbindliche Schwellen: `≥0.85` HIGH, `0.60–0.85` MEDIUM, `<0.60` LOW. Test deckt alle drei Bereiche ab. |
| Encoding-Probleme bei Umlauten | niedrig | mittel | `normalizer.py` fold-t Umlaute deterministisch (`ä→ae`, `ö→oe`, `ü→ue`, `ß→ss`) |
| Intake-API ändert sich später | mittel | mittel | `models.py` als einzige Schnittstelle; `__init__.py` Re-Export bewahrt API |

---

## 4. Schutzregel-Compliance (Auflistung pro Regel)

| Regel | Phase 1 Compliance |
|---|---|
| 1. Keine bestehenden Dateien löschen | ✅ Keine Löschung |
| 2. Keine bestehenden Interfaces brechen | ✅ Nur additive `eos_cli.py`-Erweiterung |
| 3. Keine Calendar-Write ohne Approval-Loop | ✅ Phase 1 hat kein Calendar-Write überhaupt |
| 4. Keine Tasks-Auto-Complete | ✅ Phase 1 hat keine Task-Mutation |
| 5. Keine Habit-Events überschreiben | ✅ Phase 1 hat keine Habit-Mutation |
| 6. Keine Termine/Aufgaben erfinden | ✅ Phase 1 ist Klassifikation, keine Datenproduktion |
| 7. Keine LLM-Output direkt persistieren | ✅ Phase 1 ist deterministisch, keine LLM |
| 8. Idempotenz für Schreibaktionen | n/a — Phase 1 schreibt nicht |
| 9. Live-E2E oder Markierung | ✅ `verify_intake_engine.py` als Phase-1-Test; Live-Telegram-E2E erst Phase 2 |
| 10. Bestehende CLI funktioniert weiter | ✅ Test: alle bestehenden `verify_*.py` müssen grün bleiben |

---

## 5. Phase-1-Akzeptanzkriterien

Phase 1 ist abgenommen, wenn:

1. ✅ `python3 -m tests.verify_intake_engine` läuft grün
2. ✅ Alle bestehenden `verify_*.py` laufen grün (Regression)
3. ✅ `python3 -m src.eos_cli intake parse "morgenroutine erledigt"` liefert `IntakeResult`-JSON
4. ✅ `python3 -m src.eos_cli intake parse "hab alles erledigt"` liefert Confidence ≤ 0.85 + `requires_confirmation: true` + Confirmation-Question
5. ✅ `python3 -m src.eos_cli intake parse "<unbekannter Text>"` liefert `intent: unknown` mit Confidence < 0.60
6. ✅ Keine SQLite-Writes durch Intake (verifiziert per stat-Diff vor/nach Lauf)
7. ✅ Bestehende `eos_cli` Commands unverändert (verifiziert per `verify_eos_cli.py`)

---

## 6. Bewusst nicht in Phase 1

- LLM-basierte Intent-Klassifikation (kommt später als optionaler 2nd-Pass)
- Audio-Intake (Phase 6 laut V3-Spec)
- Intent-Ausführung (Mutation) — Phase 2 baut Habit-Coaching-Engine darauf
- `energy_checkin` Persistenz (Phase 3)
- Calendar-Proposal (Phase 4)
- Calendar-Write mit Approval (Phase 5)

---

## 7. Freigabe

Mit dieser Audit-Datei ist die **strukturelle Sicherheit** von Phase 1 dokumentiert. Implementierung kann beginnen.

Referenzen:
- [EOS-V3-INTELLIGENT-LOOP-SPEC.md](EOS-V3-INTELLIGENT-LOOP-SPEC.md) §3 (Understanding Engine)
- [EOS-CURRENT-STATE-2026-04-30.md](EOS-CURRENT-STATE-2026-04-30.md)
