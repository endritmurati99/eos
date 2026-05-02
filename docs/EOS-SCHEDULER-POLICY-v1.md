# EOS Scheduler Policy v1

## Zweck
Diese Policy definiert den produktionsnahen Scheduler-Layer fuer EOS Phase 1 auf einem VPS-/Docker-Setup.
Der Scheduler-Layer ist fuer proaktive, operative Briefings und Reminder zustaendig.

Er erweitert EOS nicht um neue Gesamtarchitektur, sondern operationalisiert bestaetigte EOS-Faehigkeiten:
- Live Google Calendar Read
- Telegram-Ausgabe
- Planungszeitzone `Europe/Berlin`
- bestehende Daily-/Weekly-Planning-Policy
- bestehende Prep-Reminder-Policy

## Produktionsziel des Scheduler-Layers
- proaktive Nachrichten stabil und reproduzierbar ausloesen
- immer auf frischen Kalenderdaten arbeiten
- doppelte Sends verhindern
- bei Fehlern fail-closed statt spekulativ senden
- Informationsdichte hoeher gewichten als Nachrichtenanzahl

## Phase-1-Jobset
Phase 1 enthaelt genau diese drei Jobs:

| Job | Rolle | Trigger |
|---|---|---|
| `evening_briefing` | taeglicher Hauptanker fuer morgen | taeglich `20:30 Europe/Berlin` |
| `sport_prep_reminder` | ergaenzender Vortags-Reminder fuer relevante Sporttermine | Vortag `08:30 Europe/Berlin` |
| `weekly_sync` | strategischer Wochenanker | Sonntag `18:00 Europe/Berlin` |

Andere proaktive Jobs sind in Phase 1 nicht aktiv.

## Triggerzeiten
Alle Triggerzeiten sind operative Wall-Clock-Zeiten in `Europe/Berlin`.
Nicht die Container-Default-Zeitzone, nicht UTC und nicht relative Laufzeitabstaende sind massgeblich.

Verbindliche Trigger:
- `evening_briefing`: jeden Tag `20:30 Europe/Berlin`
- `sport_prep_reminder`: taeglich `08:30 Europe/Berlin`, prueft Sporttermine fuer morgen
- `weekly_sync`: Sonntag `18:00 Europe/Berlin`, betrachtet die kommende Kalenderwoche Montag bis Montag

## Nachrichtendichte
Der Scheduler arbeitet nach dem Grundsatz:
Informationsdichte vor Nachrichtenanzahl.

Regeln:
- genau eine Nachricht pro Job-Ausloesung
- keine gesplitteten Multi-Part-Nachrichten
- keine Motivationssprache
- keine Filler-Saetze
- nur operative Formulierungen
- mehrere Nachrichten am selben Tag nach Moeglichkeit vermeiden

Spezielle Phase-1-Regel:
- `sport_prep_reminder` ist rein ergaenzend und nur bei echter Relevanz aktiv
- `evening_briefing` bleibt der primaere Anker fuer morgen
- `weekly_sync` bleibt der strategische Wochenanker

## Grundregeln fuer Senden
Ein Scheduler-Job darf nur senden, wenn alle folgenden Bedingungen erfuellt sind:
- der Job wurde durch einen externen Scheduler einmalig getriggert
- der Trigger wird in `Europe/Berlin` interpretiert
- unmittelbar vor dem Send wurde ein frischer Live-Calendar-Read ausgefuehrt
- der Job hat seinen fachlichen Relevanztest bestanden
- persistenter State ist verfuegbar
- der Idempotenz-Key ist fuer den Zielzeitraum noch nicht im Status `sent`
- die Nachricht laesst sich ohne Spekulation aus bestaetigten Daten bilden

## Grundregeln fuer Nicht-Senden
Ein Scheduler-Job darf nicht senden, wenn mindestens eine dieser Bedingungen vorliegt:
- Calendar-Read ist fehlgeschlagen oder nicht frisch
- persistenter State ist nicht erreichbar
- fuer den Zielzeitraum existiert bereits ein `sent`-Eintrag
- die Job-spezifischen Sendebedingungen sind nicht erfuellt
- erforderliche strukturierte Eingaben fehlen und duerfen nicht geraten werden

Beispiele:
- kein `sport_prep_reminder` ohne relevanten Sporttermin fuer morgen
- kein `sport_prep_reminder` fuer Sportarten ohne definierte Checkliste
- kein frei erfundener `Top-3 morgen`-Block ohne verifizierte persistente Aufgabenbasis

## Daten- und Wahrheitsregeln
- Google Calendar ist die Primaerquelle fuer harte Termine und feste Sportbloecke
- mindestens `primary` und `Sport` muessen aggregiert werden
- `data/calendar.json` bleibt Test-/Fallback-Artefakt und ist keine Primaerquelle
- Google Tasks ist in Phase 1 nicht als produktiv verifizierte Aufgabenquelle vorausgesetzt
- `Top-3 morgen` und `gekuerzte Ziele` duerfen nur aus einer verifizierten persistenten Task-Snapshot-Quelle befuellt werden
- fehlt diese Quelle, muss EOS die fehlende Aufgabenbasis explizit markieren statt Prioritaeten zu erfinden

## Sunday Policy
Am Sonntag bleiben zwei Trigger aktiv:
- `weekly_sync` um `18:00 Europe/Berlin`
- `evening_briefing` um `20:30 Europe/Berlin`

Das ist in Phase 1 zulaessig, weil beide Jobs unterschiedliche Ebenen abdecken:
- `weekly_sync` = kommende Woche
- `evening_briefing` = naechster Tag

Beide Nachrichten muessen nicht redundant formuliert werden.

## Warum Morning Briefing in Phase 1 nicht aktiv ist
Ein Morning Briefing ist bewusst nicht Teil von Phase 1.

Gruende:
- Phase 1 optimiert auf niedrige Nachrichtenanzahl und hohe operative Relevanz
- Donnerstag bis Samstag sind harte Belastungstage
- fruehe Schichten sind kein guter Standard-Slot fuer zusaetzliche proaktive Nachrichten
- die Vorbereitung fuer morgen wird bereits durch `evening_briefing` abgedeckt
- ein zusaetzliches Morning Briefing erhoeht in Phase 1 das Risiko fuer Noise statt Nutzen

## Nicht verhandelbar
- keine In-Container-`while true`- oder `sleep`-Schleifen als Produktionsmodell
- `systemd`-Timer zuerst, `cron` nur als Fallback
- jeder Send basiert auf frischem Live-Read
- persistenter State ist Pflicht
- Idempotenz ist Pflicht
- keine doppelten Sends
- kein Motivationsstil
- keine spekulativen Pfade oder Secrets in Go-Live-Dokumenten
