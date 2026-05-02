# EOS Coaching Engine v1

## Zweck
Dieses Dokument definiert die deterministische Coaching Engine fuer EOS V2.
Die Engine bewertet Kalender plus Aufgaben gegen die bestaetigte EOS-Policy.

Die Engine ist ausdruecklich nicht:
- ein generischer Produktivitaets-Coach
- eine Scoring-Maschine mit Black-Box-Magie
- eine Research- oder Guru-Persona

## Produktive Rolle
Die Coaching Engine liefert fuer einen Tag:
- `TrafficLightStatus`
- belastbare Gruende
- eine kurze Einschaetzung
- genau eine konkrete Empfehlung
- optional genau eine Warnung

## Interne Vertrage

### `TrafficLightStatus`
`TrafficLightStatus = green | yellow | red`

### `OverloadReason`
`OverloadReason` ist eine endliche Menge fachlicher Gruende:
- `hard_shift_plus_fixed_sport`
- `too_many_heavy_blocks`
- `fragmented_capacity`
- `insufficient_recovery`
- `prep_risk`
- `poor_distribution`
- `missing_task_basis`

### `SingleRecommendation`
`SingleRecommendation = { key, text }`

Zulaessige `key`-Werte in v1:
- `protect_recovery`
- `cut_extra_block`
- `pick_top1`
- `use_single_focus_block`
- `skip_deep_work`
- `prepare_tonight`

### `CoachContext`
`CoachContext` enthaelt mindestens:
- `businessDateBerlin`
- `hardEvents[]`
- `openTasks[]`
- `taskSourceStatus`
- `focusWindows[]`
- `hasFixedSportBlock`
- `isHardLoadDay`
- `routinesRequired`
- `prepItems[]`

### `CoachEvaluation`
`CoachEvaluation = { status, reasons[], assessment, recommendation, warning? }`

Regeln:
- `reasons[]` darf leer sein nur bei eindeutig `green`
- `recommendation` ist immer genau ein Eintrag
- `warning` ist optional und maximal ein Eintrag

## Eingangsregeln
Die Engine arbeitet nur mit bestaetigten Datenquellen:
- harte Termine aus Google Calendar
- offene Aufgaben aus Google Tasks, falls verfuegbar
- EOS-Policy fuer harte Belastungstage, Sport und Deep Work

Die Engine darf nicht:
- neue Termine erfinden
- nicht verifizierte Tasks als Wahrheiten behandeln
- generische Lifestyle- oder Produktivitaetsthesen einfuehren

## Harte EOS-Regeln

### Belastungstage
- Donnerstag bis Samstag gelten als harte Belastungstage
- Standardannahme fuer diese Tage: fruehe Schicht und konservative Zusatzplanung

### Deep Work
- ein Deep-Work-Block = 60 Minuten Fokus plus 10 Minuten Spaziergang
- harte Arbeitstage tragen hoechstens einen plausiblen zusaetzlichen schweren Block
- harter Arbeitstag plus fixer Sport bedeutet meist kein echter Deep-Work-Block

### Sportlogik
- fixer Sportkurs aus dem Kalender = harter Sportblock
- Gym = flexibler Block
- Cardio = flexibler Block
- Calisthenics wird nicht automatisch zusaetzlich gesetzt

### Coaching-Grenzen
- genau eine konkrete Empfehlung
- optional genau eine Warnung
- keine taegliche Produktivitaetspredigt
- kein Web- oder Research-Framing

## Ableitungslogik
Die Engine bewertet in fester Reihenfolge:
1. harte Kalenderlast
2. harter Arbeitstag ja/nein
3. fixer Sportblock ja/nein
4. verfuegbare zusammenhaengende Fokusfenster
5. offene Aufgabenbasis vorhanden ja/nein
6. Routinen und Vorbereitung sichtbar ja/nein
7. Gesamtverteilung realistisch ja/nein

## Statuslogik

### `red`
`red` wird gesetzt, wenn mindestens eine harte Ueberlastbedingung vorliegt:
- harter Arbeitstag plus fixer Sport plus weiterer schwerer Block
- kein realer 60+10-Fokusblock verfuegbar, aber hoher Arbeitsanspruch bleibt bestehen
- mehrere schwere Bloecke konkurrieren auf einem harten Belastungstag
- Recovery oder Vorbereitung fuer morgen kippt sichtbar weg

Typische `reasons[]`:
- `hard_shift_plus_fixed_sport`
- `too_many_heavy_blocks`
- `fragmented_capacity`
- `insufficient_recovery`

### `yellow`
`yellow` wird gesetzt, wenn der Tag nur mit konservativer Kuerzung sauber bleibt:
- ein zusaetzlicher Block sollte gestrichen oder geschuetzt werden
- der Tag ist machbar, aber fragil
- Aufgabenbasis fehlt teilweise oder Vorbereitung ist knapp

Typische `reasons[]`:
- `poor_distribution`
- `prep_risk`
- `missing_task_basis`
- `fragmented_capacity`

### `green`
`green` wird gesetzt, wenn:
- harte Termine, Routinen und Belastung sauber zusammenpassen
- keine EOS-Regel verletzt wird
- die Zusatzplanung realistisch bleibt
- kein stilles Ueberplanen erkennbar ist

## Empfehlungsauswahl
Die Engine waehlt genau eine Empfehlung mit klarer Prioritaet:
1. Recovery schuetzen
2. harten Zusatzblock streichen
3. auf Top-1 reduzieren
4. einen einzelnen Fokusblock schuetzen
5. Deep Work ganz streichen
6. Vorbereitung heute Abend sichern

Beispiele:
- `protect_recovery` fuer harte Arbeitstage plus Sport
- `cut_extra_block` wenn die Tageslast objektiv zu hoch ist
- `pick_top1` wenn nur ein sauberer operativer Schwerpunkt realistisch ist
- `prepare_tonight` wenn morgen Vorbereitung die Engstelle ist

## Warnungsregel
Eine Warnung wird nur gesetzt, wenn ein echtes Risiko explizit genannt werden muss:
- Ueberladung
- schlechte Verteilung
- fehlende Aufgabenbasis
- fehlende Vorbereitung

Die Warnung ist:
- kurz
- operativ
- nicht moralisierend

## Fehlende Aufgabenbasis
Wenn Google Tasks nicht verfuegbar ist:
- `taskSourceStatus` wird explizit als nicht vollstaendig markiert
- die Engine darf `yellow` wegen `missing_task_basis` setzen
- die Empfehlung darf auf Schutz der Kalenderstruktur oder Reduktion auf Top-1 gehen
- es duerfen keine erfundenen Prioritaeten erscheinen

## Persistenzbezug
Jede produktive Tagesbewertung kann in `daily_evaluations` gespeichert werden.
Gespeichert werden duerfen:
- `business_date_berlin`
- `status`
- `reasons`
- `assessment`
- `recommendation`
- `warning`
- Snapshot-Referenzen

Die Engine speichert keine neuen Primaerwahrheiten ueber Termine oder Aufgaben.

## Abnahmekriterien
Die Coaching Engine ist in v1 nur dann fachlich korrekt, wenn:
- `green`, `yellow` und `red` auf echten Testtagen plausibel sind
- Thu-Sat konservativ bewertet werden
- fixer Sport als harter Lastfaktor zaehlt
- Deep Work nie gegen die 60+10-Regel oder harte Belastungstage erzwungen wird
- genau eine konkrete Empfehlung ausgegeben wird
- keine generische Produktivitaetssprache auftaucht
