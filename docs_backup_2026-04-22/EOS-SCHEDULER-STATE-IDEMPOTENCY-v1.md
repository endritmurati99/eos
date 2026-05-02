# EOS Scheduler State & Idempotency v1

## Zweck
Dieses Dokument definiert den persistenten Scheduler-State und die verbindlichen Idempotenzregeln fuer EOS Phase 1.

## Grundsatz
Persistenter State ist Pflicht.
Ohne persistenten State darf kein produktiver Scheduler-Send stattfinden.

Ziele:
- doppelte Sends verhindern
- Reboots ueberstehen
- Retry-Verhalten kontrollieren
- Dry-Run von produktiven Sends sauber trennen

## Bevorzugte State-Variante

### Primaer
SQLite auf verifiziertem persistenten Storage.

Begruendung:
- atomare Updates sind einfacher als mit einer freien JSON-Datei
- parallele Trigger lassen sich robuster absichern
- Status, Lease und Retry-Metadaten bleiben strukturiert

### Minimal-Fallback
JSON-Datei auf verifiziertem persistenten Storage.

Einschraenkung:
- nur Minimal-Fallback
- hoeheres Risiko fuer Race Conditions
- nur zulaessig, wenn SQLite fuer Phase 1 technisch noch nicht verfuegbar ist

## Pflichtfelder pro State-Record
Jeder Joblauf braucht mindestens diese Felder:
- `job`
- `idempotency_key`
- `target_window_start_berlin`
- `target_window_end_berlin`
- `state_status`
- `run_id`
- `attempt_count`
- `created_at_utc`
- `updated_at_utc`
- `lease_expires_at_utc`
- `calendar_read_status`
- `delivery_status`
- `last_error`

Optional, aber empfohlen:
- `message_digest`
- `task_snapshot_ref`
- `provider_delivery_ref`

## Idempotenz-Keys
Verbindliche Keys:
- `evening_briefing:<target_date_berlin>`
- `sport_prep_reminder:<target_date_berlin>`
- `weekly_sync:<week_start_date_berlin>`

Beispiele:
- `evening_briefing:2026-04-22`
- `sport_prep_reminder:2026-04-22`
- `weekly_sync:2026-04-27`

## Zulaessige Statuswerte
- `sending`
- `sent`
- `skipped`
- `failed`
- `dry_run`

## Statussemantik

### `sending`
- markiert einen aktiven Lauf mit exklusiver In-Flight-Lease
- blockiert parallele Duplikate fuer denselben Idempotenz-Key
- Lease laeuft nach 15 Minuten ab
- nach Lease-Ablauf darf ein neuer Lauf den Key erneut uebernehmen

### `sent`
- nur dieser Status blockiert spaetere produktive Sends fuer denselben Key dauerhaft
- darf erst gesetzt werden, wenn Delivery bestaetigt ist und der State-Commit erfolgreich war

### `skipped`
- dokumentiert bewusstes Nicht-Senden
- blockiert keinen spaeteren Neuversuch
- typische Gruende: keine Relevanz, fehlender Sporttermin, fehlende gemappte Checkliste

### `failed`
- dokumentiert technischen oder fachlichen Fehler ohne erfolgreichen Send
- blockiert keinen spaeteren Neuversuch

### `dry_run`
- dokumentiert einen Testlauf ohne produktive Auslieferung
- darf nie als produktiver Send interpretiert werden
- darf keinen `sent`-Eintrag erzeugen

## Wann ein Job als gesendet gilt
Ein Job gilt nur dann als gesendet, wenn beide Bedingungen erfuellt sind:
- der Delivery-Pfad bestaetigt die Nachricht als erfolgreich uebernommen oder zugestellt
- der State wird erfolgreich als `sent` persistiert

Nicht ausreichend:
- Nachricht nur lokal gebaut
- Transportversuch nur gestartet
- unklare Provider-Antwort
- unbekannter Zustand nach Timeout

## Verhalten bei Retry
Verbindliche Retry-Regeln:
- kein Retry bei fehlgeschlagenem Calendar-Read
- kein Retry bei fehlgeschlagenem State-Zugriff
- genau ein begrenzter Retry nach 30 Sekunden nur bei eindeutigem Transportfehler vor Provider-Akzeptanz
- kein automatischer Retry bei unbekanntem Delivery-Ausgang

Jeder Retry muss:
- denselben Idempotenz-Key verwenden
- einen frischen Calendar-Read ausfuehren
- den State erneut pruefen

## Verhalten bei Reboot
Nach Reboot gilt:
- `sent` bleibt verbindlich und blockiert weitere Sends fuer denselben Key
- `skipped` und `failed` duerfen spaetere Neuversuche nicht blockieren
- `sending` darf nur bis zum Lease-Ablauf blockieren
- abgelaufene `sending`-Leases muessen als neu uebernehmbar gelten

## Verhalten bei Doppelausloesung
Wenn zwei Trigger denselben Job fuer denselben Zielzeitraum nahezu gleichzeitig starten:
- der erste erfolgreiche Lease-Erwerb setzt `sending`
- der zweite Lauf sieht den aktiven Lease-Zustand und beendet sich ohne Send
- nur ein Lauf darf die Nachricht produktiv ausliefern

## Verhalten bei unbekanntem Delivery-Ausgang
Wenn nach dem Send-Versuch unklar bleibt, ob die Nachricht angenommen wurde:
- Status nicht auf `sent` setzen
- Zustand als `failed` oder gleichwertig dokumentieren
- kein automatischer Retry
- Fall fuer manuelle Verifikation loggen

Begruendung:
Unklare Delivery-Lagen sind das Hauptrisiko fuer Doppel-Sends.

## Dry-Run-Regel
Dry-Run fuehrt den fachlichen Jobpfad aus:
- Triggerlogik
- Zeitfensterlogik
- Live-Calendar-Read
- Relevanzpruefung
- Nachrichtskomposition
- Logging

Dry-Run fuehrt nicht aus:
- produktiver Send
- Setzen von `sent`

## Nicht verhandelbar
- kein produktiver Send ohne persistenten State
- kein `sent` ohne bestaetigte Delivery
- `sent` ist der einzige dauerhaft blockierende Status
- jeder Retry nutzt frische Live-Daten
