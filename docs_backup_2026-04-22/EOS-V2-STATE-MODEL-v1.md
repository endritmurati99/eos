# EOS V2 State Model v1

## Zweck
Dieses Dokument definiert den persistenten Derived-State-Layer fuer EOS V2.
Der bevorzugte Speicher ist SQLite auf verifiziertem persistenten Storage.

## Grundsatz
SQLite ist in V2 nur abgeleiteter State.
SQLite ist nicht:
- Primaerquelle fuer Google Calendar
- Primaerquelle fuer Google Tasks
- Ersatz fuer Obsidian-Vault-Inhalte

SQLite wird verwendet fuer:
- Job-Historie
- Delivery-Historie
- Tagesbewertungen
- Weekly-Review-Summaries
- Task-Snapshots
- technische Idempotenz

## Zeit- und Datumsregeln
- fachliche Tage und Wochen werden in `Europe/Berlin` modelliert
- technische Zeitstempel werden in UTC gespeichert
- Business-Dates sind als Berlin-Lokaldaten gespeichert
- Fenstergrenzen fuer Scheduler-Jobs werden als Berlin-Lokalzeit gespeichert

## Kernvertrag
`JobRunRecord = { job, idempotencyKey, targetWindowBerlin, runStatus, deliveryStatus, lastError }`

Regeln:
- `job` ist der normative Jobname
- `idempotencyKey` ist pro Zielzeitraum eindeutig
- `runStatus` folgt der Statussemantik `sending | sent | skipped | failed | dry_run`
- `deliveryStatus` trennt Delivery von Fachlogik
- `lastError` speichert den letzten relevanten Fehlertext oder Fehlercode

## Pflichttabellen

### `job_runs`
Eine Zeile pro logischem Joblauf und Idempotenz-Key.

Pflichtspalten:
- `id` INTEGER PRIMARY KEY
- `job` TEXT NOT NULL
- `run_id` TEXT NOT NULL
- `idempotency_key` TEXT NOT NULL
- `target_window_start_berlin` TEXT NOT NULL
- `target_window_end_berlin` TEXT NOT NULL
- `target_business_date_berlin` TEXT NULL
- `week_start_date_berlin` TEXT NULL
- `run_status` TEXT NOT NULL
- `attempt_count` INTEGER NOT NULL DEFAULT 1
- `lease_expires_at_utc` TEXT NOT NULL
- `calendar_read_status` TEXT NOT NULL
- `task_read_status` TEXT NOT NULL
- `delivery_status` TEXT NOT NULL
- `message_digest` TEXT NULL
- `last_error` TEXT NULL
- `created_at_utc` TEXT NOT NULL
- `updated_at_utc` TEXT NOT NULL

Pflichtindizes:
- `UNIQUE(job, idempotency_key)`
- Index auf `run_status`
- Index auf `target_business_date_berlin`

### `message_deliveries`
Eine Zeile pro Delivery-Versuch.

Pflichtspalten:
- `id` INTEGER PRIMARY KEY
- `run_id` TEXT NOT NULL
- `job` TEXT NOT NULL
- `idempotency_key` TEXT NOT NULL
- `delivery_attempt` INTEGER NOT NULL
- `provider` TEXT NOT NULL
- `delivery_status` TEXT NOT NULL
- `provider_delivery_ref` TEXT NULL
- `provider_response_code` TEXT NULL
- `last_error` TEXT NULL
- `created_at_utc` TEXT NOT NULL
- `updated_at_utc` TEXT NOT NULL

Pflichtindizes:
- Index auf `run_id`
- Index auf `idempotency_key`

### `daily_evaluations`
Eine Zeile pro Berlin-Geschaeftstag und Bewertungslauf.

Pflichtspalten:
- `id` INTEGER PRIMARY KEY
- `business_date_berlin` TEXT NOT NULL
- `evaluation_source` TEXT NOT NULL
- `traffic_light_status` TEXT NOT NULL
- `reasons_json` TEXT NOT NULL
- `assessment_text` TEXT NOT NULL
- `recommendation_key` TEXT NOT NULL
- `recommendation_text` TEXT NOT NULL
- `warning_text` TEXT NULL
- `task_snapshot_id` INTEGER NULL
- `created_at_utc` TEXT NOT NULL

Pflichtindizes:
- `UNIQUE(business_date_berlin, evaluation_source)`
- Index auf `traffic_light_status`

### `weekly_reviews`
Eine Zeile pro `weekly_sync`-Zielwoche.

Pflichtspalten:
- `id` INTEGER PRIMARY KEY
- `week_start_date_berlin` TEXT NOT NULL
- `lookback_start_berlin` TEXT NOT NULL
- `lookback_end_berlin` TEXT NOT NULL
- `patterns_json` TEXT NOT NULL
- `reduced_targets_json` TEXT NOT NULL
- `recommendation_text` TEXT NOT NULL
- `task_snapshot_id` INTEGER NULL
- `created_at_utc` TEXT NOT NULL

Pflichtindizes:
- `UNIQUE(week_start_date_berlin)`

### `task_snapshots`
Eine Zeile pro erfasster Aufgabenbasis.

Pflichtspalten:
- `id` INTEGER PRIMARY KEY
- `snapshot_scope` TEXT NOT NULL
- `captured_at_utc` TEXT NOT NULL
- `business_date_berlin` TEXT NOT NULL
- `provider` TEXT NOT NULL
- `provider_status` TEXT NOT NULL
- `is_partial` INTEGER NOT NULL DEFAULT 0
- `failed_lists_json` TEXT NULL
- `tasks_by_list_json` TEXT NOT NULL
- `open_task_count` INTEGER NOT NULL

Pflichtindizes:
- Index auf `business_date_berlin`
- Index auf `snapshot_scope`

## Optionale Cache-Tabelle

### `calendar_snapshots`
Nur optional und nur als Cache.

Zulaessige Rolle:
- Troubleshooting
- Review-Hilfsdaten
- Debugging

Nicht zulaessige Rolle:
- Ersatz fuer frischen Live-Calendar-Read vor einem produktiven Send

Empfohlene Spalten:
- `id`
- `snapshot_scope`
- `captured_at_utc`
- `window_start_berlin`
- `window_end_berlin`
- `provider`
- `events_json`

## Idempotenz-Keys
Normative Keys in V2:
- `evening_reset:<target_date_berlin>`
- `weekly_sync:<week_start_date_berlin>`

Legacy-Kontext aus V1:
- `evening_briefing:<target_date_berlin>` bleibt nur fuer Migrationslesbarkeit relevant

## Statussemantik

### `sending`
- aktiver Lauf mit exklusiver Lease
- blockiert parallele Duplikate

### `sent`
- Delivery bestaetigt
- blockiert spaetere produktive Sends dauerhaft

### `skipped`
- bewusst nicht gesendet
- blockiert spaetere Neuversuche nicht

### `failed`
- technischer oder fachlicher Fehler ohne bestaetigten Send
- blockiert spaetere Neuversuche nicht

### `dry_run`
- Testlauf ohne produktive Delivery
- darf nie als produktiver Send zaehlen

## Retry-Semantik
Verbindliche Regeln:
- kein Retry bei fehlgeschlagenem Calendar-Read
- kein Retry bei fehlgeschlagenem State-Zugriff
- kein Retry bei Task-Provider-Ausfall als Ursache fuer Partial Degradation
- genau ein Retry nach 30 Sekunden nur bei eindeutigem Transportfehler vor Provider-Akzeptanz
- kein automatischer Retry bei unbekanntem Delivery-Ausgang

Jeder Retry nutzt:
- denselben Idempotenz-Key
- frische Live-Daten
- denselben logischen `job_runs`-Record mit erhoehter `attempt_count`
- einen neuen `message_deliveries`-Eintrag

## Retention-Defaults
Standard-Retention in v1:
- `job_runs`: 180 Tage
- `message_deliveries`: 180 Tage
- `task_snapshots`: 30 Tage
- `daily_evaluations`: 365 Tage
- `weekly_reviews`: 365 Tage
- optionale `calendar_snapshots`: 14 Tage

Regel:
- Retention darf spaeter erweitert werden
- Retention darf nicht dazu fuehren, dass Primaerwahrheiten in SQLite nachgebaut werden

## Failure-Verhalten
- kein produktiver Send ohne SQLite-State
- kein `sent` ohne bestaetigte Delivery
- kein lokaler Ersatz-Wahrheitszustand fuer fehlgeschlagene Provider-Schritte
- unbekannter Delivery-Ausgang bleibt `failed` oder aehnlich offen, niemals `sent`

## Go-Live-Minimum
Der V2-State-Layer ist nur dann live-faehig, wenn:
- die Pflichttabellen vorhanden sind
- `UNIQUE(job, idempotency_key)` greift
- Reboot und Lease-Ablauf keine Doppel-Sends erzeugen
- Berlin-Daten und UTC-Timestamps sauber getrennt sind
- Snapshots und Bewertungen klar als Derived State erkennbar bleiben
