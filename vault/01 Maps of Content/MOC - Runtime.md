# MOC - Runtime

Diese Seite ist der Einstieg in den Runtime- und Betriebszustand von EOS.

Ziel:
- verstehen, was EOS technisch zum Laufen bringt
- zwischen Spezifikation, laufender Runtime und bekannten Betriebsproblemen unterscheiden
- direkt in die relevanten technischen Dokumente springen

Technische Wahrheit bleibt in `docs/`.
Diese MOC-Datei ist die Navigations- und Orientierungsschicht.

---

## 1. Wofür die Runtime-Schicht da ist

Die Runtime-Schicht entscheidet darüber, ob EOS nur auf dem Papier gut aussieht oder im echten Betrieb funktioniert.

Sie umfasst insbesondere:
- laufenden OpenClaw-Dienst
- Container-Umgebung
- Environment-Variablen
- Auth- und Token-Zugriffe
- Scheduler-Ausführung
- Logging
- Dateizugriffe
- Rechte und Persistenz

Ohne stabile Runtime:
- Specs helfen nur begrenzt
- Bots antworten inkonsistent
- Integrationen laufen nur im Terminal, aber nicht im echten Dienst
- Scheduler-Jobs senden doppelt oder gar nicht

---

## 2. Was aktuell bestätigt ist

### Betriebsmodell
- EOS läuft als `personal-assistant` im OpenClaw-Kontext
- VS-Code-SSH ist der bevorzugte Operator-Pfad für echte Änderungen und Prüfungen
- `docs/` und `vault/` liegen im selben Workspace und sind operatorisch nutzbar

### Grundsätze
- Workspace ist Default-Arbeitsbereich, aber keine harte Sandbox
- Europe/Berlin ist die operative Zeitbasis
- Secrets gehören nicht in Markdown-Dateien
- Runtime-Probleme müssen im echten Dienst geprüft werden, nicht nur in Shell-Tests

### Dokumentationsstand
- Runtime-Fix-Dokumente existieren
- Open-Issues-Struktur existiert
- Scheduler-Härtung ist spezifiziert, aber noch nicht produktiv ausgerollt

---

## 3. Was nur teilweise verifiziert ist

### Google Calendar Runtime Path
Technisch wurden Read/Write-Pfade bereits in kontrollierten Kontexten verifiziert.

Nicht vollständig ausgehärtet war bzw. ist:
- derselbe Zugriff im echten laufenden Bot-Prozess
- konsistente Environment-Weitergabe
- Keyring-Unlock im Container-/Dienstkontext
- saubere Reproduzierbarkeit nach Restart

### Vault als Live-Backend
Die Dateistruktur ist vorhanden.
Noch nicht vollständig verifiziert:
- finaler produktiver Mount
- dauerhafte Schreibpfade
- Writeback-Qualität
- Verhalten nach Neustarts / Container-Recreate

### Scheduler Runtime
Spezifikation vorhanden.
Noch nicht produktiv verifiziert:
- systemd-/cron-Ausführung
- Dry-Run im echten Deployment
- Idempotenz im Live-Betrieb
- Logging-Pfade
- Retry-/Failure-Verhalten

---

## 4. Die wichtigsten Runtime-Probleme

### 1. Unterschied zwischen Terminal und Bot-Runtime
Ein Befehl kann im Terminal funktionieren, aber im laufenden EOS-Bot fehlschlagen.

Typische Ursache:
- manuell gesetzte ENV im Shell-Test
- aber fehlende ENV im echten Dienststart

### 2. Keyring- und Token-Probleme
Wenn Auth gespeichert ist, aber der laufende Dienst sie nicht aufschließen kann:
- Read scheitert
- Write scheitert
- Scheduler-Jobs scheitern indirekt
- EOS wirkt „dumm“, obwohl das Problem rein operativ ist

### 3. Berechtigungen und Persistenz
Typische Probleme:
- falscher Eigentümer auf Dateien oder Verzeichnissen
- Container kann lesen, aber nicht schreiben
- Zustand geht nach Neustart verloren
- testweise Pfade funktionieren, produktive Pfade nicht

### 4. Zeitbasis
Wenn Host, Container, App und Kalender unterschiedliche Zeitannahmen haben:
- Reminder feuern falsch
- „morgen“ wird falsch interpretiert
- Weekly Sync läuft zum falschen Zeitpunkt
- Daily-/Evening-Logik analysiert den falschen Tag

---

## 5. Runtime-Prinzipien

### Principle 1: Real service first
Immer den echten laufenden Dienst prüfen, nicht nur ad hoc Shell-Kommandos.

### Principle 2: One runtime source
Secrets und Runtime-ENV sollen an einer sauberen Quelle hängen, nicht verteilt in mehreren Halbquellen.

### Principle 3: No fake green
Ein grüner Terminal-Test reicht nicht, wenn der Bot-Pfad rot ist.

### Principle 4: Persist state intentionally
Wichtiger Zustand muss Reboots und Recreates überleben.

### Principle 5: Logs are part of the product
Ohne Logs keine verlässliche Diagnose.

---

## 6. Was in die Runtime gehört

### Environment
Beispiele:
- Zeitzone
- Auth-relevante Variablen
- Pfade auf Token-/Secret-Dateien
- State-DB-Pfad
- ggf. Scheduler-Konfiguration

### Persistenter Zustand
Beispiele:
- Tokens
- Keyring-Dateien
- lokale State-Datenbank
- Job-Historie
- ggf. Vault-Mounts

### Operator-Werkzeuge
- VS-Code-SSH
- Terminal
- Claude Code / Codex
- Logs
- Datei- und Rechteprüfung

---

## 7. Was ausdrücklich nicht in die Runtime-Doku gehört

Diese MOC ist kein Platz für:
- Secrets
- echte Tokens
- Passwörter
- kopierte `.env` Inhalte
- spekulative Hostpfade als Fakten

Die Runtime-Schicht braucht:
- saubere Regeln
- Prüfpfade
- Runbooks
nicht: geheime Inhalte im Markdown

---

## 8. Zusammenspiel mit anderen Schichten

## Runtime + Calendar
Kalender-Read/Write ist nur dann produktiv, wenn:
- Auth
- Keyring
- ENV
- Dienstkontext
stabil sind

## Runtime + Scheduler
Scheduler-Jobs brauchen:
- korrekte Zeitbasis
- Zugriff auf aktuelle Daten
- State
- Logging
- Idempotenz

## Runtime + Vault
Vault-Nutzung im Betrieb hängt an:
- Schreibrechten
- persistenter Ablage
- sauberem Pfadmodell
- nicht an schöner Theorie

## Runtime + Tasks
Google Tasks wird nur dann produktiv nutzbar, wenn:
- Auth headless stabil läuft
- Tokens sicher liegen
- Partial Failure sauber behandelt wird

---

## 9. Failure-Verhalten

Wenn eine Runtime-Komponente fehlschlägt, muss EOS:
- den Fehler sauber loggen
- keine falsche Erfolgsmeldung erzeugen
- möglichst degradiert weiterarbeiten
- klar zwischen:
  - verfügbar
  - teilweise verfügbar
  - nicht verfügbar
unterscheiden

Beispiele:
- Calendar blockiert → keine harte Kalenderfantasie
- Tasks blockiert → weiter mit Chat-Tasks, aber klar markiert
- Scheduler blockiert → keine „enabled“-Behauptung

---

## 10. Wichtigste technische Dokumente

### Runtime
- [docs/runtime/README-RUNTIME-FIX.txt](../../docs/runtime/README-RUNTIME-FIX.txt)
- [docs/runtime/EOS-RUNTIME-FIX-PROMPT.txt](../../docs/runtime/EOS-RUNTIME-FIX-PROMPT.txt)
- [docs/runtime/EOS-RUNTIME-FIX-INSTRUCTIONS.txt](../../docs/runtime/EOS-RUNTIME-FIX-INSTRUCTIONS.txt)
- [docs/runtime/EOS-RUNTIME-CHECKLIST.txt](../../docs/runtime/EOS-RUNTIME-CHECKLIST.txt)
- [docs/runtime/EOS-RUNTIME-FIX-COMMANDS.txt](../../docs/runtime/EOS-RUNTIME-FIX-COMMANDS.txt)
- [docs/runtime/docker-compose-snippets.txt](../../docs/runtime/docker-compose-snippets.txt)

### Architektur und Betrieb
- [docs/architecture/EOS-ARCHITECTURE-v1.md](../../docs/architecture/EOS-ARCHITECTURE-v1.md)
- [docs/architecture/EOS-V2-TECHNICAL-SPEC.md](../../docs/architecture/EOS-V2-TECHNICAL-SPEC.md)
- [docs/tests/EOS-LIVE-E2E-TESTS-v1.md](../../docs/tests/EOS-LIVE-E2E-TESTS-v1.md)

### Status und Blocker
- [../00 Home/EOS Current Status.md](../00%20Home/EOS%20Current%20Status.md)
- [../00 Home/EOS Open Issues.md](../00%20Home/EOS%20Open%20Issues.md)

---

## 11. Nächste Runtime-Schritte

### Kurzfristig
1. echten Dienstpfad sauber prüfen
2. Environment-Quelle konsolidieren
3. Keyring-/Auth-Probleme sauber auflösen
4. Persistenzpfade prüfen
5. Logging und Dry-Run-Pfade für Scheduler vorbereiten

### Danach
6. Google Tasks headless stabilisieren
7. Derived State produktiv einführen
8. Scheduler-Jobs kontrolliert aktivieren

---

## 12. Wie du diese Seite nutzt

Wenn du wissen willst:

### „Warum funktioniert EOS im Chat nicht, obwohl der Test im Terminal grün war?“
- lies Abschnitt 4 und 5

### „Welche Runtime-Probleme sind typisch?“
- lies Abschnitt 4 und 9

### „Wo ist die technische Wahrheit dazu?“
- springe zu Abschnitt 10

### „Was ist als Nächstes operativ dran?”
- lies Abschnitt 11

---

## 13. Aktuelle Systembestandsaufnahme

Vollständige Bestandsaufnahme des laufenden Systems (Agents, Cron-Jobs, was funktioniert, was blockiert ist):

→ [[EOS-SYSTEM-OVERVIEW]] in `14 Knowledge/`

Wichtige Beobachtung (2026-04-22): Der Sport-Bag-Reminder-Cron hat `gog` erfolgreich genutzt und den Calisthenics-Termin gefunden. Das zeigt, dass Kalender-Lesezugriff in der bestehenden EOS-Haupt-Session funktioniert. BLK-001/BLK-002 betreffen nur Szenarien ohne TTY (isolierte Sessions, Cold-Start).