# EOS Scheduler Live E2E v1

## Zweck
Dieses Dokument definiert minimale produktionsnahe Live-E2E-Tests fuer den EOS-Scheduler-Layer in Phase 1.

## Testprinzipien
- jeder Test arbeitet mit frischem Calendar-Read
- Dry-Run und produktiver Lauf werden getrennt betrachtet
- Idempotenz wird pro Zielzeitraum verifiziert
- Failure-Faelle muessen fail-closed enden
- kein Test darf spekulative Inhalte als Erfolg werten

## E2E-1: `evening_briefing` Live

### Ziel
Verifizieren, dass EOS am Abend eine operative Morgen-Nachricht aus bestaetigten Daten bildet.

### Testvoraussetzung
- fuer morgen existieren echte Kalenderdaten
- falls `Top-3 morgen` erwartet werden, existiert ein verifizierter persistenter Task-Snapshot
- persistenter State ist verfuegbar

### Ablauf
1. `evening_briefing` fuer den naechsten Berlin-Lokaltag ausloesen
2. Live-Calendar-Read fuer morgen ausfuehren
3. Idempotenz-Key `evening_briefing:<target_date_berlin>` pruefen
4. Nachricht bilden
5. Nachricht senden
6. State als `sent` committen

### Erwartung
- eine einzelne Nachricht
- `Harte Termine morgen` korrekt
- `Deep-Work-Vorschlag` folgt EOS-Lastlogik
- `Sport morgen` korrekt
- `Warnung bei Ueberladung` nur wenn fachlich noetig
- fehlender Task-Snapshot wird explizit markiert statt Top-3 zu raten

### Nicht bestanden wenn
- Termine halluziniert werden
- `Top-3 morgen` ohne verifizierte Aufgabenbasis geraten wird
- mehr als eine Nachricht fuer denselben Lauf gesendet wird
- `sent` ohne bestaetigte Delivery gesetzt wird

## E2E-2: `sport_prep_reminder` Live

### Ziel
Verifizieren, dass nur relevante, gemappte Sporttermine fuer morgen einen Reminder ausloesen.

### Testvoraussetzung
- morgen existiert mindestens ein echter gemappter Sporttermin
- die zugehoerige Checkliste ist definiert
- persistenter State ist verfuegbar

### Ablauf
1. `sport_prep_reminder` ausloesen
2. Live-Calendar-Read fuer morgen ausfuehren
3. relevante Termine filtern
4. Mapping pruefen
5. eine gebuendelte kurze Nachricht senden
6. State als `sent` committen

### Erwartung
- nur eine kurze operative Nachricht
- nur definierte Checklistenpunkte
- keine geratenen Packlisten
- mehrere qualifizierte Termine werden nach Moeglichkeit gebuendelt

### Nicht bestanden wenn
- Reminder ohne echten Kalendereintrag gesendet wird
- unmappte Sportarten Inhalte erzeugen
- falsche Checkliste verwendet wird
- mehrere Spam-Nachrichten statt einer gebuendelten Nachricht entstehen

## E2E-3: `weekly_sync` Live

### Ziel
Verifizieren, dass EOS am Sonntag die kommende Kalenderwoche strategisch und operativ zusammenfasst.

### Testvoraussetzung
- fuer die kommende Woche existieren echte Kalenderdaten
- falls `gekuerzte Ziele` aus Aufgaben abgeleitet werden sollen, existiert ein verifizierter persistenter Task-Snapshot
- persistenter State ist verfuegbar

### Ablauf
1. `weekly_sync` am Sonntag oder simuliert fuer Sonntag `18:00 Europe/Berlin` ausloesen
2. Wochenfenster Montag `00:00` bis Montag `00:00` bilden
3. Live-Calendar-Read fuer dieses Wochenfenster ausfuehren
4. Idempotenz-Key `weekly_sync:<week_start_date_berlin>` pruefen
5. Nachricht bilden
6. Nachricht senden
7. State als `sent` committen

### Erwartung
- Ausgabe fuer genau die kommende Kalenderwoche
- `Arbeitstage` korrekt
- `fixe Sportkurse` korrekt
- `flexible Bloecke` als Vorschlaege, nicht als Garantien
- fehlende Aufgabenbasis wird explizit markiert statt Ziele zu erfinden

### Nicht bestanden wenn
- Rest-Sonntag in die Woche hineinfaellt
- nur ein rollierendes 7-Tage-Fenster betrachtet wird
- Zielreduktionen ohne Aufgabenbasis halluziniert werden

## Dry-Run-Test pro Job

### Ziel
Verifizieren, dass dieselbe Fachlogik ohne produktiven Send durchlaufen wird.

### Ablauf
1. Job im Dry-Run starten
2. Live-Calendar-Read ausfuehren
3. Relevanz und Idempotenz pruefen
4. Nachricht bilden
5. Ergebnis loggen

### Erwartung
- kein produktiver Send
- kein `sent`-Eintrag
- nachvollziehbares Log
- fachlich dieselbe Entscheidung wie im Produktivlauf

### Nicht bestanden wenn
- Dry-Run Telegram sendet
- Dry-Run `sent` schreibt
- Dry-Run andere Entscheidungslogik nutzt als der Produktivlauf

## Idempotenz-Test

### Ziel
Verifizieren, dass derselbe Zielzeitraum nicht doppelt gesendet wird.

### Ablauf
1. Job produktiv fuer einen gueltigen Zielzeitraum starten
2. denselben Job fuer denselben Zielzeitraum erneut starten

### Erwartung
- erster Lauf sendet genau einmal
- zweiter Lauf sendet nicht
- zweiter Lauf loggt einen klaren Duplicate- oder `sent`-Block-Grund

### Nicht bestanden wenn
- der zweite Lauf erneut sendet
- `sending` oder `sent` falsch behandelt wird

## Relevanz-Test fuer `sport_prep_reminder`

### Fall A: gemappter Termin vorhanden
Erwartung:
- genau ein Reminder

### Fall B: nur ungemappte Sporttermine vorhanden
Erwartung:
- kein Reminder

### Fall C: gemappte und ungemappte Sporttermine vorhanden
Erwartung:
- Reminder nur mit gemappten Terminen und deren Checklisten

## Wochen-Test fuer `weekly_sync`

### Ziel
Verifizieren, dass das Wochenfenster immer Montag-bis-Montag ist.

### Erwartung
- Query startet am kommenden Montag `00:00 Europe/Berlin`
- Query endet am darauffolgenden Montag `00:00 Europe/Berlin`
- kein rollierendes Sieben-Tage-Modell

## Failure-Kriterien
Der Scheduler-Test gilt als fehlgeschlagen, wenn mindestens eines davon passiert:
- doppelter Send fuer denselben Idempotenz-Key
- falsche Berlin-Zeit oder falscher Zieltag
- Send ohne frischen Live-Calendar-Read
- Reminder mit geratenen Prep-Items
- Briefing mit geratenen Aufgaben oder Zielen
- produktiver Send trotz fehlendem persistenten State
- automatischer Retry nach unbekanntem Delivery-Ausgang
- `sent` ohne bestaetigte Delivery

## Go-Live-Minimum
Vor produktivem Einsatz sollten mindestens erfolgreich verifiziert sein:
- ein Dry-Run fuer jeden der drei Jobs
- ein Live-Send pro Job
- ein Idempotenz-Test
- ein Relevanz-Test fuer `sport_prep_reminder`
- ein Montag-bis-Montag-Test fuer `weekly_sync`
