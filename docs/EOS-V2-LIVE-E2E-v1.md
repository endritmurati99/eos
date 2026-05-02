# EOS V2 Live E2E v1

## Zweck
Dieses Dokument definiert die minimalen produktionsnahen Live-E2E-Tests fuer EOS V2.
Es deckt Google Tasks, Evening Reset, Coaching Engine, Weekly Sync, Idempotenz, Dry-Run, Berlin-Zeitbasis und Partial Failures ab.

## Testprinzipien
- jeder Test arbeitet mit frischen Live-Daten, soweit verfuegbar
- Dry-Run und produktiver Lauf werden getrennt betrachtet
- keine spekulativen Inhalte gelten als Erfolg
- `Europe/Berlin` ist fuer fachliche Fenster und Bewertung verbindlich
- fail-closed ist Pflicht bei Calendar- oder State-Fehlern

## Voraussetzungen
- Google Calendar Live-Read ist verfuegbar
- Google Tasks ist technisch angebunden oder bewusst als ausfallender Testpfad testbar
- SQLite-State ist persistent erreichbar
- Telegram-Delivery-Pfad ist testbar

## E2E-1: Google Tasks Live Read

### Ziel
Verifizieren, dass EOS offene Aufgaben ueber alle vier Listen liest.

### Ablauf
1. offene Tasks ohne Listenfilter lesen
2. Ergebnis nach `Inbox`, `Next`, `Waiting`, `This Week` gruppieren
3. `completed`-Tasks ausblenden

### Erwartung
- genau diese vier Listen in kanonischer Reihenfolge
- keine erfundenen Listen
- keine `completed`-Tasks im Default-Read

### Nicht bestanden wenn
- `This Week` nur als berechnete Sicht behandelt wird
- Listen fehlen, ohne als Fehler genannt zu werden
- `completed`-Tasks sichtbar bleiben

## E2E-2: Google Tasks Live Create

### Ziel
Verifizieren, dass EOS Tasks in der Default- und Zielliste korrekt anlegt.

### Ablauf
1. Task ohne Zielliste anlegen
2. Task mit expliziter Zielliste `This Week` anlegen
3. beide Ergebnisse live lesen

### Erwartung
- Default landet in `Inbox`
- explizites Ziel landet in `This Week`
- Status ist `needsAction`
- kein stilles Auto-Routing

## E2E-3: Google Tasks Live Complete

### Ziel
Verifizieren, dass EOS Tasks eindeutig abschliesst oder sauber blockiert.

### Ablauf
1. eindeutigen offenen Task abschliessen
2. denselben Titel erneut im Default-Read pruefen
3. mehrdeutigen Titel pruefen

### Erwartung
- eindeutiger Task wird `completed`
- der abgeschlossene Task verschwindet aus dem offenen Default-Read
- mehrdeutiger Titel fuehrt zu genau einer Rueckfrage

## E2E-4: Evening Reset Dry-Run

### Ziel
Verifizieren, dass `evening_reset` dieselbe Fachlogik ohne produktiven Send durchlaeuft.

### Ablauf
1. `evening_reset` im Dry-Run fuer morgen starten
2. Live-Calendar-Read fuer morgen ausfuehren
3. optionalen Task-Read ausfuehren
4. Nachricht komponieren

### Erwartung
- kein produktiver Send
- kein `sent`
- nachvollziehbares Log
- gleiche inhaltliche Entscheidung wie im spaeteren Live-Lauf

## E2E-5: Evening Reset Live

### Ziel
Verifizieren, dass `evening_reset` genau eine operative Morgen-Nachricht sendet.

### Ablauf
1. `evening_reset` fuer den naechsten Berlin-Lokaltag produktiv starten
2. Idempotenz-Key `evening_reset:<target_date_berlin>` pruefen
3. Nachricht senden
4. State als `sent` committen

### Erwartung
- genau eine Nachricht
- harte Termine fuer morgen korrekt
- Top-1 oder Top-3 realistisch
- Vorbereitung heute sichtbar
- genau eine konkrete Empfehlung

### Nicht bestanden wenn
- Aufgabenbasis erfunden wird
- mehr als eine Nachricht fuer denselben Zieltag gesendet wird
- `sent` ohne bestaetigte Delivery gesetzt wird

## E2E-6: Coaching Engine Real Days

### Ziel
Verifizieren, dass `green`, `yellow` und `red` auf echten Testtagen plausibel sind.

### Testfaelle
- `green`: sauberer Tag ohne Ueberplanung
- `yellow`: enger, aber noch rettbarer Tag
- `red`: harter Arbeitstag plus fixer Sport plus weiterer schwerer Block

### Erwartung
- Status ist datenbasiert
- Thu-Sat werden konservativ bewertet
- genau eine konkrete Empfehlung
- keine generischen Produktivitaetstipps

## E2E-7: Weekly Sync Live

### Ziel
Verifizieren, dass `weekly_sync` Review plus Wochenvorschau kombiniert.

### Ablauf
1. `weekly_sync` fuer Sonntag `18:00 Europe/Berlin` starten
2. `lookback7d` aus den letzten 7 Berlin-Lokaltagen bilden
3. `nextWeekWindow` Montag `00:00` bis Montag `00:00` bilden
4. frischen Kalender fuer die kommende Woche lesen
5. Nachricht senden

### Erwartung
- eine einzige kombinierte Nachricht
- Muster aus echten Daten
- kommende Woche Montag-bis-Montag
- gekuerzte oder fragile Ziele explizit benannt
- genau eine konkrete Empfehlung

### Nicht bestanden wenn
- nur eine generische Wochenzusammenfassung entsteht
- die Vorschau ein rollierendes 7-Tage-Fenster nutzt
- Ueberladung nicht klar benannt wird

## E2E-8: Idempotenztest

### Ziel
Verifizieren, dass derselbe Zielzeitraum nicht doppelt sendet.

### Ablauf
1. Job produktiv fuer einen gueltigen Zielzeitraum starten
2. denselben Job fuer denselben Zielzeitraum erneut starten

### Erwartung
- erster Lauf sendet genau einmal
- zweiter Lauf sendet nicht
- zweiter Lauf loggt den Block-Grund klar

## E2E-9: Partial Failure bei Tasks

### Ziel
Verifizieren, dass Task-Ausfaelle explizit und ohne Halluzination behandelt werden.

### Fall A
Tasks komplett nicht erreichbar.

Erwartung:
- `evening_reset` und `weekly_sync` duerfen weiterlaufen
- fehlende Aufgabenbasis wird explizit genannt
- keine erfundenen Top-3 oder Wochenziele

### Fall B
Nur einzelne Listen fallen aus.

Erwartung:
- fehlende Listen werden klar genannt
- nur bestaetigte Listen fliessen ein
- EOS behauptet keine vollstaendige Aufgabenbasis

## E2E-10: Calendar- oder State-Failure

### Ziel
Verifizieren, dass produktive Sends fail-closed enden.

### Erwartung
- kein Send bei Calendar-Read-Fehler
- kein Send bei State-Fehler
- sauberer `failed`- oder `skipped`-Pfad
- kein spekulativer Ersatzinhalt

## E2E-11: Unklarer Delivery-Ausgang

### Ziel
Verifizieren, dass unbekannte Provider-Ergebnisse nicht als Erfolg gewertet werden.

### Erwartung
- Status nicht auf `sent`
- kein automatischer Retry bei unklarem Ausgang
- Fall wird fuer manuelle Pruefung geloggt

## E2E-12: Berlin-Zeitbasis

### Ziel
Verifizieren, dass Trigger und Fenster auf `Europe/Berlin` basieren.

### Erwartung
- `evening_reset` zielt immer auf morgen in Berlin
- `weekly_sync` nutzt kommende Woche Montag-bis-Montag
- Logs enthalten Berlin- und UTC-Zeit
- DST-Umstellung verschiebt die fachlichen Fenster nicht falsch

## Go-Live-Minimum
Vor produktiver V2-Freigabe sollten mindestens erfolgreich bestaetigt sein:
- ein Tasks Live Read
- ein Tasks Live Create
- ein Tasks Live Complete
- ein `evening_reset` Dry-Run
- ein `evening_reset` Live-Lauf
- reale `green`, `yellow` und `red` Coaching-Beispiele
- ein `weekly_sync` Dry-Run oder Live-Test
- ein Idempotenztest
- ein Partial-Failure-Test fuer Tasks
- ein Berlin-Zeitbasis-Test
