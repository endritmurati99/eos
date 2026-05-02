# EOS Review Engine v1

## Zweck
Dieses Dokument definiert die kombinierte Weekly-Review- und Weekly-Sync-Logik fuer EOS V2.
Der Sonntagsjob bleibt `weekly_sync`, liefert aber in V2 eine kombinierte Ausgabe:
- Rueckblick auf die letzten 7 Tage
- Mustererkennung
- konkrete Strukturierung fuer die kommende Woche

## Normativer Job
- Jobname: `weekly_sync`
- Trigger: Sonntag `18:00 Europe/Berlin`

## Zeitfenster

### Rueckblick
`lookback7d` umfasst die letzten 7 Berlin-Lokaltage bis zum Triggerzeitpunkt.

### Vorschau
`nextWeekWindow` umfasst die kommende Kalenderwoche:
- Start: kommender Montag `00:00 Europe/Berlin`
- Ende: darauffolgender Montag `00:00 Europe/Berlin`

Nicht zulaessig:
- rollierende 7-Tage-Fenster als Ersatz fuer die kommende Woche
- Sonntag-zu-Sonntag-Planung statt Montag-bis-Montag

## Interne Vertrage

### `PatternSignal`
`PatternSignal = { key, severity, evidence, implication }`

Zulaessige `key`-Werte in v1:
- `overload_cluster`
- `carry_over_repeat`
- `fragmented_day_pattern`
- `hard_shift_sport_stack`
- `missed_deep_work`
- `prep_friction_repeat`

### `WeeklyReviewContext`
`WeeklyReviewContext` enthaelt mindestens:
- `lookback7d`
- `nextWeekWindow`
- `hardEvents[]`
- `taskSnapshot`
- `dailyEvaluations[]`
- `deliveryHistory`

### `WeeklySyncSummary`
`WeeklySyncSummary = { lookback7d, nextWeekWindow, patterns[], reducedTargets[], weekRecommendation }`

Regeln:
- `patterns[]` enthaelt nur datenbasierte Signale
- `reducedTargets[]` nennt explizit gekuerzte oder fragile Ziele
- `weekRecommendation` ist genau eine konkrete Empfehlung

## Datenquellen
Die Review Engine arbeitet mit:
- frischem Calendar-Read fuer die kommende Woche
- Task-Basis, falls verfuegbar
- gespeicherten `daily_evaluations`, falls verfuegbar
- Review- und Delivery-Historie aus Derived State

Die Review Engine darf nicht:
- fehlende Wochenmuster erfinden
- Aufgaben oder Termine raten
- ohne Kalenderbasis einen produktiven Send ausloesen

## Musterklassen

### `overload_cluster`
Mehrere enge oder rote Tage haeuften sich.
Signalquellen:
- `daily_evaluations`
- harte Kalenderballung

### `carry_over_repeat`
Dieselben offenen Loops tauchen wiederholt auf oder wurden nicht sauber geschlossen.

### `fragmented_day_pattern`
Mehrere Tage hatten keine realen 60+10-Fokusfenster, obwohl hoher Anspruch blieb.

### `hard_shift_sport_stack`
Harte Arbeitstage und fixe Sportbloecke stapelten sich sichtbar.

### `missed_deep_work`
Sinnvolle Deep-Work-Fenster wurden wiederholt nicht realisiert.

### `prep_friction_repeat`
Vorbereitung fuer Arbeit, Sport oder Uebergaenge fuehrte wiederholt zu Reibung.

## Ableitungslogik
Die Engine arbeitet in fester Reihenfolge:
1. Rueckblick-Daten sammeln
2. taegliche Signale und Stored Evaluations konsolidieren
3. Muster verdichten
4. kommende Woche Montag-bis-Montag lesen
5. harte Termine und harte Lasttage markieren
6. flexible Ziele konservativ verteilen
7. reduzierte oder fragile Ziele explizit benennen
8. genau eine strukturelle Wochenempfehlung ableiten

## Reduktionslogik fuer die kommende Woche
Wenn die Woche zu voll ist, gilt die EOS-Kuerzungsreihenfolge:
1. `Cardio` Block 2
2. `Cardio` Block 1
3. `Gym` Block 2
4. `Gym` Block 1
5. sekundaerer Deep-Work-Block

Nicht reduzierbar als Wochenziel:
- harte Termine
- Arbeitstage
- fixe Sportkurse
- Mindest-Routinen

## Outputvertrag
Die Ausgabe folgt dem Weekly-Review-Template und enthaelt:
- `Rueckblick 7 Tage`
- `Muster`
- `Naechste Woche hart gesetzt`
- `Empfohlene Verteilung`
- `Gekuerzte oder riskante Punkte`
- `Meine Empfehlung`
- `Nicht vergessen`

Regeln:
- genau eine Nachricht pro Sonntagstrigger
- genau eine konkrete Empfehlung
- keine redundante zweite Sonntags-Wochenbotschaft innerhalb desselben Jobs
- keine Guru-Sprache

## Partial Degradation

### Wenn Tasks fehlen
- `weekly_sync` darf weiterlaufen
- offene Aufgabenbasis wird explizit als eingeschraenkt markiert
- reduzierte Ziele duerfen nur aus bestaetigten Daten abgeleitet werden

### Wenn `daily_evaluations` fehlen
- Mustererkennung faellt auf Kalender plus Task-Snapshots zurueck
- die fehlende Bewertungsbasis wird explizit genannt

### Wenn Calendar fehlt
- kein Send
- fail-closed

## Idempotenz
Normativer Idempotenz-Key:
- `weekly_sync:<week_start_date_berlin>`

Nur `sent` blockiert einen spaeteren produktiven Zweitversuch fuer dieselbe Zielwoche.

## Live-Abnahmekriterien
`weekly_sync` ist in v1 nur dann go-live-faehig, wenn:
- der Rueckblick echte Muster statt Filler erkennt
- die kommende Woche Montag-bis-Montag geplant wird
- harte Arbeitstage und fixe Sportkurse korrekt als Last wirken
- gekuerzte Ziele explizit und nachvollziehbar benannt werden
- genau eine konkrete Empfehlung gegeben wird
- fehlende Datenbasen offen benannt statt ueberspielt werden
