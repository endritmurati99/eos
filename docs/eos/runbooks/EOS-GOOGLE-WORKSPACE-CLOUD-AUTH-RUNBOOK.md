# EOS Google Workspace Cloud Auth Runbook

Status: readiness only. Cloud console steps, OAuth flows, Maps calls, Drive calls, Gmail calls, and Calendar calls are not live verified by this change.

## 1. Goal

Prepare EOS for a shared Google platform strategy across Gmail, Drive, Calendar, and Maps/Routes without adding live calls, write scopes, secrets, or persistent location history.

## 2. Why A Shared Strategy Is Needed

EOS will eventually combine read-only signals from mail, documents, calendar locations, and route estimates. A shared Google Cloud and secret-handling strategy prevents scope drift and keeps Phase 1 integrations auditable.

## 3. Gmail Read-only

Gmail remains owned by the open Gmail PRs. This branch does not change `src/eos_mail`. The intended Phase 1 scope is:

```text
https://www.googleapis.com/auth/gmail.readonly
```

## 4. Drive Metadata Read-only

Drive readiness is metadata-only. EOS may list file id, filename, MIME type, modified time, and web link. EOS must not download file content or persist raw documents.

Required scope:

```text
https://www.googleapis.com/auth/drive.metadata.readonly
```

## 5. Calendar Read-only

Calendar location intelligence expects read-only event metadata, start/end times, location, and calendar role. Calendar writes remain out of scope.

Required scope:

```text
https://www.googleapis.com/auth/calendar.readonly
```

## 6. Maps / Routes API Readiness

Maps readiness uses an API key placeholder only. This branch uses a deterministic fake provider. Live route calls are a later verification step.

## 7. OAuth Token Storage

Store OAuth tokens outside the repository and reference them with environment variables. Do not commit tokens, provider config, screenshots containing auth URLs, or one-time codes.

## 8. API Key Storage

Store Maps API keys outside the repository. `.env.example` may contain only an empty placeholder.

## 9. Environment Variables

Use `.env.example` as the non-secret template:

```text
EOS_GOOGLE_ACCOUNT=your-google-account@example.com
EOS_GOOGLE_TOKEN_PATH=
EOS_GOOGLE_CREDENTIALS_PATH=
EOS_GMAIL_READONLY_ENABLED=false
EOS_DRIVE_READONLY_ENABLED=false
EOS_CALENDAR_READONLY_ENABLED=false
EOS_MAPS_ROUTES_ENABLED=false
EOS_GOOGLE_MAPS_API_KEY=
EOS_HOME_LOCATION_LABEL=home
EOS_DEFAULT_TRAVEL_MODE=driving
EOS_TRAVEL_TIME_BUFFER_MINUTES=15
```

## 10. Live E2E Activation

Run live E2E only after the database runtime blocker is fixed and the read-only PR sequence is merged. Start with bounded read-only smoke tests, then verify each provider contract separately.

## 11. Forbidden Scopes

Forbidden early scopes include Gmail modify/send/compose, full mail access, full Drive access, Drive file write access, full Calendar access, and Calendar event write access.

## 12. Forbidden Actions

Do not send, delete, archive, label, unsubscribe, download Drive content, change Drive permissions, create Calendar events, update Calendar events, delete Calendar events, or perform live location tracking.

## 13. Privacy

Use synthetic locations in fixtures. Do not store real addresses, latitude/longitude history, route history, document bodies, mail bodies, tokens, credentials, or API keys.

## 14. Troubleshooting

- `live_verified=false`: expected until local provider and Google Cloud setup are tested.
- Missing API key: acceptable for fake-provider tests.
- Missing OAuth token: acceptable for readiness tests.
- Readonly database failure: classify as a runtime blocker outside Google Platform readiness.
