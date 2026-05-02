# MOC - Scheduler

Diese Seite ist der Einstieg in den Scheduler-Layer von EOS.

Ziel:
- verstehen, welche Jobs EOS später proaktiv ausführen soll
- zwischen spezifiziert, teilweise vorbereitet und noch nicht produktiv unterscheiden
- direkt in die relevanten technischen Dokumente springen

Technische Wahrheit bleibt in `docs/`.
Diese MOC-Datei ist nur die Navigations- und Orientierungsschicht.

---

## 1. Wofür der Scheduler da ist

Der Scheduler macht EOS von einem rein reaktiven Assistant zu einem proaktiven Operations-System.

Ohne Scheduler:
- User schreibt → EOS antwortet

Mit Scheduler:
- ein definierter Zeitpunkt wird erreicht
- EOS liest aktuelle Daten
- EOS erzeugt ein Briefing, einen Reminder oder eine Auswertung
- EOS sendet genau eine operative Nachricht

Der Scheduler ist nur sinnvoll, wenn er:
- idempotent ist
- sauber loggt
- keine doppelten Nachrichten sendet
- auf frischen Daten basiert
- Europe/Berlin durchgängig korrekt verwendet

---

## 2. Was aktuell schon festgelegt ist

### Scheduler-Prinzipien
- systemd timers sind das bevorzugte Zielmodell
- cron ist nur Fallback
- keine In-Container-`while true`- oder `sleep`-Schleifen als Primärlösung
- jeder Job braucht:
  - Dry-Run
  - Logging
  - Idempotenz
  - klares Failure-Verhalten

### Grundregeln
- vor jedem Send frischer Calendar-Read
- keine doppelten Sends
- keine spekulativen Reminder
- keine Erinnerungen auf Basis veralteter Daten
- Europe/Berlin ist Pflicht-Zeitbasis

### Job-Denke
Ein Scheduler-Job ist nicht nur „eine Nachricht zu einer Uhrzeit“.
Er braucht:
- Trigger
- Datenquellen
- Send-Regeln
- Nicht-Send-Regeln
- State
- Idempotenz-Key
- Fehlerbehandlung

---

## 3. Welche Jobs aktuell vorgesehen sind

## Phase 1 Kernjobs

### 1. Evening Briefing
Zweck:
- Vorbereitung auf morgen

Inhalt:
- harte Termine morgen
- Top-3 morgen
- Deep-Work-Vorschlag
- Sport morgen
- Vorbereitung / Nicht vergessen
- Warnung bei Überladung

Zielzeit:
- 20:30 Europe/Berlin

### 2. Sport Prep Reminder
Zweck:
- frühzeitige Vorbereitung bei relevantem Sport am Folgetag

Inhalt:
- kurze Reminder-Nachricht
- nur definierte Checkliste
- kein Motivationsstil

Zielzeit:
- 08:30 Europe/Berlin am Vortag

### 3. Weekly Sync
Zweck:
- Wochenstruktur und strategische Übersicht

Inhalt:
- harte Termine
- Arbeitstage
- fixe Sportkurse
- flexible Blöcke
- gekürzte oder verschobene Ziele
- Warnung bei Überladung
- Nicht vergessen

Zielzeit:
- Sonntag 18:00 Europe/Berlin

---

## 4. Was noch nicht aktiv sein sollte

### Nicht in Phase 1
- aggressives Morning Briefing
- mehrere Reminder am selben Morgen
- Daily Productivity Tip
- tip-of-the-day / websearch-gesteuerte Inhalte
- unsaubere Auto-Rescheduling-Logik
- Reminder ohne definierte Checkliste

### Monthly Planning
Monthly Planning ist sinnvoll, aber nicht Phase-1-kritisch.
Es sollte erst aktiviert werden, wenn:
- Evening Briefing stabil ist
- Weekly Sync stabil ist
- Idempotenz und Logs im echten Betrieb grün sind

---

## 5. Scheduler-State

Der Scheduler braucht eine persistente State-Schicht.

Wofür:
- Send-Historie
- Job-Runs
- Idempotenz
- technische Nachvollziehbarkeit
- spätere Tagesbewertungen / Reviews

Wichtig:
Diese State-Schicht ist **nicht** Source of Truth für:
- harte Termine
- aktive Aufgaben

Sie speichert nur:
- derived state
- Send-Status
- Review-Zustand
- Job-Metadaten

---

## 6. Idempotenz

Idempotenz ist Pflicht.

Beispiel:
- derselbe Job wird doppelt ausgelöst
- der Server rebootet
- ein Timer feuert erneut
- ein Retry läuft

Dann darf EOS **nicht** dieselbe Nachricht zweimal senden.

Beispiel-Idempotenz-Keys:
- `2026-04-22_evening_briefing`
- `2026-04-22_sport_prep_2026-04-23_kickboxen`
- `2026-W17_weekly_sync`

Vor jedem Send:
1. prüfen
2. wenn bereits gesendet → abbrechen
3. wenn nicht gesendet → senden und Zustand speichern

---

## 7. Zeitbasis

Für den Scheduler ist Zeitkonsistenz ein Produktionspunkt.

Zu prüfen:
- Host-Zeit
- Container-Zeit
- App-Zeit
- Calendar-Query-Zeit

Ziel:
- Europe/Berlin überall konsistent

Typische Fehlerbilder:
- Reminder zwei Stunden zu spät
- falscher Kalendertag
- Weekly Sync am falschen Sonntag
- „morgen“ wird als UTC-morgen statt Berlin-morgen gelesen

---

## 8. Failure-Verhalten

Ein Job darf nicht einfach still scheitern.

### Wenn Calendar-Read scheitert
- loggen
- kein Blind-Send
- keine Fantasie-Nachricht

### Wenn Checkliste fehlt
- keinen geratenen Reminder senden
- sauber loggen
- optional Skip

### Wenn Telegram-Send scheitert
- begrenzter Retry
- klarer Logeintrag
- Idempotenz sauber behandeln

### Wenn Daten unvollständig sind
- lieber kein Send
- statt halbgaren Output

---

## 9. Output-Prinzipien

Scheduler-Nachrichten müssen:
- kurz sein
- operativ sein
- eine hohe Informationsdichte haben
- nicht nerven
- keine Motivationsfloskeln enthalten

### Evening Briefing
- morgen strukturiert vorbereiten

### Sport Prep Reminder
- nur relevante Vorbereitung
- keine zweite Aufgabenliste

### Weekly Sync
- echte Wochensteuerung
- keine diffuse Zusammenfassung

---

## 10. Was aktuell noch offen ist

### Technisch offen
- produktive systemd-Integration
- persistenter State
- Logging im Live-Betrieb
- Dry-Run-Implementierung
- Idempotenz-Implementierung
- echte Live-E2E-Tests

### Fachlich offen
- finale Aktivierungsreihenfolge
- exakte Nicht-Send-Regeln
- wie stark Sport Prep und Evening Briefing zusammengeführt werden sollen
- ob Monthly Planning später ein eigener Job wird

---

## 11. Wichtigste technische Dokumente

### Scheduler-Kern
- [docs/scheduler/EOS-SCHEDULER-POLICY-v1.md](../../docs/scheduler/EOS-SCHEDULER-POLICY-v1.md)
- [docs/scheduler/EOS-SCHEDULER-JOBS-v1.md](../../docs/scheduler/EOS-SCHEDULER-JOBS-v1.md)
- [docs/scheduler/EOS-SCHEDULER-IMPLEMENTATION-v1.md](../../docs/scheduler/EOS-SCHEDULER-IMPLEMENTATION-v1.md)
- [docs/scheduler/EOS-SCHEDULER-STATE-IDEMPOTENCY-v1.md](../../docs/scheduler/EOS-SCHEDULER-STATE-IDEMPOTENCY-v1.md)
- [docs/scheduler/EOS-SCHEDULER-TIMEBASE-v1.md](../../docs/scheduler/EOS-SCHEDULER-TIMEBASE-v1.md)
- [docs/scheduler/EOS-SCHEDULER-LIVE-E2E-v1.md](../../docs/scheduler/EOS-SCHEDULER-LIVE-E2E-v1.md)

### Job-nahe Logik
- [docs/scheduler/EOS-EVENING-RESET-v1.md](../../docs/scheduler/EOS-EVENING-RESET-v1.md)
- [docs/scheduler/EOS-REVIEW-ENGINE-v1.md](../../docs/scheduler/EOS-REVIEW-ENGINE-v1.md)
- [docs/scheduler/EOS-PREP-REMINDER-POLICY-v1.md](../../docs/scheduler/EOS-PREP-REMINDER-POLICY-v1.md)
- [docs/scheduler/EOS-PREP-REMINDER-TRIGGER-PATH-v1.md](../../docs/scheduler/EOS-PREP-REMINDER-TRIGGER-PATH-v1.md)
- [docs/scheduler/EOS-PREP-CHECKLIST-MAPPINGS-v1.md](../../docs/scheduler/EOS-PREP-CHECKLIST-MAPPINGS-v1.md)

---

## 12. Nächste Scheduler-Schritte

### Kurzfristig
1. State-Modell final festziehen
2. Dry-Run implementieren
3. Idempotenz implementieren
4. Evening Briefing zuerst logic-first bauen
5. dann Sport Prep Reminder
6. dann Weekly Sync

### Danach
7. Live-E2E pro Job
8. produktiver Rollout
9. erst später weitere Jobs wie Monthly Planning

---

## 13. Wie du diese Seite nutzt

Wenn du wissen willst:

### „Welche Jobs soll EOS später haben?“
- lies Abschnitt 3 und 4

### „Was ist dafür technisch zwingend?“
- lies Abschnitt 5 bis 8

### „Wo ist die technische Wahrheit dazu?“
- springe zu Abschnitt 11

### „Was ist als Nächstes dran?“
- lies Abschnitt 12

---

## 14. Verbindliche Entscheidungen

- [[ADR - Calendar as Source of Truth]] — Scheduler-Jobs müssen vor jedem Send frisch aus dem Kalender lesen. Kein Cache, keine Markdown-Kopien.
- [[ADR - Tasks as Source of Truth]] — Evening Reset, Weekly Sync und Task-nahe Jobs greifen auf Google Tasks zu, nicht auf Vault-Notizen.
