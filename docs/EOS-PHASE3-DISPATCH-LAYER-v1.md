# EOS Phase 3 — Dispatch Layer, Pending Confirmations & Energy Log v1

**Stand:** 2026-05-01
**Status:** Plan — noch nicht implementiert
**Vorgänger:** [EOS-PHASE2-HABIT-COACHING-v1.md](EOS-PHASE2-HABIT-COACHING-v1.md), [EOS-V3-INTELLIGENT-LOOP-SPEC.md](EOS-V3-INTELLIGENT-LOOP-SPEC.md) §5

---

## 1. Was Phase 3 liefert

Phase 3 schließt die operative Schleife. Nach Abschluss von Phase 2 hat EOS Module ohne Verbindung. Phase 3 verbindet sie:

```text
Telegram Input
→ Intake Parse          (src/intake/intent_router.py)
→ Confidence Gate       (src/dispatch/router.py)
→ Pending Confirmation  (src/confirmations/service.py)  ← neu
→ Service Dispatch      (src/dispatch/router.py)        ← neu
→ Habit Event           (src/habits/service.py)
→ Energy Log            (src/energy/service.py)          ← neu
→ Persistenz            (SQLite: eos_v2.db)
→ Telegram Response     (JSON output → OpenClaw Agent)
→ Live-E2E-Nachweis
```

**Kernlieferungen:**

- `src/dispatch/` — Router, der IntakeResult entgegennimmt und an Services weiterleitet
- `src/confirmations/` — Pending-Confirmation-Service für mehrdeutige Eingaben
- `src/energy/` — Energy-Check-in-Persistenz (neue Tabelle `daily_energy_logs`)
- Drei neue SQLite-Tabellen: `pending_confirmations`, `daily_energy_logs`, `dispatch_log`
- Sieben neue CLI-Subcommands unter `dispatch`, `confirmations`, `energy`
- Fünf neue Intents in `intake/models.py`: `habit_relapse`, `habit_recovery`, `habit_failure`, `energy_checkin` (präziser als `daily_checkin`), `confirm_response`
- Verify-Suite `tests/verify_dispatch_layer.py` (Ziel: ≥ 20 Assertions)
- Live-E2E-Nachweis für 5 definierte Flows

---

## 2. Was NICHT Teil von Phase 3 ist

| Thema | Phase |
|---|---|
| Calendar Write | Phase 7 |
| Planning Proposal Engine | Phase 5 |
| Approval Layer für Calendar | Phase 6 |
| Tagesmodus-Auto-Klassifikation | Phase 4 |
| Personal Policy Loader/Evaluator | Phase 4 |
| Review Engine | Phase 8 |
| LLM-generierte Freitextantworten | Phase 4+ |
| Life Graph | Phase 10 |
| Audio-Intake | Phase 6 |

Verifiziert durch Test `test_no_calendar_write_no_planning`: `dispatch/router.py` darf kein `calendar_write`, `create_event` oder `planning_proposal` importieren oder aufrufen.

---

## 3. Neue Intents (Erweiterung intake/models.py)

Phase 2 hat `habit_log`, `habit_status`, `daily_checkin`, `plan_request`, `task_capture`, `calendar_proposal_request`, `review_request`, `unknown` definiert.

Phase 3 ergänzt:

| Intent | Auslöser | Beispiel |
|---|---|---|
| `habit_relapse` | reduce-Habit mit Rückfall | „hab wieder gescrollt" |
| `habit_recovery` | Recovery-Version einer verpassten Habit | „2-Minuten-Reset gemacht" |
| `habit_failure` | Habit mit explizitem Grund verpasst | „verschlafen heute" |
| `confirm_response` | Antwort auf eine offene Pending Confirmation | „ja, morgenroutine" |

`daily_checkin` bleibt erhalten und wird der primäre Intent für Energy-Check-ins. Die Entity-Extraktion in `intent_router.py` wird für `daily_checkin` um numerische Parsing-Logik erweitert (Schlaf, Energie, Stress, etc.).

---

## 4. Datenmodell — drei neue Tabellen

Alle drei Tabellen werden in `src/database/models.py` additiv ergänzt (`CREATE TABLE IF NOT EXISTS`). Kein Ändern bestehender Tabellen außer über `_ensure_columns()`.

### 4.1 `pending_confirmations`

```sql
CREATE TABLE IF NOT EXISTS pending_confirmations (
    id TEXT PRIMARY KEY,                     -- UUID4
    created_at_utc TEXT NOT NULL,
    expires_at_utc TEXT NOT NULL,            -- created + 30 Minuten
    user_id TEXT NOT NULL DEFAULT 'cli',     -- telegram:CHAT_ID oder 'cli'
    source TEXT NOT NULL DEFAULT 'cli',      -- 'telegram' | 'cli'
    original_text TEXT NOT NULL,
    parsed_intent TEXT NOT NULL,
    parsed_entities_json TEXT,               -- JSON-Objekt aus IntakeResult.entities
    missing_fields_json TEXT,                -- JSON-Array der fehlenden Felder
    confirmation_question TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',  -- pending | resolved | expired | cancelled
    resolved_at_utc TEXT,
    resolution_json TEXT                     -- JSON mit resolvierten Feldern
);

CREATE INDEX IF NOT EXISTS idx_pending_confirmations_status_user
    ON pending_confirmations(status, user_id);
```

**Status-Übergänge:**
```
pending → resolved  (User antwortet, Dispatch führt aus)
pending → expired   (30 min überschritten, kein Input)
pending → cancelled (User sendet explizit "abbrechen")
```

### 4.2 `daily_energy_logs`

```sql
CREATE TABLE IF NOT EXISTS daily_energy_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    local_date TEXT NOT NULL,               -- YYYY-MM-DD Berlin
    timestamp_utc TEXT NOT NULL,
    sleep_quality INTEGER,                  -- 1–10 oder NULL
    energy_level INTEGER,                   -- 1–10
    physical_fatigue INTEGER,               -- 1–10
    mental_load INTEGER,                    -- 1–10
    stress INTEGER,                         -- 1–10
    motivation INTEGER,                     -- 1–10
    soreness INTEGER,                       -- 1–10
    notes_json TEXT,                        -- JSON-Array mit Freitextnotizen
    source TEXT NOT NULL DEFAULT 'cli'      -- 'telegram' | 'cli'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_energy_logs_date_source
    ON daily_energy_logs(local_date, source);
```

**Idempotenz:** Ein zweiter Check-in für denselben Tag und dieselbe Source überschreibt den bestehenden Eintrag (`INSERT OR REPLACE`). Es gibt maximal einen Eintrag pro Tag pro Source.

**Pflichtfelder:** Nur `energy_level` ist Pflicht. Alle anderen Felder sind optional und werden `NULL` gesetzt, wenn der User sie nicht nennt.

### 4.3 `dispatch_log`

```sql
CREATE TABLE IF NOT EXISTS dispatch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_utc TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'cli',
    input_hash TEXT NOT NULL,              -- SHA256 der original_text (hex)
    intent TEXT NOT NULL,
    confidence REAL NOT NULL,
    action_type TEXT NOT NULL,             -- s. Tabelle unten
    target_service TEXT,                   -- 'HabitService' | 'EnergyService' | 'ConfirmationService' | NULL
    result_status TEXT NOT NULL,           -- ok | pending | error | skipped
    idempotency_key TEXT,                  -- optional, für Habit-Events
    error_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_dispatch_log_timestamp
    ON dispatch_log(timestamp_utc);
```

**`action_type`-Werte:**

| action_type | Bedeutung |
|---|---|
| `habit_mark_done` | HabitService.mark_done aufgerufen |
| `habit_skip` | HabitService.skip_habit aufgerufen |
| `habit_relapse` | HabitService.log_relapse aufgerufen |
| `habit_recovery` | HabitService.log_recovery aufgerufen |
| `habit_failure` | HabitService.log_failure_mode aufgerufen |
| `energy_log` | EnergyService.log aufgerufen |
| `pending_confirmation` | Keine Persistenz, Rückfrage erzeugt |
| `confirmation_resolve` | Pending Confirmation aufgelöst |
| `noop` | Kein Dispatch, unbekannter Intent oder low confidence |

`dispatch_log` ist **append-only**. Kein DELETE, kein UPDATE.

---

## 5. Neue Module

### 5.1 Verzeichnisstruktur

```
src/
├── dispatch/
│   ├── __init__.py      ← Re-Export: dispatch_text, DispatchResult
│   ├── router.py        ← Hauptlogik: dispatch_text()
│   ├── actions.py       ← Intent → Action Mapping, Idempotenz-Key-Generierung
│   └── result.py        ← DispatchResult Dataclass
├── confirmations/
│   ├── __init__.py      ← Re-Export: ConfirmationService, PendingConfirmation
│   ├── models.py        ← PendingConfirmation Dataclass
│   └── service.py       ← ConfirmationService: create, resolve, expire, list
└── energy/
    ├── __init__.py      ← Re-Export: EnergyService, EnergyLog
    ├── models.py        ← EnergyLog Dataclass, parse_energy_text()
    └── service.py       ← EnergyService: log, today, history
```

### 5.2 `src/dispatch/result.py`

```python
@dataclass(frozen=True)
class DispatchResult:
    status: str               # ok | pending | error | skipped
    action_type: str          # s. dispatch_log.action_type
    intent: str
    confidence: float
    response_text: str        # kurze deutsche Antwort für Telegram
    response_markdown: str    # längere Markdown-Version für CLI-Output
    habit_id: str | None      # wenn Habit betroffen
    energy_log_id: int | None # wenn Energy Log geschrieben
    confirmation_id: str | None  # wenn Pending Confirmation erzeugt
    error: str | None
```

### 5.3 `src/dispatch/router.py` — Hauptlogik

```
dispatch_text(raw_text, *, source="cli", user_id="cli", db_path=None) -> DispatchResult
```

**Ablauf:**

1. `classify_intent(raw_text)` → `IntakeResult`
2. Prüfe offene Pending Confirmations für diesen `user_id`
   - Wenn vorhanden + Intent = `confirm_response` oder confidence < MEDIUM:
     → Pending Confirmation resolven, erneut dispatchen mit ergänzten Entities
3. Confidence Gate:
   - `≥ CONFIDENCE_HIGH (0.85)` + `requires_confirmation=False` → direkt dispatchen
   - `≥ CONFIDENCE_MEDIUM (0.60)` + `requires_confirmation=True` → Pending Confirmation erzeugen
   - `< CONFIDENCE_MEDIUM` → immer Pending Confirmation
   - `intent="unknown"` → noop, Rückfrage
4. Action-Dispatch (nur wenn Confidence ausreichend):
   - `habit_log` → `HabitService.mark_done()` oder `skip_habit()` je nach `completion` Entity
   - `habit_relapse` → `HabitService.log_relapse()`
   - `habit_recovery` → `HabitService.log_recovery()`
   - `habit_failure` → `HabitService.log_failure_mode()`
   - `daily_checkin` → `EnergyService.log()`
5. `dispatch_log` schreiben (immer, auch bei noop)
6. `DispatchResult` zurückgeben

**Idempotenz-Regel für Habit-Events:**

Idempotency-Key = `{intent}:{habit_id}:{local_date}`. Wenn `dispatch_log` bereits einen Eintrag mit diesem Key und `result_status=ok` für heute enthält → `result_status=skipped`, kein zweites Write.

### 5.4 `src/confirmations/service.py`

| Methode | Signatur | Zweck |
|---|---|---|
| `create(intake_result, *, user_id, source, db_path)` | → `PendingConfirmation` | Erzeugt Confirmation, schreibt DB |
| `resolve(confirmation_id, resolution_text, *, db_path)` | → `PendingConfirmation` | Setzt status='resolved', schreibt resolution_json |
| `expire_all(*, db_path)` | → `int` | Setzt alle pending→expired wo expires_at_utc < jetzt |
| `list_pending(user_id, *, db_path)` | → `list[PendingConfirmation]` | Alle pending Confirmations dieses Users |
| `cancel(confirmation_id, *, db_path)` | → `PendingConfirmation` | Setzt status='cancelled' |

### 5.5 `src/energy/models.py` — `parse_energy_text()`

Deterministisch. Kein LLM.

Erkennt numerische Werte nach deutschen Schlüsselwörtern:
- `schlaf`, `sleep` → `sleep_quality`
- `energie`, `energy` → `energy_level`
- `stress` → `stress`
- `müde`, `muede`, `fatigue`, `körper` → `physical_fatigue`
- `mental`, `kopf`, `konzentration` → `mental_load`
- `motivation`, `motiviert` → `motivation`
- `muskelkater`, `kater`, `soreness` → `soreness`

Akzeptiert Formate: `energie 7`, `energie: 7/10`, `energie=7`.

Gibt `EnergyLog`-Dataclass zurück. Felder ohne Match = `None`.

Validierung: Werte müssen 1–10 sein. Außerhalb des Bereichs → Fehler, kein teilweises Schreiben.

### 5.6 `src/energy/service.py`

| Methode | Signatur | Zweck |
|---|---|---|
| `log(energy_log, *, db_path)` | → `dict` | `INSERT OR REPLACE` in `daily_energy_logs` |
| `today(*, db_path)` | → `dict \| None` | Heutiger Eintrag |
| `history(days, *, db_path)` | → `list[dict]` | Letzte N Tage |

---

## 6. Erweiterte Module

### 6.1 `src/database/models.py`

Additiv: drei neue `CREATE TABLE IF NOT EXISTS`-Blöcke in `init_db()`.
Keine bestehenden Tabellen werden geändert.

### 6.2 `src/intake/models.py`

`SUPPORTED_INTENTS` erweitert um:
- `"habit_relapse"`
- `"habit_recovery"`
- `"habit_failure"`
- `"confirm_response"`

### 6.3 `src/intake/intent_router.py`

Neue Routing-Blöcke in `classify_intent()`:
- `habit_relapse`: Schlüsselwörter „rückfall", „rückgefallen", „wieder geschrolt", „wieder gegessen", „erwischt"
- `habit_recovery`: Schlüsselwörter „2 minuten", „zwei minuten", „reset", „minimalversion", „trotzdem gemacht"
- `habit_failure`: Schlüsselwörter „verschlafen", „vergessen", „keine zeit", „keine lust", „nicht geschafft" + Verneinung
- `confirm_response`: Auslöser wenn `list_pending(user_id)` > 0 und Input kurz + konkret

Entity-Extraktion für `daily_checkin` um numerische Parse-Logik erweitert:
- Gibt `entities = {"sleep_quality": 6, "energy_level": 5, "stress": 7, ...}` zurück
- Felder ohne Treffer werden nicht gesetzt (kein `None` in entities)

### 6.4 `src/eos_cli.py`

Sieben neue Subcommands (additiv):

```
python3 -m src.eos_cli dispatch handle "<text>" [--user-id <id>] [--source {telegram,cli}]
python3 -m src.eos_cli dispatch log [--limit 20]

python3 -m src.eos_cli confirmations list [--user-id <id>]
python3 -m src.eos_cli confirmations resolve <confirmation_id> "<response_text>"
python3 -m src.eos_cli confirmations expire

python3 -m src.eos_cli energy log "<text>" [--date YYYY-MM-DD]
python3 -m src.eos_cli energy today
```

Alle geben JSON zurück (kompatibel mit `--json-only`).
Bestehende Subcommands (`run-job`, `habits`, `intake`) bleiben **unverändert**.

---

## 7. Fünf Phase-3-Flows

### Flow 1: Eindeutiger Habit-Log

```
Input:   "morgenroutine erledigt"
Intent:  habit_log (confidence ≥ 0.85)
Scope:   specific (habit_hint = morgenroutine)

→ HabitService.mark_done("morgenroutine", mode="full")
→ dispatch_log: action_type=habit_mark_done, result_status=ok
→ Response: "✓ Morgenroutine für heute als erledigt markiert."
```

### Flow 2: Mehrdeutiger Habit-Log → Rückfrage

```
Input:   "hab alles erledigt"
Intent:  habit_log (confidence 0.65)
Scope:   all_today (requires_confirmation=True)

→ ConfirmationService.create(...)
→ dispatch_log: action_type=pending_confirmation, result_status=pending
→ Response: "Welche Habit meinst du? Alle heutigen, oder eine bestimmte Routine?"
```

### Flow 3: Confirmation Resolve → Dispatch

```
Input:   "morgenroutine und abend"  (als Antwort auf offene Confirmation)
→ ConfirmationService.resolve(confirmation_id, ...)
→ Router erkennt confirm_response, ergänzt Entities
→ HabitService.mark_done("morgenroutine"), mark_done("abend")
→ dispatch_log: 2× action_type=habit_mark_done
→ Response: "✓ Morgenroutine und Abendroutine markiert."
```

### Flow 4: Energy Check-in

```
Input:   "schlaf 6, energie 5, stress 7, körper müde 6"
Intent:  daily_checkin (confidence ≥ 0.85)
Entities: {sleep_quality: 6, energy_level: 5, stress: 7, physical_fatigue: 6}

→ EnergyService.log(...)
→ dispatch_log: action_type=energy_log, result_status=ok
→ Response: "📊 Check-in gespeichert. Energie 5/10, Stress 7/10 — heute eher leichter Modus."
```

### Flow 5: Unbekannter Input → kein Write

```
Input:   "war ganz okay heute"
Intent:  unknown (confidence 0.30)

→ dispatch_log: action_type=noop, result_status=skipped
→ Response: "Ich bin mir nicht sicher, was du meinst. Habit erledigt? Energy Check-in?"
→ Kein Schreiben in habit_events oder daily_energy_logs.
```

---

## 8. Verifikation

### 8.1 Verify-Suite `tests/verify_dispatch_layer.py`

**Mindestanforderung:** ≥ 20 Assertions, alle grün.

Abgedeckte Tests:

| Test | Beschreibung |
|---|---|
| `test_dispatch_habit_log_high_confidence` | Flow 1: direktes mark_done |
| `test_dispatch_creates_pending_on_ambiguous` | Flow 2: Rückfrage erzeugen |
| `test_dispatch_confirmation_resolve` | Flow 3: Confirmation + Dispatch |
| `test_dispatch_energy_checkin` | Flow 4: Energy Log schreiben |
| `test_dispatch_unknown_no_write` | Flow 5: noop, kein Write |
| `test_dispatch_idempotency` | Zweiter Aufruf mit gleichem Habit+Datum → skipped |
| `test_dispatch_log_append_only` | dispatch_log wird nie überschrieben |
| `test_confirmation_expires_after_30min` | expire_all setzt überfällige Confirmations |
| `test_energy_log_upsert_same_day` | Zweiter Check-in selber Tag → REPLACE |
| `test_energy_parse_partial` | Nur energy_level → rest None |
| `test_energy_parse_out_of_range` | Wert 11 → Fehler, kein Write |
| `test_dispatch_habit_relapse_intent` | habit_relapse → log_relapse |
| `test_dispatch_habit_recovery_intent` | habit_recovery → log_recovery |
| `test_new_intents_in_supported` | SUPPORTED_INTENTS enthält alle 4 neuen |
| `test_no_calendar_write_no_planning` | dispatch/router.py importiert kein calendar_write |
| `test_init_db_idempotent_phase3` | init_db doppelt aufrufen → kein Fehler |
| `test_cli_dispatch_handle_json` | CLI dispatch handle → valides JSON |
| `test_cli_energy_today_empty` | energy today ohne Log → {"status": "no_data"} |
| `test_cli_confirmations_list_empty` | confirmations list ohne Einträge → {"confirmations": []} |
| `test_verify_existing_tests_regression` | alle Phase-2-Tests bleiben grün |

### 8.2 Regression: Alle bisherigen Verify-Tests

| Test | Muss weiter grün |
|---|---|
| `verify_habit_coaching` | ✓ |
| `verify_habit_tracker` | ✓ |
| `verify_intake_engine` | ✓ |
| `verify_eos_cli` | ✓ |
| `verify_eos_core` | ✓ |
| `verify_eos_state` | ✓ |
| `verify_v2_foundation` | ✓ |
| alle weiteren | ✓ |

### 8.3 Live-E2E-Nachweis (Pflicht für Phase-3-Abnahme)

Unit-Tests und synthetische Tests reichen **nicht** für Abnahme. Live-E2E ist Pflichtbestandteil.

Die fünf Flows werden mit echten CLI-Aufrufen gegen die Produktionsdatenbank (`eos_v2.db`) ausgeführt und die Datenbankeinträge werden direkt verifiziert:

```bash
# Flow 1
python3 -m src.eos_cli --json-only dispatch handle "morgenroutine erledigt"
# → prüfe: habit_events enthält today + done_full für habit-morning-routine

# Flow 2
python3 -m src.eos_cli --json-only dispatch handle "hab alles erledigt"
# → prüfe: pending_confirmations enthält 1 Eintrag mit status=pending

# Flow 3
CONF_ID=$(python3 -c "import sqlite3; ...")  # hol aktuelle Confirmation-ID
python3 -m src.eos_cli --json-only confirmations resolve $CONF_ID "morgenroutine"
# → prüfe: pending_confirmations status=resolved, habit_events gesetzt

# Flow 4
python3 -m src.eos_cli --json-only dispatch handle "schlaf 6, energie 5, stress 7"
# → prüfe: daily_energy_logs enthält today mit sleep_quality=6, energy_level=5, stress=7

# Flow 5
python3 -m src.eos_cli --json-only dispatch handle "war ganz okay"
# → prüfe: kein neuer habit_events Eintrag, dispatch_log action_type=noop
```

---

## 9. Schnittstelle zu EOS OpenClaw-Agent (Telegram-E2E)

Der EOS OpenClaw-Agent ruft `dispatch handle` als CLI-Tool auf und gibt das JSON weiter.

**Erwartetes Verhalten des Agents:**

```
User → Telegram: "morgenroutine erledigt"
Agent → CLI: python3 -m src.eos_cli --json-only dispatch handle "morgenroutine erledigt"
Agent liest JSON response_text aus Result
Agent → Telegram: "✓ Morgenroutine für heute als erledigt markiert."
```

**Für Pending Confirmations:**

```
User → Telegram: "hab alles erledigt"
Agent → CLI: dispatch handle "hab alles erledigt"
Agent liest confirmation_question aus Result
Agent → Telegram: "Welche Habit meinst du? Alle heutigen oder eine bestimmte?"

User → Telegram: "morgenroutine und abend"
Agent → CLI: dispatch handle "morgenroutine und abend" --user-id telegram:6526468834
Agent liest response_text
Agent → Telegram: "✓ Morgenroutine und Abendroutine markiert."
```

Die `--user-id`-Option ermöglicht die Zuordnung offener Confirmations zu konkreten Telegram-Nutzern. Der Agent übergibt immer `--user-id telegram:<chat_id>`.

---

## 10. Schutzregeln-Compliance

| Regel | Anforderung |
|---|---|
| Keine bestehende Datei gelöscht | ✓ — nur neue Module |
| Keine bestehenden Interfaces gebrochen | ✓ — alle neuen CLI-Subcommands additiv |
| `eos_state.json` unverändert | ✓ — keine neuen State-Felder in Phase 3 |
| Calendar Write nicht in Phase 3 | ✓ — verifiziert per Test |
| Keine LLM-Output direkt persistiert | ✓ — alle Writes deterministisch |
| Idempotenz für Schreibaktionen | ✓ — dispatch_log idempotency_key |
| Alle Phase-0–2-Tests grün | ✓ — Regression-Test in Suite |
| Kein Telegram-Send aus dispatch/energy | ✓ — nur JSON-Output, Agent entscheidet |

---

## 11. Bewusst NICHT in Phase 3

- `src/policy/loader.py` — Personal Policy (Phase 4)
- `src/policy/evaluator.py` — Policy Evaluation (Phase 4)
- Tagesmodus-Klassifikation — Phase 4
- LLM-Freitext-Generierung für Antworten — deterministische Templates in Phase 3
- Telegram-Gateway-Code in Python — Agent ruft CLI auf, kein direktes Telegram-SDK
- `gog` Calendar-Integration in Dispatch — Phase 4 (Tagesstatus)
- Approval-Table und Proposal-ID — Phase 6

---

## 12. Risiken

| Risiko | Einschätzung | Gegenmaßnahme |
|---|---|---|
| Offene Confirmation wird nicht gefunden, wenn User-ID inkonsistent | kritisch | user_id immer aus Telegram-Chat-ID, niemals erraten |
| Energy-Parse erkennt falsche Werte | mittel | Bereichsvalidierung 1–10, bei Fehler kein teilweises Schreiben |
| Dispatch feuert doppelt bei Retry | kritisch | Idempotency-Key in dispatch_log, vor jedem Write prüfen |
| Confirmation läuft ab und User merkt es nicht | mittel | 30-Minuten-Fenster, expire_all per CLI/Scheduler aufrufbar |
| Intent-Erkennung für `confirm_response` zu breit | mittel | nur auslösen wenn tatsächlich offene Confirmation existiert |
| dispatch_log wächst unbegrenzt | niedrig | Phase 4 ergänzt optionale Cleanup-Policy |
| Regression in Phase-2-Tests durch neue Intents | niedrig | SUPPORTED_INTENTS ist additiv, bestehende Keys unverändert |

---

## 13. Nächste Schritte nach Phase 3 (Phase 4 Vorschlag)

1. **Daily Command Center**: Tagesstatus aus Calendar + Tasks + Energy Log + Habits zusammenführen
2. **Tagesmodus-Klassifikation**: `normal_day`, `hard_load_day`, `recovery_day`, `sprint_day` etc.
3. **Personal Policy Loader**: `docs/personal-policy/EOS-PERSONAL-POLICY.md` → `personal_policy.compiled.json`
4. **Policy Evaluator**: Dispatch-Entscheidungen gegen Policy prüfen (z.B. kein Deep Work bei `sick_day`)

Phase 4 ist nur sinnvoll, wenn Phase-3-Live-E2E vollständig bestanden ist.
