# EOS Tasks Integration v1

## Zweck
Dieses Dokument definiert den minimalen, produktionsnahen Google-Tasks-v1-Pfad fuer EOS V2.
Fokus:
- provider-neutraler Adapter
- direkte User-Task-Wahrheit in Google Tasks
- Read, Create und Complete
- klares Failure-Verhalten

## Produktive Rolle
- Google Tasks ist die Primaerquelle fuer aktive offene Aufgaben
- EOS liest und schreibt Aufgaben nicht primar aus lokalen JSON-Dateien oder SQLite
- SQLite darf nur Snapshots, Review-Daten oder technische Historie halten

## Normativer Providerpfad
Zielarchitektur:
- direkter Google-Tasks-Zugriff ueber OAuth2 mit User Consent
- refresh-token-basierte, headless-faehige Laufzeit

Erlaubter Uebergangspfad:
- ein Bridge-/Gateway-Pfad darf voruebergehend als Adapter eingesetzt werden
- der Adapter ist nicht die normative Zielarchitektur
- Bridge-Pfade muessen dieselbe EOS-Semantik einhalten

## Scope v1
- Listen lesen
- offene Tasks lesen
- Task anlegen
- Task abschliessen
- echte Listenstruktur fuer `Inbox`, `Next`, `Waiting`, `This Week`

Nicht Teil von v1:
- Delete
- Move
- Clear
- Bulk-Aktionen
- automatische Umsortierung
- Subtask-Ausbau

## Kanonische Listen
`TaskListName` ist in v1 exakt:
- `Inbox`
- `Next`
- `Waiting`
- `This Week`

Regeln:
- `This Week` ist eine echte Google-Tasks-Liste, keine abgeleitete Sicht
- neue Tasks landen ohne explizite Liste in `Inbox`
- EOS sortiert neue Tasks nicht automatisch nach `Next`, `Waiting` oder `This Week` um

## Provider-neutrale Adaptergrenze

### Interne Vertrage
`TaskListName = Inbox | Next | Waiting | This Week`

`TaskRef = taskId | uniqueTitle`

`TaskCreateInput = { title, notes?, due?, listName? }`

`TaskOperationResult = success | not_found | ambiguous | provider_error`

### Normativer Adapter
`TaskGateway` muss mindestens diese Operationen bereitstellen:
- `readOpenTasks(listNames?)`
- `createTask(input)`
- `completeTask(ref)`

### Erwartete Semantik
- `readOpenTasks()` liest standardmaessig offene Tasks aus allen vier kanonischen Listen
- Reihenfolge ist immer `Inbox`, `Next`, `Waiting`, `This Week`
- `createTask()` legt einen offenen Task in der Ziel-Liste an
- `completeTask()` setzt den Task in seiner bestehenden Liste auf `completed`

Provider-spezifische IDs, Wire-Formate und OAuth-Details bleiben hinter der Adaptergrenze.

## Read-Verhalten

### Default-Read
Ohne explizite Listenangabe:
- lies offene Tasks aus allen vier Listen
- zeige nur `needsAction`
- gruppiere in der Reihenfolge `Inbox`, `Next`, `Waiting`, `This Week`
- zeige keine `completed`, `deleted` oder `hidden` Tasks

### Expliziter Read
- bei expliziter Listenangabe liest EOS nur diese Liste
- bei `taskId` wird exakt diese Aufgabe aufgeloest
- bei Titel wird nur dann direkt aufgeloest, wenn der Titel unter allen offenen Tasks eindeutig ist

### Mehrdeutigkeit
Wenn derselbe offene Titel mehrfach existiert:
- kein stilles Raten
- genau eine kurze Rueckfrage
- kein Erfolg ohne eindeutige Aufloesung

## Create-Verhalten

### Pflicht- und Optionalfelder
- Pflicht: `title`
- optional: `notes`
- optional: `due`
- optional: `listName`

### Defaults
- ohne `listName` => `Inbox`
- Status nach Erstellung => `needsAction`
- keine automatische Nebenwirkung auf Calendar, Vault oder Scheduler

### Due-Feld
`due` wird intern als ISO-8601-Wert behandelt.
Die Adapter-Schicht normalisiert ihn auf das vom Provider benoetigte Wire-Format.

## Complete-Verhalten
- zuerst `taskId` aufloesen
- sonst eindeutigen offenen Titel aufloesen
- nur offene Tasks duerfen abgeschlossen werden
- Abschluss bedeutet Statuswechsel zu `completed`
- kein Delete
- kein Move
- kein Clear

Nach erfolgreichem Abschluss:
- der Task bleibt in seiner Liste bestehen
- er verschwindet aus dem Default-Read offener Aufgaben

## Listen-Mapping
Die kanonischen Namen `Inbox`, `Next`, `Waiting`, `This Week` werden zur Laufzeit auf provider-spezifische Listen-IDs gemappt.

Regeln:
- das Mapping ist Konfiguration, nicht fachliche Logik
- alle vier Listen muessen vor produktiver Freigabe real existieren
- eine fehlende kanonische Liste ist Go-Live-blockierend

## TaskGateway-Outputs

### Read-Output
Der Adapter liefert mindestens:
- `status`
- `tasksByList`
- `provider`
- `readAtUtc`
- `failedLists` falls vorhanden

### Mutation-Output
`createTask()` und `completeTask()` liefern mindestens:
- `status`
- `provider`
- `taskId` bei Erfolg
- `listName` bei Erfolg
- `lastError` bei `provider_error`

## Partial Degradation
V2 verlangt, dass EOS bei Task-Problemen nicht still wird.

### Bei Read-Fehlern
Wenn der Task-Provider nicht erreichbar ist oder das Mapping unvollstaendig ist:
- markiere den Zustand explizit als `provider_error`
- nenne klar, dass die Aufgabenbasis derzeit nicht verfuegbar ist
- erfinde keine Prioritaeten
- erfinde keine Top-3

### Bei partiellen Listenfehlern
Wenn nur ein Teil der vier Listen gelesen werden kann:
- melde die ausgefallenen Listen explizit
- verwende nur bestaetigte Daten aus erreichbaren Listen
- behaupte nicht, dass die offene Aufgabenbasis vollstaendig ist

### Bei Create-/Complete-Fehlern
- behaupte keinen Erfolg ohne bestaetigte Provider-Wirkung
- gib `provider_error` klar aus
- fuehre keine lokale Ersatzmutation in SQLite oder JSON aus

## Scheduler- und Review-Bezug
Die Tasks-Integration versorgt spaetere V2-Module, ersetzt sie aber nicht:
- `evening_reset` darf bei Task-Ausfall mit expliziter Einschraenkung weiterlaufen
- `weekly_sync` darf bei Task-Ausfall kalenderbasiert weiterlaufen, muss die fehlende Aufgabenbasis aber nennen
- `daily_evaluations` und `weekly_reviews` speichern nur abgeleitete Einschaetzungen und Snapshot-Referenzen

## Sicherheits- und Betriebsregeln
- keine Secrets in Doku-Dateien
- keine Annahme eines neuen Google-Projekts in dieser Phase
- keine lokale JSON-Datei als Ersatz fuer einen fehlgeschlagenen Live-Write
- keine Vermischung von Providerpfad und fachlicher EOS-Policy

## Live-Abnahmekriterien
Go fuer v1 nur wenn:
- alle vier Listen real existieren
- Read ueber alle vier Listen funktioniert
- Create in `Inbox` und `This Week` funktioniert
- Complete per `taskId` und eindeutigen Titeln funktioniert
- Mehrdeutigkeit fuehrt zu Rueckfrage statt Fehlabschluss
- Providerfehler werden explizit berichtet

No-Go wenn:
- `This Week` nur als abgeleitete Sicht behandelt wird
- EOS neue Tasks automatisch umsortiert
- EOS bei Providerfehlern still bleibt
- EOS lokale Ersatz-Wahrheiten fuer fehlgeschlagene Provider-Aktionen erzeugt
