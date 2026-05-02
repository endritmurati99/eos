# EOS V2 Technical Spec

## Zweck
Dieses Dokument friert den fachlichen und technischen Zielzustand fuer EOS V2 als reine Spezifikationsphase ein.
Es ersetzt keine produktive Laufzeit, fuehrt keine Host-Aenderungen aus und aktiviert keine neuen Jobs.

## V2-Zielbild
EOS soll von einem reaktiven Planungsassistenten zu einem belastbaren persoenlichen Operations-System ausgebaut werden.
V2 priorisiert:
- Google Tasks als operatives Task-System
- Evening Reset als taeglichen Abendanker fuer den Folgetag
- eine deterministische Coaching Engine auf Basis echter EOS-Policy
- einen abgesicherten Scheduler mit persistentem State
- Weekly Review plus strukturierende Wochenvorschau
- eine spaetere saubere Obsidian-/Vault-Schicht ohne Big-Bang-Automation

## Bestaetigte V1-Basis
Die folgenden Punkte gelten in dieser V2-Spezifikation als bestaetigt:
- EOS laeuft als Agent `personal-assistant`
- Google Calendar Live-Read ist der bestaetigte Pfad fuer harte Termine
- operative Planungszeitzone ist `Europe/Berlin`
- taegliche und woechentliche Planungsregeln sind fachlich definiert
- Scheduler-Hardening, Dry-Run und Idempotenz wurden in V1 bereits normativ beschrieben

## Architekturprinzipien

### Source of Truth
- Google Calendar = harte Termine und feste Zeitbloecke
- Google Tasks = aktive offene Aufgaben
- Obsidian Vault = Brain Dumps, Daily Notes, Verlauf, Wissen
- SQLite = nur abgeleiteter State, Review-Daten, Job-Historie und Cache

SQLite ist in V2 ausdruecklich nicht die Primaerquelle fuer Kalender oder Aufgaben.

### Betriebsmodell
- EOS bleibt der sichtbare Hauptagent
- Scheduler wird `systemd`-timer-first gedacht
- `cron` ist nur Fallback
- keine In-Container-`while true`- oder `sleep`-Worker als Primaerloesung
- `Europe/Berlin` ist die fachliche Zeitbasis fuer Trigger, Tagesgrenzen und Wochenfenster
- jeder produktive Job braucht Logging, Dry-Run, Idempotenz und definiertes Failure-Verhalten

### Produktive Leitregel
EOS soll:
- operativ sein
- kurz sein
- Ueberladung klar benennen
- genau eine konkrete Empfehlung geben

EOS soll nicht:
- generische Produktivitaetstipps liefern
- eine Research-/Guru-Persona spielen
- ungeprueft autonom umplanen
- neue Primaerquellen erfinden

## V2-Module

### Google Tasks Integration v1
Umfang:
- Task Read
- Task Create
- Task Complete
- echte Listenstruktur mit `Inbox`, `Next`, `Waiting`, `This Week`
- provider-neutraler Adapter mit direktem OAuth2-Zielpfad

Nicht Teil von Phase 1:
- Delete
- Move
- Subtasks-first-Ausbau
- Bulk-Umsortierung
- Prioritaetsmagie

### Coaching Engine v1
Die Engine bewertet Kalender plus Aufgaben gegen EOS-Regeln und liefert:
- Tagesstatus in `green`, `yellow` oder `red`
- kurze Einschaetzung
- optional eine Warnung
- genau eine konkrete Empfehlung

### Evening Reset v1
`evening_reset` ist der normative V2-Name fuer den taeglichen Abendanker des Folgetags.
Die Nachricht schliesst den Tag operativ ab, macht offene Punkte sichtbar und richtet morgen aus.

### Weekly Review / Weekly Sync
`weekly_sync` bleibt der normative Sonntagsjob.
Er kombiniert:
- Rueckblick auf die letzten 7 Tage
- Mustererkennung
- konkrete strukturelle Empfehlung fuer die kommende Woche

### State Layer
Persistenter State dient nur fuer:
- Job-Historie
- Delivery-Historie
- Tagesbewertungen
- Weekly-Review-Summaries
- technische Idempotenz
- optionale Snapshots als Derived State

### Obsidian / Vault Vorbereitung
V2 Phase 0-4 bereitet nur die spaetere Anbindung vor.
Minimal zulaessig:
- Brain Dump zu Inbox-Konzept
- Daily Note Grundstruktur

Nicht zulaessig:
- wilde Vollautomatisierung
- neue, unbestaetigte Mount-Pfade als Fakt

## Phasenmodell

### Phase 0 - Spec Freeze
In dieser Phase werden nur Spezifikations- und Entwurfsdokumente erzeugt oder aktualisiert.
Keine Live-Automation, keine Host-Aenderungen, keine Scheduler-Aktivierung.

### Phase 1 - Google Tasks v1
Implementiert werden:
- Read
- Create
- Complete
- Listenmapping
- Fehlerverhalten
- Partial Degradation

### Phase 2 - Evening Reset
Implementiert werden:
- `evening_reset`
- Dry-Run
- Logging
- Idempotenz
- Telegram-Send
- Nutzung von Calendar plus Tasks

### Phase 3 - Coaching Engine
Implementiert werden:
- Regelbewertung
- Ampelstatus
- konkrete Empfehlung
- Persistenz in Tagesbewertungen

### Phase 4 - Weekly Review
Implementiert werden:
- 7-Tage-Auswertung
- Mustererkennung
- strukturierende Wochenempfehlung
- kombinierter `weekly_sync`

### Phase 5 - Obsidian / Vault
Nur vorbereiten oder minimal anbinden:
- Brain Dump zu Inbox
- Daily Notes Grundstruktur

## Legacy Runtime Drift
Die im aktuellen Workspace beobachteten Eintraege in `cron/jobs.json` sind nicht die normative V2-Zielarchitektur.
Dazu gehoeren insbesondere:
- `daily-briefing-morning-0800`
- `weekly-planning-reminder-sunday-1800`
- `sport-bag-reminder-evening-before`
- `Deep Work reminder`

Diese Eintraege gelten in V2 als Legacy Runtime Drift:
- prompt-getrieben statt sauberem Job-Runner-Modell
- nicht deckungsgleich mit den eingefrorenen V2-Jobdefinitionen
- nicht ausreichend fuer den V2-Hardening-Anspruch

Wichtig:
- die Spec-Freeze-Phase benennt diese Drift explizit
- sie aendert diese Jobs nicht
- sie deployed nichts

## Normative Jobnamen in V2
- `evening_reset` = normativer V2-Name des taeglichen Abendjobs
- `evening_briefing` = Legacy-Alias aus V1-Dokumenten und bestehender Laufzeit
- `weekly_sync` = normativer Sonntagsjob in V1 und V2

Folgeregel:
- neue V2-Dokumente verwenden `evening_reset`
- Migrationshinweise duerfen `evening_briefing` nur noch als Legacy-Kontext nennen

## Scheduler-Prioritaet in V2
Der erste produktive V2-Jobset-Fokus ist absichtlich klein:
- `evening_reset`
- `weekly_sync`

Noch nicht Teil des ersten Live-Jobsets:
- `sport_prep_reminder`
- `morning_briefing`

## Nicht-Ziele in dieser Phase
- kein Big-Bang-Rollout
- kein blinder Direkt-Deploy
- keine neuen Google-Projekte
- keine Secrets in Dokumenten
- keine automatische `systemd`-Installation
- keine `cron`-Aenderung
- keine Host-Mutationen
- keine neue Gesamtarchitektur ausserhalb des EOS-V2-Zielbilds

## Deliverables dieser Spec-Freeze-Phase
Pflicht:
- `docs/EOS-V2-TECHNICAL-SPEC.md`
- `docs/EOS-TASKS-INTEGRATION-v1.md`
- `docs/EOS-COACHING-ENGINE-v1.md`
- `docs/EOS-EVENING-RESET-v1.md`
- `docs/EOS-REVIEW-ENGINE-v1.md`
- `docs/EOS-V2-STATE-MODEL-v1.md`
- `docs/EOS-V2-TIMERS-v1.md`
- `docs/EOS-V2-LIVE-E2E-v1.md`

Empfohlen:
- `templates/evening-reset-output.md`
- `templates/weekly-review-output.md`

## Rollout-Reihenfolge nach Dokumentenabnahme
1. Spec Review und Inkonsistenzpruefung
2. Google Tasks Adapter plus Live-E2E
3. State Layer plus Idempotenzpfad
4. Evening Reset Dry-Run und Live-E2E
5. Coaching Engine auf echten Testtagen
6. Weekly Sync Dry-Run und Sonntags-Live-E2E
7. spaeter minimale Vault-Anbindung

## Spec-Freeze-Abnahme
Die Spec-Freeze-Phase gilt nur dann als abgeschlossen, wenn:
- alle acht V2-Dokumente vorhanden sind
- Jobnamen, Zeitfenster und Source-of-Truth-Regeln konsistent sind
- V2 `evening_reset` sauber gegen V1 `evening_briefing` abgegrenzt ist
- der aktuelle Cron-Zustand als Legacy Drift markiert ist
- keine Datei Hostpfade, Unit-Namen oder Secrets als bestaetigte Fakten erfindet
