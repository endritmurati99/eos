# EOS V2 Timers v1

## Zweck
Dieses Dokument definiert die Scheduler- und Timer-Anforderungen fuer EOS V2.
Es beschreibt das normative Zielmodell, nicht die aktuelle Legacy-Laufzeit.

## Grundsatz
V2 ist `systemd`-timer-first.
Fallback ist `cron`.
Nicht zulaessig als Primaermodell:
- In-Container-`while true`
- In-Container-`sleep`-Polling
- unklare Sammelprozesse mit mehreren Jobs in einem Dauerloop

## Erster Live-V2-Jobset
In der ersten produktiven V2-Welle werden nur diese Jobs live gedacht:

| Job | Rolle | Trigger |
|---|---|---|
| `evening_reset` | taeglicher Abendanker fuer morgen | taeglich `20:30 Europe/Berlin` |
| `weekly_sync` | kombinierter Wochenrueckblick und Wochenanker | Sonntag `18:00 Europe/Berlin` |

Nicht Teil des ersten Live-Jobsets:
- `sport_prep_reminder`
- `morning_briefing`

## Zeitbasis
- fachliche Wahrheit ist `Europe/Berlin`
- Triggerzeiten sind Wall-Clock-Zeiten in Berlin
- UTC dient nur fuer Logs und Persistenz

Verbindliche Fenster:
- `evening_reset` arbeitet fuer morgen `00:00` bis uebermorgen `00:00`
- `weekly_sync` plant die kommende Woche Montag `00:00` bis Montag `00:00`

## Job-Runner-Modell
Jeder Trigger startet genau einen einmaligen Joblauf.

Pflichten pro Lauf:
- Jobname entgegennehmen
- Dry-Run vs produktiv unterscheiden
- Berlin-Zielfenster berechnen
- Live-Calendar-Read ausfuehren
- optionalen Task-Read ausfuehren
- Idempotenz und State pruefen
- Nachricht komponieren
- Delivery kontrolliert ausfuehren oder skippen
- strukturiert loggen

## Logging-Pflichten
Jeder Lauf loggt mindestens:
- `job`
- `run_id`
- `trigger_time_berlin`
- `trigger_time_utc`
- `target_window_start_berlin`
- `target_window_end_berlin`
- `runtime_timezone`
- `calendar_read_status`
- `task_read_status`
- `decision`
- `delivery_status`
- `state_status`

## Dry-Run-Pflicht
Jeder Job braucht einen Dry-Run.

Dry-Run umfasst:
- Zeitfensterlogik
- Live-Reads
- Relevanz- und Idempotenzpruefung
- Nachrichtskomposition
- Logging

Dry-Run umfasst nicht:
- produktiven Send
- Setzen von `sent`

## Failure-Regeln
- fail-closed bei Calendar-Read-Fehler
- fail-closed bei State-Fehler
- keine spekulativen Defaults
- Task-Ausfall ist bei `evening_reset` und `weekly_sync` ein Partial-Degradation-Fall, kein Send-Verbot

## Operator-Rollout
Dieses Dokument beschreibt nur operator-facing Schritte, keine automatische Installation.

### Schritt 1
Zeitbasis pruefen:
- Host-Zeit korrekt
- Berlin-Zeit korrekt
- Job-Runner rechnet mit `Europe/Berlin`

### Schritt 2
One-shot-Laufmodell bestaetigen:
- jeder Timer-Trigger startet genau einen Lauf
- keine Dauerprozesse

### Schritt 3
State-Layer pruefen:
- SQLite persistent erreichbar
- Idempotenz-Keys blockieren korrekt
- Lease-Verhalten ist nachvollziehbar

### Schritt 4
Dry-Runs durchfuehren:
- mindestens ein Dry-Run fuer `evening_reset`
- mindestens ein Dry-Run fuer `weekly_sync`

### Schritt 5
Jobweise Live-Freigabe:
- zuerst `evening_reset`
- danach `weekly_sync`
- nie beide ohne vorherige Dry-Run-Abnahme aktivieren

## `systemd`-Timer-First
Normative Eigenschaften:
- einmaliger Trigger pro Job
- saubere Berlin-Zeit
- gute Operator-Sichtbarkeit
- kontrollierte Restart- und Failure-Semantik

Dieses Dokument nennt absichtlich keine:
- Unit-Namen
- Hostpfade
- Installationsskripte
- Secrets

## `cron`-Fallback
Falls `systemd` real nicht verfuegbar oder unpraktisch ist:
- `cron` darf denselben One-shot-Job-Runner ausloesen
- dieselben Berlin-Zeitregeln gelten
- dieselbe Dry-Run-, Logging- und Idempotenzlogik gilt

`cron` ersetzt nicht:
- State Layer
- Dry-Run
- Logging
- Idempotenz

## Legacy Drift gegen V2
Die aktuelle prompt-getriebene `cron/jobs.json`-Konfiguration gilt nicht als V2-Zielbild.
Sie ist in dieser Spezifikation nur Migrationskontext.

## Go-Live-Minimum
Vor der ersten produktiven V2-Aktivierung muessen mindestens bestaetigt sein:
- Berlin-Zeit stimmt
- Dry-Run pro Job funktioniert
- Idempotenz verhindert Duplikate
- Partial Degradation bei Task-Ausfall ist nachvollziehbar
- keine Host-Automation wurde blind aus Doku erzeugt
