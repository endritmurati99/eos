# EOS Scheduler Timebase v1

## Zweck
Dieses Dokument definiert die verbindliche Zeitbasis fuer EOS-Scheduler-Jobs in Phase 1.

## Grundsatz
Die operative Scheduler-Zeitzone ist `Europe/Berlin`.
Diese Zeitzone steuert:
- Triggerauswertung
- Datumsschnitt fuer morgen
- Wochenfenster fuer `weekly_sync`
- Anzeigezeiten in Nachrichten
- Calendar-Query-Grenzen

UTC bleibt relevant fuer technische Timestamps im State und Logging, aber nicht fuer die fachliche Tages- und Wochenlogik.

## Vier Zeitebenen

### Host-Zeit
Die Host-Zeit ist die Zeitbasis des bevorzugten Schedulers, wenn `systemd`-Timer auf dem VPS laufen.

Regeln:
- Host-Zeit muss korrekt sein
- Timer muessen in `Europe/Berlin` oder aequivalent korrekt auf Berlin-Zeit bezogen auswerten
- Host-Zeit darf nicht stillschweigend auf UTC verbleiben, wenn der Job lokal auf Berlin-Zeit geplant ist

### Container-Zeit
Die Container-Zeit ist die Laufzeitsicht innerhalb des EOS-Runtime-Containers.

Regeln:
- Container-Zeit muss mit der operativen Berlin-Zeit kompatibel sein
- fehlendes `TZ=Europe/Berlin` ist ein bekanntes Risiko
- Container-Zeit darf nicht abweichend von Host und App die Tagesgrenzen verschieben

### App-Zeit
App-Zeit ist die Zeit, die EOS intern fuer Datumslogik und Fensterbildung verwendet.

Regeln:
- App-Zeit muss `Europe/Berlin` explizit verwenden
- keine naiven Datumsoperationen ohne Zeitzonenbezug
- `morgen` und `kommende Woche` werden immer aus Berlin-Lokaltagen berechnet

### Calendar-Query-Zeit
Calendar-Queries muessen ebenfalls in Berlin-Lokalzeit begrenzt werden.

Regeln:
- taegliche Jobs fragen `00:00` bis `00:00` des Folgetags in `Europe/Berlin`
- `weekly_sync` fragt Montag `00:00` bis naechster Montag `00:00` in `Europe/Berlin`
- Rueckgaben muessen auf Berlin-Zeit normalisiert werden, bevor fachliche Regeln greifen

## Verbindliche Zeitfenster

### `evening_briefing`
- Zieltag = naechster Berlin-Lokaltag
- Query-Fenster = morgen `00:00 Europe/Berlin` bis uebermorgen `00:00 Europe/Berlin`

### `sport_prep_reminder`
- Zieltag = naechster Berlin-Lokaltag
- Query-Fenster = morgen `00:00 Europe/Berlin` bis uebermorgen `00:00 Europe/Berlin`

### `weekly_sync`
- Zielwoche = kommende Kalenderwoche in Berlin-Zeit
- Query-Fenster = naechster Montag `00:00 Europe/Berlin` bis darauffolgender Montag `00:00 Europe/Berlin`

Nicht zulaessig:
- rollierende Sieben-Tage-Fenster als Ersatz fuer `weekly_sync`
- UTC-Tagesgrenzen fuer taegliche Jobs
- Sonntagabend bis Sonntagabend als Wochenlogik

## Pruefregeln fuer `Europe/Berlin`
Vor produktivem Go-Live sollte verifiziert werden:
- Host zeigt die korrekte lokale Berliner Zeit
- Container zeigt die korrekte lokale Berliner Zeit oder verarbeitet `TZ=Europe/Berlin` korrekt
- die App bildet `morgen` und `naechsten Montag` korrekt
- Calendar-Reads liefern Events in den erwarteten Berliner Tagesgrenzen
- Sommer-/Winterzeit-Umstellung verschiebt Trigger und Fenster nicht falsch

## Typische Fehlerbilder

### UTC-Trigger-Drift
Symptom:
- Job triggert zwei Stunden zu frueh oder zu spaet

Ursache:
- Host-Scheduler oder Container laeuft faktisch in UTC

### Fehlendes Container-`TZ`
Symptom:
- Job startet zur richtigen Host-Zeit, aber App berechnet den falschen Zieltag

Ursache:
- Container oder App verwendet lokale Default-Zeit ohne `Europe/Berlin`

### Naive Datumsarithmetik
Symptom:
- `morgen` oder `kommende Woche` kippt an Tages- oder DST-Grenzen

Ursache:
- Offsetlose Datumslogik oder String-Manipulation statt zonenbewusster Zeitrechnung

### DST-Grenzfehler
Symptom:
- Wochen- oder Tagesfenster sind an Sommer-/Winterzeit-Umstellung um eine Stunde verschoben

Ursache:
- feste UTC-Offsets statt echte `Europe/Berlin`-Zeitzonenlogik

### Falsches Sunday/Monday-Window
Symptom:
- `weekly_sync` betrachtet Rest-Sonntag oder naechste sieben Tage statt kommender Kalenderwoche

Ursache:
- relative Zeitfenster statt Montag-bis-Montag-Logik

## Logging-Empfehlung fuer Zeitbasis
Jeder Joblauf sollte mindestens diese Zeitfelder loggen:
- `trigger_time_berlin`
- `trigger_time_utc`
- `target_window_start_berlin`
- `target_window_end_berlin`
- `runtime_timezone`
- `calendar_query_timezone`

## Nicht verhandelbar
- `Europe/Berlin` ist die fachliche Wahrheit
- UTC ist nur technische Begleitzone fuer Logs und Persistenz
- alle Scheduler-Fenster muessen auf Berlin-Lokaltagen basieren
