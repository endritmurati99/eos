# EOS Google Live Readiness Policy v1

## Ziel

Diese Policy definiert Gates fuer Google-Dienste. Sie erlaubt keine Live-Calls durch sich selbst und dient als Freigabe- und Testmatrix fuer Gmail, Drive, Maps/Routes und Calendar Location/Travel-Time.

## Gate-Matrix

- G0 synthetic only: Nur Fixtures, Fakes und lokale Tests.
- G1 contract fake provider: API-Vertraege werden gegen Fake Provider validiert.
- G2 local config preflight: Lokale Konfiguration, Scopes, Flags und Redaction werden ohne Live-Call geprueft.
- G3 bounded live read-only test: Begrenzter Live-Read-only-Test mit explizitem Gate `EOS_GOOGLE_LIVE_E2E_ENABLED=true`.
- G4 limited production dry-run: Produktionsnaher Dry-Run ohne persistente Writes.
- G5 controlled reversible write: Begrenzter, reversibler Write mit Rollback-Plan und neuer Freigabe.

## Aktuell erlaubter Stand

- Gmail: maximal G2; G3 pending.
- Drive: maximal G1; G2 pending.
- Maps: maximal G1; G2 pending.
- Calendar Travel-Time: maximal G1; G2 pending.

## Verboten ohne neue Freigabe

- Gmail writes.
- Drive file downloads.
- Calendar writes.
- Maps live tracking.
- Task writes from mail.

## No-Live-Calls Default

Alle Google-Live-Pfade sind standardmaessig blockiert. Bounded Live Readiness darf erst als moeglich gelten, wenn `EOS_GOOGLE_LIVE_E2E_ENABLED=true` und der jeweilige Service-Flag explizit aktiviert ist.

## Disable Switches

- `EOS_GOOGLE_LIVE_E2E_ENABLED=false` blockiert alle Live-E2E-Gates.
- `EOS_GMAIL_READONLY_ENABLED=false` blockiert Gmail Live Read-only.
- `EOS_DRIVE_READONLY_ENABLED=false` blockiert Drive Live Read-only.
- `EOS_MAPS_ROUTES_ENABLED=false` blockiert Maps/Routes Live Estimates.
- Calendar Location/Travel-Time hat in diesem Gate keinen Live-Enable-Switch und bleibt blockiert.

## Logging und Retention

Gate-Checks duerfen nur redigierte Statusdaten ausgeben. Rohdaten aus Gmail, Drive, Maps, Calendar, Credentials, Tokens, OTPs und Reset-Links duerfen nicht in Logs, Smoke-Outputs oder Runtime-State landen.
