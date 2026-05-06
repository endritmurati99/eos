# EOS Gmail Shadow Mode Implementation v1

Status: Agent 3 implementation plan and notes

## Goal

Implement Gmail read-only shadow mode for EOS without Gmail mutations. The feature lists bounded Gmail messages, fetches safe metadata, normalizes classification-ready summaries, emits dry-run audit output, and can render a basic digest.

## Implemented Surface

CLI:

```bash
python3 -m src.eos_cli mail audit --last 7d --dry-run
python3 -m src.eos_cli mail digest --today --dry-run
python3 -m src.eos_cli mail auth-check --dry-run
```

Mail commands are dry-run by default. `--no-dry-run` is rejected because Phase 1 has no write mode.

Modules:

```text
src/eos_mail/gmail_client.py
src/eos_mail/ingestion.py
src/eos_mail/repository.py
src/eos_mail/digest.py
src/eos_mail/audit.py
src/eos_mail/auth_preflight.py
```

## Gmail Access

The implementation uses a read-only client interface:

```text
list_messages(query: str, max_results: int) -> list[MessageRef]
get_message_summary(message_id: str) -> MailSummary
```

The included `gog` adapter uses read commands only:

```text
gog gmail messages search ...
gog gmail get ... --format metadata
```

No methods exist for send, delete, archive, unsubscribe, or label modification.

Live Gmail E2E is not verified by this implementation. The following provider contracts remain unverified until credentials and a reviewed production command run are available:

```text
gog gmail messages search JSON shape in production
gog gmail get --format metadata JSON shape in production
```

## Scope Requirement

Required future Gmail scope:

```text
https://www.googleapis.com/auth/gmail.readonly
```

Suggested `gog` auth shape when explicitly approved:

```bash
gog auth add <account> --services gmail --readonly --gmail-scope=readonly
```

This implementation does not run auth, does not change OAuth configuration, and does not add Gmail write scopes.

OAuth readiness is documented in:

```text
docs/eos/runbooks/EOS-GMAIL-GOOGLE-CLOUD-OAUTH-RUNBOOK.md
docs/eos/contracts/EOS-GMAIL-GOG-CONTRACT-v1.md
```

`mail auth-check --dry-run` performs local preflight only. It checks read-only scope expectations, `gog` availability, account configuration, optional token and credential path presence, and write-scope detection without importing credentials or calling Gmail.

## Stored Data Shape

`MailSummary` includes:

```text
message_id
thread_id
sender
to
subject
date
snippet
headers_subset
has_attachments
label_ids
```

Allowed headers:

```text
From
To
Subject
Date
List-Unsubscribe
Authentication-Results
```

Raw bodies, raw threads, attachment bodies, OTPs, reset links, tokens, and full message payloads are not persisted.

## Persistence

Round 1 uses in-memory repository storage only. SQLite persistence is intentionally deferred because the repo has no migration framework and `data/eos_v2.db` is currently tracked.

Future persistence should add schema-managed tables only after security review:

```text
email_messages
mail_audit_runs
```

## Digest

The digest renderer uses metadata-only fallback buckets:

```text
likely_important
likely_newsletters
likely_finance_security
review_needed
unknown
```

Security and finance-like messages take precedence over newsletter grouping.

## Failure Behavior

If Gmail credentials or scopes are missing, CLI returns a structured failure such as:

```text
auth_required
config_missing
provider_error
```

Errors are sanitized and do not print token contents, account identifiers, auth URLs, credential paths, or raw provider output that appears secret-bearing.

## Non-Goals

Not implemented:

- Gmail label writes
- archive
- delete
- send
- unsubscribe
- task creation
- calendar changes
- OAuth scope changes
- SQLite migration
