# EOS Gmail gog Contract v1

Status: assumed contract. Live `gog` Gmail command syntax and JSON response shapes are not verified by this repository change. The bounded live provider contract remains pending.

```yaml
provider_contract_verified: false
live_e2e_verified: false
```

## Assumed Read-only Commands

Search bounded message references:

```bash
gog gmail messages search <query> --max <n> --json --results-only --no-input
```

Fetch metadata for one message:

```bash
gog gmail get <message_id> --format metadata --headers From,To,Subject,Date,List-Unsubscribe,Authentication-Results --json --results-only --no-input
```

The runtime adapter adds the configured account with `-a <account>` and never passes Gmail write scopes.

## Expected Data Shape

Search output is expected to contain message reference objects with an `id` or `message_id`, and optionally `threadId` or `thread_id` plus labels.

Metadata output is expected to contain a single Gmail message object with metadata headers, `snippet`, attachment filenames, and labels. EOS stores only the normalized `MailSummary` fields and does not persist raw bodies, raw payloads, attachment bodies, OTPs, reset links, or full mail text.

## Local Contract Verification

These commands define the pending bounded live provider contract after Google Cloud OAuth is configured and reviewed. They are not executed by this integration change:

```bash
gog --help
gog gmail --help || true
gog gmail messages --help || true
gog gmail messages search "newer_than:1d" --max 1 --json --results-only --no-input
gog gmail get <message_id> --format metadata --headers From,To,Subject,Date,List-Unsubscribe,Authentication-Results --json --results-only --no-input
```

If the installed `gog` syntax differs:

1. Document the real syntax here.
2. Update `src/eos_mail/gmail_client.py`.
3. Update the contract tests.
4. Rerun the Gmail mail test suite.

## Forbidden Contract Surface

The contract must not include Gmail label writes, archive, delete, trash, send, compose, unsubscribe actions, mark read/unread, or write scopes:

```text
https://www.googleapis.com/auth/gmail.modify
https://www.googleapis.com/auth/gmail.send
https://www.googleapis.com/auth/gmail.compose
https://mail.google.com/
```

`List-Unsubscribe` is allowed only as a metadata header read from Gmail, not as an unsubscribe action.

## CLI Gate Status

The Phase 1 CLI exposes `mail auth-check`, `mail audit`, and `mail digest` only as dry-run/preflight commands. These commands do not prove the live provider contract and must not be cited as evidence that Gmail works live.
