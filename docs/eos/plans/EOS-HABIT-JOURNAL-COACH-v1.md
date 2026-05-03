# EOS Habit Journal Coach v1

Status: Agent 3 implementation plan and notes

## 1. Ziel

EOS Habit Journal Coach v1 interpretiert synthetische Tages- und Wochensignale deterministisch:

```text
Habits + Energy + Mood + Journal -> Morning Prompt / Evening Review / Minimum Viable Day
```

Das Modul erzeugt keine Telegram-Sends, schreibt keine Datenbank und aendert keine bestehenden Habit-, Energy-, Job- oder CLI-Flows.

## 2. Architektur

Neue reine Servicemodule:

```text
src/eos_journal/
src/eos_notifications/
```

`eos_journal` verarbeitet Daily Signals, Tagesstatus, Prompts, Reviews, Minimum-Day-Aktionen und Wochen-Trends. `eos_notifications` entscheidet, ob ein Ereignis ueberhaupt Push-wuerdig ist.

## 3. Daily Signals

Input ist `DailySignalInput`:

```text
date
sleep_quality
energy_level
mood_level
stress_level
deep_work_done
training_done
evening_shutdown_done
open_task_count
calendar_load_score
```

Statuswerte:

```text
stable
tight
overloaded
recovery_needed
```

Die Regeln bleiben bewusst hart und nachvollziehbar: niedriger Schlaf, niedrige Energie, niedrige Stimmung, hoher Stress, hohe Kalenderlast, viele offene Aufgaben, verpasstes Training, kein Deep Work und fehlender Shutdown erzeugen Risk Flags.

## 4. Morning Prompt

Der Morning Prompt ist kurz und operativ:

```text
Fokus
Minimum
Risiko
kurzes nicht-attribuiertes Platzhalter-Zitat
```

Keine langen Motivationsreden und keine falsche Autor-Zuschreibung.

## 5. Evening Review

Der Evening Review enthaelt:

```text
Stabil
Offen
Energieverlust
Morgen
```

Er nutzt keine Schuldlogik, keine Streak-Bestrafung und keine medizinischen oder therapeutischen Aussagen.

## 6. Minimum Viable Day

Normaltag:

```text
1 Deep Work Block
Mailblock
Sport/Routine
```

Schlechter Tag:

```text
20 Minuten Bewegung
1 kleiner Fokusblock
Abend Shutdown
```

Ueberladener Tag:

```text
Nur Pflichttermine
1 wichtigste Aufgabe
keine Zusatzbloecke
```

## 7. Habit Trends

Wochen-Signale erkennen:

```text
training_repeatedly_missed
deep_work_stable
sleep_unstable
mood_declining
overload_risk_rising
```

Output ist `HabitTrendOutput` mit `trend_summary`, `risk_flags` und `recommendations`.

## 8. Notification Budget

`should_notify(...)` blockiert Noise:

- Morning Prompt und Evening Review sind innerhalb des Budgets erlaubt.
- Low Priority Newsletter sind niemals Push.
- Quiet Hours blockieren nicht-kritische Ereignisse.
- Security- und Deadline-Risiken mit hoher Dringlichkeit duerfen eskalieren.
- Ist das Tagesbudget verbraucht, werden normale und niedrige Signale blockiert.

## 9. Safety / Non-Therapy Boundary

Dieses Modul ist kein Therapie- oder Medizinprodukt. Es stellt keine Diagnosen, bewertet keine Gesundheit und ersetzt keine professionelle Beratung. Es erzeugt nur kurze operative Planungs- und Reflexionshinweise.

## 10. Tests

Testabdeckung:

```text
tests/eos_journal/
tests/eos_notifications/
tests/fixtures/journal/
```

Geprueft werden Status-Erkennung, Prompt-Struktur, Review-Struktur, Minimum-Day-Aktionen, Habit-Trends, Quiet Hours, Notification Budget, Newsletter-Suppression und das Fehlen von Schuld-, Streak-, Therapie- und Medizin-Sprache.

## 11. Naechste Phase

Naechste Phase: optionale CLI- und Telegram-Delivery-Integration. Diese Phase braucht ein separates Delivery-Konzept mit Idempotenz, Notification Budget Enforcement und expliziten Live-E2E-Tests.
