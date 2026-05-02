# EOS Operating Contract v1

## Zweck
Dieser Vertrag beschreibt die bestätigten Betriebsannahmen und die offenen Punkte für EOS im laufenden OpenClaw-Setup.

## Bestätigt
- EOS läuft als eigener Agent `personal-assistant`
- EOS hat eigenes Telegram-Routing
- Google Calendar Live-Read funktioniert produktiv
- Planungszeitzone ist `Europe/Berlin`
- Daily Planning und Weekly Planning sind fachlich definiert

## Betriebsannahmen
### Workspace und Pfade
- Der Agent arbeitet primär im konfigurierten Workspace
- Der Workspace ist Arbeitsbasis und Kontextquelle
- Der Workspace ist **keine harte Sandbox** ohne zusätzliche Sandbox-, Tool- und Container-Policies
- Absolute Pfade und zusätzliche Dateizugriffe dürfen nicht blind als sicher angenommen werden

### Mounts und Vault-Pfade
- Persistente Vault-Pfade müssen explizit definiert und im realen Setup verifiziert werden
- Keine angenommenen Containerpfade als Fakt dokumentieren, bevor sie im laufenden Deployment bestätigt wurden
- Der Vault-Mount muss an den tatsächlich konfigurierten Workspace oder an einen bewusst referenzierten Pfad im Agent-Kontext gebunden werden

### Google Calendar
- Google Calendar ist aktuell die produktiv bestätigte externe Zeitquelle
- Relevante Kalender werden aggregiert, mindestens `primary` und `Sport`
- Calendar Read ist Primärquelle für harte Termine

### Google Tasks
- Google Tasks ist noch nicht produktiv finalisiert
- Für persönlichen EOS-Zugriff ist der Standardpfad: OAuth 2.0 mit User Consent und Refresh-Token
- Service Account ist hierfür **nicht** der Standardpfad
- Drittanbieter- oder Proxy-Wege dürfen nur bewusst akzeptiert und abgesichert eingesetzt werden

### Obsidian / Vault
- Obsidian wird im VPS-Kontext als Markdown-Vault-Dateisystem gedacht, nicht als Desktop-App-Annahme
- Schreibpfade, Mounts und Permissions müssen im echten Containerlauf verifiziert werden

### Skills / Tools / Sicherheit
- Minimale Skill-Sichtbarkeit pro Agent ist Teil des Sicherheitsmodells
- Kontrollierte Tool-Rechte sind wichtiger als bloß generische Firewall-Ratschläge
- Platzhalter-Bezeichnungen für Skills oder Komponenten dürfen nicht als bestätigte Systemfakten behandelt werden

## Platzhalter-Regel
Wenn ein Komponentenname nicht live im Setup verifiziert wurde, muss er als eines von drei Dingen markiert werden:
- bestätigt
- Zielbild
- Platzhalter

## Produktionsregel
Nur bestätigte Komponenten dürfen als operative Wahrheit in Go-Live-Dokumenten stehen.
