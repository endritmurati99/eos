# EOS V3 – Intelligent Loop Spec

**Stand:** 2026-04-30
**Status:** Spezifikation (kein Live-Code, kein Host-Change)
**Vorgänger:** [EOS-V2-TECHNICAL-SPEC.md](EOS-V2-TECHNICAL-SPEC.md), [EOS-CURRENT-STATE-2026-04-30.md](EOS-CURRENT-STATE-2026-04-30.md)

---

## 0. Premise Correction

EOS braucht **nicht** primär „mehr Funktionen". EOS braucht eine bessere Schleife:

```
Verstehen → Planen → Rückfragen → Speichern → Auswerten → Verhalten anpassen
```

Sonst wird EOS nur ein Reminder-Bot mit KI-Text.

V1/V2 hat die deterministische Basis abgesichert (Calendar-Read, Habit-Events, Coaching-Engine, Scheduler, Idempotenz). V3 setzt die **Intelligenz-Schicht** darauf.

---

## 1. Der intelligente Sprung

Kein „Chatbot bedient Kalender", sondern fünf zusammenhängende Schritte:

1. **EOS versteht** unstrukturierte Eingaben (Text, Audio).
2. **EOS prüft** sie gegen Kalender, Aufgaben, Habits, Energie und Regeln.
3. **EOS schlägt vor** — eine konkrete Handlung.
4. **EOS schreibt erst nach Zustimmung.**
5. **EOS lernt** aus Ausführung, Ausfall, Energie, Stimmung und Wiederholungsmustern.

Diese Loop ist das Architekturprinzip von V3.

---

## 2. Vier Engines

| Engine | Rolle | Heute | V3 |
|---|---|---|---|
| **Understanding Engine** | Audio/Text → strukturierte Intents | Tolerant-Parser für Habit-Free-Text | Confidence-basiertes Intent-Schema |
| **Habit Coaching Engine** | Routinen aufbauen, schlechte Gewohnheiten reduzieren | done_full/partial/skip/missed | + recovery, trigger tracking, adaptive reminder, Wochenmuster |
| **Planning Engine** | Kalender + Tasks + Energie + Habits → Tagesplan | Capacity-Check, Top-3 ranking | Proposal mit harten/weichen Constraints + Approval Write |
| **Review Engine** | Lernen über Tage und Wochen | weekly_sync mit 7-Tage-Rückblick | Mustererkennung über Wochen, Realismus-Check |

---

## 3. Engine 1 — Understanding Engine

### 3.1 Zweck
Eingaben (Telegram-Text, Telegram-Audio nach Transkription) zuverlässig in **strukturierte Intents** umwandeln. Konfidenz explizit machen.

### 3.2 Intent-Schema v1

```json
{
  "intent": "habit_log",
  "confidence": 0.82,
  "entities": {
    "habit_scope": "all_today",
    "completion": "done_full"
  },
  "requires_confirmation": true,
  "raw_input": "hab alles erledigt"
}
```

### 3.3 Endliche Intent-Klassen (v1)

- `habit_log` — Habit-Event loggen
- `habit_status_query` — „wie steht's mit Habits"
- `task_create` — neue Aufgabe
- `task_complete` — Aufgabe erledigt
- `task_query` — „was ist offen"
- `calendar_query` — „was steht heute/morgen an"
- `calendar_propose` — Plan-Vorschlag anfordern
- `calendar_write` — Termin/Block eintragen (nur nach Approval)
- `energy_checkin` — Energie/Belastung melden
- `bad_habit_relapse` — Rückfall melden (Trigger-Tracking)
- `brain_dump` — unstrukturierter Gedanke → Vault Inbox
- `clarification_needed` — Eingabe zu mehrdeutig

### 3.4 Confidence-Gates (verbindlich)

| Confidence | Verhalten |
|---|---|
| `> 0.85` (hoch) | Direkt loggen / handeln |
| `0.60 – 0.85` (mittel) | Vorschlag anzeigen + 1-Klick-Bestätigung |
| `< 0.60` (niedrig) | Rückfrage stellen, nicht raten |
| Kritische Schreibaktion (Calendar-Write, Task-Delete) | **immer** Approval, unabhängig von Confidence |

### 3.5 Beispiel: ambiguous Input

User: *„hab alles erledigt"*

EOS:
```
Ich interpretiere das als heutige Habits:
- Morgenroutine: done_full
- Hängenlassen: done_full
- Abendroutine: noch offen

Stimmt das? (ja / nur morgen / nur klimmzug / alle drei)
```

---

## 4. Engine 2 — Habit Coaching Engine

### 4.1 Habit-Typen (v3 erweitert)

| Typ | Zweck | Beispiel |
|---|---|---|
| `build` | Aufbauende Routine | Morgenroutine, Hängenlassen |
| `reduce` | Schlechte Gewohnheit reduzieren | Doomscrolling abends |
| `maintain` | Bestehendes Niveau halten | Skin Care |
| `recovery` | Mindest-Reset bei Ausfall | 2-Min-Notfall-Yoga |

### 4.2 Habit-Definition v3 (Beispiel `build`)

```yaml
habit_id: morning_routine
type: build
minimum_version:
  - yoga_mobility
  - skin_care
full_version:
  - yoga_mobility
  - skin_care
  - infrared
  - coconut_oil
target_time: "07:00"
failure_modes:
  - verschlafen
  - keine_zeit
  - vergessen
  - keine_lust
  - körperlich_müde
recovery_rule:
  same_day_minimum_until: "12:00"
  if_missed: "2-minute reset version"
```

### 4.3 Habit-Definition v3 (Beispiel `reduce`)

```yaml
habit_id: doomscrolling_night
type: reduce
trigger_window: "21:30-23:30"
replacement_action:
  - handy_weglegen
  - zaehneputzen
  - 5_minuten_dehnen
checkin_question: "Gab es heute Abend unnötiges Scrollen?"
trigger_tracking:
  - mued
  - stress
  - langeweile
  - aufschieben
  - handy_im_bett
```

**Regel:** Schlechte Gewohnheiten werden nicht „verboten". EOS trackt **Trigger, Kontext und Ersatzhandlung**.

### 4.4 Check-in-Fragen bei Rückfall (`reduce`-Typ)

- Was war der Auslöser?
- War es Müdigkeit, Stress, Langeweile oder Aufschieben?
- Welche Ersatzhandlung hat funktioniert?
- Morgen gleiche Barriere einbauen oder anpassen?

### 4.5 Funktionsumfang Habit Engine v3

- Minimum-Version + Full-Version
- `skip_reason`, `missed_reason`
- `recovery_version` (z.B. „2-Min-Reset")
- `streak_protection` (bei Recovery weiterzählen)
- adaptive Reminder (Zeit ↔ tatsächliches Erfüllungsfenster lernen)
- Trigger-Tracking bei `reduce`-Habits
- Wochenmuster: „Morgenroutine klappt Mo–Mi, kippt Do–Sa" → Empfehlung Zeitverschiebung

### 4.6 SQLite-Erweiterung (`eos_v2.db`)

Neue / erweiterte Spalten in `habit_events`:
- `failure_mode` (TEXT, nullable)
- `trigger_context` (JSON, nullable)
- `replacement_action` (TEXT, nullable)
- `energy_after` (INT 1-10, nullable)
- `recovery_used` (BOOL)

Neue Tabelle: `habit_pattern_signals` (Wochenmuster, ableitbar, niemals Primärquelle).

---

## 5. Engine 3 — Planning Engine

### 5.1 Zweck
Kalender + Tasks + Energie + Habits zu **einem realistischen Tagesplan** kombinieren. Erst Vorschlag, dann (nach Approval) Schreiben.

### 5.2 Harte Constraints (nicht verhandelbar)
- bestehende Termine
- Arbeit
- fixer Sport
- Schlafzeit
- Wegezeiten
- Erholungsfenster
- maximale Deep-Work-Blöcke
- keine Überplanung an harten Belastungstagen (Do–Sa)

### 5.3 Weiche Constraints (gewichtet)
- Priorität (P1/P2/P3)
- Deadline
- Energiebedarf
- Tageszeit-Präferenz
- Kontextwechsel-Kosten
- mentale Belastung
- Erholungsbedarf
- Habit-/Routine-Konflikte

### 5.4 Vorschlagsformat (Telegram-Output)

```
Analyse:
Morgen Arbeit bis 14:00, Kickboxen 16:00.
Echter Deep-Work-Block vor Sport ist riskant.

Vorschlag:
15:00–15:30  leichte Erledigung
19:30–20:30  Bachelorarbeit Fokusblock
20:30–20:40  Spaziergang
21:30        Abendroutine Minimum-Version

Soll ich das so in den Kalender schreiben? (ja / anpassen / nein)
```

### 5.5 Approval-Modi für Schreibaktionen

| Modus | Verhalten |
|---|---|
| **Read-only** | EOS analysiert und empfiehlt. Kein Write. |
| **Proposal** | EOS erzeugt Planvorschlag. Schreibt nicht. |
| **Approval Write** | EOS schreibt erst nach explizitem „Ja, eintragen" |

### 5.6 Erlaubte Schreibaktionen (nach Approval)
- Deep-Work-Blöcke eintragen
- Routinen blocken
- Puffer eintragen
- Aufgaben in Google Tasks erstellen
- geplante Aufgaben als erledigt markieren
- einfache neue Termine erstellen

### 5.7 Verbotene autonome Aktionen
- bestehende Termine **verschieben**
- Termine **absagen**
- Sportkurse entfernen
- fremde Einladungen beantworten
- wiederkehrende Regeln ändern
- harte Termine löschen

Diese benötigen **immer** explizite Zustimmung pro Aktion, nicht pro Session.

---

## 6. Engine 4 — Review Engine v3

### 6.1 Erweitert über V2

V2-`weekly_sync` deckt Sonntag 18:00 mit 7-Tage-Rückblick ab. V3 ergänzt:

- **Tagesauswertung abends** (Teil von `evening_briefing` oder eigener Job)
- **Mustererkennung über Wochen** (nicht nur 7 Tage)
- **Realismus-Check:** „Welche Planung war unrealistisch?"
- **Habit-Time-Learning:** „Welche Habit-Zeit funktioniert wirklich?"
- **Task-Drift-Tracking:** „Welche Tasks werden chronisch verschoben?"

### 6.2 Neue Pattern-Klassen über V2 hinaus
- `habit_time_misalignment` — Habit-Zielzeit passt nicht zu echter Erfüllung
- `chronic_task_deferral` — Aufgabe ≥ 3× verschoben
- `unrealistic_capacity_repeated` — Capacity-Plan vs. Ist-Erfüllung weicht systematisch ab
- `bad_habit_trigger_cluster` — gleicher Trigger führt wiederholt zu Rückfall

### 6.3 Output: Adaptive Empfehlung

Beispiel:
> „Morgenroutine wurde Do–Sa in 4 von 5 Wochen verfehlt. Empfehlung: Zielzeit Do–Sa auf 07:30 setzen oder Minimum-Version als Default an Belastungstagen."

---

## 7. Daily Operating Loop

### 7.1 Morgens (07:00 – 09:00)
- Was steht heute hart im Kalender?
- Was ist die Tageskapazität?
- Welche 1–3 Ziele sind realistisch?
- Welche Habit-Minimum-Version gilt heute?
- Gibt es Konflikte?
- **Energy-Check-in** (siehe §8)

### 7.2 Tagsüber
- Reminder vor Fokusblock
- Nach Fokusblock kurzer Check:
  - erledigt?
  - Fokusqualität (1–10)?
  - Energie danach (1–10)?
  - Block verlängern, stoppen oder verschieben?

### 7.3 Abends (20:30 – 22:00)
- Habits checken (Telegram-Push falls offen)
- offene Aufgaben triagieren
- morgen vorbereiten (`evening_briefing` V2 Job)
- schlechte Gewohnheiten reflektieren
- Schlafbarriere setzen (z.B. `doomscrolling_night` Reminder)

### 7.4 Wöchentlich (So 18:00, V2 Job)
- Welche Routinen wurden häufig geschafft?
- Wo entstehen Ausfälle?
- Welche Termine zerstören Planung?
- Welche Aufgaben werden immer verschoben?
- Was muss reduziert werden?

---

## 8. Energie- und Belastungsmodell

### 8.1 Tägliches Energie-Profil (`energy_checkin`)

```yaml
energy_checkin:
  sleep_quality: 1-10
  physical_fatigue: 1-10
  mental_load: 1-10
  soreness: 1-10
  motivation: 1-10
  stress: 1-10
```

### 8.2 Mapping Energie → Tagesplan

| Zustand | Planung |
|---|---|
| Hohe Energie | 1–2 Deep-Work-Blöcke |
| Mittlere Energie | 1 Fokusblock + leichte Tasks |
| Niedrige Energie | Minimum-Routine, Admin, Recovery |
| Harte Belastung + fixer Sport | **kein** zusätzlicher harter Block |

### 8.3 Persistenz
- `energy_checkin` Events landen in `eos_v2.db` (neue Tabelle `energy_log`)
- Planning Engine liest aktuelle Werte als weiche Constraints
- Review Engine erkennt Muster („mental_load > 7 → Deep Work scheitert")

---

## 9. Task Intelligence

### 9.1 Pflicht-Metadaten pro Task

```yaml
task:
  title: "Kapitel 3 überarbeiten"
  priority: P1 | P2 | P3
  estimated_minutes: 60
  energy_required: high | medium | low
  deadline: "2026-05-03"
  context: bachelor | admin | client | …
  next_action: "Abschnitt 3.2 prüfen"
  status: open | done | deferred
```

### 9.2 Untriaged-Behandlung

EOS markiert untriagierte Tasks **aktiv** (nicht still):

> „Diese Aufgabe ist nicht planbar, weil Aufwand und Deadline fehlen. (1) jetzt triagieren (2) später (3) verwerfen"

Triage muss **vor** Top-3-Planung erfolgen — sonst rät EOS, was V1-Behavior-Rules explizit verbieten.

---

## 10. Memory- und Speicherregeln

| Information | Zielsystem |
|---|---|
| Termin | Google Calendar |
| Aufgabe | Google Tasks |
| Habit-Event | SQLite (`eos_v2.db`) |
| Energy-Checkin | SQLite |
| Trigger-Kontext (`reduce`-Habit) | SQLite |
| langfristige Regel | `eos_state.json` |
| Tagesnotiz | Vault (`memory/YYYY-MM-DD.md`) |
| Projektwissen | Vault |
| flüchtige Chat-Antwort | nirgends (Telegram-Verlauf reicht) |

**Regel:** EOS darf nicht alles „merken". Speicherwürdigkeit ist eine Engine-Entscheidung, kein Default.

---

## 11. Proaktivitätspolitik (Anti-Spam)

Der 30-Min-Heartbeat ist gefährlich, wenn er ohne Relevanz sendet.

### 11.1 Send-Regeln

```yaml
proactivity_policy:
  silent_check_every: 30min
  send_only_if:
    - upcoming_hard_conflict
    - missed_habit_window
    - deep_work_block_due
    - untriaged_day
    - overdue_high_priority_task
    - evening_reset_needed
    - bad_habit_trigger_window_active
```

### 11.2 Stille Bedingungen
- Nachts (22:00 – 07:00) außer kritisch
- < 30 min seit letztem Send
- Kein Neuwissen seit letztem Check
- User hat innerhalb der letzten Stunde einen Send explizit weggeklickt

**Leitsatz:** EOS soll nicht ständig reden. EOS soll dann reden, wenn eine **Entscheidung nötig ist**.

---

## 12. Risiken & Gegenmaßnahmen

| Risiko | Warum relevant | Gegenmaßnahme |
|---|---|---|
| Zu viele Reminder | führt zu Ignorieren | nur bei Entscheidungsbedarf senden (§11) |
| Falsches Audio-Verständnis | gefährlich bei Kalender + Tasks | Confidence-Gates + Rückfragen (§3.4) |
| Überplanung | macht EOS unbrauchbar | Capacity Engine begrenzt hart (§5.2) |
| Halluzinierte Termine | kritisch | nur bestätigte Calendar-Daten (V1-Regel bleibt) |
| Zu viel Memory | macht System unpräzise | klare Speicherregeln (§10) |
| Calendar Write zu früh | kann Chaos erzeugen | erst Proposal, dann Approval Write (§5.5) |
| Fitness vermischt sich mit EOS | Scope-Verlust | **Solara coacht Fitness, EOS plant Zeit + Routinen** |

---

## 13. Phasenmodell V3

### Phase 0 — Spec Freeze
Dieses Dokument. Kein Code, kein Host-Change.

### Phase 1 — Intent Schema v1
- `Intent`-Datenstruktur in `src/understanding/intents.py`
- Confidence-Gates implementieren
- Telegram-Pfad: Text → Intent → bestehende CLI-Handler
- Live-E2E: `Telegram Text → Habit Log → SQLite Event`

### Phase 2 — Habit Engine v3
- `build`/`reduce`/`maintain`/`recovery`-Typen in `eos_state.json` Schema
- Trigger-Tracking-Tabelle in SQLite
- Recovery-Version + Streak-Protection
- Adaptive Reminder (Zeitlernen)

### Phase 3 — Energy Layer
- `energy_checkin` Intent + Persistenz
- Mapping in Planning Engine
- Live-E2E: `Energy-Checkin → Tagesplan-Anpassung`

### Phase 4 — Planning Engine als Proposal
- Plan-Vorschlag basierend auf Calendar + Tasks + Energy + Habits
- **Noch ohne Calendar Write** — nur Telegram-Output
- Live-E2E: `Telegram Text → Planvorschlag`

### Phase 5 — Calendar Write mit Approval
- OAuth-Calendar-Write-Pfad aktivieren
- Approval-Loop: Vorschlag → „Ja, eintragen" → Write
- Endliche erlaubte Schreibaktionen (§5.6)
- Live-E2E: `Telegram Text → Planvorschlag → Approval → Google Calendar Write`

### Phase 6 — Audio Intake
- Telegram-Audio → Transkription (Whisper-Skill)
- Transkript → Intent → bestehende Pfade
- Live-E2E: `Telegram Audio → Intent → Rückfrage`

### Phase 7 — Review Engine v3
- Pattern-Klassen erweitert (§6.2)
- Habit-Time-Learning
- Realismus-Check
- Live-E2E: `Daily Review → Vault Note`

### Phase 8 — Vault Mount
- Obsidian-Filesystem-Mount produktiv
- Brain-Dump-Pfad live
- Tagesnotizen + Wochenrückblick in Vault

---

## 14. Live-E2E Akzeptanzkriterien (verbindlich)

Erst wenn **alle** folgenden Pfade live grün sind, ist die jeweilige Phase abgenommen. Parser-/Dry-Run-Tests reichen nicht.

| Phase | E2E-Test |
|---|---|
| 1 | Telegram Text → Intent → Habit Log → SQLite Event |
| 3 | Telegram Text → Energy-Checkin → SQLite + Plan-Anpassung |
| 4 | Telegram Text → Planvorschlag (Telegram-Output) |
| 5 | Telegram Text → Planvorschlag → Approval → Google Calendar Write |
| 6 | Telegram Audio → Transkription → Intent → Rückfrage |
| 7 | Daily Review → Vault-Note geschrieben |

---

## 15. Beispiel-Dialoge (V3-Zielzustand)

### Beispiel 1 — Habit-Free-Text mit Mehrdeutigkeit
> User: „Hab alles erledigt."
>
> EOS:
> ```
> Ich habe das als heutige Habits interpretiert:
> - Morgenroutine: done_full
> - Hängenlassen: done_full
> - Abendroutine: noch offen
>
> Stimmt das?
> ```

### Beispiel 2 — Plan-Vorschlag mit Approval
> User: „Morgen muss ich Bachelor, Sport und paar Erledigungen machen."
>
> EOS:
> ```
> Morgen ist ein gelber Tag.
> Grund: fixer Sport und begrenztes Abendfenster.
>
> Vorschlag:
> - 09:00–10:00  Bachelorarbeit Deep Work
> - 10:00–10:10  Spaziergang
> - 14:30–15:00  Erledigungen
> - Sport bleibt unverändert
> - Abendroutine nur Minimum-Version
>
> Soll ich Bachelorarbeit und Erledigungen in den Kalender eintragen?
> ```

### Beispiel 3 — Bad-Habit-Rückfall mit Trigger-Frage
> User: „Ich habe wieder zu lange gescrollt."
>
> EOS:
> ```
> Ich logge das als Rückfall bei Abend-Scrollen.
> Eine Frage: Was war der Hauptauslöser?
> 1. Müdigkeit
> 2. Stress
> 3. Langeweile
> 4. Aufschieben
> 5. Handy lag im Bett
> ```

---

## 16. Bewusste V3-Nicht-Ziele

- Kein autonomes Termine-Verschieben oder -Absagen
- Kein „immer reden" — Send nur bei Entscheidungsbedarf
- Keine LLM-Halluzination als Primärquelle (V1-Regel bleibt: nur bestätigte Daten)
- Keine Fitness-Coaching-Vermischung (das macht Solara)
- Keine globale Memory-Sammelwut — Speicherwürdigkeit ist Engine-Entscheidung
- Keine Big-Bang-Vault-Automation — schrittweise mit Phasen 7+8

---

## 17. Kurzurteil

V3 verschiebt EOS vom **Reminder-Bot mit Coaching-Engine** zum **persönlichen Operations-System mit echter Lernschleife**.

Der entscheidende Unterschied: EOS speichert nicht nur Events, sondern **versteht sie**, **prüft sie**, **fragt nach**, **schlägt vor**, **schreibt nach Approval** und **lernt über Wochen**.

Die V1/V2-Basis (deterministische Engine, Idempotenz, Scheduler, JSON-Schema) bleibt das Fundament — V3 baut Intelligenz **darauf**, nicht **daneben**.
