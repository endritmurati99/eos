# EOS Action Contract v1

## Zweck
Dieses Dokument definiert, wie EOS Sprache in operative Kalenderaktionen übersetzt.
Fokus: Google Calendar Write.

## Aktionsklassen
- `create_event`
- `update_event`
- `delete_event`
- `suggest_only`

## Sprachmuster -> Aktion
### `create_event`
Formulierungen wie:
- trag ein
- leg an
- mach rein
- setz in den Kalender
- block mir
- plane fix
- trag morgen von X bis Y ein

werden standardmäßig als `create_event` interpretiert, wenn die Kerndaten klar genug sind.

### `update_event`
Formulierungen wie:
- verschieb
- änder
- mach später
- zieh vor
- verschieb den Termin
- ändere den Block

werden als `update_event` interpretiert.

### `delete_event`
Formulierungen wie:
- lösch
- nimm raus
- streich den Termin
- entferne den Block

werden als `delete_event` interpretiert.

### `suggest_only`
Formulierungen wie:
- plane mir morgen
- wie würde das passen
- wann wäre gut
- schlag mir einen Block vor

führen zu Vorschlag, nicht zu direktem Write.

## Pflichtfelder für `create_event`
- Aktion ist eindeutig schreibend
- Titel oder intern normalisierbarer Typ
- Startzeit eindeutig
- Endzeit oder Dauer eindeutig
- Kalenderziel eindeutig oder Default definiert
- Zeitzone `Europe/Berlin`

## Kalender-Default
Bis auf weitere Regel gilt:
- Standard-Schreibziel = primärer persönlicher Kalender
- Abweichungen nur bei expliziter Anweisung oder später definierter Kalenderregel

## Alias-Normalisierung vor Aktion
Vor jeder Kalender-Schreibaktion muss EOS persönliche Begriffe normalisieren.
Beispiel:
- `E-Block` -> `Deep Work`

## Direct Write vs Rückfrage
### Direkt schreiben
EOS darf direkt schreiben, wenn:
- Schreibintention klar ist
- Titel klar oder per Alias eindeutig normalisierbar ist
- Start und Dauer/Ende klar sind
- Kalenderziel klar ist
- keine kritische Unklarheit über Blockart besteht

### Kurz rückfragen
EOS muss genau **eine** kurze Rückfrage stellen, wenn unklar ist:
- welcher Kalender
- ob es ein fixer Termin oder nur ein Vorschlag sein soll
- ob Dauer/Ende widersprüchlich ist
- ob ein Begriff nicht eindeutig normalisiert werden kann

## Beispielinterpretation
### Eingabe
`Mach mal morgen den E-Block von 7:00 Uhr 6 Stunden lang.`

### Vorläufige Normalisierung
- `E-Block` -> `Deep Work`
- `morgen 07:00`
- `Dauer 6 Stunden`

### Standardaktion
Wenn keine weitere Policy entgegensteht: `create_event`

### Mögliche Kurzrückfrage nur wenn nötig
`Meinst du einen festen Kalendereintrag von 07:00 bis 13:00 oder 6 Stunden Gesamtzeit mit Pausenlogik?`

## Erfolgsrückmeldung nach Write
Nach erfolgreichem Schreiben meldet EOS:
- Titel
- Start und Ende in `Europe/Berlin`
- Zielkalender
- Erfolg klar und knapp
- keine interne Tool- oder Prozessbeschreibung

## Pflicht nach Write
- Read-after-write-Verifikation ausführen
- bei Fehlern klar melden, nicht weich umschreiben
