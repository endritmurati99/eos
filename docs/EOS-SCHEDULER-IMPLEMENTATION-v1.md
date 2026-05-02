# EOS Scheduler Implementation v1

## Zweck
Dieses Dokument beschreibt das bevorzugte technische Zielmodell fuer den EOS-Scheduler-Layer in Phase 1.

Der Fokus liegt auf einem robusten, produktionsnahen Ausloesepfad fuer VPS und Docker.
Es dokumentiert keine spekulativen Hostpfade, Containerpfade, Unit-Namen oder Secrets.

## Zielmodell
Bevorzugtes Produktionsmodell:
- `systemd`-Timer auf dem Host
- pro Trigger ein einmaliger Joblauf
- kein dauerhafter In-Container-Loop
- kein `while true`
- kein `sleep`-Polling als Produktionsmechanik

Fallback:
- `cron`, wenn `systemd` im realen VPS-Setup nicht verfuegbar oder nicht praktikabel ist

## Komponenten auf hoher Ebene
Der Scheduler-Layer besteht in Phase 1 logisch aus:
- Host-Scheduler-Layer
- einmaligem Job-Runner `<job-runner>`
- Live-Calendar-Reader via `gog`
- Planner/Composer fuer die jeweilige Job-Nachricht
- persistentem State Store
- Delivery-Adapter fuer Telegram
- strukturiertem Logging

Diese Komponenten koennen im realen Setup innerhalb eines Containers, ueber `docker exec`, ueber einen dedizierten Dienst oder ueber einen anderen bestaetigten Runtime-Pfad angesprochen werden.
Die exakte technische Verdrahtung bleibt bis zur VPS-Verifikation offen.

## systemd-timer-first
Bevorzugte Ablaufidee:
1. Host-Timer triggert exakt zur Berlin-Zeit
2. Host startet einen einmaligen Joblauf fuer genau einen Jobtyp
3. Der Joblauf bestimmt sein Berlin-Zielfenster
4. Der Joblauf liest live Google Calendar
5. Der Joblauf prueft Relevanz und Idempotenz
6. Der Joblauf komponiert die Nachricht
7. Der Joblauf sendet oder skippt
8. Der Joblauf schreibt strukturiertes Logging und State

Regeln:
- ein Timer-Ereignis = ein Joblauf
- keine Endlosschleifen im Container
- keine mehreren Jobtypen in einem unklaren Sammelprozess

## cron-Fallback
Wenn `systemd` nicht das reale Zielmodell ist, darf `cron` als Fallback dokumentiert werden.

Dabei gelten dieselben Regeln:
- Berlin-Zeit muss korrekt eingehalten werden
- jeder Cron-Tick startet nur einen einmaligen Joblauf
- dieselbe Idempotenz- und State-Logik bleibt Pflicht
- Cron ersetzt nicht Dry-Run, Logging oder Relevanzpruefung

## Job-Runner-Anforderungen
Der einmalige `<job-runner>` muss pro Lauf mindestens koennen:
- `job` entgegennehmen
- Dry-Run vs produktiv unterscheiden
- Berlin-Zeitfenster korrekt berechnen
- Live-Calendar-Read ausfuehren
- vorhandenen State lesen und Lease setzen
- die job-spezifische Nachricht komponieren
- den Delivery-Adapter kontrolliert aufrufen
- Ergebnis strukturiert loggen

## Dry-Run-Modell
Jeder Job braucht einen verpflichtenden Dry-Run-Modus.

Dry-Run umfasst:
- Triggerkontext
- Zeitfensterbildung
- Live-Calendar-Read
- Relevanz- und Idempotenzpruefung
- Nachrichtskomposition
- Logging

Dry-Run umfasst nicht:
- produktiven Telegram-Send
- Setzen eines produktiven `sent`-Status

Dry-Run ist Pflicht, damit fachliche Inhalte geprueft werden koennen, ohne Telegram zu spammen.

## Logging-Modell
Logging muss sauber, strukturiert und pro Lauf nachvollziehbar sein.

Pflichtfelder:
- `job`
- `run_id`
- `trigger_time_berlin`
- `target_window`
- `idempotency_key`
- `calendar_read_status`
- `decision`
- `skip_reason`
- `delivery_status`
- `state_status`

Empfohlene Zusatzfelder:
- `runtime_timezone`
- `attempt_count`
- `message_digest`
- `provider_delivery_ref`
- `error_code`
- `error_detail`

## Failure-Verhalten
Der Scheduler arbeitet fail-closed.

Regeln:
- kein Send bei Calendar-Read-Fehler
- kein Send bei State-Fehler
- kein Send bei unklaren Pflichtdaten
- kein freies Auffuellen fehlender Inhalte
- kein automatisches Weiterlaufen in spekulative Defaults

Typische Failure-Faelle:
- `gog`-Read liefert keinen verwertbaren Kalenderzustand
- State Store ist nicht erreichbar
- Delivery-Adapter liefert unklaren Zustand
- Aufgaben-Snapshot fehlt fuer `Top-3 morgen` oder `gekuerzte Ziele`

Fachfolge:
- Job skippt oder failt kontrolliert
- Fehler wird geloggt
- Nachricht wird nicht geraten

## Retry-Verhalten
Verbindliche Regeln:
- kein Retry bei fehlgeschlagenem Calendar-Read
- kein Retry bei fehlgeschlagenem State-Zugriff
- genau ein begrenzter Retry nach 30 Sekunden bei eindeutigem Transportfehler vor Provider-Akzeptanz
- kein automatischer Retry bei unbekanntem Delivery-Ausgang

Jeder Retry muss:
- denselben Idempotenz-Key nutzen
- frische Kalenderdaten lesen
- den State neu pruefen

## Relevanz- und Inhaltslogik
- `evening_briefing` ist der taegliche Hauptanker fuer morgen
- `sport_prep_reminder` ist nur ergaenzend und nur bei echter Relevanz aktiv
- `weekly_sync` ist der strategische Wochenanker
- mehrere Nachrichten am selben Tag sind zu minimieren
- operative Dichte ist wichtiger als stilistische Laenge
- kein Motivationsstil

## Platzhalter-Regel
In dieser Spezifikation duerfen nur Platzhalter fuer unbestaetigte Runtime-Details verwendet werden, zum Beispiel:
- `<service>`
- `<container>`
- `<job-runner>`
- `<state-store>`

Nicht zulaessig:
- unbestaetigte Hostpfade
- unbestaetigte Containerpfade
- unbestaetigte Unit-Namen
- Secrets oder Zugangsdaten

## Nicht verhandelbar
- `systemd`-timer-first
- `cron` nur als Fallback
- kein Loop-basierter Scheduler im Container
- Dry-Run pro Job
- sauberes Logging pro Lauf
- persistenter State und Idempotenz als Pflicht
