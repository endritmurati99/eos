# EOS Live E2E Tests v1

## Ziel
Belastbare Live-Ende-zu-Ende-Prüfung für EOS statt bloßer Architekturannahmen.

## Testprinzip
Nur Live-E2E-Pfade zählen als produktive Verifikation.

## E2E-1: Telegram -> Google Calendar -> Daily Plan
### Ziel
Prüfen, ob EOS harte Termine live aus Google Calendar liest und in korrekter Reihenfolge in die Tagesplanung überführt.

### Eingabe
`Plane mir heute den Tag`

### Erwartung
- Harte Termine werden live gelesen
- mindestens `primary` und `Sport` werden berücksichtigt
- Zeitzone `Europe/Berlin`
- Antwort im festen Daily-Planning-Format
- keine Kalenderhalluzinationen

## E2E-2: Telegram -> Weekly Aggregation -> Weekly Plan
### Ziel
Prüfen, ob EOS harte Termine, Arbeitstage, fixe Sportkurse und flexible Blöcke korrekt über die Woche aggregiert.

### Eingabe
`Plane mir die Woche`

### Erwartung
- Wochenformat in fixer Reihenfolge
- gesetzte flexible Blöcke sichtbar
- gekürzte/verschobene Ziele klar benannt
- Überladung explizit markiert

## E2E-3: Telegram -> Manual Tasks -> Daily Prioritization
### Ziel
Prüfen, ob EOS manuelle Aufgaben per Chat als Übergangslösung korrekt priorisiert.

### Eingabe
```text
Plane mir heute den Tag.

Offene Aufgaben:
- ...
- ...
- ...
```

### Erwartung
- Top-3 werden plausibel priorisiert
- Deep-Work-Block nur bei realistischer Kapazität
- Nicht vergessen enthält nur relevante Prep-/Carry-Punkte

## E2E-4: Telegram -> Google Tasks (später)
### Ziel
Produktive Aufgabenintegration nach Phase 1.

### Erwartung
- OAuth2 + Refresh-Token-basierter Zugriff
- Live-Read und Live-Write funktionieren
- keine doppelte Wahrheit zwischen Chat und Tasks

## E2E-5: Telegram -> Obsidian Vault (später)
### Ziel
Brain Dump / Daily Note Write in echten Vault-Pfad.

### Erwartung
- Vault-Pfad ist real verifiziert
- Datei erscheint am erwarteten Ort
- keine Permission-Fehler
- keine Ordnerinflation

## Betriebschecks
### Log-Check
- Container-/Runtime-Logs auf Zugriffs- oder Permission-Fehler prüfen
- bei Vault-Integration insbesondere auf Schreibfehler achten

### API-Check
- Google Calendar: echter Tages- oder Wochenplan mit Live-Daten
- Google Tasks: bei späterer Integration echte Aufgaben lesen/schreiben

### File-Check
- bei Vault-Integration prüfen, ob die erwartete Markdown-Datei real im Zielpfad entsteht

## Readiness-Kriterien für Phase 1
- 7 reale Nutzungstage
- keine Kalenderhalluzinationen
- Pläne bleiben kurz, operativ und korrekt
- Überladung wird sauber markiert
- Arbeit, Sport, Routinen und Deep Work werden realistisch balanciert
