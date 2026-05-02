# MOC - Architecture

Diese Seite ist der Einstieg in die EOS-Architektur aus menschlicher Sicht.

Ziel:
- schnell verstehen, wie EOS aufgebaut ist
- zwischen bestätigtem Stand, Zielbild und offenen Punkten unterscheiden
- direkt in die richtige technische Spezifikation springen

Technische Wahrheit bleibt in `docs/`.
Diese MOC-Datei ist die Navigations- und Orientierungsschicht.

---

## 1. Architektur auf einen Blick

EOS ist als persönlicher Operations- und Planungsassistent aufgebaut.

Kernidee:

- Telegram = Eingabekanal
- EOS / `personal-assistant` = Orchestrator
- Google Calendar = harte Termine
- Google Tasks = aktive Aufgaben
- Vault = Brain Dumps, Daily Notes, Wissen
- Scheduler = proaktive Briefings und Reminder
- lokale State-Schicht = nur abgeleiteter Zustand, nicht Primärquelle

---

## 2. Was aktuell bestätigt ist

### Agenten- und Workspace-Modell
- eigener Agent: `personal-assistant`
- eigener Workspace
- getrennte Dokumentationsschichten:
  - `docs/` = technische Spezifikationen
  - `vault/` = Navigation und Arbeitswissen

### Kalender
- Google Calendar Read ist technisch verifiziert
- Google Calendar Write ist technisch verifiziert
- Europe/Berlin ist die operative Zeitbasis

### Planung
- Daily Planning ist spezifiziert
- Weekly Planning ist spezifiziert
- Überladungslogik ist definiert
- Deep Work folgt dem Muster:
  - 60 Minuten Fokus
  - 10 Minuten Spaziergang

### Intake
- manuelle Task-Erfassung per Chat ist möglich
- Brain Dumps können strukturell im Vault abgelegt werden

---

## 3. Was nur teilweise verifiziert ist

### Calendar Assistant Layer
Der rohe technische Calendar-Pfad ist verifiziert.
Nicht vollständig ausgehärtet ist noch:
- Alias-Verständnis
- Action-Contract in Grenzfällen
- Runtime-Stabilität im echten Bot-Pfad
- durchgängige Produktionshärtung

### Vault
Die Vault-Struktur ist da.
Noch nicht voll produktiv:
- automatisches Writeback
- sichere Routing-Logik für Brain Dumps
- Daily-Note-Aktualisierung durch EOS

### Scheduler
Scheduler-Policy und Job-Definitionen existieren.
Noch nicht voll produktiv:
- systemd/cron-Rollout
- Idempotenz in Live-Betrieb
- Dry-Run und Logging im echten Betrieb
- Reminder-/Briefing-Jobs als stabiler Produktionspfad

---

## 4. Was noch offen ist

### Google Tasks
Google Tasks ist als Zielsystem gesetzt, aber noch nicht voll live als Primärquelle integriert.

Offen:
- finaler headless-sicherer Integrationspfad
- minimale produktive V1-Umsetzung
- Live-E2E für Read / Create / Complete

### Review Loop
Evening Reset und Weekly Review sind spezifiziert, aber noch nicht voll implementiert.

### Derived State
Eine lokale State-Schicht für:
- Job-Historie
- Tagesbewertungen
- Review-Summaries
- Idempotenz
ist architektonisch vorgesehen, aber noch nicht endgültig umgesetzt.

---

## 5. Architekturprinzipien

### Source of Truth
- Google Calendar = harte Termine
- Google Tasks = aktive offene Aufgaben
- Vault = Brain Dumps, Daily Notes, Wissen
- lokaler State = nur derived state

### Bounded Coach Mode
EOS soll:
- Überladung benennen
- schlechte Verteilung benennen
- genau eine konkrete Empfehlung geben

EOS soll nicht:
- zum generischen Produktivitäts-Guru werden
- tägliche Research-/Motivationsausgaben liefern
- technische Unsicherheiten verstecken

### Human-first Navigation
- `docs/` definiert technische Wahrheit
- `vault/` hilft dir, schnell die richtige Wahrheit zu finden

---

## 6. Architekturebenen

## Ingress
- Telegram

## Orchestrator
- EOS / `personal-assistant`

## Systems of Record
- Google Calendar
- Google Tasks
- Vault

## Derived State / Control
- Scheduler-State
- Job-Historie
- Review-Daten
- Idempotenz-Schicht

## Output
- Daily Planning
- Weekly Planning
- Reminder
- Review
- später: Evening Reset / Weekly Review / kontrolliertes Vault-Writeback

---

## 7. Wichtigste Architekturentscheidungen

### Entscheidung 1
Google Calendar bleibt die einzige Wahrheit für harte Termine.

### Entscheidung 2
Google Tasks soll die einzige Wahrheit für aktive offene Aufgaben werden.

### Entscheidung 3
Vault ist Markdown-first und dient als langfristige Wissens- und Verlaufsstruktur.

### Entscheidung 4
Scheduler und lokale Datenbank speichern nur derived state, nie Primärwahrheit.

### Entscheidung 5
Technische Spezifikationen bleiben in `docs/`, nicht im Vault.

---

## 8. Die wichtigsten technischen Dokumente

### Kernarchitektur
- [docs/INDEX.md](../../docs/INDEX.md)
- [docs/architecture/EOS-ARCHITECTURE-v1.md](../../docs/architecture/EOS-ARCHITECTURE-v1.md)
- [docs/architecture/EOS-CAPABILITY-MAP.md](../../docs/architecture/EOS-CAPABILITY-MAP.md)
- [docs/architecture/EOS-V2-TECHNICAL-SPEC.md](../../docs/architecture/EOS-V2-TECHNICAL-SPEC.md)

### Verhalten und Policy
- [docs/policy/EOS-PLANNING-POLICY-v1.md](../../docs/policy/EOS-PLANNING-POLICY-v1.md)
- [docs/policy/EOS-OPERATING-CONTRACT-v1.md](../../docs/policy/EOS-OPERATING-CONTRACT-v1.md)
- [docs/policy/EOS-ACTION-CONTRACT-v1.md](../../docs/policy/EOS-ACTION-CONTRACT-v1.md)
- [docs/policy/EOS-ALIASES-v1.md](../../docs/policy/EOS-ALIASES-v1.md)
- [docs/policy/EOS-COACHING-ENGINE-v1.md](../../docs/policy/EOS-COACHING-ENGINE-v1.md)
- [docs/policy/EOS-ROUTINES-AND-CHECKLISTS-v1.md](../../docs/policy/EOS-ROUTINES-AND-CHECKLISTS-v1.md)

### Scheduler
- [docs/scheduler/EOS-SCHEDULER-POLICY-v1.md](../../docs/scheduler/EOS-SCHEDULER-POLICY-v1.md)
- [docs/scheduler/EOS-SCHEDULER-JOBS-v1.md](../../docs/scheduler/EOS-SCHEDULER-JOBS-v1.md)
- [docs/scheduler/EOS-SCHEDULER-IMPLEMENTATION-v1.md](../../docs/scheduler/EOS-SCHEDULER-IMPLEMENTATION-v1.md)
- [docs/scheduler/EOS-SCHEDULER-STATE-IDEMPOTENCY-v1.md](../../docs/scheduler/EOS-SCHEDULER-STATE-IDEMPOTENCY-v1.md)
- [docs/scheduler/EOS-EVENING-RESET-v1.md](../../docs/scheduler/EOS-EVENING-RESET-v1.md)
- [docs/scheduler/EOS-REVIEW-ENGINE-v1.md](../../docs/scheduler/EOS-REVIEW-ENGINE-v1.md)

### Integrationen
- [docs/integrations/EOS-CALENDAR-WRITE-E2E-v1.md](../../docs/integrations/EOS-CALENDAR-WRITE-E2E-v1.md)
- [docs/integrations/EOS-TASKS-INTEGRATION-v1.md](../../docs/integrations/EOS-TASKS-INTEGRATION-v1.md)
- [docs/integrations/EOS-TASKS-ACTION-CONTRACT-v1.md](../../docs/integrations/EOS-TASKS-ACTION-CONTRACT-v1.md)

### Tests
- [docs/tests/EOS-LIVE-E2E-TESTS-v1.md](../../docs/tests/EOS-LIVE-E2E-TESTS-v1.md)
- [docs/tests/EOS-V2-LIVE-E2E-v1.md](../../docs/tests/EOS-V2-LIVE-E2E-v1.md)

---

## 9. Nächste Architektur-Schritte

### Kurzfristig
1. Runtime sauber stabilisieren
2. Google Tasks v1 minimal integrieren
3. Evening Reset logic-first bauen
4. Scheduler härten

### Danach
5. Weekly Review aktivieren
6. Vault Writeback vorsichtig einführen
7. Review Loop schließen

---

## 10. Wie du diese Seite nutzt

Wenn du wissen willst:

### „Was ist EOS überhaupt?“
- lies Abschnitt 1 bis 4

### „Was ist schon echt, was nur geplant?“
- lies Abschnitt 2 bis 4

### „Wo ist die technische Wahrheit dazu?“
- springe zu Abschnitt 8

### „Was ist als Nächstes dran?“
- lies Abschnitt 9

---

## 11. Verbindliche Entscheidungen

- [[ADR - Calendar as Source of Truth]] — Google Calendar ist die einzige Quelle für harte Zeit-Commitments.
- [[ADR - Tasks as Source of Truth]] — Google Tasks ist die einzige Quelle für aktive offene Arbeit.

Diese ADRs fixieren die beiden zentralen Source-of-Truth-Grenzen in der EOS-Architektur. Vault und Derived State sind damit explizit keine primären Autoritäten mehr.