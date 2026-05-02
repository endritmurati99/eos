# EOS Prep Reminder Policy v1

## Zweck
EOS sendet am Vortag morgens kurze, operative Vorbereitungserinnerungen für relevante Sporttermine des Folgetags.

## Trigger-Bedingung
Ein Reminder darf nur gesendet werden, wenn im live gelesenen Google Calendar für morgen ein relevanter Sporttermin vorhanden ist.

## Datenquelle
- Nur aktueller Google Calendar Read
- Keine lokalen Stub-Dateien als Primärquelle
- Keine freien Vermutungen über nicht vorhandene Termine

## Standardzeit
- Standard: `08:30` in `Europe/Berlin`
- Alternative Konfiguration: `09:00` in `Europe/Berlin`

## Relevante Terminarten
V1 relevant:
- BJJ / Brazilian Jiu-Jitsu
- Kickboxen
- weitere Sportarten nur, wenn dafür eine definierte Checklisten-Zuordnung existiert

## Nachrichtsstil
- kurz
- operativ
- keine Motivationsfloskeln
- keine geratenen Packlisten
- nur definierte Checklisten verwenden

## Bündelungsregel
Wenn am Folgetag mehrere relevante Sporttermine anstehen:
- möglichst eine gebündelte Nachricht senden
- je Termin nur die zugehörige definierte Kurz-Checkliste nennen
- keine unnötigen Wiederholungen

## Sicherheitsregel
- Kein Reminder ohne aktuellen Kalendernachweis
- Kein Reminder auf Basis alter Planungsannahmen
- Kein freies Ergänzen nicht definierter Items

## Ausgabemuster
### Einzelsport
Morgen steht `TERMINTITEL` an, `UHRZEIT`.
Nicht vergessen:
- ...
- ...

### Mehrere Sporttermine
Morgen stehen diese Sporttermine an:
- `TERMINTITEL 1`, `UHRZEIT`
- `TERMINTITEL 2`, `UHRZEIT`

Nicht vergessen:
`TERMINTITEL 1`
- ...

`TERMINTITEL 2`
- ...
