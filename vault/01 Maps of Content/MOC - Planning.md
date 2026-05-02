# MOC - Planning

Diese Seite ist der Einstieg in die Planungslogik von EOS.

Ziel:
- verstehen, wie EOS Tages- und Wochenplanung strukturiert
- zwischen bestätigtem Verhalten, definierter Policy und offenen Punkten unterscheiden
- direkt in die relevanten technischen Spezifikationen springen

Technische Wahrheit bleibt in `docs/`.
Diese MOC-Datei ist die Navigations- und Orientierungsschicht.

---

## 1. Wofür die Planungsschicht da ist

Die Planungsschicht ist das operative Herz von EOS.

Sie verbindet:
- harte Termine
- offene Aufgaben
- Deep Work
- Sport
- Routinen
- Überladungsbewertung

Ohne diese Schicht wäre EOS nur:
- Kalenderleser
- Aufgabenanzeige
- Reminder-System

Mit dieser Schicht wird EOS zu einem:
- Planungsassistenten
- Tagesstrukturierer
- Überladungsdetektor
- bounded coach für echte Arbeits- und Sporttage

---

## 2. Was aktuell bestätigt ist

### Grundstruktur
EOS hat eine definierte Daily- und Weekly-Planning-Logik.

### Daily Planning
Das Daily Planning ist in dieser Reihenfolge gedacht:

1. harte Termine heute
2. Top-3 Aufgaben
3. Deep-Work-Block
4. Sportblock
5. Nicht vergessen
6. Warnung bei Überladung

### Weekly Planning
Das Weekly Planning ist in dieser Reihenfolge gedacht:

1. harte Termine
2. Arbeitstage
3. fixe Sportkurse
4. gesetzte flexible Blöcke
5. gekürzte oder verschobene Ziele
6. Warnung bei Überladung
7. Nicht vergessen

### Zeitbasis
- Europe/Berlin ist die operative Planungszeit
- Kalender ist die Primärquelle für harte Termine

### Deep Work
- Standardblock = 60 Minuten Fokus
- danach 10 Minuten Spaziergang
- nicht 90 Minuten Standardblock

### Belastungstage
- Donnerstag bis Samstag 05:45 bis 14:00 gelten als harte Belastungstage

---

## 3. Was planerisch als Regel schon feststeht

## Harte Prioritäten
Bei Kollisionen gilt grundsätzlich:

1. harte Termine
2. Arbeit
3. fixe Sportkurse
4. Mindest-Routine
5. Deep Work
6. dringende Kurzaufgaben
7. sonstige manuelle Aufgaben
8. Gym
9. Cardio
10. volle Routine

## Belastungslogik
- an harten Arbeitstagen nur konservative Zusatzplanung
- Arbeitstag plus fixer Sport = meist kein weiterer harter Block
- fragmentierter Tag = kein echter Deep-Work-Block
- lieber ein sinnvoller Hauptblock als künstliche Überplanung

## Sportlogik
- fixer Kurs aus Calendar = harter Sportblock
- Gym = flexibel
- Cardio = flexibel
- Calisthenics nicht automatisch doppelt

## Routine-Logik
Mindest-Routine bleibt.
Volle Routine darf gekürzt werden.

---

## 4. Was nur teilweise verifiziert ist

### Assistant-Schicht
Die Policy ist definiert, aber nicht in allen Live-Ausgaben sauber angewendet.

Bekannte Schwachstellen aus früheren Outputs:
- Platzhalter bei Top-3
- zu generische Empfehlungen
- teilweise unvollständige Routinen
- Packlisten ohne saubere explizite Quelle
- zeitweise falscher Deep-Work-Blockstandard

### Bounded Coach Mode
Definiert ist:
- genau eine konkrete Empfehlung
- genau eine Warnung, wenn nötig
- keine Guru-/Research-Drift

Noch nicht voll ausgehärtet:
- alle Daily-/Weekly-Ausgaben im echten Betrieb
- strikte Kürze und operative Dichte
- saubere Begrenzung des Coach-Anteils

---

## 5. Was noch offen ist

### Live-Härtung der Planungsoutputs
Die größte offene Lücke ist nicht die Policy auf Papier, sondern:
- konsistente Anwendung im echten Assistant-Output
- keine Platzhalter
- keine impliziten Halluzinationen
- klare Unterscheidung zwischen:
  - echten Daten
  - Annahmen
  - offenen Lücken

### Tasks als echte Primärquelle
Solange Google Tasks nicht live integriert ist, bleibt Planung teilweise auf:
- Chat-Input
- manuelle Erfassung
- temporäre Strukturierung
angewiesen

### Scheduler-Kopplung
Evening Briefing, Weekly Sync und weitere Jobs brauchen diese Planungslogik als Basis.
Die Planungsschicht muss also auch scheduler-tauglich und idempotent formulierbar sein.

---

## 6. Planungsprinzipien

### Principle 1: Real calendar first
Planung orientiert sich zuerst an realen harten Terminen.

### Principle 2: One clear recommendation
EOS soll nicht viele Tipps geben, sondern eine konkrete Verbesserung.

### Principle 3: No fake precision
Wenn Daten fehlen, soll EOS das sagen.
Keine Kalenderfantasie, keine Pseudo-Sicherheit.

### Principle 4: Capacity over ambition
Planung orientiert sich an realistischer Kapazität, nicht an Wunschdichte.

### Principle 5: Morning is not sacred by default
Für dein reales Leben mit Frühschichten ist ein Vorabend-Briefing oft wertvoller als ein aggressives Frühbriefing.

---

## 7. Daily Planning im Zielbild

Ein gutes Daily Planning von EOS soll:

- harte Termine klar auflisten
- konkrete Top-3 nennen
- Deep Work realistisch setzen
- Sport und Vorbereitung berücksichtigen
- Überladung direkt markieren
- maximal eine konkrete Empfehlung geben

Ein schlechtes Daily Planning wäre:
- vage
- platzhalterhaft
- moralisch oder motivierend statt operativ
- research-lastig
- zeitlich unrealistisch

---

## 8. Weekly Planning im Zielbild

Ein gutes Weekly Planning von EOS soll:

- die Woche strukturell lesbar machen
- Arbeitstage und Sport real mitdenken
- flexible Blöcke sinnvoll verteilen
- Überladung und schlechte Verteilung benennen
- Wochenziele realistisch reduzieren, wenn nötig

Ein schlechtes Weekly Planning wäre:
- nur ein Kalenderdump
- ohne Engstellenanalyse
- ohne Kürzungslogik
- ohne konkrete Struktur-Empfehlung

---

## 9. Zusammenspiel mit anderen Schichten

## Planning + Calendar
- Calendar = harte Zeit
- Planning organisiert darum herum

## Planning + Tasks
- Tasks liefern offene operative Arbeit
- Planning priorisiert und verteilt sie

## Planning + Scheduler
- Scheduler nutzt Planning-Logik für Briefings und Reviews
- daher muss Planning auch maschinenlesbar und stabil genug sein

## Planning + Vault
- Vault speichert Kontext, Daily Notes, Brain Dumps
- Vault ist nicht Primärquelle für harte Termine oder aktive Tasks
- Vault kann Planung reflektieren, aber nicht ersetzen

---

## 10. Failure-Verhalten

Wenn Calendar fehlt:
- keine harte Zeitlogik vortäuschen
- offen sagen, dass harte Termine gerade nicht zuverlässig lesbar sind

Wenn Tasks fehlen:
- degradieren auf Chat-Tasks
- das klar kennzeichnen

Wenn Daten unvollständig sind:
- konkrete Lücke benennen
- keine künstlich präzise Planung ausgeben

Wenn der Tag überladen ist:
- nicht alles reinquetschen
- aktiv reduzieren
- explizit warnen

---

## 11. Wichtigste technische Dokumente

### Planungskern
- [docs/policy/EOS-PLANNING-POLICY-v1.md](../../docs/policy/EOS-PLANNING-POLICY-v1.md)
- [docs/policy/EOS-OPERATING-CONTRACT-v1.md](../../docs/policy/EOS-OPERATING-CONTRACT-v1.md)
- [docs/policy/EOS-ALIASES-v1.md](../../docs/policy/EOS-ALIASES-v1.md)
- [docs/policy/EOS-ACTION-CONTRACT-v1.md](../../docs/policy/EOS-ACTION-CONTRACT-v1.md)
- [docs/policy/EOS-COACHING-ENGINE-v1.md](../../docs/policy/EOS-COACHING-ENGINE-v1.md)
- [docs/policy/EOS-ROUTINES-AND-CHECKLISTS-v1.md](../../docs/policy/EOS-ROUTINES-AND-CHECKLISTS-v1.md)

### Scheduler-nahe Planung
- [docs/scheduler/EOS-SCHEDULER-POLICY-v1.md](../../docs/scheduler/EOS-SCHEDULER-POLICY-v1.md)
- [docs/scheduler/EOS-EVENING-RESET-v1.md](../../docs/scheduler/EOS-EVENING-RESET-v1.md)
- [docs/scheduler/EOS-REVIEW-ENGINE-v1.md](../../docs/scheduler/EOS-REVIEW-ENGINE-v1.md)

### Integrationen
- [docs/integrations/EOS-CALENDAR-WRITE-E2E-v1.md](../../docs/integrations/EOS-CALENDAR-WRITE-E2E-v1.md)
- [docs/integrations/EOS-TASKS-INTEGRATION-v1.md](../../docs/integrations/EOS-TASKS-INTEGRATION-v1.md)

---

## 12. Nächste Planungsschritte

### Kurzfristig
1. Planning-Outputs weiter härten
2. keine Platzhalter mehr zulassen
3. bounded coach mode sauber durchziehen
4. Google Tasks v1 anbinden
5. Evening Reset auf echter Planungslogik aufsetzen

### Danach
6. Weekly Review mit echtem Verlauf koppeln
7. Scheduler-Jobs produktiv aktivieren
8. Planung mit Vault-Writeback vorsichtig verbinden

---

## 13. Wie du diese Seite nutzt

Wenn du wissen willst:

### „Wie plant EOS grundsätzlich?“
- lies Abschnitt 1 bis 6

### „Was ist schon stabil, was noch nicht?“
- lies Abschnitt 2 bis 5

### „Wo ist die technische Wahrheit dazu?“
- springe zu Abschnitt 11

### „Was ist als Nächstes dran?“
- lies Abschnitt 12

---

## 14. Verbindliche Entscheidungen

- [[ADR - Calendar as Source of Truth]] — Daily Planning und Weekly Planning lesen Kalender live; keine manuell kopierten Listen.
- [[ADR - Tasks as Source of Truth]] — Tasks-Kontext kommt aus Google Tasks. Chat-Tasks sind nur Capture-Einstieg und Fallback bei Auth-Ausfall.