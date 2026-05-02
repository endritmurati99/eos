# EOS System Overview

**Stand: 2026-04-22**

Vollständige Bestandsaufnahme des laufenden Systems — was existiert, was läuft, was blockiert ist, was ungeklärt ist.

---

## 1. Plattform: OpenClaw

| Eigenschaft | Wert |
|-------------|------|
| Version | 2026.4.15 |
| Container | `openclaw-qt6t-openclaw-1` |
| Laufzeit | 22 Stunden (Stand: 22.04.) |
| Port | `127.0.0.1:46301` — nur localhost, nicht ins Internet exponiert ✓ |
| Konfigdatei | `/data/.openclaw/openclaw.json` |

OpenClaw ist der Agent-Host. Er verwaltet alle Agents, Cron-Jobs, den Telegram-Gateway, Modell-Verbindungen, Plugins, Skills und Sessions.

Parallel läuft ein zweiter Container: `hermes-agent-6eu4-hermes-agent-1` — Port `32768→4860/tcp`, seit 2 Stunden aktiv. Keine Dokumentation dafür. Unbekannte Funktion. Nichts in `openclaw.json` erwähnt.

---

## 2. Agent-Familie (8 Agents)

Jeder Agent hat einen eigenen Telegram-Bot und eine eigene Workspace-Identität. Nur EOS hat einen vollständig ausgebauten Workspace mit Docs, Vault, Templates, Tests und Daten.

| Agent | Name | Modell | Bot | Rolle |
|-------|------|--------|-----|-------|
| `main` | main | (default: GPT-5.4-mini) | `8635109777:…` | Haupt-Agent, Standard-DM |
| `personal-assistant` | Eos (Personal Assistant) | GPT-5.4-mini | `8634473256:…` | **EOS** — Planer, Kalender, Tasks |
| `pharos` | Pharos (Research) | Gemini 2.5 Pro | `8722196187:…` | Recherche, Orientierung |
| `solara` | Solara (Fitness) | GPT-5.4-mini | `8707561138:…` | Fitness, Coaching, Klienten |
| `photon` | Photon (Coding) | GPT-5.1-codex | `8788385095:…` | Code, Debugging, Automation |
| `lucent` | Lucent (Writing) | Claude Sonnet 4.6 | — | Texte, E-Mails, Kommunikation |
| `aurelius` | Aurelius (Decision) | GPT-5.4 | `8781493462:…` | Entscheidungen, Reviews |
| `lux` | Lux (Utility) | GPT-5.4-mini | `8765291315:…` | Schnelle Einzel-Tasks |

**Beobachtung:** Alle anderen Agents (Pharos bis Lux) haben nur `IDENTITY.md`, `SOUL.md`, `USER.md` und einen `memory/`-Ordner. Sie sind konfiguriert aber inhaltlich noch minimal. EOS ist der einzige Agent mit vollständigem Workspace.

---

## 3. EOS Workspace-Struktur (personal-assistant)

```
workspaces/personal-assistant/
├── IDENTITY.md        — Name, Vibe, Emoji
├── SOUL.md            — Systemrolle, Regeln, Behavior
├── HEARTBEAT.md       — Periodische Agent-Checks (aktuell leer)
├── PLAN.md            — Implementierungsplan
├── MEMORY.md          — Memory-Index
├── AGENTS.md          — Agenten-Übersicht
├── TOOLS.md           — Tool-Übersicht
├── USER.md            — User-Kontext (Endrit)
├── data/              — Operative Datendateien
│   ├── tasks.json         ← STUB (kein live Google Tasks)
│   ├── calendar.json      ← Test-Artefakt (kein live Kalender)
│   ├── planning-schema.json
│   ├── profile.json
│   └── routines.json
├── docs/              — Alle technischen Spezifikationen (31 Dateien)
├── docs_backup_2026-04-22/ — Backup vor letzter Refaktorierung
├── integrations/      — Integrationsnotizen
├── memory/            — Agent-Memory-Files
├── src/               — Quellcode (falls vorhanden)
├── templates/         — Output- und Intake-Templates (10 Dateien)
├── tests/             — E2E-Tests
└── vault/             — Dieser Vault (Human Navigation Layer)
```

---

## 4. Telegram-Setup

**Konfiguration in `openclaw.json`:**

- **dmPolicy**: `allowlist` — nur Endrit (Telegram-ID `6526468834`) kann DMs senden ✓
- **groupPolicy**: `allowlist` ✓
- **Gruppe** `-1003851215474`: konfiguriert mit Topics 2 und 5 (beide behandeln sich wie DMs, `requireMention: false`)
- **historyLimit**: 50 Messages pro Kontext
- **streaming**: `partial` — partielle Antworten werden gestreamt

Jeder Agent bekommt seinen eigenen Bot-Account (8 Accounts total). Das Routing läuft über `bindings`: AccountId → AgentId.

---

## 5. Cron-Jobs (4 Jobs, alle auf EOS)

### 5.1 Sport-Bag-Reminder (LÄUFT ✓)
- **Name:** `sport-bag-reminder-evening-before`
- **Schedule:** täglich 20:00 Europe/Berlin
- **Aufgabe:** Prüft den Kalender von morgen, sendet Sporttaschen-Erinnerung wenn Sport geplant
- **Letzter Lauf:** 2026-04-22, 20:00 — **Erfolg**
  - Geliefert: "Pack heute schon deine Sporttasche. Morgen: 17:00–18:00 Calisthenics draußen"
  - Modell: gpt-5.4, Tokens: 28.148 Input / 311 Output
- **Nächster Lauf:** 2026-04-23, 20:00

### 5.2 Daily Morning Briefing (BEREIT, NOCH NICHT GELAUFEN)
- **Name:** `daily-briefing-morning-0800`
- **Schedule:** täglich 08:00 Europe/Berlin
- **Aufgabe:** Morgenbriefing mit Kalender, Aufgaben, Analyse, Empfehlung
- **Status:** Erstellt, wartet auf ersten Lauf
- **Nächster Lauf:** 2026-04-23, 08:00

### 5.3 Weekly Planning Sunday (BEREIT, NOCH NICHT GELAUFEN)
- **Name:** `weekly-planning-reminder-sunday-1800`
- **Schedule:** Sonntags 18:00 Europe/Berlin
- **Aufgabe:** Wochenplanung mit Kalender + Tasks + Analyse + Empfehlung
- **Status:** Erstellt, wartet auf Sonntag
- **Nächster Lauf:** 2026-04-26 (Sonntag), 18:00

### 5.4 Deep Work Reminder (DEAKTIVIERT, FEHLER)
- **Name:** `Deep Work reminder`
- **Schedule:** War ein One-Shot für 2026-04-22T09:00 (Berlin)
- **Status:** `enabled: false`, `deleteAfterRun: true`
- **Fehler:** `"Sandbox mode requires Docker, but the 'docker' command was not found in PATH"`
- **Ursache:** Job lief in einer isolierten Session (`sessionTarget: "isolated"`), Sandbox versuchte Docker zu nutzen, Docker CLI war im Container nicht verfügbar
- **Konsequenz:** Kein realer Schaden. Job ist deaktiviert.

---

## 6. Was funktioniert (verifiziert)

| Funktion | Beweis |
|----------|--------|
| Telegram-Kanal | Alle Bots konfiguriert und verbunden |
| Sport-Bag-Reminder Cron | Letzter Lauf erfolgreich, Nachricht zugestellt |
| Kalender-Lesezugriff via gog | Sport-Reminder fand erfolgreich den Calisthenics-Termin |
| dmPolicy / Allowlist | Nur Endrit kann DMs senden |
| Sandbox-Config | Konfiguriert: `mode=non-main`, `scope=session`, `network=bridge` |
| mDNS deaktiviert | `discovery.mdns.mode: "off"` ✓ |
| Sensitive Log-Redaktion | `logging.redactSensitive: "tools"` ✓ |
| Elevated Tools disabled | `tools.elevated.enabled: false` ✓ |
| Port nur auf localhost | `127.0.0.1:46301` ✓ |
| 7 spezialisierte Agents | Konfiguriert, Bots zugeordnet |

---

## 7. Was blockiert ist

### BLK-001 / BLK-002 — Keyring-Problem (gog)
- **Symptom:** `gog` schlägt bei interaktiven Planungs-Anfragen fehl
  - `no TTY available for keyring file backend password prompt`
  - Keyring-Datei-Permissions unter `/data/.config/gogcli/keyring/`
- **Wichtige Beobachtung:** Der Sport-Reminder-Cron hat `gog` erfolgreich benutzt. Das legt nahe, dass `gog` im Kontext der laufenden EOS-Haupt-Session funktioniert, aber in neuen/isolierten Sessions scheitert (TTY fehlt → kein interaktives Passwort-Prompt möglich).
- **Fix:** `GOG_KEYRING_PASSWORD` als Umgebungsvariable setzen

### Docker CLI fehlt (für isolierte Cron-Sessions)
- **Symptom:** Sandbox-Mode schlägt fehl für Jobs mit `sessionTarget: "isolated"`
- **Hinweis:** CLAUDE.md beschreibt einen Startup-Script, der Docker CLI installieren soll — offenbar lief dieser entweder nicht oder der Job startete vor der Installation
- **Aktuell:** Kein aktiver Job betroffen (der fehlgeschlagene Job ist deaktiviert)

### Google Tasks — nur Stub
- **`data/tasks.json`** enthält `"provider": "google_tasks_stub"` mit handgepflegten Test-Aufgaben
- **Kein Live-Zugriff** auf Google Tasks API
- **Entschieden:** Rolle via [[ADR - Tasks as Source of Truth]] — Google Tasks = Primärquelle. Implementierung (Auth + v1) noch offen

### Vault Writeback
- Kein automatisches Schreiben in Daily Notes oder andere Vault-Dateien vom Agent
- Alle Vault-Dokumente sind manuell oder per Claude Code entstanden

---

## 8. Was unklar / ungeklärt ist

### hermes-agent Container
- Läuft: `hermes-agent-6eu4-hermes-agent-1`, Port `32768→4860/tcp`
- Nicht in `openclaw.json` dokumentiert
- Keine Erwähnung im Vault oder in den Docs
- Unbekannte Funktion — könnte ein separater Agent-Spawner oder ein Test-Container sein

### EOS V2
- In `docs/` liegen mehrere `EOS-V2-*` Dokumente:
  - `EOS-V2-TECHNICAL-SPEC.md`
  - `EOS-V2-LIVE-E2E-v1.md`
  - `EOS-V2-FOUNDATION-IMPLEMENTATION-v1.md`
  - `EOS-V2-STATE-MODEL-v1.md`
  - `EOS-V2-TIMERS-v1.md`
- Impliziert eine geplante Architektur-Generation nach der aktuellen
- Implementierungsstatus: unklar, vermutlich nur Specs

### `src/` Verzeichnis
- Existiert im Workspace, Inhalt nicht erkundet
- Könnte EOS-spezifischen Code enthalten (z.B. Python-Scheduler-Implementierung)

### OpenAI Subscription vs. API
- Models-Config enthält sowohl `openai-codex/gpt-5.4-mini` als auch `openai/gpt-5.4-mini` als separate Einträge
- `openai-codex` = OAuth-basierte Subscription (Auth-Profil für endrit.murati99@gmail.com existiert)
- `openai` = direkte API-Key-Nutzung
- EOS und mehrere Agents nutzen `openai-codex/gpt-5.4-mini` (Subscription)

### Cron-Job-Modell bei Sport-Reminder
- Der Sport-Reminder lief mit `gpt-5.4` (full model), obwohl EOS als Agent `gpt-5.4-mini` konfiguriert hat
- Mögliche Erklärung: Der Job läuft in der bestehenden EOS-Session, und die Session nutzte evtl. ein anderes Modell zu dem Zeitpunkt

---

## 9. Memory-System

- **Backend:** QMD (`/data/.npm-global/bin/qmd`)
- **Sources:** `memory` + `sessions` (experimentell: Session-Memory aktiv)
- **Heartbeat:** alle 30 Minuten (HEARTBEAT.md ist aktuell leer → kein Heartbeat-Task)
- **Context Pruning:** cache-ttl, 1 Stunde
- **Compaction:** Safeguard-Mode mit Memory-Flush

---

## 10. Plugins & Skills

**Aktive Plugins:**
- `oxylabs-ai-studio-openclaw` v1.0.2 (installiert 2026-04-16)
- `telegram`
- `openai`
- `anthropic`
- `google`
- `browser` (headless, kein Sandbox)
- `memory-core`

**Aktive Skills:**
- `hhmail` — E-Mail-Skill
- `model-switch` — Modell-Wechsel zur Laufzeit
- Zusatzverzeichnis: `/data/.openclaw/skills`

---

## 11. Verhältnis zu den Vault-Dokumenten

Das hier beschriebene System ist der operative Unterbau dessen, was in der Vault als „Phase 1", „EOS-Architektur" und „Blocker" dokumentiert ist.

- [[EOS Current Status]] — gibt den Phasenstatus wieder
- [[EOS Open Issues]] — BLK-001, BLK-002, PEND-001 bis PEND-004
- [[MOC - Architecture]] — Architektur-Übersicht (konzeptionell)
- [[MOC - Scheduler]] — Spezifikationen hinter den Cron-Jobs
- [[MOC - Tasks]] — Zielarchitektur für das, was jetzt nur ein Stub ist
- [[ADR - Calendar as Source of Truth]] — Binding: Google Calendar ist die einzige Zeitquelle
- [[ADR - Tasks as Source of Truth]] — Binding: Google Tasks ist die einzige Task-Quelle

---

## Zuletzt aktualisiert

**2026-04-22** — Erste vollständige Systembestandsaufnahme.
