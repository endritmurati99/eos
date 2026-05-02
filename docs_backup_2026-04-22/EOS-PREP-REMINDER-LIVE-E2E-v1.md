# EOS Prep Reminder Live E2E v1

## Ziel
Minimaler Live-Ende-zu-Ende-Test für einen Vortags-Sport-Reminder.

## Testvoraussetzung
- Morgen existiert ein echter relevanter Sporttermin im Google Calendar
- Beispiel: BJJ oder Kickboxen
- Termin ist über den normalen Google Calendar Read sichtbar

## Testablauf
1. Triggerzeit simulieren oder Cron einmalig auslösen
2. EOS liest morgen live aus Google Calendar
3. EOS erkennt den relevanten Sporttermin
4. EOS wählt die definierte Checkliste
5. EOS sendet die kurze Reminder-Nachricht nach Telegram

## Erwartung
- Reminder wird nur gesendet, wenn der morgige Termin real im Kalender steht
- Nachricht ist kurz und operativ
- Nachricht enthält nur definierte Checklistenpunkte
- keine Motivationsfloskeln
- keine geratenen zusätzlichen Packlisten

## Minimalbeispiel Erwartung
Morgen steht Brazilian Jiu-Jitsu an, 17:45.
Nicht vergessen:
- Gi oder No-Gi
- Wasser
- Handtuch
- Tape
- Mundschutz
- Abfahrtszeit prüfen
- Duschzeug

## Bestanden wenn
- Kalendertermin korrekt erkannt
- richtige Checkliste verwendet
- Telegram-Nachricht korrekt gesendet
- keine Halluzinationen

## Nicht bestanden wenn
- Reminder ohne echten Kalendereintrag gesendet wird
- falsche oder erfundene Packliste enthalten ist
- falsche Sportart gemappt wird
- mehrere Termine unnötig in getrennte Spam-Nachrichten zerfallen
