# EOS Tasks Live E2E v1

## Zweck
Konkrete Live-Tests fuer den operativen Google-Tasks-v1-Pfad von EOS.

## Voraussetzung
- Google Tasks Zugriff ist technisch verbunden
- vier reale Listen existieren: `Inbox`, `Next`, `Waiting`, `This Week`
- Read fuer offene Tasks funktioniert
- Write fuer Task-Erstellung und Abschluss funktioniert

## Test 1: Listen lesen
### Eingabe
`Zeig mir meine offenen Aufgaben.`

### Erwartung
- EOS liest offene Tasks aus `Inbox`, `Next`, `Waiting`, `This Week`
- Ausgabe ist nach genau dieser Reihenfolge gruppiert
- `completed`-Tasks erscheinen nicht im Default-Read

## Test 2: Einzel-Task per ID lesen
### Eingabe
`Lies Task task-next-thesis-outline.`

### Erwartung
- EOS erkennt `task_read`
- genau der Task `task-next-thesis-outline` wird gelesen
- Titel, Liste, Status und optionale Felder stimmen

## Test 3: Einzel-Task per eindeutigem Titel lesen
### Eingabe
`Lies die Aufgabe "Bachelorarbeit Gliederung finalisieren".`

### Erwartung
- EOS erkennt `task_read`
- genau ein offener Task wird ueber den Titel aufgeloest
- keine unnoetige Rueckfrage

## Test 4: Task ohne Zielliste anlegen
### Eingabe
`Leg die Aufgabe "Rechnung an Krankenkasse senden" an.`

### Erwartung
- EOS erkennt `task_create`
- Task wird in `Inbox` angelegt
- Status ist `needsAction`
- EOS meldet Titel und Zielliste klar zurueck

## Test 5: Task mit expliziter Zielliste anlegen
### Eingabe
`Leg die Aufgabe "Bachelorarbeit Expose ueberarbeiten" in This Week an.`

### Erwartung
- EOS erkennt `task_create`
- Task wird in `This Week` angelegt
- Status ist `needsAction`
- EOS verschiebt den Task nicht still in eine andere Liste

## Test 6: Eindeutigen Task abschliessen
### Eingabe
`Markier "Mietvertrag scannen" als erledigt.`

### Erwartung
- EOS erkennt `task_complete`
- genau der offene Task wird aufgeloest
- Status wechselt auf `completed`
- Task bleibt in seiner bestehenden Liste

## Test 7: Mehrdeutigen Task nur nach Rueckfrage abschliessen
### Eingabe
`Markier "Mit Max Ruecksprache halten" als erledigt.`

### Erwartung
- EOS erkennt `task_complete`
- EOS fuehrt keinen stillen Abschluss aus
- EOS stellt genau eine kurze Rueckfrage mit den Kandidaten aus `Next` und `This Week`

## Test 8: Completed Task verschwindet aus Default-Read
### Direkt nach Test 6
- EOS liest die offenen Aufgaben erneut
- der eben abgeschlossene Task erscheint nicht mehr im Default-Read
- andere offene Tasks bleiben sichtbar

## Failure
- falsche Liste
- stilles Auto-Routing bei `task_create`
- Abschluss des falschen Tasks bei doppeltem Titel
- Erfolgsmeldung ohne reale API-Wirkung
- `completed`-Task bleibt im Default-Read offener Aufgaben sichtbar

## Go / No-Go
### Go
- Listen-Read funktioniert ueber alle vier Listen
- Einzel-Task-Read per ID und per eindeutigem Titel funktioniert
- Create ohne Zielliste landet in `Inbox`
- Create mit Zielliste landet in der genannten Liste
- Complete arbeitet eindeutig oder fragt genau einmal nach

### No-Go
- `This Week` wird nur als abgeleitete Sicht statt als echte Liste behandelt
- EOS routet neue Tasks ohne Anweisung automatisch um
- EOS schliesst bei Mehrdeutigkeit ohne Rueckfrage ab
- EOS zeigt `completed`-Tasks im Default-Read offener Aufgaben
