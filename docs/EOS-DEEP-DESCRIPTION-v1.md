# EOS – Deep Description (2026-04-30)

## 1) Kurzantwort: Was ist EOS?

EOS (`personal-assistant`) ist ein **operativer, termin- und aufgabenzentrierter Planungsagent** für eine einzelne Person.  
Er ist nicht dafür gebaut, beliebiges Wissen zu liefern oder breit zu beraten.  
EOS ist darauf optimiert, aus echten Datenquellen (Kalender, Tasks, Routinen) belastbare Tages- und Wochenstruktur zu erzeugen und diese zuverlässig zu liefern.

In der Praxis bedeutet das:
- ein Telegram-konfigurierter Agent, der Daten liest,
- Regeln auf bestehende Realität (z. B. harte Termine) anwendet,
- Entscheidungen mit klaren Prioritäten trifft,
- und mit klaren, kleinen, umsetzbaren Ergebnissen antwortet (statt langer Erklärtexte).

## 2) Zielbild vs. aktueller Stand

### Zielbild
- Ein stabiles EOS für Alltag und Produktivität.
- Operatives Verhalten statt Beratung.
- Verlässliche tägliche Planung, Wochenüberblick, Habit-Tracking und Reminder.
- Feste Datenquellen und eindeutige Verantwortungszonen („Single Source of Truth“).
- Sichere, nachvollziehbare Deployments mit Retry-/Idempotenzmechanismen.

### Aktueller Stand (praktisch nutzbar)
- Starkes Kernsystem ist bereits drin und strukturiert:
  - dedizierter EOS-Workspace,
  - Telegram-Routing,
  - harte Zeitslots aus Google Calendar (mind. `primary` + `Sport`),
  - tägliche und wöchentliche Planungs-Logik,
  - Habit-Engine mit Eventing,
  - Job-Orchestrierung und Delivery-Tracking,
  - mehrere CLI-Operationen für direkte Interaktion.
- Einige Integrationen sind im Zielbild klar, aber in der Produktivprüfung noch nicht vollständig verifiziert (u. a. produktive Task-Write-/Vault-Pfade).

## 3) Was genau macht EOS heute technisch?

### A) Datenzugriff
- **Google Calendar (via `gog`)**: operativer Primärzustand für harte Termine.
- **Google Tasks (OAuth2)**: Task-Lese-/Schreib-Fluss vorgesehen; teilweise live-read robust, Write-/Complete-Pfad technisch vorhanden aber nicht durchgängig auf End-to-End-Produktion bestätigt.
- **local state**: JSON + SQLite als strukturierte Zwischenzustände (nicht als unklare Mehrheitswahrheit).

### B) Planungslogik
- Core-Regeln sind in Dokumenten und Policies hinterlegt:
  - `EOS-PLANNING-POLICY-v1`
  - `EOS-SCHEDULER-POLICY-v1`
  - `EOS-COACHING-ENGINE-v1`
- Die Planung ist konfliktbewusst:
  - harte Events zuerst,
  - dann Priorisierung von Work-, Sport- und Routineblöcken,
  - danach Deep Work und optionale Zusatzblöcke.
- Deep-Work-Standard ist bewusst konservativ definiert, inklusive Energiemanagement.

### C) Ausgabe- und Ausführungsmodell
- Outputs nutzen Template-Dateien (Telegram + Vault-Notizen).
- „Eine klare Nachricht statt Theorie“ ist Leitprinzip: wenige Empfehlungen, hoher Umsetzungsgrad.
- Jede planbare Handlung wird als klarer Schritt beschrieben (statt als lange Begründung).

### D) Jobs / Scheduler
- Es gibt wiederkehrende Jobs für Morgen-/Abend-/Wochensichten (mit festen Uhrzeiten).
- Idempotenzschlüssel sorgen dafür, dass Wiederholungen nicht doppelt liefern.
- Zustände werden persistiert, so dass Send- und Delivery-Pfade kontrolliert sind.

### E) Interaktion
- Hauptschnittstelle ist CLI (`python3 -m src.eos_cli`):
  - `health`
  - `daily-plan`, `weekly-plan`
  - `habits`
  - `tasks`
  - `run-job`
  - `cron-audit`, `model-audit`
- Zusätzlich sind Telegram-basierte Habit-Text-Eingaben vorgesehen (`habits handle "<text>"`).

## 4) Wofür ist EOS da? (Nutzen)

EOS löst ein Problem:  
**„Was ist heute wirklich machbar?“** statt „Was wäre theoretisch ideal?“.

Der Nutzen in der täglichen Nutzung:
- Entlastung bei der Selbstplanung durch harte Realität zuerst.
- Schutz vor Überladung durch Kapazitätsregeln und Prioritäten.
- Konsistenz durch wiederkehrende Planungspunkte (täglich/weekly/habit).
- geringere mentale Reibung: strukturierte Textantworten statt chaotischer To-Do-Liste.

## 5) Architekturprinzip

EOS trennt Datenquellen und Zustände bewusst:

1. **System of Record (z. B. Calendar/Tasks/Vault):** echte Quelle des Inhalts.
2. **Derived State (SQLite):** Hilfszustand für Habit-/Ausführungsmetriken.
3. **Runtime/Delivery State:** Idempotenz- und Job-Ausführungshistorie.

Diese Trennung verhindert:
- „Wahrheitsduplikate“ (z. B. dieselbe Information mehrfach widersprüchlich),
- ungeklärte Überschreibungen,
- unstabile Reihenfolgen bei wiederholten Läufen.

## 6) Was ist *nicht* EOS?

- Kein allgemeiner Wissensassistent.
- Kein allgemeiner „Life-Coach“, kein Fitness-Coach (abgetrennt von Solara).
- Nicht primär ein Chatbot für offene Beratung.
- Nicht primär Marketing- oder Schreibassistent.

## 7) Risiko- und Qualitätsbild

- **Stabil:** Kern-Planungslogik, habit-service, CLI-Basis, Job-Scheduling-Mechanik.
- **Teilspezifisch hartnäckig:** externe Integrationen müssen in jedem Deploy sauber validiert werden.
- **Wesentliche Qualitätsherausforderung:** klare Grenzen zwischen Stub-, Fallback- und Produktivpfaden bleiben immer explizit dokumentiert und nicht verwässert.

## 8) Konkrete Verbesserungsmöglichkeiten

### Kurzfristig (1–2 Wochen)
- End-to-End-Validierung für produktiven Google-Tasks-Write + Complete.
- Klare, automatisierte Smoke-Checks vor jedem Job-Lauf (vor allem bei Datenquellen-Ausfällen).
- Vereinheitlichter Output-Monitor für fehlgeschlagene Job-Läufe inkl. Fehlerklassen.

### Mittelfristig (1–2 Monate)
- Vollständige Vault-Anbindung (Markdown-Notebook als echter persistenter Arbeitsweg).
- Strukturierte Incident-Liste + RCA-Template (z. B. „Was ist passiert / Warum / Was war der Rückweg“).
- Einheitliche Metrik für „Overload-Risiko“ (statt nur Binär-Status).

### Strategisch
- EOS als Teil einer größeren „Decision Graph“-Ansicht ausbauen:  
  - Kalender → Aufgaben → Fokus → Habit → Energie.
- Optionaler Safety-Mode (streng, moderat, kreativ) für unterschiedliche Tageslagen.
- Standardisierte Audit-Berichte (Tätigkeitsverlauf, Konflikte, Abweichungen) für wöchentliche Review-Entscheidungen.

## 9) Was könnten wir wirklich verbessern, wenn Fokus auf Wirkung liegt?

Nicht auf „mehr Features“, sondern auf:
1. weniger Ambiguität in den Datenquellen,
2. bessere Nachvollziehbarkeit bei Fehlerfällen,
3. stabilere Betriebsresilienz bei API-Ausfällen,
4. klarere Rückwege bei inkonsistenten Inputs,
5. höhere Vorhersagequalität durch konsistente, kleine Messgrößen statt neuer Regeln.

## 10) Fazit

EOS ist bereits ein sehr konkreter operativer Kern für persönliche Planungsführung, nicht ein allgemeiner Chat-Assistent.  
Seine Reife hängt jetzt vor allem davon ab, wie robust die externen Pfade (Tasks, Vault, Deploy/Observability) in Produktion werden und wie gut die Fehlerfälle beobachtbar gemacht werden.

