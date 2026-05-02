# EOS Phase 2 — Habit Coaching Engine v1

**Stand:** 2026-04-30
**Status:** Implementiert, alle 15 Verify-Tests grün
**Vorgänger:** [EOS-PHASE2-AUDIT-2026-04-30.md](EOS-PHASE2-AUDIT-2026-04-30.md), [EOS-V3-INTELLIGENT-LOOP-SPEC.md](EOS-V3-INTELLIGENT-LOOP-SPEC.md) §4

---

## 1. Was Phase 2 liefert

Die Habit-Schicht versteht jetzt **Habit-Typen** und unterscheidet zwischen:

- Routinen, die **aufgebaut** werden (`build`) — z.B. Morgenroutine
- Gewohnheiten, die **reduziert** werden (`reduce`) — z.B. Doomscrolling abends
- Verhalten, das auf **Niveau gehalten** wird (`maintain`)
- **Notfall-Resets** bei Ausfall (`recovery`)

Zusätzlich:

- **Failure-Mode-Tracking** — warum verfehlt? (verschlafen, keine_zeit, etc.)
- **Trigger-Klassifikation** für `reduce`-Rückfälle (kanonisch: muede, stress, langeweile, …)
- **Recovery-Versionen** schützen den Streak (echte Notfall-Erfüllung zählt)
- **Wochenmuster-Erkennung** (deterministisch über Event-Statistiken)

---

## 2. Was *nicht* Teil von Phase 2 ist

- Telegram-Wiring (kommt mit Phase 3 — Intake-Engine → HabitService)
- Calendar Write (Phase 5)
- LLM-Klassifikation von Triggern (rein deterministisch in V3)
- Energy-Checkin (Phase 3)
- Audio-Intake (Phase 6)

Verifiziert durch `test_no_telegram_no_calendar_writes`: Der Habit-Service importiert weder `send_telegram_message` noch enthält Code für Calendar-Write.

---

## 3. Datenmodell

### 3.1 SQLite — additive Schema-Änderungen

`init_db()` erkennt neue Spalten und legt sie idempotent an (`PRAGMA table_info` + `ALTER TABLE ADD COLUMN`).

#### `habit_definitions` neue Spalten
```
habit_type                TEXT NOT NULL DEFAULT 'build'
failure_modes_json        TEXT NULL
replacement_actions_json  TEXT NULL
recovery_rule_json        TEXT NULL
trigger_window_json       TEXT NULL
```

#### `habit_events` neue Spalten
```
failure_mode    TEXT NULL
recovery_used   INTEGER NOT NULL DEFAULT 0
```

#### Neue Tabelle `habit_relapses`
```sql
CREATE TABLE habit_relapses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id TEXT NOT NULL,
    business_date_berlin TEXT NOT NULL,
    trigger_context TEXT,
    replacement_used TEXT,
    severity TEXT NOT NULL,        -- minor | moderate | major
    notes TEXT,
    created_at_utc TEXT NOT NULL,
    FOREIGN KEY (habit_id) REFERENCES habit_definitions(id)
);

CREATE INDEX idx_habit_relapses_habit_date
    ON habit_relapses(habit_id, business_date_berlin);
```

### 3.2 `eos_state.json` — additive Felder

Neue **optionale** Properties pro Habit (rückwärtskompatibel — bestehende Habits ohne diese Felder gelten weiter, Default-Type ist `build`):

```json
{
  "type": "build|reduce|maintain|recovery",
  "failure_modes": ["verschlafen", "keine_zeit"],
  "replacement_actions": ["zaehneputzen", "5_minuten_dehnen"],
  "recovery_rule": {"same_day_minimum_until": "12:00", "fallback": "two_minute_reset"},
  "trigger_window": {"start": "21:30", "end": "23:30"}
}
```

JSON-Schema-Validierung (`data/eos_state.schema.json`) akzeptiert diese Felder optional. `additionalProperties: false` bleibt strikt — neue Felder sind explizit deklariert.

---

## 4. Module

### 4.1 Neu

| Datei | Inhalt |
|---|---|
| `src/habits/types.py` | `HabitType` Enum, `RelapseSeverity` Enum, `coerce_*` Helfer |
| `src/habits/triggers.py` | `classify_trigger()` (kanonisch: muede, stress, langeweile, aufschieben, handy_im_bett, sozialer_druck, hunger, frustration, unbekannt), `normalize_replacement()` |
| `src/habits/patterns.py` | `PatternSignal` Datenklasse, `detect_patterns()` mit fünf endlichen Klassen |
| `tests/verify_habit_coaching.py` | 15 Tests inkl. Migration, Schema-Idempotenz, Pattern-Erkennung |

### 4.2 Erweitert (rückwärtskompatibel)

| Datei | Änderung |
|---|---|
| `src/database/models.py` | `_ensure_columns()` Helfer + neue Tabelle, additiv |
| `src/habits/service.py` | `seed_from_state` liest neue Felder; `_row_to_definition` exportiert sie; `_streak_through` prüft jetzt Recovery; `add_habit` akzeptiert neue Parameter; **neue Methoden:** `set_habit_type`, `log_failure_mode`, `log_relapse`, `log_recovery`, `week_patterns` |
| `src/habits/__init__.py` | Re-Export der neuen Symbole |
| `src/eos_cli.py` | Vier neue Subcommands unter `habits` |
| `data/eos_state.schema.json` | Optionale Properties in `$defs/habit` |

---

## 5. Pattern-Klassen (deterministisch, kein LLM)

`src/habits/patterns.py` erkennt fünf Klassen über `habit_events`, `habit_daily_status` und `habit_relapses`:

| Pattern-Key | Bedingung | Severity |
|---|---|---|
| `habit_time_misalignment` | ≥ 4 missed/skipped/partial in 14 Tagen + `target_time` gesetzt | moderate / major |
| `weekday_drop` | Selber Wochentag ≥ 2× nicht-`done_full` und ≥ 75 % der Vorkommen in 4 Wochen | moderate |
| `trigger_cluster` | Gleicher Trigger ≥ 3× in 14 Tagen (nur `reduce`-Habits via `habit_relapses`) | moderate / major |
| `recovery_streak_save` | ≥ 2 Recovery-Events in 28 Tagen | info |
| `replacement_works` | Gleiche Ersatzhandlung in ≥ 60 % der Rückfälle führt zu `severity=minor` (≥ 3 Vorkommen) | info |

Output: `list[PatternSignal]` mit `{key, severity, habit_id, evidence, implication}`. Verbindlich keine LLM-Inferenz — nur SQL-Counts mit harten Schwellen.

---

## 6. Streak-Protection durch Recovery

Vorher: `_streak_through` zählte nur `done_full`-Tage zurück.

Jetzt: `_day_keeps_streak()` zählt einen Tag als streak-bewahrend, wenn:
- `habit_daily_status.final_status = 'done_full'` ODER
- ein `habit_events`-Eintrag mit `recovery_used = 1` für diesen Tag existiert

Damit kann `log_recovery()` einen Streak schützen, ohne dass eine Voll-Erfüllung gemeldet werden muss. Ein Partial ohne Recovery-Flag bricht den Streak weiterhin nicht (Verhalten wie vorher), zählt aber auch nicht hoch.

---

## 7. Neue Methoden im `HabitService`

| Methode | Zweck | Mutation |
|---|---|---|
| `set_habit_type(query, habit_type)` | Bestehenden Habit auf neuen Typ migrieren | `UPDATE habit_definitions` |
| `log_failure_mode(query, *, failure_mode, …)` | `missed`-Status mit explizitem Grund schreiben | `INSERT habit_events` (failure_mode), `UPSERT habit_daily_status` |
| `log_relapse(query, *, trigger, replacement, severity, …)` | **Nur `reduce`-Habits.** Kanonisiert Trigger + Replacement, schreibt Relapse-Eintrag und korrespondierendes `skipped`-Event | `INSERT habit_relapses`, `INSERT habit_events`, `UPSERT habit_daily_status` |
| `log_recovery(query, …)` | Recovery-Version markieren, Streak schützen | `INSERT habit_events` (recovery_used=1), `UPSERT habit_daily_status='done_partial'` |
| `week_patterns(reference_date)` | Pattern-Erkennung über letzte 28 Tage | **Nur Read** |

Bestehende Methoden (`mark_done`, `skip_habit`, `pause_habit`, `add_habit`, `today`, `status`, `weekly_report`, `handle_text`, `resolve_habit`) sind **unverändert in der Signatur**. `add_habit` hat optionale neue Keyword-Parameter mit `None`-Default.

---

## 8. CLI-Erweiterungen (additiv unter `habits`)

```
python3 -m src.eos_cli habits set-type <habit> {build,reduce,maintain,recovery}
python3 -m src.eos_cli habits failure  <habit> --mode <text> [--date YYYY-MM-DD] [--notes <text>]
python3 -m src.eos_cli habits relapse  <habit> [--trigger <text>] [--replacement <text>]
                                                [--severity {minor,moderate,major}]
                                                [--date YYYY-MM-DD] [--notes <text>]
python3 -m src.eos_cli habits recovery <habit> [--date YYYY-MM-DD] [--notes <text>]
python3 -m src.eos_cli habits patterns [--reference-date YYYY-MM-DD]
python3 -m src.eos_cli habits add --name <name> [--time HH:MM] [--frequency {daily,weekly}]
                                  [--type {build,reduce,maintain,recovery}]
```

Bestehende Subcommands (`status`, `today`, `done`, `skip`, `add`, `pause`, `weekly-report`, `handle`) verhalten sich unverändert — verifiziert durch `verify_eos_cli` + `verify_habit_tracker`.

---

## 9. Verifikation

### 9.1 Verify-Suite

| Test | Ergebnis |
|---|---|
| `verify_brain_dump_vault_flow` | OK |
| `verify_cron_audit` | OK |
| `verify_daily_capacity` | OK |
| `verify_eos_cli` | OK (kein Regression) |
| `verify_eos_core` | OK |
| `verify_eos_state` | OK |
| `verify_google_tasks_degraded_state` | OK |
| `verify_habit_coaching` | OK (neu — 15 Assertions) |
| `verify_habit_tracker` | OK (kein Regression) |
| `verify_intake_engine` | OK |
| `verify_run_job_delivery` | OK |
| `verify_telegram_gateway` | OK |
| `verify_tts_pipeline` | OK |
| `verify_v2_foundation` | OK |
| `verify_weekly_plan_dry_run` | OK |

**Bilanz:** 15/15 grün, kein Regression.

### 9.2 Akzeptanzkriterien (aus Audit)

| Kriterium | Status |
|---|---|
| Habit-Type-Migration: alte Habits ohne `type` werden als `build` gelesen | ✅ `test_default_habit_type_migration` |
| `reduce`-Habit mit Metadaten anlegbar | ✅ `test_add_reduce_habit_with_metadata` |
| `log_relapse(...)` schreibt `habit_relapses` + `habit_events` (recovery_used=0) | ✅ `test_log_relapse_writes_relapse_and_event` |
| `log_recovery(...)` mit recovery_used=1, Streak bleibt erhalten | ✅ `test_log_recovery_protects_streak` |
| `week_patterns(...)` erkennt ≥ 3 Pattern-Klassen | ✅ `test_pattern_detection_finds_multiple_classes` (4 von 5 Klassen) |
| `verify_habit_tracker` (alt) bleibt grün | ✅ |
| Alle 13 weiteren bestehenden Tests bleiben grün | ✅ |
| CLI-Smoke `habits patterns` und `habits relapse` ohne Crash | ✅ |
| `init_db` idempotent bei Re-Run | ✅ `test_init_db_idempotent` |
| Kein Telegram/Calendar-Write durch Phase-2-Code | ✅ `test_no_telegram_no_calendar_writes` |

### 9.3 Produktive DB-Migration verifiziert

Bestandsaufnahme nach Test-Lauf:
- `habit_definitions` enthält neue Spalten (`habit_type`, `failure_modes_json`, …)
- `habit_events` enthält `failure_mode`, `recovery_used`
- Tabelle `habit_relapses` existiert (leer)
- Drei produktive Habits (`habit-morning-routine`, `habit-evening-routine`, `habit-pullup-bar-hang`) korrekt als `habit_type='build'` migriert
- Keine Test-Pollution: `0` Relapses, `0` Events mit failure_mode, `0` Recovery-Events

---

## 10. Live-E2E (nicht Teil von Phase 2)

Die echte Telegram-E2E-Strecke `Telegram Text → Intent → log_relapse → habit_relapses` kommt erst, wenn **Phase 3** (Intake → Service-Wiring) implementiert ist. Phase 2 liefert die Service-Schicht; Phase 3 schließt die Schleife.

---

## 11. Schutzregel-Compliance

| Regel | Compliance |
|---|---|
| 1. Keine bestehende Datei gelöscht | ✅ |
| 2. Keine bestehenden Interfaces gebrochen | ✅ — `mark_done`, `skip_habit`, `pause_habit`, `weekly_report`, `today`, `status`, `handle_text`, `resolve_habit`, `add_habit` (neue Parameter optional mit None-Default) |
| 3. Calendar-Write nur mit Approval-Loop | ✅ — Phase 2 hat keinen Calendar-Write |
| 4. Keine Tasks-Auto-Complete | ✅ |
| 5. Keine Habit-Events überschrieben | ✅ — alle neuen Events sind `INSERT`, daily_status nutzt `UPSERT` (bestehendes Verhalten) |
| 6. Keine Termine/Aufgaben erfunden | ✅ |
| 7. Keine LLM-Output direkt persistiert | ✅ — Pattern-Erkennung deterministisch via SQL |
| 8. Idempotenz für Schreibaktionen | ✅ — `init_db` idempotent; `habit_relapses` hat keine harte Idempotenz, da Rückfälle wiederholt werden können (Auslegungsentscheidung: jeder Relapse ist ein Event) |
| 9. Live-E2E oder explizite Markierung | ✅ — Phase 2 hat 15-Test Verify-Suite. Telegram-E2E explizit als Phase 3 markiert |
| 10. Bestehende CLI funktioniert weiter | ✅ — `verify_eos_cli` grün |

---

## 12. Bewusst NICHT in Phase 2

- Energy-Checkin (Phase 3)
- Calendar Write (Phase 5)
- Telegram-Wiring von Intake → Habit-Service (Phase 3)
- LLM-Klassifikation von Triggern (deterministisch in V3)
- Audio-Intake (Phase 6)
- Habit-Reminder durch Scheduler-Jobs basierend auf Patterns (Phase 4+)

---

## 13. Nächste Schritte (Phase 3 Vorschlag)

1. **Intent → Service-Wiring**: `intake.classify_intent` Output (z.B. `intent=habit_log, scope=specific, completion=done_full, habit_hint=morgenroutine`) wird durch eine neue `dispatch.py` an `HabitService.mark_done` / `log_relapse` / `log_recovery` weitergegeben.
2. **Confidence-Gating**: `requires_confirmation=True` löst Rückfrage statt direktem Schreiben aus.
3. **Energy-Checkin Persistenz**: neuer Intent `daily_checkin`, neue Tabelle `energy_log`.
4. **Telegram-E2E**: Telegram-Webhook → Intake → Dispatch → HabitService — dann ist die Schleife geschlossen.
