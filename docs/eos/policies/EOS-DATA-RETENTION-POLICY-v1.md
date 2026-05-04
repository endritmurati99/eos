# EOS Data Retention Policy v1

## 1. Ziel

Diese Policy legt fest, welche EOS-Daten gespeichert, geloggt, geloescht oder dauerhaft ausgeschlossen werden. Sie gilt fuer Gmail, Google Drive, Google Maps/Routes, Google Calendar Location/Travel-Time, Telegram, Runtime-DB, Logs und Smoke-Outputs.

## 2. Datenklassen

- Class 0: Public/test fixture. Oeffentliche Beispiele, synthetische Fixtures und Dummy-Daten ohne Personenbezug.
- Class 1: Operational metadata. Request-IDs, Job-Status, Gate-Ergebnisse, Timestamps und technische Laufzeitdaten ohne Personenbezug.
- Class 2: Personal metadata. E-Mail-Adressen, Kalender-Orte, Gmail/Drive-Metadaten, Chat-IDs und Route-Parameter mit Personenbezug.
- Class 3: Sensitive content. Gmail-Rohtexte, Drive-Dateiinhalte, Kalenderdetails, Location-History, OTPs, Reset-Links und sensible Telegram-Ausgaben.
- Class 4: Secrets/tokens/credentials. API Keys, OAuth Client Secrets, Access/Refresh Tokens, Bot Tokens, Credential-Dateien und absolute Credential-Pfade.

## 3. Was nie gespeichert wird

- Class 4 wird nie gespeichert, nie geloggt und nie committet.
- OTPs und Reset-Links werden nie gespeichert.
- Gmail raw bodies werden nicht dauerhaft gespeichert.
- Drive file content wird nicht automatisch heruntergeladen.
- Maps location history wird nicht gespeichert.
- Telegram output enthaelt keine sensiblen Rohdaten.

## 4. Was temporaer gespeichert werden darf

- Class 0 und Class 1 duerfen fuer Tests, Smoke-Ausgaben und lokale Diagnose temporaer gespeichert werden.
- Class 2 darf nur temporaer gespeichert werden, wenn ein konkreter, dokumentierter Laufzeitgrund besteht.
- Class 3 darf nur im Speicher oder in sofort geloeschten lokalen Testartefakten verarbeitet werden.
- Class 4 darf nicht temporaer persistiert werden.

## 5. Was dauerhaft gespeichert werden darf

- Class 0 darf dauerhaft in Tests, Dokumentation und Fixtures gespeichert werden.
- Class 1 darf dauerhaft gespeichert werden, wenn Logs keine Personen- oder Secret-Werte enthalten.
- Class 2 darf dauerhaft nur mit expliziter Produktfreigabe, dokumentiertem Zweck und Loeschregel gespeichert werden.
- Class 3 und Class 4 duerfen nicht dauerhaft gespeichert werden.

## 6. Retention-Zeiten

- Class 0: unbefristet, solange die Daten synthetisch oder oeffentlich bleiben.
- Class 1: 90 Tage Standard-Retention fuer Runtime- und Audit-Metadaten.
- Class 2: maximal 30 Tage ohne neue Freigabe.
- Class 3: keine dauerhafte Retention; nur fluechtige Verarbeitung.
- Class 4: keine Retention.

## 7. Loeschregeln

- Class 2 und Class 3 werden geloescht, sobald der Laufzeitzweck endet.
- Smoke-Outputs muessen vor Persistenz redigiert werden.
- Loeschungen duerfen keine Secrets in Audit-Logs schreiben.
- Backups muessen dieselben Klassen- und Retention-Regeln einhalten.

## 8. Audit Logs

Audit Logs duerfen Gate-Status, Zeitpunkte, Komponentennamen und redigierte Fehler enthalten. Sie duerfen keine Rohinhalte, Tokens, Credential-Pfade, OTPs, Reset-Links oder Live-Google-Payloads enthalten.

## 9. Gmail

Gmail ist maximal fuer bounded read-only Tests vorgesehen, bis Live-Vertraege und E2E belegt sind. Roh-Bodies und Attachments werden nicht dauerhaft gespeichert. Task Writes aus Mail sind ohne neue Freigabe verboten.

## 10. Drive

Drive ist metadata-only, bis eine neue Freigabe Drive-Content erlaubt. Automatische Downloads, persistierte File-Inhalte und unkontrollierte Caches sind verboten.

## 11. Maps/Locations

Routes duerfen nur als begrenzte Estimate-Inputs verarbeitet werden. Live Tracking, Timeline-Importe und Location-History-Retention sind verboten.

## 12. Calendar

Calendar Location/Travel-Time darf nur read-only und metadata-minimal bewertet werden. Calendar Writes sind ohne neue Freigabe verboten.

## 13. Telegram

Telegram-Ausgaben muessen redigiert sein, bevor sie geloggt oder in Smoke-Outputs gespeichert werden. Chat-IDs gelten mindestens als Class 2.

## 14. DB Runtime State

Die Runtime-DB darf Class 0, Class 1 und explizit freigegebene Class 2 speichern. Class 3 ist nur mit gesonderter Freigabe und enger Retention erlaubt. Class 4 ist verboten.
