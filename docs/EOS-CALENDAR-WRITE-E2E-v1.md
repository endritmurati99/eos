# EOS Calendar Write E2E v1

## Zweck
Konkrete Live-Tests für den operativen Google-Calendar-Write-Pfad von EOS.

## Voraussetzung
- Google Calendar OAuth ist aktiv
- Write-Scope ist vorhanden
- Zielkalender ist definiert
- Zeitzone ist `Europe/Berlin`

## Test 1: Create Event
### Eingabe
`Trage morgen von 07:00 bis 13:00 einen Deep-Work-Block ein.`

### Erwartung
- EOS erkennt `create_event`
- EOS wählt den richtigen Zielkalender
- EOS legt den Termin mit korrekter Start-/Endzeit an
- EOS meldet Erfolg klar zurück
- Event ist real in Google Calendar sichtbar

## Test 2: Read-after-write
### Direkt nach Test 1
- EOS liest den neu angelegten Termin wieder aus
- Titel, Start, Ende, Kalender stimmen

### Failure
- Event nicht auffindbar
- falscher Kalender
- falsche Zeit oder falsche Zeitzone

## Test 3: Update Event
### Eingabe
`Verschieb den Deep-Work-Block morgen auf 08:00 bis 14:00.`

### Erwartung
- EOS erkennt `update_event`
- genau der richtige Termin wird aktualisiert
- EOS meldet die neue Zeit korrekt
- Read-after-write bestätigt die Änderung

## Test 4: Collision Test
### Eingabe
Schreibaktion für einen Termin, der mit hartem Termin kollidiert

### Erwartung
- EOS erkennt die Kollision
- EOS schreibt nicht blind
- EOS stellt genau eine knappe Rückfrage oder meldet Konflikt klar

## Test 5: Failure Handling
### Szenarien
- fehlender Write-Scope
- Token ungültig
- Zielkalender unklar
- API-Fehler

### Erwartung
- EOS meldet Fehler explizit
- kein falscher Erfolgstext
- keine erfundene erfolgreiche Erstellung

## Go / No-Go
### Go
- Create funktioniert
- Update funktioniert
- Read-after-write funktioniert
- Kollisionen werden sauber behandelt

### No-Go
- Event wird nicht wirklich erstellt
- Event landet im falschen Kalender
- Antwort behauptet Erfolg ohne reale API-Wirkung
- Read-after-write fehlt oder ist inkonsistent
