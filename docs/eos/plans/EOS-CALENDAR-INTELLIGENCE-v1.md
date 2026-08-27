# EOS Calendar Intelligence v1

## 1. Ziel

EOS Calendar Intelligence v1 ist ein read-only Modul für Meeting Briefs, Kalenderkonflikte, Vorbereitungsvorschläge, Meeting Lookup und Follow-up-Kandidaten. Es arbeitet ausschließlich auf bereits geladenen Kalender-DTOs und führt keine Calendar Writes, keine Google Calendar API Calls, keine Gmail-Verknüpfung und keine Task-Erstellung aus.

## 2. Architektur

Das Modul lebt unter `src/eos_calendar_intelligence/` und besteht aus reinen Python-Funktionen:

- `meeting_brief.py`: operativer Brief aus Event-Feldern
- `conflict_detector.py`: Tages- und Meeting-Konflikte
- `prep_windows.py`: vorgeschlagene Vorbereitungsfenster
- `meeting_lookup.py`: Suche über synthetische Eventdaten
- `followups.py`: Follow-up-Kandidaten aus Event-Text
- `types.py`: DTOs und kleine Format-/Normalisierungshelfer

Die Funktionen importieren keine Gateways, keine Jobs, keine Mail-Module und keine HTTP-/Subprocess-Clients.

## 3. Input/Output

Input ist `CalendarEventInput`:

- `event_id`
- `title`
- `start`
- `end`
- `location`
- `description`
- `attendees`
- `calendar_role`

Outputs sind read-only DTOs:

- `MeetingBrief`
- `CalendarConflictReport`
- `PrepWindowSuggestion`
- `MeetingLookupResult`
- `MeetingLookupCandidate`

## 4. Meeting Briefs

`build_meeting_brief(event)` erzeugt kurze operative Briefs mit:

- Ziel
- Kontextpunkten
- Vorbereitung
- Risiken
- Follow-up-Kandidaten
- Confidence Score

v1 erkennt deterministisch: Review Meeting, Projekt Sync, Arzttermin, Sporttermin, Uni-Termin, Deadline-Meeting, Interview/Call und Admin-Termin.

## 5. Conflict Detection

`detect_calendar_conflicts(events)` erkennt:

- überlappende Events
- keine oder zu kurze Pausen
- mehr als vier Stunden Meetings am Tag
- kein 90-Minuten-Deep-Work-Fenster
- Sportblock durch Termin blockiert oder gequetscht
- Abendüberladung
- Meeting ohne klares Prep Window

Das Ergebnis enthält nur `risk_level`, `issues` und `suggestions`. Es werden keine Events geändert.

## 6. Prep Windows

`suggest_prep_windows(events, busy_events=None)` schlägt read-only Fenster vor:

- 15 Minuten für kleine Meetings
- 30 Minuten für mittlere Meetings
- 60 Minuten für wichtige Meetings

Wenn das direkte Fenster vor dem Meeting belegt ist, wird ein früheres Fenster vorgeschlagen. Das Modul schreibt keinen Kalendertermin.

## 7. Meeting Lookup

`lookup_meeting(query, events, reference_date=None)` beantwortet Fragen wie:

- "Was war nochmal das Meeting mit X?"
- "Meeting gestern mit Max"
- "Termin wegen Rechnung"
- "Call über Gmail"

Die Suche normalisiert deutsche und englische Tokens, wertet Titel, Beschreibung, Ort und Teilnehmer aus und liefert bis zu drei Kandidaten mit Confidence, Belegen und Unsicherheit.

## 8. Follow-up Candidates

`detect_followup_candidates(event)` erkennt Hinweise wie:

- follow up
- action items
- send afterwards
- review
- decision
- next steps
- protokoll
- unterlagen schicken

Das Ergebnis sind nur Kandidaten. Es werden keine Tasks erstellt.

## 9. Tests

Die Tests verwenden mindestens 20 synthetische Fixtures unter `tests/fixtures/calendar_intelligence/` und prüfen:

- Meeting-Brief-Felder und Meeting-Typen
- Konflikterkennung und Risikostufen
- Prep-Window-Dauern und Read-only-Verhalten
- Lookup Ranking, Top-3-Kandidaten und Unsicherheit
- Follow-up-Kandidaten
- keine Gateway-, Gmail-, Subprocess-, Requests- oder Calendar-Write-Abhängigkeiten

## 10. Nicht-Ziele

- keine Google Calendar API Calls
- keine Calendar Writes
- keine Event-Erstellung
- keine Event-Änderung
- keine CLI-Integration
- keine Gmail-Verknüpfung
- keine Task-Erstellung
- keine Secrets

## 11. Nächste Phase: CLI + Gmail/Vault-Kontext

Die nächste Phase kann eine CLI-Integration und Kontextanreicherung aus Gmail/Vault planen. Diese Phase muss eigene Authorization- und Privacy-Grenzen definieren und darf Calendar Writes nur nach expliziter Policy-Entscheidung einführen.
