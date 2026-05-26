# EOS Google Live E2E Gate Runbook

## 1. Ziel

Dieses Runbook beschreibt, wie bounded Google Live Readiness vorbereitet und bewertet wird. Es implementiert keine Live-Calls und ersetzt keine gesonderte Freigabe.

## 2. Voraussetzungen

- `EOS_GOOGLE_LIVE_E2E_ENABLED=true` ist gesetzt.
- Der jeweilige Service-Flag ist explizit gesetzt.
- Scopes sind minimal und read-only, solange kein G5 genehmigt ist.
- Redaction- und Secret-Pattern-Tests laufen gruen.
- Keine echten Credentials werden committet, geloggt oder in Smoke-Outputs geschrieben.

## 3. Gmail bounded read-only live test

- Nur Read-only.
- Nur eine kleine, explizit begrenzte Ergebnismenge.
- Keine Writes, keine Task-Erzeugung, keine dauerhafte Body-Retention.
- Erfolg bedeutet nur, dass G3 technisch erreichbar ist; es ist keine Produktionsfreigabe.

## 4. Drive metadata-only live test

- Nur Metadata.
- Keine automatischen Downloads.
- Keine Datei-Inhalte in Logs oder Runtime-State.
- Erfolg bedeutet nur, dass Metadata-only Readiness plausibel ist.

## 5. Maps route estimate live test

- Nur einzelner, begrenzter Route Estimate.
- Keine Live-Tracking-Session.
- Keine Location-History-Retention.
- Inputs und Outputs werden vor Speicherung redigiert oder verworfen.

## 6. Calendar location/travel-time test

- Nur Read-only Location/Travel-Time Bewertung.
- Keine Calendar Writes.
- Keine dauerhafte Speicherung detaillierter Event-Orte ohne separate Freigabe.

## 7. Disable switches

- Global: `EOS_GOOGLE_LIVE_E2E_ENABLED=false`.
- Gmail: `EOS_GMAIL_READONLY_ENABLED=false`.
- Drive: `EOS_DRIVE_READONLY_ENABLED=false`.
- Maps: `EOS_MAPS_ROUTES_ENABLED=false`.
- Calendar Location/Travel-Time: kein Live-Enable-Switch in diesem Gate; bleibt blockiert.

## 8. Rollback

- Disable Switch auf `false` setzen.
- Laufende Jobs stoppen.
- Redigierte Logs pruefen.
- Temporare Class-2/Class-3-Artefakte loeschen.
- Keine Secrets in Incident- oder Audit-Text kopieren.

## 9. What success means

Success bedeutet, dass der jeweilige Gate-Test begrenzt, read-only, redigiert und ohne unerlaubte Persistenz durchfuehrbar ist.

## 10. What success does not mean

Success bedeutet keine Freigabe fuer Writes, breite Produktion, automatische Downloads, Location Tracking, Task Writes aus Mail oder dauerhafte Speicherung sensibler Inhalte.
