# MOC - Vault

Diese Seite ist der Einstieg in die Vault-Schicht von EOS.

Ziel:
- verstehen, wofür der Vault da ist
- zwischen echter Wissensschicht, operativer Nutzung und offenem Zielbild unterscheiden
- direkt in die relevanten technischen Spezifikationen springen

Technische Wahrheit bleibt in `docs/`.
Diese MOC-Datei ist die Navigations- und Orientierungsschicht.

---

## 1. Wofür der Vault da ist

Der Vault ist die menschliche Wissens-, Navigations- und Verlaufsschicht von EOS.

Er ist gedacht für:
- Brain Dumps
- Daily Notes
- Weekly Reviews
- Ideen
- Projektkontext
- Operator-Wissen
- Runbooks
- Entscheidungen und ADRs

Der Vault ist **nicht** gedacht als Primärquelle für:
- harte Termine
- aktive offene Aufgaben
- technische Vertragswahrheit

Kurz:
- `docs/` definiert
- `vault/` erklärt, verknüpft, dokumentiert und begleitet

---

## 2. Was aktuell bestätigt ist

### Struktur
Die Vault-Struktur ist als Schicht neben `docs/` angelegt.

Gedachte Hauptbereiche:
- `00 Home/`
- `01 Maps of Content/`
- `10 Inbox/`
- `11 Daily Notes/`
- `12 Projects/`
- `13 Areas/`
- `14 Knowledge/`
- `15 Ideas/`
- `90 Archive/`

### Rolle im System
Der Vault ist die:
- menschliche Navigationsschicht
- Arbeits- und Überblicksschicht
- Langzeitkontext-Schicht
- Second-Brain-Basis

### Dokumentationsprinzip
- `docs/` = technische kanonische Spezifikationen
- `vault/` = verständliche Navigations- und Wissensschicht

---

## 3. Was aktuell nur teilweise vorhanden ist

### Brain Dump Routing
Brain Dumps können strukturell im Vault abgelegt werden.
Noch nicht voll produktiv:
- sauberes automatisches Routing
- konsistente Verlinkung
- Dublettenvermeidung
- kontrollierte Archivierung

### Daily Notes
Die Struktur für Daily Notes ist sinnvoll und vorgesehen.
Noch nicht voll produktiv:
- automatisches Writeback aus EOS
- stabile Tageszusammenfassungen
- Verknüpfung mit offenen Aufgaben und Projektkontext

### Projekt- und Ideenfluss
Projekte und Ideen sind als Kategorien klar.
Noch nicht voll produktiv:
- automatische Umwandlung von Idea → Project
- Routing-Qualität aus Brain Dumps
- konsistente Pflege durch EOS

---

## 4. Was noch offen ist

### Live Writeback
Die zentrale offene Frage ist nicht die Struktur, sondern die sichere Nutzung im Betrieb.

Offen:
- wann EOS in den Vault schreiben darf
- welche Note-Typen EOS automatisch anlegen darf
- wie Duplikate verhindert werden
- wie Links und Namenskonventionen konsistent bleiben

### Persistenz / Mount
Für produktiven Betrieb ist offen bzw. noch nicht final verifiziert:
- der endgültige Live-Mount
- die Persistenz über Neustarts
- die Rechte für sauberes Schreiben
- die Rolle des Vault im echten VPS-Betrieb

### Qualitätsgrenzen
Der Vault darf nicht mit:
- halbgaren Notizen
- Duplikaten
- spekulativen Klassifizierungen
- unnötigen Zwischenständen
zugemüllt werden

---

## 5. Vault-Prinzipien

### Principle 1: Markdown first
Der Vault ist markdown-first.
Nicht App-first, nicht plugin-first, nicht GUI-first.

### Principle 2: Human navigation first
Der Vault soll dir helfen, das System zu steuern, nicht es komplizierter zu machen.

### Principle 3: No second source of truth
Der Vault darf keine konkurrierende Wahrheit zu Calendar oder Tasks erzeugen.

### Principle 4: Conservative writeback
EOS soll nur kontrolliert und mit klaren Regeln in den Vault schreiben.

### Principle 5: Linkability matters
Der Vault lebt von sauberer Verlinkung:
- Daily Notes
- Projects
- Ideas
- Brain Dumps
- technische Specs
sollen sinnvoll miteinander verknüpft sein

---

## 6. Wichtige Vault-Bereiche

## 00 Home
Startpunkt:
- Dashboard
- Current Status
- Open Issues

## 01 Maps of Content
Thematische Einstiegspunkte:
- Architecture
- Planning
- Scheduler
- Tasks
- Vault
- Runtime

## 10 Inbox
Rohinput:
- ungeordnete Brain Dumps
- noch nicht triagierte Notizen

## 11 Daily Notes
Tageskontext:
- was war relevant
- was wurde gemacht
- was blieb offen
- was ist morgen wichtig

## 12 Projects
Verbindliche aktive Vorhaben:
- laufende Projekte
- jeweils mit nächstem Schritt

## 13 Areas
Stabile Lebens- und Arbeitsbereiche:
- Gesundheit
- Karriere
- Lernen
- Organisation
- etc.

## 14 Knowledge
Operator-Wissen und Referenzmaterial:
- Runbooks
- Troubleshooting
- Hintergrundwissen

## 15 Ideas
Noch nicht commitete Ideen:
- Rohideen
- mögliche Projekte
- explorative Ansätze

## 90 Archive
Archivierte und abgeschlossene Inhalte

---

## 7. Note-Typen

### brain_dump_note
Ort:
- `10 Inbox/`

Zweck:
- roher Input
- später triagieren

### daily_note
Ort:
- `11 Daily Notes/`

Zweck:
- Tageshub
- Verlauf
- Kontext
- Rückblick

### project_note
Ort:
- `12 Projects/`

Zweck:
- aktives Vorhaben
- klares Commitment
- nächster Schritt

### idea_note
Ort:
- `15 Ideas/`

Zweck:
- explorativ
- noch nicht committed
- später promotebar oder archiviert

---

## 8. Zusammenspiel mit anderen Schichten

## Vault + Docs
- `docs/` liefert technische Wahrheit
- `vault/` übersetzt diese Wahrheit in Orientierung und Operator-Navigation

## Vault + Tasks
- operative Aufgaben gehören in Google Tasks
- der Vault darf Aufgaben referenzieren, aber nicht ersetzen

## Vault + Calendar
- harte Termine kommen aus Google Calendar
- der Vault darf Termin-Kontext dokumentieren, aber nicht Primärquelle sein

## Vault + Scheduler
- Evening Reset und Weekly Review können Inhalte in Daily Notes oder Reviews schreiben
- dafür braucht es später kontrolliertes Writeback

## Vault + Brain Dumps
- Brain Dumps beginnen im Vault
- von dort gehen operative Elemente weiter in:
  - Tasks
  - Calendar
  - Projects
  - Ideas
  - Knowledge

---

## 9. Failure-Verhalten

Wenn Vault-Writeback nicht funktioniert:
- EOS darf nicht stillschweigend so tun, als sei geschrieben worden
- Fehler muss sauber loggen
- keine Success-Meldung ohne echten Write

Wenn Routing unsicher ist:
- lieber Inbox statt falsche Zielnote
- lieber konservativ als kreativ

Wenn ein Brain Dump unklar ist:
- nicht automatisch zu stark interpretieren
- lieber als Rohinput behalten

---

## 10. Wichtigste technische Dokumente

### Vault-Kern
- [docs/vault/EOS-VAULT-v1.md](../../docs/vault/EOS-VAULT-v1.md)
- [docs/vault/EOS-BRAIN-DUMP-v1.md](../../docs/vault/EOS-BRAIN-DUMP-v1.md)

### Verwandte technische Dokumente
- [docs/architecture/EOS-ARCHITECTURE-v1.md](../../docs/architecture/EOS-ARCHITECTURE-v1.md)
- [docs/architecture/EOS-V2-TECHNICAL-SPEC.md](../../docs/architecture/EOS-V2-TECHNICAL-SPEC.md)
- [docs/policy/EOS-OPERATING-CONTRACT-v1.md](../../docs/policy/EOS-OPERATING-CONTRACT-v1.md)
- [docs/scheduler/EOS-EVENING-RESET-v1.md](../../docs/scheduler/EOS-EVENING-RESET-v1.md)
- [docs/scheduler/EOS-REVIEW-ENGINE-v1.md](../../docs/scheduler/EOS-REVIEW-ENGINE-v1.md)

### Orientierung
- [../00 Home/EOS Dashboard.md](../00%20Home/EOS%20Dashboard.md)
- [../00 Home/EOS Current Status.md](../00%20Home/EOS%20Current%20Status.md)
- [../00 Home/EOS Open Issues.md](../00%20Home/EOS%20Open%20Issues.md)

---

## 11. Nächste Vault-Schritte

### Kurzfristig
1. MOCs fertigstellen
2. Dashboard / Status / Open Issues sauber halten
3. Brain-Dump- und Note-Typ-Regeln stabilisieren
4. Writeback-Regeln definieren

### Danach
5. konservatives Vault-Writeback einführen
6. Daily Notes mit Evening Reset koppeln
7. Reviews in Weekly- und Monthly-Schichten aufbauen
8. Project-/Idea-Routing vorsichtig automatisieren

---

## 12. Wie du diese Seite nutzt

Wenn du wissen willst:

### „Wofür ist der Vault überhaupt?“
- lies Abschnitt 1 bis 5

### „Was ist da schon echt und was noch offen?“
- lies Abschnitt 2 bis 4

### „Wie hängt der Vault mit Tasks, Calendar und Docs zusammen?“
- lies Abschnitt 8

### „Wo ist die technische Wahrheit dazu?“
- springe zu Abschnitt 10

### „Was ist als Nächstes dran?“
- lies Abschnitt 11

---

## 13. Verbindliche Entscheidungen

- [[ADR - Calendar as Source of Truth]] — der Vault darf Kalender-Kontext dokumentieren, aber nie Primärquelle für harte Zeit werden.
- [[ADR - Tasks as Source of Truth]] — der Vault darf Tasks referenzieren, aber nie die Primärhaltung offener operativer Aufgaben übernehmen.

Der Vault ist explizit **keine** Source of Truth für Zeit oder aktive Aufgaben. Er ist Navigations- und Wissensschicht.