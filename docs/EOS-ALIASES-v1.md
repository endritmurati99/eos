# EOS Aliases v1

## Zweck
Persönliche Kurzbegriffe und Alltagsbegriffe werden hier auf interne Standardbegriffe normalisiert.

## Bestätigte Aliases
- `E-Block` = `Deep Work`
- `Deep Work` = `Deep Work`
- `BJJ` = `Brazilian Jiu-Jitsu`

## Sportbegriffe
- `Gym` = flexibler Trainingsblock Gym
- `Cardio` = flexibler Cardio-Block
- `Kickboxen` = fixer oder kalenderbasierter Sportkurs, wenn im Kalender vorhanden
- `Calisthenics` = optionaler Trainingsblock, nicht automatisch doppelt setzen

## Routinebegriffe
- `Morgenroutine` = Mindest- oder volle Morgenroutine je Tagesbelastung
- `Abendroutine` = Mindest- oder volle Abendroutine je Tagesbelastung

## Kalenderbegriffe
- `mein Kalender` = persönlicher primärer Kalender, solange keine andere Regel definiert ist
- `Sport` = Sport-Kalender

## Normalisierungsregel
Vor operativer Aktion gilt:
1. Freitextbegriff lesen
2. gegen Alias-Tabelle prüfen
3. auf internen Standardbegriff abbilden
4. erst dann Intent-zu-Action-Mapping ausführen

## Unklare Begriffe
Wenn ein Begriff nicht in der Alias-Tabelle steht und nicht sicher ableitbar ist:
- genau eine kurze Rückfrage
- keine Halluzination
