# EOS Gmail Google Cloud OAuth Runbook

Status: Phase 1 read-only readiness notes. Google Cloud UI steps, live provider contract, and live Gmail E2E are not verified by this repository change.

## 1. Goal

Prepare EOS for Gmail read-only shadow mode without adding Gmail write actions, storing real secrets, or persisting personal mail bodies.

## 2. Why Gmail Needs Google Cloud OAuth

Gmail API access requires a Google Cloud project, Gmail API enablement, an OAuth consent screen, OAuth client credentials, and a refresh token granted for the intended scope. EOS Phase 1 expects the local `gog` provider to own the OAuth flow and token storage.

## 3. Read-only Phase-1 Scope

Required scope:

```text
https://www.googleapis.com/auth/gmail.readonly
```

Forbidden early scopes:

```text
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/gmail.compose
https://mail.google.com/
```

## 4. Google Cloud Project

Use a dedicated Google Cloud project for EOS Gmail experimentation. Keep production and development credentials separate. Do not commit project IDs, OAuth client JSON, tokens, or exported provider config.

## 5. Enable Gmail API

In the selected Google Cloud project, enable the Gmail API. The exact Cloud Console navigation can change, so verify the current UI before documenting production screenshots or operator instructions.

## 6. OAuth Consent Screen

Configure an OAuth consent screen suitable for the account type. Add only the read-only Gmail scope for Phase 1. Keep the app in the smallest practical test-user set until live E2E is reviewed.

## 7. OAuth Client Credentials

Create OAuth client credentials appropriate for the `gog` flow used locally. Store the downloaded credentials JSON outside the repository and reference it through environment configuration only.

## 8. Token Storage

Store refresh tokens outside the repository. Recommended environment variables are documented in `.env.example`. Do not commit tokens, provider config directories, credential JSON, or screenshots containing auth URLs or one-time codes.

## 9. gog-based Auth

The current read-only adapter assumes `gog` handles credentials and tokens. A possible auth shape is:

```bash
gog auth add <account> --services gmail --readonly --gmail-scope=readonly
```

This command shape is guidance only until verified against the installed `gog` version.

## 10. Environment Variables

Use placeholder values in `.env.example` and real values only in local secret stores:

```text
EOS_GOG_BIN=gog
EOS_GOOGLE_ACCOUNT=your-google-account@example.com
EOS_GOOGLE_TOKEN_PATH=
EOS_GMAIL_SCOPES=https://www.googleapis.com/auth/gmail.readonly
EOS_GMAIL_READONLY_ENABLED=false
EOS_GMAIL_MAX_RESULTS=50
EOS_GOOGLE_CREDENTIALS_PATH=
```

## 11. Pending Live E2E Test

No live Gmail E2E or OAuth browser flow is executed by this integration. The bounded live provider contract remains pending until an operator can verify all of the following with reviewed credentials and no secret output:

- explicit `https://www.googleapis.com/auth/gmail.readonly` scope configuration or provider auth status
- no Gmail write scopes
- one bounded metadata-only search
- one bounded metadata-only message fetch
- no stored full bodies, tokens, auth URLs, OTPs, reset links, or raw payloads in output

## 12. Troubleshooting

- `config_missing`: install or configure `gog`, set `EOS_GOOGLE_ACCOUNT`, or prepare OAuth credentials.
- `warning` with `scope_not_verifiable`: add an explicit read-only Gmail scope list or provider auth status before treating readiness as configured.
- `auth_required`: grant a read-only Gmail token through the approved provider flow.
- `provider_error`: inspect the local `gog` version and compare it with the contract in `docs/eos/contracts/EOS-GMAIL-GOG-CONTRACT-v1.md`.
- `failed` with write scopes detected: remove all Gmail write scopes before retrying.

## 13. Forbidden Actions

Phase 1 must not label, archive, delete, trash, send, compose, unsubscribe, mark read/unread, create tasks, create calendar events, or request Gmail write scopes.
