# EOS Scheduler Jobs v1

## Zweck
Dieses Dokument definiert die drei Phase-1-Scheduler-Jobs fuer EOS mit klaren Triggern, Eingaben, Outputs und Sendelogik.

## Gemeinsame Job-Regeln
Fuer alle Jobs gilt:
- Triggerbewertung in `Europe/Berlin`
- vor jedem Send frischer Live-Calendar-Read
- mindestens `primary` und `Sport` aggregieren
- keine Sends ohne persistenten State
- keine Sends bei bestehendem Idempotenz-Status `sent`
- genau eine Nachricht pro Job-Ausfuehrung
- keine spekulativen Inhalte
- Dry-Run durchlaeuft dieselbe Fachlogik, sendet aber nicht

## `evening_briefing`

### Rolle
Taeglicher Hauptanker fuer den naechsten Tag.

### Trigger
- taeglich `20:30 Europe/Berlin`

### Zielzeitraum
- morgen `00:00 Europe/Berlin` bis uebermorgen `00:00 Europe/Berlin`

### Eingabedaten
- frischer Live-Read aller harten Termine fuer morgen
- Aggregation mindestens aus `primary` und `Sport`
- verifizierter persistenter Task-Snapshot fuer offene Aufgaben, falls verfuegbar
- bestehende EOS-Planungsregeln fuer Belastung, Deep Work und Sport
- definierte Vorbereitungs-/Carry-Hinweise aus Kalender- und Planungslogik

### Outputfelder
- `Harte Termine morgen`
- `Top-3 morgen`
- `Deep-Work-Vorschlag`
- `Sport morgen`
- `Vorbereitung / Nicht vergessen`
- `Warnung bei Ueberladung`

### Sendebedingungen
- frischer Calendar-Read fuer morgen erfolgreich
- persistenter State verfuegbar
- kein vorhandener `sent`-Eintrag fuer `evening_briefing:<target_date_berlin>`
- Nachricht kann aus bestaetigten Daten gebildet werden

### Nicht-Sendebedingungen
- Calendar-Read fehlgeschlagen
- State-Zugriff fehlgeschlagen
- Idempotenz-Key ist bereits `sent`
- Delivery-Pfad ist vor Send fachlich nicht erreichbar

### Fachregeln
- `Top-3 morgen` darf nur aus verifiziertem persistentem Task-Snapshot abgeleitet werden
- fehlt diese Quelle, muss das Outputfeld explizit melden, dass die Aufgabenbasis fehlt
- Deep Work folgt dem EOS-Standard: `60 Minuten Fokus + 10 Minuten Spaziergang`
- Donnerstag bis Samstag sind harte Belastungstage
- Ueberladung muss frueh und explizit markiert werden
- kein Motivationsstil

## `sport_prep_reminder`

### Rolle
Kurzer, operativer Vortags-Reminder fuer relevante Sporttermine.

### Trigger
- taeglich `08:30 Europe/Berlin`

### Zielzeitraum
- morgen `00:00 Europe/Berlin` bis uebermorgen `00:00 Europe/Berlin`

### Eingabedaten
- frischer Live-Calendar-Read fuer morgen
- Aggregation mindestens aus `primary` und `Sport`
- bestehende Mapping-Regeln aus `EOS-PREP-CHECKLIST-MAPPINGS-v1.md`
- bestehende Reminder-Regeln aus `EOS-PREP-REMINDER-POLICY-v1.md`

### Outputfelder
- kurzer Kopf mit relevantem Sporttermin oder gebuendelten Sportterminen
- pro qualifiziertem Termin nur die definierte Kurz-Checkliste
- keine weiteren Felder ausser der operativen Reminder-Nachricht

### Sendebedingungen
- fuer morgen existiert mindestens ein relevanter Sporttermin
- fuer jeden aufgenommenen Termin existiert eine definierte Checklisten-Zuordnung
- frischer Calendar-Read erfolgreich
- persistenter State verfuegbar
- kein vorhandener `sent`-Eintrag fuer `sport_prep_reminder:<target_date_berlin>`

### Nicht-Sendebedingungen
- kein relevanter Sporttermin fuer morgen
- nur unmappte Sporttermine vorhanden
- Calendar-Read fehlgeschlagen
- State-Zugriff fehlgeschlagen
- Idempotenz-Key ist bereits `sent`

### Fachregeln
- nur definierte Checklisten verwenden
- keine geratenen Packlisten
- unmappte Sportarten werden ignoriert und duerfen keinen Reminder ausloesen
- mehrere qualifizierte Termine werden nach Moeglichkeit in einer Nachricht gebuendelt
- ein Mix aus gemappten und ungemappten Terminen fuehrt nur fuer die gemappten Termine zu Inhalt

## `weekly_sync`

### Rolle
Strategischer Wochenanker fuer die kommende Kalenderwoche.

### Trigger
- Sonntag `18:00 Europe/Berlin`

### Zielzeitraum
- kommende Woche Montag `00:00 Europe/Berlin` bis naechster Montag `00:00 Europe/Berlin`

### Eingabedaten
- frischer Live-Calendar-Read fuer die kommende Woche
- Aggregation mindestens aus `primary` und `Sport`
- verifizierter persistenter Task-Snapshot fuer offene Aufgaben und Zielreduktion, falls verfuegbar
- bestehende EOS-Wochenlogik fuer Belastung, Sportziele, Deep Work und Ueberladung

### Outputfelder
- `Harte Termine`
- `Arbeitstage`
- `fixe Sportkurse`
- `flexible Bloecke`
- `gekuerzte Ziele`
- `Warnung bei Ueberladung`
- `Nicht vergessen`

### Sendebedingungen
- frischer Calendar-Read fuer den kommenden Montag-bis-Montag-Zeitraum erfolgreich
- persistenter State verfuegbar
- kein vorhandener `sent`-Eintrag fuer `weekly_sync:<week_start_date_berlin>`
- Nachricht kann ohne Spekulation aus bestaetigten Daten gebildet werden

### Nicht-Sendebedingungen
- Calendar-Read fehlgeschlagen
- State-Zugriff fehlgeschlagen
- Idempotenz-Key ist bereits `sent`
- Delivery-Pfad ist vor Send fachlich nicht erreichbar

### Fachregeln
- Wochenfenster ist immer die kommende Kalenderwoche, nicht die naechsten sieben Tage
- `gekuerzte Ziele` folgen der bestehenden EOS-Reduktionslogik
- fehlt ein verifizierter Task-Snapshot, muss die fehlende Aufgabenbasis explizit markiert werden statt Ziele zu erfinden
- feste Sportkurse bleiben harte Bloecke
- flexible Bloecke bleiben Vorschlaege, keine Zusagen
- Ueberladung muss klar benannt werden

## Idempotenz-Keys pro Job
- `evening_briefing:<target_date_berlin>`
- `sport_prep_reminder:<target_date_berlin>`
- `weekly_sync:<week_start_date_berlin>`

## Prioritaet bei Mehrfachausloesung
Wenn derselbe Job fuer denselben Zielzeitraum mehrfach getriggert wird:
- `sent` blockiert weiteren Send
- `skipped` blockiert keinen spaeteren Neuversuch
- `failed` blockiert keinen spaeteren Neuversuch
- `sending` blockiert parallel laufende Duplikate nur waehrend der Lease-Zeit
