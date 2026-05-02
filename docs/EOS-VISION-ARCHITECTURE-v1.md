# EOS Vision Architecture v1

**Stand:** 2026-05-01
**Scope:** Strategischer Architekturplan für EOS als persönliches Operating System
**Modus:** Spec-Phase, **kein Code**, kein Host-Change. Liefert Entscheidungsgrundlage für Phase 3+.

---

## 1. Critical Architecture Assessment

### 1.1 Was heute *gut* ist (verteidigen)

| Bereich | Stärke |
|---|---|
| **Agent-Trennung** | EOS läuft als eigener `personal-assistant` Agent, dedizierter Telegram-Bot. Kein Multi-Agent-Zoo, klare Identität. |
| **Systems-of-Record-Disziplin** | Calendar / Tasks / Vault / SQLite haben **strikt getrennte Rollen**. SQLite ist explizit *nur* Derived State. |
| **Deterministische Coaching-Engine** | Endliche Reasons + endliche Recommendations + Ampelstatus. Keine LLM-Halluzination im Kern. |
| **Idempotenter Scheduler** | Jeder Job hat Idempotenz-Key, keine Doppel-Sends. systemd-Timer rufen direkt das CLI auf — 0 Token-Kosten für reine Status-Sends. |
| **JSON-Schema-validierter State** | `eos_state.json` ist strikt schema-validiert, neue Felder müssen explizit deklariert sein. |
| **Verify-Disziplin** | 15 grüne Verify-Tests, Migration nachweislich rückwärtskompatibel. Keine Tests die nur „TODO" bedeuten. |
| **Phase 1 + 2 Ergebnis** | Intake-Engine (deterministische Intent-Klassifikation) + Habit Coaching Engine (Typen, Trigger, Recovery, Patterns) sind fertig und stabil. |

### 1.2 Was heute *strukturell schwach* ist (Hauptangriffspunkte für V3)

| Schwäche | Konkrete Wirkung |
|---|---|
| **Keine geschlossene Schleife** | Intake klassifiziert, aber niemand wired den Output an die Service-Mutationen. Habit-Service hat `log_relapse` — wird aber von keiner Telegram-Strecke aufgerufen. |
| **Kein Energy-/Belastungs-Modell** | Planning kennt `energy_profile` als statische Tagesfenster, aber kein dynamischer Energie-Check-in fließt in Tagespläne ein. |
| **Kein Dialog-/Approval-State** | EOS „fragt zurück" existiert in der Spec, aber es gibt keine Tabelle für **pending_confirmations** — bedeutet: nach einer Rückfrage geht der Kontext verloren. |
| **Kein Calendar-Write-Pfad** | Calendar-Write ist bewusst deaktiviert. Approval-Flow existiert nur als Konzept. Ohne Write bleibt EOS ein Empfehlungsbot, kein Operations-System. |
| **Kein Tagesmodus-Modell** | „hard_load_day" lebt implizit als Wochentags-Heuristik (Do–Sa). Kein expliziter Tagesmodus, keine Mode-aware Habit-Versionen. |
| **Vault produktiv nicht gemountet** | Reviews existieren nur in SQLite, nicht in Markdown — keine Langzeit-Lesbarkeit für den Menschen. |
| **Kein Pattern-Feedback-Loop** | `week_patterns()` erkennt Muster, aber keine Empfehlung wird daraus automatisch in Plan-Outputs übernommen. Erkennung ohne Konsequenz = Theater. |
| **Kein Life-Graph** | Goals → Projects → Tasks → Habits → Reviews existieren als isolierte Tabellen, ohne explizite Beziehung. „Bachelorarbeit" ist als Projekt nirgends modelliert. |
| **Kein Routing zu Spezialisten** | Solara/Pharos/Photon/Lucent/Aurelius/Lux existieren als Workspaces, aber EOS hat keinen Routing-Pfad. „Ich brauche einen Recovery-Plan" landet bei EOS statt bei Solara. |
| **Cron-/systemd-Doppelpfad** | OpenClaw-Cron-Jobs sind disabled, systemd-Timer aktiv. Funktioniert, aber Source-of-Truth-Doppelung. Sollte explizit dokumentiert oder konsolidiert werden. |

### 1.3 Risiken in der heutigen Struktur

- **Heartbeat-Spam:** Heartbeat sendet alle 30 Min, ohne Bedingungs-Filter („nur wenn Entscheidung nötig"). Kann zu Ignorier-Verhalten führen.
- **Untriaged Tasks:** Schon im State sind alle 9 task_annotations `untriaged`. Planning Engine hat damit aktuell **keine** valide Top-3-Basis — wird vom `daily_capacity` zwar erkannt, aber nicht eskaliert.
- **JSON-State-Mutation:** Wenn Phase 3+ neue Felder ergänzt (z.B. `tagesmodus`, `energy_log_pointer`), muss jede Erweiterung schema-validiert und rückwärtskompatibel sein — sonst kippt die Validierung der bestehenden Datei.
- **Telegram als einziger Eingang:** Wenn der Bot abstürzt oder Token rotiert, ist EOS stumm. Kein Backup-Eingang (Web-UI, lokales CLI mit Telegram-Mirror).

---

## 2. Vision Architecture

### 2.1 Leitsatz

> EOS soll nicht mehr Features haben. EOS soll **bessere Entscheidungen** treffen.

Jede Architekturentscheidung in V3 wird gegen diesen Maßstab geprüft. Ein Feature, das keine messbar bessere Entscheidung ermöglicht, kommt nicht rein.

### 2.2 Sechs Kernsysteme (Zielbild)

```
┌────────────────────────────────────────────────────────────────┐
│                      Telegram (Eingang)                        │
└──────────────────────────┬─────────────────────────────────────┘
                           ▼
        ┌──────────────────────────────────────────┐
        │  1. Intake Layer                         │
        │     - text/audio → Intent + Confidence   │
        │     - Confidence-Gate (high/med/low)     │
        │     - Pending-Confirmation State         │
        └──────────────┬───────────────────────────┘
                       ▼
        ┌──────────────────────────────────────────┐
        │  2. State Layer (Sources of Record)      │
        │     - Google Calendar (hard events)      │
        │     - Google Tasks (active tasks)        │
        │     - Vault (knowledge, reviews)         │
        │     - SQLite (events, derived, IDs)      │
        │     - JSON-State (policy, rules)         │
        └──────────────┬───────────────────────────┘
                       ▼
       ┌────────────────────────────────────────────┐
       │  3. Planning Layer                         │
       │     - Hard + soft constraints              │
       │     - Tagesmodus (normal/hard/recovery/…)  │
       │     - Energy + Sleep + Stress              │
       │     - Output: Plan + Begründung + Risiko   │
       └─────────────┬─────────────────────────────┘
                     ▼
   ┌───────────────────────────────────────────────────┐
   │  4. Habit Coaching Layer                          │
   │     - Versionen: full/min/emergency/recovery/…    │
   │     - Typen: build/maintain/reduce/avoid/recovery │
   │     - Trigger + Barriere + Ersatzhandlung         │
   │     - Pattern-Feedback in Plan                    │
   └───────────────┬───────────────────────────────────┘
                   ▼
   ┌──────────────────────────────────────────────────┐
   │  5. Review Layer                                 │
   │     - Daily / Weekly / Monthly Review            │
   │     - Pattern-Insights → Personal Policy Engine  │
   │     - Vault-Note pro Review                      │
   └────────────────┬─────────────────────────────────┘
                    ▼
   ┌──────────────────────────────────────────────────┐
   │  6. Approval Layer                               │
   │     - Vorschläge sammeln                         │
   │     - Erlaubte Aktionen post-Approval            │
   │     - Audit-Log jeder Schreibaktion              │
   │     - Calendar-Write / Task-Write / Vault-Write  │
   └──────────────────────────────────────────────────┘
```

### 2.3 Was EOS *bewusst nicht* wird

- Kein Fitness-/Trainings-Coach — das macht **Solara**.
- Kein Research-Agent — das macht **Pharos**.
- Kein Coding-Tool — das macht **Photon**.
- Kein Schreib-Assistent — das macht **Lucent**.
- Keine Entscheidungs-Eskalation für externe Themen — das macht **Aurelius**.
- Kein Quick-Task-Helfer für triviale Anfragen — das macht **Lux**.

EOS ist der **Orchestrator des persönlichen Lebens**, nicht der Allesmacher.

---

## 3. Proposed Module Map

### 3.1 Bestand (heute, soll bestehen bleiben)

| Modul | Rolle | V3-Verhalten |
|---|---|---|
| `src/runtime.py` | Pfade + .env | Bleibt unverändert |
| `src/eos_core.py` | Schema, Capacity, Ranking | Bleibt unverändert |
| `src/eos_cli.py` | CLI-Dispatcher | Wächst um 4–6 neue Subcommands (additiv) |
| `src/audits.py` | Cron/Models/Vault Audits | Erweitert um `audit_pending_confirmations` |
| `src/database/models.py` | SQLite-Schema | Wächst additiv um neue Tabellen |
| `src/habits/{service,types,triggers,patterns}.py` | Habit Coaching v1 | **fertig (Phase 2)**, V3 ergänzt nur Versionen |
| `src/intake/{models,normalizer,confidence,intent_router}.py` | Intent-Klassifikation | **fertig (Phase 1)**, V3 ergänzt audio-Pfad |
| `src/jobs/{daily_capacity,evening_reset,weekly_plan,runner}.py` | Scheduler-Jobs | Erweitert um Mode-aware Output |
| `src/gateways/{google_tasks,telegram,tts_*}.py` | I/O-Gateways | Bleibt; Calendar-Write-Modul kommt **separat** als `src/gateways/google_calendar.py` |
| `src/vault/brain_dump.py` | Vault-Schreiber | Wächst um Daily/Weekly-Note-Renderer |

### 3.2 Neu (V3, additiv)

| Modul | Rolle |
|---|---|
| `src/intake/audio.py` | Telegram-Audio → Whisper-Transkript → Intent (nutzt bestehende `local-whisper` Skill) |
| `src/dispatch/__init__.py` + `router.py` | **Bindeglied zwischen Intake und Service-Layer.** Nimmt `IntakeResult` und ruft passende Service-Methode (Habit, Plan, Calendar). Hier sitzt das **Confidence-Gating** in einer einzigen Stelle. |
| `src/dispatch/pending.py` | Pending-Confirmation-State (SQLite-Tabelle `pending_confirmations`). Speichert mehrdeutige Eingaben für Rückfrage-Antworten. |
| `src/energy/__init__.py` + `service.py` | Energy- und Belastungs-Logging (Schlaf, Stress, Soreness, Motivation). SQLite-Tabelle `energy_log`. |
| `src/planning/__init__.py` + `proposer.py` | **Planning Proposal Engine** — kombiniert Calendar + Tasks + Habits + Energy + Tagesmodus zu einem strukturierten Vorschlag. |
| `src/planning/modes.py` | Endliche Tagesmodi (`normal_day`, `hard_load_day`, `recovery_day`, `sprint_day`, `admin_day`, `social_day`, `exam_mode`, `travel_mode`, `sick_day`) + Mode-Klassifikator. |
| `src/planning/policy.py` | **Personal Policy Engine** — endliche, deterministische Wenn-Dann-Regeln (z.B. „wenn Schlafqualität < 5, dann nur Top-1"). |
| `src/approval/__init__.py` + `gateway.py` | Approval-Layer. Zentrale Stelle, an der jede Schreibaktion ankommt — schreibt nach Approval und protokolliert ins `approval_log`. |
| `src/calendar/writer.py` | Calendar-Write-Adapter mit endlicher Whitelist erlaubter Aktionen (`create_block`, `create_admin_block`). Niemals `delete`/`move` ohne Sonderfreigabe. |
| `src/review/{daily,weekly,monthly}.py` | Review-Generatoren mit echten Datenfragen. Schreibt ins `daily_evaluations`, optional ins Vault. |
| `src/review/insights.py` | Pattern-Insights → konvertiert `PatternSignal` aus Habit-Patterns in Plan-Hinweise. |
| `src/lifegraph/__init__.py` + `model.py` | Goal/Project/Task/Habit/Block-Graph. Optional Phase 6+. |
| `src/routing/__init__.py` + `router.py` | Routing-Adapter zu Solara/Pharos/Photon/Lucent/Aurelius/Lux (nutzt OpenClaw-Subagent-Mechanik). Phase 7+. |
| `tests/verify_dispatch.py`, `verify_planning.py`, `verify_approval.py`, `verify_review.py`, `verify_energy.py`, `verify_lifegraph.py`, `verify_routing.py` | Verify-Tests pro neuem Modul |
| `docs/EOS-V3-PHASE3-DISPATCH.md`, `docs/EOS-V3-PHASE4-PLANNING.md`, `docs/EOS-V3-PHASE5-CALENDAR-WRITE.md`, `docs/EOS-V3-PHASE6-REVIEW.md`, `docs/EOS-V3-PHASE7-ROUTING.md` | Spec pro Phase |

### 3.3 Verbotene Module (explizite Nicht-Ziele)

- ❌ Kein `src/llm/` mit direkten Anthropic-/OpenAI-Calls in der Service-Schicht. Falls LLM nötig, dann als optionaler Layer hinter Confidence-Gate, niemals als Primärquelle.
- ❌ Kein `src/voice_assistant.py` mit eigener Audio-Pipeline. Nur über `local-whisper` Skill via `src/intake/audio.py`.
- ❌ Kein „universal_dispatcher.py" — Dispatch ist auf endliche Intents beschränkt.
- ❌ Kein paralleler State-Speicher (kein Redis, kein extra-DB).

---

## 4. Data Model Upgrade Plan

### 4.1 SQLite-Erweiterungen (additiv, idempotent über `_ensure_columns`)

#### Neu: `pending_confirmations`
```
id INTEGER PRIMARY KEY
chat_id TEXT NOT NULL
intent TEXT NOT NULL
entities_json TEXT NOT NULL
confirmation_question TEXT NOT NULL
created_at_utc TEXT NOT NULL
expires_at_utc TEXT NOT NULL          -- typisch +30min
resolved INTEGER NOT NULL DEFAULT 0
resolved_at_utc TEXT
resolution_choice TEXT
```
Verbindlich: jede mehrdeutige Eingabe legt einen Eintrag an, jede Folge-Antwort konsumiert genau einen.

#### Neu: `energy_log`
```
id INTEGER PRIMARY KEY
business_date_berlin TEXT NOT NULL
captured_at_utc TEXT NOT NULL
sleep_quality INTEGER          -- 1..10
physical_fatigue INTEGER       -- 1..10
mental_load INTEGER            -- 1..10
soreness INTEGER               -- 1..10
motivation INTEGER             -- 1..10
stress INTEGER                 -- 1..10
notes TEXT
source TEXT NOT NULL           -- cli | telegram | derived
```

#### Neu: `behavior_events`
Für `reduce`/`avoid`-Habits über das hinaus, was `habit_relapses` schon kann:
```
id INTEGER PRIMARY KEY
habit_id TEXT NOT NULL
event_at_utc TEXT NOT NULL     -- exakter Zeitpunkt, nicht nur Datum
trigger_canonical TEXT NOT NULL
trigger_freeform TEXT
context TEXT                   -- z.B. "im Bett", "vor dem Laptop"
intensity INTEGER              -- 1..10
barrier_used TEXT              -- z.B. "Handy außerhalb des Betts"
replacement_used TEXT
notes TEXT
```
`habit_relapses` bleibt der Tagesaggregat. `behavior_events` ist die Punktbeobachtung.

#### Neu: `tagesmodus`
```
business_date_berlin TEXT PRIMARY KEY
mode TEXT NOT NULL             -- normal_day | hard_load_day | …
classifier_source TEXT NOT NULL -- auto | user | calendar_inference
notes TEXT
created_at_utc TEXT NOT NULL
updated_at_utc TEXT NOT NULL
```

#### Neu: `task_metadata`
Erweitert die heute schon vorhandenen `task_annotations` aus dem JSON-State um persistente, schreibbare Felder:
```
task_external_id TEXT PRIMARY KEY    -- Google Tasks ID
project TEXT
priority TEXT                         -- P1|P2|P3|untriaged
estimated_minutes INTEGER
energy_required TEXT                  -- high|medium|low|unknown
deadline_date TEXT
next_action TEXT
defer_count INTEGER NOT NULL DEFAULT 0
last_reviewed_at_utc TEXT
triage_status TEXT                    -- ready|needs_triage
```

#### Neu: `approval_log`
```
id INTEGER PRIMARY KEY
proposed_at_utc TEXT NOT NULL
proposed_action TEXT NOT NULL         -- z.B. "calendar.create_block"
payload_json TEXT NOT NULL
status TEXT NOT NULL                  -- pending|approved|denied|expired|executed|failed
approved_at_utc TEXT
executed_at_utc TEXT
external_id TEXT                      -- z.B. Google Calendar event id
error TEXT
```

#### Neu: `review_log`
```
id INTEGER PRIMARY KEY
review_kind TEXT NOT NULL              -- daily|weekly|monthly
business_date_berlin TEXT NOT NULL
created_at_utc TEXT NOT NULL
data_json TEXT NOT NULL                -- vollständige Review-Antworten
vault_path TEXT                        -- falls in Vault gespiegelt
```

### 4.2 JSON-State (`eos_state.json`)

**Additiv und schema-validiert:**

```json
{
  "schema_version": 2,
  "modes": {
    "default": "normal_day",
    "calendar_inference_rules": [
      { "if": "fixed_sport_block AND work_shift", "then": "hard_load_day" },
      { "if": "no_hard_event AND weekend", "then": "social_day" }
    ]
  },
  "personal_policy_rules": [
    { "id": "p001", "if": "sleep_quality < 5", "then": "limit_to_top1" },
    { "id": "p002", "if": "task_deferred_3x", "then": "request_resize" }
  ],
  "lifegraph": {
    "goals": [],
    "projects": [],
    "default_review_cadence": "weekly"
  }
}
```

Schema-Migration: `schema_version: 1 → 2` mit Migrator, der bestehende V1-Files **nicht** invalidiert.

### 4.3 Vault-Struktur

Verbindlich (passt zur EOS-V1-Spec):
```
00 Inbox/                  ← Brain Dumps
10 Daily Notes/YYYY-MM-DD.md
20 Reviews/weekly-YYYY-Www.md
21 Reviews/monthly-YYYY-MM.md
30 Projects/<project-slug>.md
40 Knowledge/
50 Decisions/<decision-slug>.md
```

Phase 8 mountet diese Struktur produktiv ein, Reviews schreiben ab Phase 6 hinein.

---

## 5. Conversation Flow Plan

### 5.1 Flow A — Habit-Eingabe (mit Confidence-Gate)

```
User (Telegram):  „hab alles erledigt"
        │
        ▼
intake.classify_intent()  →  intent=habit_log, confidence=0.78, scope=all_today
        │
        ▼
dispatch.router.dispatch()
        │
        ├─ confidence >= 0.85  →  HabitService.mark_done(scope) direkt
        │
        ├─ 0.60 <= confidence < 0.85  →  pending_confirmations.create(...)
        │                                Telegram: „Ich interpretiere …
        │                                          Stimmt das? (ja/nein)"
        │
        └─ confidence < 0.60  →  Telegram: konkrete Rückfrage, kein Logging
```

### 5.2 Flow B — Tagesplan-Vorschlag

```
User: „plane mir den Tag"
        │
        ▼
intent=plan_request, confidence=0.92
        │
        ▼
planning.proposer.build_day_proposal(date=today)
   ├─ liest Calendar (live)
   ├─ liest Tasks (canonical lists)
   ├─ liest Habits (today)
   ├─ liest Energy-Log (latest)
   ├─ klassifiziert Tagesmodus
   ├─ wendet personal_policy_rules an
   └─ erzeugt PlanProposal { mode, blocks, top1, risks, recommendation }
        │
        ▼
Telegram: strukturierter Vorschlag (nutzt template `daily-output.md`)
          „Soll ich Top-1 als Calendar-Block eintragen? (ja/nein)"
```

### 5.3 Flow C — Calendar-Write nach Approval

```
User: „ja, eintragen"
        │
        ▼
dispatch.router resolves pending_confirmations.latest(chat_id)
        │
        ▼
approval.gateway.execute(action="calendar.create_block", payload={...})
   ├─ approval_log.insert(status=approved)
   ├─ calendar.writer.create_block(...)  → Google Calendar API
   ├─ approval_log.update(status=executed, external_id=...)
   └─ Telegram: „Block ‚Kapitel 3.2' 09:00–10:00 angelegt."
```

### 5.4 Flow D — Bad-Habit-Rückfall

```
User: „ich habe wieder zu lange gescrollt"
        │
        ▼
intent=bad_habit_event, confidence=0.83
        │
        ▼
dispatch.router → erkennt „scroll" → resolve_habit("doomscrolling-night")
                                     habit_type="reduce"
        │
        ▼
Telegram: „Was war der Hauptauslöser? (1) Müdigkeit (2) Stress (3) Langeweile (4) Aufschieben (5) Handy im Bett"
        │  (pending_confirmations gesetzt)
        │
        ▼
User: „1"
        │
        ▼
HabitService.log_relapse(habit, trigger="müdigkeit", severity="moderate")
        │
        ▼
behavior_events.insert(...)
Telegram: „Eingetragen. Morgen Barriere setzen: Handy außerhalb des Betts laden? (ja/nein)"
```

### 5.5 Flow E — Daily Check-in / Energy

```
User: „checkin: schlaf 4, stress 8, motivation 5"
        │
        ▼
intent=daily_checkin, entities parsed deterministisch
        │
        ▼
energy.service.log_checkin(...)
        │
        ▼
planning.proposer.adjust_today_if_needed()
   ├─ wendet personal_policy_rules an (z.B. sleep<5 → limit_to_top1)
   └─ schickt nur dann Telegram, wenn Anpassung nötig ist
```

---

## 6. Approval and Safety Plan

### 6.1 Aktions-Whitelist

| Aktion | Modus | Erlaubt |
|---|---|---|
| `calendar.create_block` (Deep Work, Routine, Admin) | Approval | ✅ |
| `calendar.create_event_simple` (neue, nicht wiederkehrend) | Approval | ✅ |
| `tasks.create` | Approval | ✅ |
| `tasks.complete` | Approval | ✅ |
| `vault.write_review` (daily/weekly/monthly) | Approval | ✅ |
| `habit_state.persist_evaluation` | Auto | ✅ (deterministisch, kein User-Approval nötig) |
| `calendar.delete_event` | **Sonderfreigabe pro Aktion** | ⚠️ |
| `calendar.move_event` | **Sonderfreigabe pro Aktion** | ⚠️ |
| `calendar.modify_recurring_rule` | **Sonderfreigabe pro Aktion** | ⚠️ |
| `tasks.bulk_complete` | **Sonderfreigabe pro Aktion** | ⚠️ |
| `calendar.respond_external_invite` | **Verboten in V3** | ❌ |
| `calendar.modify_sport_event` | **Verboten in V3** | ❌ |

### 6.2 Approval-Lebenszyklus

```
PROPOSED → (User „ja") → APPROVED → EXECUTED  → log final
        \ (User „nein") → DENIED   → log final
        \ (Timeout)     → EXPIRED  → log final
        \ (Exec-Fehler) → FAILED   → log final
```

**Verbindlich:**
- Jeder Übergang ins `approval_log` mit Timestamp.
- TTL für `PROPOSED` = **30 Min** (passt zur Heartbeat-Frequenz).
- Wenn `EXECUTED` einen `external_id` zurückgibt, wird dieser persistiert (für späteren Re-Lookup oder Undo).

### 6.3 Audit-Anforderungen

- Jede Schreibaktion **muss** in `approval_log` landen (auch automatische).
- `audit_pending_confirmations` CLI-Health-Check meldet Pending-Stau (z.B. „> 5 PROPOSED älter als 2h").
- Rate-Limit: max **3 Calendar-Writes pro Stunde** (Schutz gegen Loop-Bug).

### 6.4 Safety-Invarianten

1. **Niemals** ohne Approval externe Schreibaktion.
2. **Niemals** ohne frischen Calendar-Read direkt vor einem Write (Race-Schutz).
3. **Immer** Idempotenz-Key pro Approval (kein doppeltes Anlegen).
4. **Niemals** LLM-Output direkt als Schreib-Payload — Payload muss durch ein Schema validiert werden.
5. **Niemals** an Nicht-Endrit-Chat senden (Telegram-Allowlist).

---

## 7. Testing Strategy

### 7.1 Vier Testklassen

| Klasse | Zweck | Beispiele |
|---|---|---|
| **Unit Tests** | Einzelne reine Funktionen | `classify_trigger("müde") == "muede"` |
| **Contract Tests** | Schemas + Service-Verträge | `IntakeResult.to_dict()` ist JSON-serialisierbar; `eos_state.json` validiert gegen Schema |
| **Synthetic Tests** | Service mit Test-DB, ohne externe APIs | `verify_habit_coaching.py` — temp-DB, simulierte Wochenmuster |
| **Live-E2E Tests** | Echter Telegram-Bot, echtes Google Calendar/Tasks | Manuell, dokumentiert pro Feature |

### 7.2 Pflicht-E2E pro Feature

| # | Flow | Akzeptanz |
|---|---|---|
| E1 | Telegram-Text → Intake → Habit Event → SQLite | Habit-Event sichtbar in `eos_v2.db`, Telegram-Bestätigung erhalten |
| E2 | Telegram-Text → Tagesplan-Vorschlag → Telegram-Antwort | Strukturierter Plan im Chat, `daily_evaluations` geschrieben |
| E3 | Telegram-Approval → Calendar-Re-Read → Calendar-Write | Echter Termin in Google Calendar, `approval_log` mit `external_id` |
| E4 | Daily-Check-in → Review → SQLite | `energy_log` + `review_log` Eintrag |
| E5 | Weekly-Review → Vault-Note | Markdown-Datei in `20 Reviews/weekly-YYYY-Www.md` |
| E6 | Task Capture → Google Tasks | Echter Task in Inbox-Liste, `task_metadata` befüllt |
| E7 | Task Complete nach Approval → Google Tasks | Task in Google als done, `approval_log` mit `executed` |

**Verbindlich:** Produktionsreife darf nur erklärt werden, wenn die zugehörige E2E-Strecke einmal komplett grün gelaufen ist und im Spec-Doc dokumentiert wurde.

### 7.3 Coverage-Erwartung

- Habit + Intake: ≥ 90 % (heute schon)
- Dispatch + Approval: 100 % der Übergänge im State-Diagramm getestet
- Planning Engine: jeder Tagesmodus + jede Personal-Policy-Regel mit mindestens einem Test

---

## 8. Implementation Roadmap

| Phase | Inhalt | Status | Abnahme |
|---|---|---|---|
| **0** | Repository-Audit | ✅ Done | `EOS-PHASE2-AUDIT-2026-04-30.md` |
| **1** | Intake Engine (deterministische Intent-Klassifikation) | ✅ Done | 17 Tests grün |
| **2** | Habit Coaching Engine (Typen, Trigger, Recovery, Patterns) | ✅ Done | 15 neue Tests, alle 15 verify_* grün |
| **3** | **Dispatch Layer** (Intake → Service-Wiring) + Pending-Confirmations + Energy-Log | ⏳ Next | E1 + E4 grün |
| **4** | **Planning Proposal Engine** + Tagesmodus + Personal-Policy-Engine | ⏳ | E2 grün |
| **5** | **Approval Layer** + Calendar-Write (read-write OAuth) | ⏳ | E3 + E6 + E7 grün |
| **6** | **Review Layer** (Daily/Weekly/Monthly) + Pattern-Insights → Plan | ⏳ | E5 grün |
| **7** | **Routing zu Spezialisten** (Solara/Pharos/Photon/Lucent/Aurelius/Lux) | Future | Test-Routing-Strecke pro Subagent |
| **8** | **Vault produktiv mounten** + Daily/Review-Notes schreiben | Future | Markdown-Files erscheinen im Vault |
| **9** | **Audio-Intake** (Telegram-Audio → Whisper → Intent) | Future | E1 mit Audio-Variante |
| **10** | **Life-Graph** (Goals/Projects/Tasks/Habits-Graph) | Future | Pattern-Insights nutzen Graph-Beziehungen |

**Reihenfolge ist verbindlich** — Phase n setzt Phase n-1 voraus.

---

## 9. Risks and Open Questions

### 9.1 Risiken

| Risiko | Wahrscheinlichkeit | Schweregrad | Gegenmaßnahme |
|---|---|---|---|
| **Calendar-Write Loop-Bug schreibt 50 Termine** | mittel | hoch | Rate-Limit `3 writes/h`, Pre-Write-Read, Idempotenz-Key, `approval_log` |
| **Pending-Confirmation-Stau** (User antwortet nicht) | hoch | niedrig | TTL = 30 Min, automatisches `EXPIRED` |
| **JSON-State-Schema-Migration bricht alte Files** | niedrig | hoch | Schema-Version-Migrator + Verify-Test pro Migration |
| **Telegram-Token rotiert, EOS stumm** | niedrig | mittel | Health-Check mit Telegram-Ping; eskaliert via Email-Fallback |
| **LLM kommt durch Hintertür rein** | niedrig | hoch | Verboten per Test (`grep` auf `anthropic`/`openai` in Service-Schicht) |
| **Routing schickt Health-Daten an falschen Agent** | mittel | hoch | Routing-Whitelist; Solara hat eigenen Telegram-Bot, EOS ruft nur APIs |
| **Pattern-Insights spammt Tagespläne** | mittel | mittel | Max 1 Insight pro Plan, gewichtet nach `severity` |
| **Habit-Versionen werden nie gepflegt** | hoch | niedrig | CLI-Hilfen + Default-Templates für neue Habits |

### 9.2 Offene Fragen (Klärung **vor** Phase 3 sinnvoll)

1. **Cron vs. systemd:** Bleibt der Doppelpfad bestehen, oder konsolidieren wir auf systemd? *Empfehlung:* systemd als Primary (Token-frei), OpenClaw-Cron nur für Jobs, die wirklich einen Agent-Turn brauchen (z.B. Heartbeat).
2. **Audio-Latenz:** Ist Whisper lokal schnell genug für „Habit erledigt"-Sprachnachrichten (< 3s)? Falls nein → Phase 9 hinten anstellen.
3. **Calendar-Write OAuth-Scope:** `tasks` ist schon da; brauchen wir einen separaten Calendar-Write-Scope oder nutzen wir denselben Refresh-Token?
4. **Vault-Path:** Wo wird der Obsidian-Vault produktiv gemountet — im Container oder am Host? Beide haben Konsequenzen für Backup und Editor-Zugriff.
5. **Tagesmodus-Klassifikation:** Soll EOS den Modus automatisch raten (aus Calendar) oder explizit nachfragen? *Empfehlung:* Auto-Vorschlag + Override per Telegram („morgen ist sprint_day").
6. **Personal Policy Engine — wer schreibt die Regeln?** User per Telegram oder per Markdown-Edit? *Empfehlung:* Markdown-First (`docs/EOS-PERSONAL-POLICY.md`) + CLI-Loader.
7. **Subagent-Routing:** Wie ruft EOS einen Spezialisten — über OpenClaw-Subagents, über direkten CLI-Hop, oder über Telegram-Cross-Bot-Trigger? *Empfehlung:* Subagents via OpenClaw, sobald Phase 7 startet.
8. **Bachelorarbeit als Goal:** Soll der Life-Graph diesen einen konkreten Baum schon in Phase 6 modellieren oder warten wir auf Phase 10?

### 9.3 Annahmen, die geprüft werden müssen

- Google Tasks OAuth läuft headless dauerhaft (Refresh-Token-Mechanik stabil über Wochen).
- Telegram-Heartbeat-Limit von 30 Min ist okay (kein Spam-Empfinden).
- `daily_evaluations` und `task_snapshots` wachsen langsam genug, dass keine Pruning-Strategie nötig ist (vermutlich richtig für 1–2 Jahre).

---

## 10. Exact Next Coding Steps (Phase 3)

**Bevor Code geschrieben wird, gilt das Phase-0-Audit-Ritual:** neuer Audit-Markdown, der die Module benennt, Schutzregeln auflistet, Risiken klassifiziert.

### 10.1 Phase 3 — Dispatch Layer + Pending-Confirmations + Energy-Log

**Ziel-Akzeptanz:** E1 (Telegram-Text → Habit-Event) und E4 (Daily-Check-in → Energy-Log) live grün.

**Konkrete Code-Schritte (in Reihenfolge):**

1. **Audit-Doc** `docs/EOS-PHASE3-AUDIT-2026-05-XX.md` mit
   - Liste betroffener Dateien
   - Schutzregeln (keine bestehende Habit-/Intake-API ändern)
   - Risiken pro Modul
2. **Schema-Erweiterung** `src/database/models.py`:
   - Neue Tabelle `pending_confirmations`
   - Neue Tabelle `energy_log`
   - `_ensure_columns` für Migration
3. **Energy-Service** `src/energy/service.py`:
   - `log_checkin(payload, source)`
   - `latest(business_date_berlin)`
   - `weekly_summary(week_start)`
4. **Pending-Confirmations** `src/dispatch/pending.py`:
   - `create(chat_id, intake_result)`
   - `latest_pending(chat_id)`
   - `resolve(id, choice)`
   - `expire_old(now_utc)`
5. **Dispatch-Router** `src/dispatch/router.py`:
   - `dispatch(intake_result, chat_id)`
   - Confidence-Gate-Logik (siehe §5.1)
   - Ruft `HabitService.mark_done` / `log_relapse` / `log_recovery` / `energy.service.log_checkin` je nach Intent
6. **CLI-Erweiterungen** `src/eos_cli.py`:
   - `dispatch handle "<text>" --chat-id <id>`
   - `energy log --sleep <n> --stress <n> ...`
   - `pending list`, `pending resolve <id> <choice>`
7. **Verify-Tests:**
   - `tests/verify_dispatch.py` (Dispatch-Logik mit allen 13 Intent-Branches)
   - `tests/verify_pending_confirmations.py`
   - `tests/verify_energy.py`
8. **Live-E2E:**
   - E1 manuell durchspielen, im Spec-Doc dokumentieren („durchgelaufen am DD-MM-YYYY mit Habit X")
   - E4 manuell durchspielen
9. **Spec-Doc** `docs/EOS-PHASE3-DISPATCH-v1.md` mit Akzeptanz, Migrations-Status, E2E-Nachweis

### 10.2 Was Phase 3 *nicht* anfasst

- Kein Calendar-Write (Phase 5)
- Kein Tagesplan-Vorschlag (Phase 4)
- Kein Vault-Write (Phase 6/8)
- Kein Audio (Phase 9)
- Kein Routing (Phase 7)

### 10.3 Vor Phase 3 zu klären

- Antwort auf offene Fragen 1, 5, 6 aus §9.2 (Cron vs. systemd, Mode-Klassifikation, Policy-Quelle).
- Bestätigung, dass die heutigen Habit- und Intake-Interfaces als „eingefroren" gelten.

---

## 11. Anhang — Dokument-Referenzen

- [EOS-V3-INTELLIGENT-LOOP-SPEC.md](EOS-V3-INTELLIGENT-LOOP-SPEC.md) — Loop-Spec (Verstehen → Planen → Rückfragen → Speichern → Auswerten → Anpassen)
- [EOS-CURRENT-STATE-2026-04-30.md](EOS-CURRENT-STATE-2026-04-30.md) — Bestand vor Phase 1+2
- [EOS-PHASE2-AUDIT-2026-04-30.md](EOS-PHASE2-AUDIT-2026-04-30.md) — Phase-1-Audit
- [EOS-PHASE2-HABIT-COACHING-v1.md](EOS-PHASE2-HABIT-COACHING-v1.md) — Phase-2-Spec (Habit Coaching v1)
- [EOS-ARCHITECTURE-v1.md](EOS-ARCHITECTURE-v1.md), [EOS-CAPABILITY-MAP.md](EOS-CAPABILITY-MAP.md) — Bestands-Architektur
- [EOS-COACHING-ENGINE-v1.md](EOS-COACHING-ENGINE-v1.md), [EOS-REVIEW-ENGINE-v1.md](EOS-REVIEW-ENGINE-v1.md), [EOS-SCHEDULER-JOBS-v1.md](EOS-SCHEDULER-JOBS-v1.md) — bestehende deterministische Engines
- [EOS-VAULT-v1.md](EOS-VAULT-v1.md) — Vault-Strategie
