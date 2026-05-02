# EOS Brain Dump v1

## Zweck
Diese Spezifikation definiert den vault-first Brain-Dump-Flow fuer EOS.
Jeder Brain Dump wird zuerst als rohe Markdown-Quelle im Vault gesichert und erst danach triagiert, verlinkt und fuer moegliche Handoffs markiert.

## Scope-Grenze
- Diese Spezifikation beschreibt nur Vault-Artefakte und dokumentierte Handoff-Marker.
- Sie spezifiziert keine Google-Tasks-Integration, keine Calendar-Write-Logik, keine Scheduler-Logik und keine Runtime-Implementierung.
- `task_candidate` und `calendar_candidate` sind dokumentierte Marker im Vault, keine direkten externen Writes.

## Ergebnisartefakte
Jeder Brain Dump kann genau diese Artefakte erzeugen:

- `brain_dump_note`
- `daily_note_link`
- `project_note_link`
- `idea_note_link`
- `task_candidate`
- `calendar_candidate`

Pflichtartefakt pro Brain Dump:
- genau eine rohe `brain_dump_note`

## Verbindlicher Flow
### 1. Roh-Capture anlegen
Fuer jeden Brain Dump wird zuerst genau eine `brain_dump_note` unter `00 Inbox/YYYY-MM-DD-HHmm-brain-dump.md` angelegt.

Regeln:
- ein Brain Dump = genau eine Source Note
- auch bei mehreren Themen bleibt die Source Note eine einzelne Quelle
- der Capture-Zeitpunkt wird in der Note dokumentiert

### 2. Rohtext unveraendert bewahren
Der Abschnitt `Rohdump` enthaelt den Brain Dump unveraendert oder so nah wie moeglich am Original.

Regeln:
- keine fruehe Umsortierung des Rohtextes
- keine vorzeitige Verdichtung als Ersatz fuer den Rohdump
- Unsicherheit, Ambivalenz und Widersprueche bleiben sichtbar

### 3. Minimale Summary ergaenzen
Nach der Roh-Capture wird eine kurze Summary ergaenzt.

Regeln:
- kurz
- nur zur spaeteren Orientierung
- keine Erfindung von Deadlines, Prioritaeten oder Commitments

### 4. In Daily Note verlinken
Jeder Brain Dump wird genau einmal in die zugehoerige `daily_note` verlinkt:
- `01 Daily Notes/YYYY-MM-DD.md`

Die Daily Note ist der Tages-Hub fuer:
- den Link zur Source Note
- sichtbare Tageskontext-Verankerung
- spaetere Rueckverfolgung

### 5. In Projekt- oder Ideennoten routen
Nach der Daily-Note-Verlinkung wird entschieden, ob zusaetzliche Zielnoten noetig sind.

Route zu `project_note`, wenn klar vorliegt:
- aktives Commitment
- laufende Bearbeitung
- klarer Outcome
- belastbarer naechster Schritt

Route zu `idea_note`, wenn klar vorliegt:
- spekulativer Gedanke
- offene Richtung
- moegliches Experiment
- noch kein aktiver naechster Schritt

Regeln:
- ohne klares Commitment lieber Idee als Projekt
- eine bestehende passende Note wird verlinkt statt Duplikate anzulegen
- ein Brain Dump kann mehrere Projekt- oder Ideenlinks haben, bleibt aber trotzdem genau eine Source Note

### 6. Handoff-Marker dokumentieren
Brain Dumps duerfen Kandidaten fuer spaetere externe Systeme dokumentieren, ohne diese Systeme selbst zu veraendern.

Standard-Marker:
- `[task_candidate] ...`
- `[calendar_candidate] ...`

Bedeutung:
- `task_candidate` = aus dem Brain Dump ableitbare Aufgabe fuer spaetere Task-Behandlung
- `calendar_candidate` = termin- oder blockrelevanter Kandidat fuer spaetere Kalenderpruefung

Regeln:
- Marker dokumentieren nur Kandidaten
- Marker sind keine automatische Freigabe fuer externe Writes
- fehlende Daten bleiben als offen markiert statt erfunden zu werden

### 7. Abschluss der Triage und Archivierung
Eine `brain_dump_note` bleibt in `00 Inbox`, solange die Triage nicht abgeschlossen ist.

Eine `brain_dump_note` wird nach `90 Archive/YYYY-MM-DD-HHmm-brain-dump.md` verschoben, wenn alles Erforderliche erledigt ist:
- Rohdump erhalten
- Summary vorhanden
- Daily-Note-Link gesetzt
- notwendige Projekt-/Ideenlinks gesetzt
- moegliche Handoff-Marker dokumentiert

Ziel:
- `00 Inbox` bleibt ein echter Capture-Puffer
- `90 Archive` enthaelt die bereits verarbeiteten Source Notes

## Routing-Leitlinien
- Ein multi-topic Dump erzeugt genau eine Source Note, nicht mehrere parallele Inbox-Noten.
- Ein klar committedes Vorhaben wird als Projekt geroutet, nicht nur als Idee.
- Ein spekulativer Gedanke ohne Commitment bleibt Idee.
- Inhalte werden bevorzugt verlinkt statt zwischen mehreren Noten kopiert.
- Daily Notes bleiben Hub + Verlauf und werden nicht zu einem Duplikat des operativen Tagesplans umgebaut.

## Abnahmeszenarien
- Ein Brain Dump mit mehreren Themen erzeugt genau eine rohe Inbox-Notiz, genau einen Daily-Note-Link und nur dann Projekt- oder Ideenlinks, wenn die Routing-Regeln sie tragen.
- Ein Brain Dump mit klarem Commitment wird als Projekt geroutet und nicht nur als Idee abgelegt.
- Ein spekulativer Gedanke ohne Commitment bleibt Idee und erzeugt keine Projektstruktur.
- `task_candidate` und `calendar_candidate` bleiben dokumentierte Handoff-Marker und verursachen in dieser Spezifikation keine externen Writes.

## Nicht verhandelbar
- kein Verlust des Rohdumps
- kein direktes Umschreiben in externe Systeme innerhalb dieser Spezifikation
- keine Scheduler-, Runtime-, Docker- oder `PLAN.md`-Aenderungen als Teil des Brain-Dump-Flows
- keine Vermischung von Task-Truth, Calendar-Truth und Vault-Truth
