# EOS Architecture v1

## Zweck
Bereinigte Produktionssicht für EOS (`personal-assistant`) auf OpenClaw.
Dieses Dokument trennt strikt zwischen:
- **bestätigt**
- **Zielbild**
- **offen / unbewiesen**

---

## 1. Laufzeit- und Sicherheitsmodell

| Bereich | Status | Aussage |
|---|---|---|
| Agent-Workspace | bestätigt | Der Workspace ist der Standard-Arbeitsbereich und Default-CWD für den Agenten. |
| Harte Sandbox | offen / unbewiesen | Der Workspace ist **keine** harte Sicherheitsgrenze ohne zusätzliche Sandbox- und Tool-Restriktionen. |
| Container-/Pfadsicht | Zielbild | Persistente externe Datenpfade sollen explizit gemountet und dokumentiert werden. |
| Minimale Rechte | Zielbild | EOS soll nur die minimal nötigen Skills, Tools und Schreibpfade erhalten. |

### Architekturregel
Workspace = Home/Arbeitsbasis, **nicht automatisch** harter Sicherheitsrand.

---

## 2. Routing und Agentenmodell

| Bereich | Status | Aussage |
|---|---|---|
| Eigener Agent `personal-assistant` | bestätigt | EOS läuft als eigener Agent mit eigenem Workspace. |
| Eigenes Telegram-Routing | bestätigt | Dedizierter Telegram-Bot und Bindings auf `personal-assistant` sind angelegt. |
| Multi-Agent-Zoo | Zielbild negativ | Es soll **kein** diffuser Zoo öffentlicher Agenten entstehen. |
| Interne Fähigkeitsmodule | Zielbild | Interne Rollen wie Planner, Calendar Reader, Routine Engine sind sinnvoll, müssen aber nicht als eigene öffentliche Agenten existieren. |

### Produktionsregel
Ein sichtbarer Hauptagent, interne klar definierte Fähigkeiten, keine unnötige öffentliche Fragmentierung.

---

## 3. Systeme of Record

| System | Status | Rolle |
|---|---|---|
| Google Calendar | bestätigt | Primärquelle für harte Termine und feste Zeitblöcke |
| Google Tasks | Zielbild | Primärquelle für aktive offene Aufgaben |
| Obsidian Vault | Zielbild | Primärquelle für Brain Dumps, Daily Notes, Verlauf, Wissen |
| `data/calendar.json` | bestätigt | Nur Test-/Fallback-Artefakt, nicht Primärquelle |
| `data/tasks.json` | bestätigt | Temporärer Stub, nicht endgültige Produktionsquelle |

### Produktionsregel
Keine Mehrfachwahrheiten. Calendar, Tasks und Vault behalten **strikt getrennte Rollen**.

---

## 4. Google Calendar

| Bereich | Status | Aussage |
|---|---|---|
| Live-Read | bestätigt | Google Calendar Read funktioniert produktiv. |
| Integrationspfad | bestätigt | Der aktuelle Live-Pfad läuft über `gog`. |
| Zeitzone | bestätigt | `Europe/Berlin` ist die operative Planungszeitzone. |
| Mehrkalender-Aggregation | bestätigt | Mindestens `primary` und `Sport` werden aggregiert. |
| Calendar Write | offen / bewusst eingeschränkt | Schreibaktionen sind noch nicht produktiv freigeschaltet. |

### Produktionsregel
Harte Termine werden live gelesen, nicht aus Freitext oder lokalen Stub-Dateien halluziniert.

---

## 5. Google Tasks

| Bereich | Status | Aussage |
|---|---|---|
| Produktivpfad | offen | Noch nicht final entschieden / nicht produktiv verifiziert |
| Maton-basierter Weg | bestätigt, aber nicht bevorzugt | Funktional denkbar, architektonisch aber nicht der saubere Standardpfad |
| Persönlicher Zugriff | bestätigt als Zielprinzip | Für persönlichen Zugriff ist OAuth2 mit User Consent + Refresh-Token der saubere Standardpfad |
| Service Account als Standard | verworfen | Für persönlichen EOS-Zugriff **nicht** die Standardannahme |

### Produktionsregel
Google Tasks für EOS möglichst direkt, headless-fähig und refresh-token-basiert anbinden.

---

## 6. Obsidian / Vault

| Bereich | Status | Aussage |
|---|---|---|
| GUI-Obsidian-App auf VPS | verworfen | Nicht die relevante Produktionsannahme |
| Vault als Markdown-Dateisystem | Zielbild | Das ist der saubere Architekturpfad |
| Live-Mount | offen | Noch nicht als produktiver Dateipfad verifiziert |
| Feste Vault-Struktur | bestätigt als Policy | `00 Inbox`, `01 Daily Notes`, `02 Projects`, `03 Areas`, `04 Knowledge`, `05 Ideas`, `90 Archive` |

### Produktionsregel
Obsidian wird als **Markdown-Vault**, nicht als Desktop-App-Abhängigkeit modelliert.

---

## 7. Planning Core

| Bereich | Status | Aussage |
|---|---|---|
| Daily Planning v1 | bestätigt | Operative Policy und Antwortformat sind festgelegt |
| Weekly Planning v1 | bestätigt | Operative Wochenlogik ist festgelegt |
| Deep Work Standard | bestätigt | 60 Minuten Fokus + 10 Minuten Gehpause |
| Mindest-/volle Routine | bestätigt | Formal getrennt und priorisiert |
| Überladungslogik | bestätigt | Belastung wird aktiv und früh markiert |

### Produktionsregel
EOS plant nicht „schön“, sondern belastungs- und konfliktbewusst.

---

## 8. Skills / Capabilities / Sicherheitsgrenze

| Bereich | Status | Aussage |
|---|---|---|
| Bestätigte reale Integration | bestätigt | `gog` für Google Calendar Read |
| Hübsch klingende Capability-Namen | offen / nur Zielbild | Namen wie `google-calendar-v3` oder `file-system-obsidian` sind ohne Verifikation keine belastbaren Systemfakten |
| Skill-Risiko | bestätigt | Skills müssen als reale Sicherheitsfläche behandelt werden |
| Minimale Skill-Sichtbarkeit | Zielbild | EOS soll nur notwendige Skills und Rechte sehen |

### Produktionsregel
Zwischen **real vorhanden**, **gewünschtes Zielbild** und **bloßem Platzhalter** immer strikt unterscheiden.

---

## 9. Persistenz und Speicherprinzip

| Bereich | Status | Aussage |
|---|---|---|
| OpenClaw/QMD Memory | bestätigt | Bereits aktiv und funktionsfähig |
| Redis/Postgres-Pflicht | verworfen | Nicht pauschal notwendig |
| Dateibasierte Artefakte | bestätigt | Für bestimmte kontrollierte Zwecke legitim |
| Source-of-Truth-Klarheit | Zielbild | Jede Datei/DB braucht eine klare Rolle, sonst drohen Race Conditions oder doppelte Wahrheiten |

### Produktionsregel
Nicht alles in DBs erzwingen. Aber jede Persistenz braucht klare Zuständigkeit.

---

## 10. Hardening

| Bereich | Status | Aussage |
|---|---|---|
| Reverse Proxy | Zielbild | empfohlen |
| Firewall / minimale offene Ports | Zielbild | empfohlen |
| Fail2Ban | Zielbild | empfohlen |
| Token-/Webhook-Validierung | Zielbild | empfohlen |
| Minimale Elevated-/Shell-Rechte | Zielbild | stark empfohlen |

### Produktionsregel
OpenClaw-spezifische Skill- und Tool-Oberfläche ist Teil des Sicherheitsmodells, nicht nur Netzwerk-Hardening.

---

## 11. Eingefrorene bestätigte Basis

Diese Teile gelten jetzt als **stabil bestätigt**:
- eigener Agent `personal-assistant`
- eigener Telegram-Bot / Routing
- Google Calendar Live-Read
- `Europe/Berlin`
- Aggregation mindestens aus `primary` + `Sport`
- Daily Planning Policy v1
- Weekly Planning Policy v1
- Vault-Strategie als Markdown-/Dateisystem-Zielbild

---

## 12. Offene Punkte für produktive Phase 2+

1. Google Tasks produktiv und headless-fähig anbinden
2. Obsidian Vault als echten persistenten Mount-/Dateipfad verifizieren
3. Skill-/Tool-Sichtbarkeit für EOS minimalisieren
4. Schreibrechte nach System getrennt und approval-aware ausrollen
5. Live-E2E für Tasks und Vault ergänzen

---

## 13. Kurzurteil

EOS ist aktuell **für Phase 1 belastbar** als:
- Telegram-gesteuerter persönlicher Planungsagent
- mit live Google Calendar Read
- mit klarer Planning Policy
- aber noch **ohne** final produktiv verifizierte Google-Tasks- und Vault-Schreibpfade
