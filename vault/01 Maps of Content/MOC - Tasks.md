# MOC - Tasks

Diese Seite ist der Einstieg in die Task-Schicht von EOS.

Ziel:
- verstehen, wie EOS mit Aufgaben umgehen soll
- zwischen aktuellem Ist-Zustand, Zielbild und offenen Punkten unterscheiden
- direkt in die relevanten technischen Spezifikationen springen

Technische Wahrheit bleibt in `docs/`.
Diese MOC-Datei ist die Navigations- und Orientierungsschicht.

---

## 1. Wofür die Task-Schicht da ist

Die Task-Schicht verbindet Planung mit echter Ausführung.

Ohne saubere Task-Schicht:
- EOS kann planen
- EOS kann priorisieren
- EOS kann warnen
- aber EOS arbeitet nur mit Chat-Input oder temporären Listen

Mit sauberen Tasks:
- offene Aufgaben haben eine echte Primärquelle
- Daily Planning und Weekly Planning greifen auf reale Aufgaben zu
- Evening Reset und Reviews können offen gebliebene Aufgaben sinnvoll behandeln
- Brain Dumps können operative Punkte sauber extrahieren

---

## 2. Was aktuell bestätigt ist

### Manuelle Task-Erfassung
- EOS kann Aufgaben aus Chat-Nachrichten aufnehmen
- EOS kann diese Aufgaben in Daily Planning und Weekly Planning einbauen
- EOS kann grob priorisieren und offene Punkte benennen

### Planungslogik
- Daily Planning berücksichtigt Aufgaben grundsätzlich
- Weekly Planning berücksichtigt Aufgaben grundsätzlich
- Überladung kann auf Basis von Aufgaben + Kalender benannt werden

### Rollenmodell
- Google Tasks ist als Zielsystem für aktive offene Aufgaben gesetzt
- Vault ist nicht die Primärquelle für aktive operative Tasks
- lokaler State ist nicht die Primärquelle für aktive operative Tasks

---

## 3. Was aktuell nur teilweise vorhanden ist

### Task-Logik ohne echtes Backend
Im Moment ist die Task-Verarbeitung funktional eher:
- Chat-Input
- temporäre Strukturierung
- operative Nutzung im Plan

Noch nicht vollständig gehärtet:
- konsistente Listenstruktur
- Live-Synchronisation
- Abschlusslogik
- Partial Failure Verhalten
- saubere Read/Create/Complete-Pfade

### Brain-Dump-Extraktion
Brain Dumps können konzeptionell in Tasks zerlegt werden.
Noch nicht voll produktiv:
- automatische Extraktion
- Routing in das echte Task-System
- Dublettenvermeidung
- Review-sichere Nachverfolgung

---

## 4. Was noch offen ist

### Google Tasks Integration
Google Tasks ist als Zielsystem definiert, aber noch nicht voll produktiv integriert.

Offen:
- finaler headless-sicherer Auth-Pfad
- minimaler produktiver V1-Umfang
- Live-E2E für:
  - Read
  - Create
  - Complete
- robustes Fehlerverhalten im laufenden EOS-Betrieb

### Task-State im Derived Layer
Es ist architektonisch sinnvoll, abgeleitete Task-Snapshots zu speichern für:
- Reviews
- Evening Reset
- Verlauf
- Job-State

Aber:
- das darf nie die Primärwahrheit ersetzen

---

## 5. Zielbild für Tasks v1

Tasks v1 soll bewusst minimal sein.

### Kernfunktionen
- offene Tasks lesen
- neue Task anlegen
- Task als erledigt markieren
- Listen sauber zuordnen

### Noch nicht in Tasks v1
- aggressive Auto-Rescheduling-Logik
- komplexe Subtask-Systeme
- Bulk-Operationen
- automatische Prioritätsmagie
- mehrdeutige Auto-Verschiebung ohne klare Freigabe

---

## 6. Empfohlene Listenstruktur

Die empfohlene operative Struktur ist:

- `Inbox`
- `Next`
- `Waiting`
- `This Week`

### Bedeutung

#### Inbox
- unsortierte neue Aufgaben
- Rohinput
- braucht spätere Klärung

#### Next
- konkrete nächste Schritte
- kurzfristig bearbeitbar

#### Waiting
- wartet auf andere Personen oder externe Faktoren

#### This Week
- diese Woche bewusst relevant
- nicht automatisch alles, sondern kuratierte Wochenebene

---

## 7. Task-Regeln für EOS

### Regel 1
Google Tasks soll die Primärquelle für aktive offene Aufgaben werden.

### Regel 2
Chat-Tasks sind Übergangsinput oder Capture-Einstieg, nicht die Dauerlösung.

### Regel 3
Vault ist für:
- Brain Dumps
- Daily Notes
- Wissen
- Verlauf
nicht für die operative Primärhaltung offener Tasks.

### Regel 4
EOS soll Aufgaben nicht künstlich aufblasen.
Keine Pseudo-Priorisierung ohne Grundlage.

### Regel 5
Bei fehlendem Task-Zugriff muss EOS degradieren, nicht schweigen.
Dann gilt:
- Planung mit Chat-Tasks
- klare Warnung, dass Live-Tasks nicht verfügbar sind

---

## 8. Zusammenspiel mit anderen Schichten

## Calendar + Tasks
- Calendar = harte Zeit
- Tasks = offene Arbeit
- EOS plant Tasks um harte Kalenderrealität herum

## Tasks + Vault
- Brain Dump im Vault
- operative Punkte werden in Tasks extrahiert
- Daily Notes referenzieren Aufgaben, ersetzen sie aber nicht

## Tasks + Scheduler
- Evening Reset braucht offene Aufgaben
- Weekly Review braucht Aufgabenverlauf
- Reminder und Briefings dürfen auf Tasks zugreifen, aber nicht still Tasks halluzinieren

---

## 9. Failure-Verhalten

Wenn Google Tasks nicht erreichbar ist:
- EOS darf nicht so tun, als hätte er echte Live-Tasks
- EOS soll sauber degradieren
- EOS soll klar sagen, dass Task-Daten gerade nicht live verfügbar sind
- EOS soll weiterhin Kalender-basierte Planung liefern können

Wenn Auth kaputt ist:
- Fehler loggen
- keine stillen Annahmen treffen
- keine Phantom-Tasks erzeugen

Wenn eine Aktion fehlschlägt:
- keine Success-Meldung ohne echten Abschluss
- Read-after-write oder sauberer Fehlerstatus

---

## 10. Was EOS mit Tasks tun soll

### Read
- offene Aufgaben aus definierter Liste lesen

### Create
- klare neue Aufgabe anlegen

### Complete
- Aufgabe als erledigt markieren

### Planning Use
- Top-3 bestimmen
- Wochenfokus ableiten
- Überladung beurteilen

### Noch nicht standardmäßig
- eigenmächtiges Umsortieren
- automatische Löschung
- automatische Massenverschiebung

---

## 11. Wichtigste technische Dokumente

### Kernintegration
- [docs/integrations/EOS-TASKS-INTEGRATION-v1.md](../../docs/integrations/EOS-TASKS-INTEGRATION-v1.md)
- [docs/integrations/EOS-TASKS-ACTION-CONTRACT-v1.md](../../docs/integrations/EOS-TASKS-ACTION-CONTRACT-v1.md)
- [docs/tests/EOS-TASKS-LIVE-E2E-v1.md](../../docs/tests/EOS-TASKS-LIVE-E2E-v1.md)

### Architektur und Verhalten
- [docs/architecture/EOS-V2-TECHNICAL-SPEC.md](../../docs/architecture/EOS-V2-TECHNICAL-SPEC.md)
- [docs/policy/EOS-OPERATING-CONTRACT-v1.md](../../docs/policy/EOS-OPERATING-CONTRACT-v1.md)
- [docs/policy/EOS-PLANNING-POLICY-v1.md](../../docs/policy/EOS-PLANNING-POLICY-v1.md)

### Verwandte Flüsse
- [docs/scheduler/EOS-EVENING-RESET-v1.md](../../docs/scheduler/EOS-EVENING-RESET-v1.md)
- [docs/scheduler/EOS-REVIEW-ENGINE-v1.md](../../docs/scheduler/EOS-REVIEW-ENGINE-v1.md)
- [docs/vault/EOS-BRAIN-DUMP-v1.md](../../docs/vault/EOS-BRAIN-DUMP-v1.md)

---

## 12. Nächste Task-Schritte

### Kurzfristig
1. finalen Integrationspfad festziehen
2. Tasks v1 minimal implementieren
3. Live-E2E für Read / Create / Complete grün bekommen
4. Partial Failure Verhalten prüfen

### Danach
5. Evening Reset mit echten offenen Tasks koppeln
6. Weekly Review mit Task-Verlauf koppeln
7. Brain-Dump-zu-Task-Routing vorsichtig automatisieren

---

## 13. Wie du diese Seite nutzt

Wenn du wissen willst:

### „Wie soll EOS mit Aufgaben umgehen?“
- lies Abschnitt 1 bis 8

### „Was ist schon echt, was noch offen?“
- lies Abschnitt 2 bis 4

### „Wo ist die technische Wahrheit dazu?“
- springe zu Abschnitt 11

### „Was ist als Nächstes dran?“
- lies Abschnitt 12

---

## 14. Verbindliche Entscheidungen

- [[ADR - Tasks as Source of Truth]] — Google Tasks ist die Primärquelle für aktive offene Aufgaben. Formalisiert die Rolle, die in Abschnitt 2, 5 und 7 beschrieben ist.
- [[ADR - Calendar as Source of Truth]] — hart planbare Zeit bleibt im Kalender. Tasks werden um diese Realität herum geplant.