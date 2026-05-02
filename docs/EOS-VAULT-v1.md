# EOS Vault v1

## Zweck
Diese Spezifikation definiert den Vault-/Second-Brain-Layer fuer EOS Phase 1.
Der Vault ist die Markdown-Primarquelle fuer Brain Dumps, Daily Notes, Projektverlauf, Ideen und langfristigen Kontext.

Diese Spezifikation erweitert nicht die Rollen von Google Calendar, Google Tasks, Scheduler, Runtime oder Docker.

## Scope-Grenze
- Der Vault beschreibt nur Struktur, Note-Typen, Benennung, Linking und Routing.
- Externe Systeme bleiben getrennt:
  - Google Calendar = harte Termine und feste Zeitbloecke
  - Google Tasks = aktive offene Aufgaben
  - Vault = Brain Dumps, Daily Notes, Verlauf, Ideen und Wissen
- Diese Spezifikation definiert keine Containerpfade, Mount-Defaults oder Runtime-Implementierung.
- Diese Spezifikation definiert keine direkte Write-Logik fuer Google Tasks oder Google Calendar.

## Verbindliche Top-Level-Struktur
EOS verwendet genau diese verpflichtenden Top-Level-Ordner:

- `10 Inbox`
- `11 Daily Notes`
- `12 Projects`
- `13 Areas`
- `14 Knowledge`
- `15 Ideas`
- `90 Archive`

Ordnerrollen:
- `10 Inbox`: rohe und noch nicht vollstaendig triagierte `brain_dump_note`
- `11 Daily Notes`: Tages-Hub, Verlauf, Brain-Dump-Verweise, aktive Projekt-/Ideenlinks, Carry Forward
- `12 Projects`: flache Sammlung aktiver `project_note`
- `13 Areas`: dauerhafte Verantwortungsbereiche und laufende Lebens-/Arbeitsbereiche
- `14 Knowledge`: dauerhafte Referenz- und Wissensnotizen
- `15 Ideas`: flache Sammlung spekulativer oder noch ungeklaerter `idea_note`
- `90 Archive`: archivierte, bereits triagierte Brain Dumps und spaeter nicht mehr aktive Notizen

Keine weiteren Top-Level-Ordner sind fuer EOS verpflichtend.
EOS fuehrt kein Folder-per-Idea- und kein Folder-per-Project-Muster als Standard ein.

## Verbindliche Note-Typen
Diese Spezifikation standardisiert genau diese Note-Typen:

- `brain_dump_note`
- `daily_note`
- `project_note`
- `idea_note`

`13 Areas` und `14 Knowledge` bleiben strukturell bestaetigte Vault-Bereiche, erhalten in diesem Change aber keine eigenen Templates oder neuen Standardtypen.

## Dateinamen und Pfade
- `brain_dump_note`: `10 Inbox/YYYY-MM-DD-HHmm-brain-dump.md`
- archivierte `brain_dump_note`: `90 Archive/YYYY-MM-DD-HHmm-brain-dump.md`
- `daily_note`: `11 Daily Notes/YYYY-MM-DD.md`
- `project_note`: `12 Projects/<project-slug>.md`
- `idea_note`: `15 Ideas/<idea-slug>.md`

Benennungsregeln:
- Daily Notes verwenden immer das ISO-Datum als Dateinamen.
- Brain Dumps verwenden Capture-Datum plus Capture-Uhrzeit in 24h-Form.
- Projekt- und Ideennoten bleiben flache Dateien mit stabilen Slugs.
- `.md` wird im Notizinhalt nicht mitgeschrieben, wenn auf Notes verlinkt wird.

## Linking-Standard
- Standard-Linking im Vault sind Obsidian-Wikilinks: `[[...]]`.
- Daily Notes verlinken relevante Brain Dumps, aktive Projekte und aktive Ideen.
- Projekt- und Ideennoten verlinken relevante Brain Dumps und relevante Daily Notes.
- Brain Dumps verlinken ihre Zielnoten, statt Inhalte mehrfach zu kopieren.
- Pfadbasierte Rohlinks im Notiztext sind nicht der Standard, solange ein Wikilink ausreicht.

## Daily Notes als Hub + Verlauf
`daily_note` ist der Tages-Hub fuer Kontext und Verlauf, nicht der Ersatz fuer den operativen Planner-Output.

Eine Daily Note enthaelt mindestens:
- Tageskontext
- Brain-Dump-Links
- aktive Projekte
- aktive Ideen oder offene Faeden
- kurze Verlaufsnotizen
- Carry Forward

Die Daily Note ersetzt nicht `templates/daily-output.md`.
`daily-output.md` bleibt der operative Tagesplan.
`daily_note` bleibt die dauerhafte Verlaufs- und Verlinkungsnote.

## Projekt vs. Idee
Routing-Regel:
- `project_note` = aktiv committetes Ergebnis mit laufendem naechsten Schritt
- `idea_note` = spekulativ, ungeklaert oder noch nicht committed

Eine `idea_note` wird zu einer `project_note`, sobald mindestens eines klar vorliegt:
- aktives Commitment
- laufende Bearbeitung
- ein belastbarer naechster Schritt
- ein konkretes Ziel, das nicht mehr nur explorativ ist

Eine `idea_note` bleibt Idee, wenn eines oder mehrere dieser Muster gelten:
- vielleicht
- spaeter
- optionales Experiment
- noch offene Richtung
- noch kein aktiver naechster Schritt

## Areas und Knowledge
- `13 Areas` steht fuer laufende Verantwortungsbereiche und stabile Kontexte.
- `14 Knowledge` steht fuer dauerhafte Referenznotizen und extrahiertes Wissen.
- Dieser Change fuehrt fuer beide Bereiche keine neuen Templates ein.
- Brain Dumps duerfen spaeter in Areas oder Knowledge verdichtet werden, aber nicht bevor die Roh-Capture- und Daily-Note-Verlinkung gesichert ist.

## Abnahmeregeln
- Daily Notes funktionieren als Hub + Verlauf und duplizieren nicht den operativen Inhalt von `daily-output.md`.
- Die Vault-Struktur bleibt bei den bestaetigten Top-Level-Ordnern und fuehrt kein Folder-per-Idea-Muster ein.
- Die Vault-Schicht bleibt markdown-first ohne verpflichtendes YAML-Frontmatter.
- Diese Spezifikation bleibt auf Vault und Templates begrenzt und fordert keine Scheduler-, Runtime-, Docker-, `SOUL.md`- oder `PLAN.md`-Aenderungen.

## Nicht verhandelbar
- kein YAML-Frontmatter als Pflicht
- markdown-first mit einfachen Abschnittsueberschriften
- keine stillschweigende Vermischung von Vault-, Task- und Calendar-Rollen
- keine neuen verpflichtenden Top-Level-Ordner
- keine Projekt- oder Ideen-Unterordner als Default
- keine Entfernung des Rohmaterials waehrend der Triage
