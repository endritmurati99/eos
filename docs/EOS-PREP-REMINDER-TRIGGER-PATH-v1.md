# EOS Prep Reminder Trigger Path v1

## Ziel
Technischer Auslösepfad für Vortags-Sport-Reminder.

## Ablauf
1. Scheduler/Cron triggert täglich um `08:30` `Europe/Berlin`
2. EOS liest live Google Calendar für morgen
3. EOS aggregiert mindestens:
   - `primary`
   - `Sport`
4. EOS filtert auf relevante Sporttermine mit definierter Checkliste
5. EOS bündelt mehrere Treffer, wenn sinnvoll
6. EOS sendet eine kurze Telegram-Nachricht

## Calendar Read
- Quelle: Google Calendar via `gog`
- Zeitzone: `Europe/Berlin`
- Query: morgen `00:00` bis übermorgen `00:00` lokal

## Filter für morgen
Ein Termin qualifiziert nur, wenn:
- er morgen liegt
- er ein relevanter Sporttermin ist
- er eine definierte Checklisten-Zuordnung hat

## Scheduler / Cron
Empfohlener Trigger:
- täglicher Cron-Job
- lokale Ausführungszeit: `08:30 Europe/Berlin`
- optional konfigurierbar auf `09:00 Europe/Berlin`

## Telegram Send
- Ziel: Endrits direkter Telegram-Chat
- Stil: kurz, operativ, gebündelt wenn mehrere Termine vorhanden
- kein Send, wenn keine qualifizierten Sporttermine für morgen gefunden wurden

## Failure-Regeln
- Wenn Calendar Read fehlschlägt: kein erfundener Reminder
- Wenn Mapping fehlt: kein Reminder für diesen Termin
- Wenn Send fehlschlägt: Fehler loggen, nicht mehrfach spammen
