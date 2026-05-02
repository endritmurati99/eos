# EOS Evening Reset v1

## Zweck
Dieses Dokument definiert `evening_reset` als den taeglichen V2-Abendjob fuer den Folgetag.
Der Job schliesst den laufenden Tag operativ ab und bereitet morgen realistisch vor.

## Normativer Name
- normativer V2-Name: `evening_reset`
- Legacy-Alias aus V1: `evening_briefing`

Regel:
- neue V2-Dokumente verwenden ausschliesslich `evening_reset`
- bestehende Live-Jobs werden in der Spec-Freeze-Phase nicht umbenannt

## Rolle
`evening_reset` ist der taegliche Hauptanker fuer morgen.
Er soll:
- offene Punkte sichtbar machen
- morgen realistisch zuspitzen
- Vorbereitung heute Abend sichern
- Ueberladung fuer morgen frueh markieren

## Trigger und Zeitfenster
- Trigger: taeglich `20:30 Europe/Berlin`
- Zieltag: naechster Berlin-Lokaltag
- Query-Fenster: morgen `00:00 Europe/Berlin` bis uebermorgen `00:00 Europe/Berlin`

UTC bleibt nur technische Begleitzone fuer Logging und Persistenz.

## Eingabedaten
`evening_reset` verwendet:
- frischen Live-Calendar-Read fuer morgen
- offene Google Tasks, falls verfuegbar
- EOS-Coaching-Engine-Regeln
- bekannte Routinen und Prep-Logik

Mindestens `primary` und `Sport` muessen aggregiert werden.

## Interner Payload
`EveningResetPayload = { targetDateBerlin, hardEvents[], openLoops[], tomorrowPriorities[], prepItems[], loadStatus, recommendation }`

Semantik:
- `targetDateBerlin` = der Folgetag in `Europe/Berlin`
- `hardEvents[]` = bestaetigte harte Termine fuer morgen
- `openLoops[]` = offene Punkte mit unmittelbarer Relevanz fuer morgen
- `tomorrowPriorities[]` = Top-1 oder Top-3, niemals erfunden
- `prepItems[]` = Dinge, die heute Abend fuer morgen vorbereitet werden sollten
- `loadStatus` = Ergebnis der Coaching-Einschaetzung
- `recommendation` = genau eine konkrete Empfehlung

## Prioritaetslogik fuer morgen

### Top-1-Modus
`tomorrowPriorities[]` enthaelt genau einen Schwerpunkt, wenn mindestens eine Bedingung gilt:
- harter Belastungstag
- harter Arbeitstag plus fixer Sport
- Aufgabenbasis ist nur teilweise verfuegbar
- morgen hat objektiv wenig sauberen Handlungsspielraum

### Top-3-Modus
`tomorrowPriorities[]` enthaelt bis zu drei Punkte nur dann, wenn:
- die Aufgabenbasis verifiziert ist
- der Folgetag kein enger roter Lasttag ist
- die Reihenfolge realistisch bleibt

## Outputvertrag
Die Ausgabe folgt dem Evening-Reset-Template und enthaelt diese Abschnitte:
- `Morgen steht fest`
- `Offene Punkte`
- `Morgenfokus`
- `Vorbereitung heute`
- `Meine Einschaetzung`
- `Meine Empfehlung`
- `Warnung`

Regeln:
- genau eine Nachricht pro Zieltag
- genau eine konkrete Empfehlung
- `Warnung` nur wenn noetig
- keine Motivationssprache
- keine generischen Tipps

## Sendebedingungen
Produktiver Send ist nur zulaessig, wenn:
- frischer Calendar-Read fuer morgen erfolgreich war
- persistenter State verfuegbar ist
- kein `sent` fuer `evening_reset:<target_date_berlin>` existiert
- die Nachricht ohne Spekulation aus bestaetigten Daten gebildet werden kann

## Nicht-Sendebedingungen
Der Job sendet nicht, wenn:
- Calendar-Read fehlgeschlagen ist
- State-Zugriff fehlgeschlagen ist
- der Idempotenz-Key bereits `sent` ist
- Delivery vor Send technisch nicht verfuegbar ist

## Partial Degradation
Ein Task-Ausfall darf `evening_reset` nicht automatisch komplett blockieren.

### Wenn Tasks nicht verfuegbar sind
Dann gilt:
- die Nachricht darf trotzdem gesendet werden
- `Morgenfokus` muss die fehlende Aufgabenbasis explizit nennen
- es duerfen keine erfundenen Top-3 erscheinen
- die Empfehlung fokussiert auf Struktur, Reduktion oder Vorbereitung

### Wenn Calendar nicht verfuegbar ist
Dann gilt:
- kein Send
- fail-closed

## Idempotenz und Status
Normativer Idempotenz-Key:
- `evening_reset:<target_date_berlin>`

Statussemantik folgt dem V1-Idempotenzmodell:
- `sending`
- `sent`
- `skipped`
- `failed`
- `dry_run`

Nur `sent` blockiert spaetere produktive Sends dauerhaft.

## Dry-Run
Dry-Run durchlaeuft:
- Zeitfensterbildung
- Live-Calendar-Read
- optionalen Task-Read
- Coaching-Einschaetzung
- Nachrichtskomposition
- Logging

Dry-Run fuehrt nicht aus:
- Telegram-Send
- Setzen eines produktiven `sent`

## Coaching-Bezug
`evening_reset` verwendet die Coaching Engine fuer:
- `loadStatus`
- Einschaetzung
- Warnung
- Empfehlung

Die Nachricht bleibt operativ und kurz.
Sie wird nicht zu einem allgemeinen Daily-Plan oder Wochenbericht ausgeweitet.

## Live-Abnahmekriterien
`evening_reset` ist in v1 nur dann go-live-faehig, wenn:
- genau eine Nachricht pro Zieltag gesendet wird
- keine Doppel-Sends auftreten
- Aufgabenbasis bei Ausfall explizit als fehlend markiert wird
- harte Termine fuer morgen korrekt sind
- Top-1 oder Top-3 realistisch bleiben
- Vorbereitung heute klar und knapp sichtbar ist
