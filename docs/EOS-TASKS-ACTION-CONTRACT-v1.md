# EOS Tasks Action Contract v1

## Zweck
Dieses Dokument definiert, wie EOS Sprache in operative Google-Tasks-Aktionen uebersetzt.
Fokus: Listenstruktur, Task Read, Task Create, Task Complete.

## Aktionsklassen
- `list_structure`
- `task_read`
- `task_create`
- `task_complete`

## Listenmodell
- `Inbox` = Default-Capture, untriagiert
- `Next` = direkt ausfuehrbar
- `Waiting` = blockiert durch andere Personen oder externe Abhaengigkeiten
- `This Week` = diese Woche verbindlich relevant, aber kein Kalenderevent

## Sprachmuster -> Aktion
### `list_structure`
Formulierungen wie:
- wie sind meine Task-Listen aufgebaut
- welche Listen nutzt EOS
- zeig mir die Google-Tasks-Struktur

werden als `list_structure` interpretiert.

### `task_read`
Formulierungen wie:
- zeig mir meine offenen Aufgaben
- lies meine Tasks
- was ist in Inbox
- was liegt in This Week
- zeig mir Task `<taskId>`
- lies die Aufgabe `<Titel>`

werden standardmaessig als `task_read` interpretiert.

### `task_create`
Formulierungen wie:
- leg eine Aufgabe an
- erstell einen Task
- pack das in Inbox
- notier das als Aufgabe
- mach fuer diese Woche einen Task

werden standardmaessig als `task_create` interpretiert.

### `task_complete`
Formulierungen wie:
- markier als erledigt
- hake ab
- setz auf fertig
- schliesse den Task ab

werden standardmaessig als `task_complete` interpretiert.

## Standardverhalten fuer `task_read`
- Default-Read = offene Tasks aus allen vier Listen
- Default-Reihenfolge = `Inbox`, `Next`, `Waiting`, `This Week`
- Bei expliziter Listenangabe liest EOS nur diese Liste
- Einzel-Task-Read wird zuerst ueber `taskId`, danach ueber eindeutigen Titel aufgeloest

## Standardfilter fuer `task_read`
- Nur `status = needsAction` wird im Default-Read angezeigt
- `completed`, `deleted` und `hidden` werden nicht angezeigt
- Task-Reads werden nicht mit Kalender- oder Vault-Aktionen vermischt

## Pflicht- und Defaultregeln fuer `task_create`
- Pflichtfeld: `title`
- Optionale Felder: `notes`, `due`, explizite Zielliste
- Ohne Zielliste geht jeder neue Task nach `Inbox`
- Neuer Task startet mit `status = needsAction`
- EOS sortiert neue Tasks nicht automatisch in `Next`, `Waiting` oder `This Week` um

## Aufloesungsregel fuer Einzel-Tasks
- Zuerst `taskId`
- Sonst eindeutiger Titel ueber alle offenen Tasks
- Bei Mehrdeutigkeit genau eine kurze Rueckfrage mit den Kandidaten
- Ohne eindeutige Aufloesung darf EOS keinen Erfolg behaupten

## Abschlussregel fuer `task_complete`
- EOS sucht nur unter offenen Tasks
- Abschluss erfolgt in der bestehenden Liste
- Abschluss bedeutet Statuswechsel auf `completed`
- `task_complete` loescht nicht
- `task_complete` verschiebt nicht
- `task_complete` fuehrt kein `clear` aus
- Nach erfolgreichem Abschluss verschwindet der Task aus dem Default-Read offener Aufgaben

## Direkt ausfuehren vs Rueckfrage
### Direkt ausfuehren
EOS darf direkt lesen, erstellen oder abschliessen, wenn:
- die Aktion klar ist
- Titel oder `taskId` klar sind
- bei `task_create` mindestens ein `title` vorliegt
- die Zielliste eindeutig oder per Default `Inbox` bestimmt ist

### Kurz rueckfragen
EOS muss genau eine kurze Rueckfrage stellen, wenn unklar ist:
- welcher von mehreren offenen Tasks mit gleichem Titel gemeint ist
- ob ein genannter Listenname einer der vier gueltigen Listen entspricht
- ob bei `task_create` ueberhaupt ein verwertbarer `title` genannt wurde

## Beispielinterpretation
### Eingabe
`Leg "Rechnung an Krankenkasse senden" als Aufgabe an.`

### Standardaktion
- `task_create`
- Zielliste `Inbox`
- Status `needsAction`

### Eingabe
`Markier "Mit Max Ruecksprache halten" als erledigt.`

### Verhalten bei Mehrdeutigkeit
Wenn derselbe offene Titel mehrfach existiert, stellt EOS genau eine kurze Rueckfrage wie:
`Ich habe zwei offene Tasks mit diesem Titel: Next und This Week. Welchen soll ich abschliessen?`

## Erfolgsrueckmeldung
- `task_read`: klare Gruppierung nach Listen oder exakte Einzel-Task-Ausgabe
- `task_create`: Titel, Zielliste, optionales Due-Datum, Status `needsAction`
- `task_complete`: Titel, Liste, Status `completed`

## Out of Scope
- Delete
- Move
- Clear
- automatische Heuristik-Umsortierung
- Scheduler-, Calendar- oder Vault-Nebenwirkungen
