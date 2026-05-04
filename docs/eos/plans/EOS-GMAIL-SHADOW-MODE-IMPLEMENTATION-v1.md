# EOS Gmail Shadow Mode Implementation v1

Status: Agent 3 implementation notes integrated with PR #4 classifier. CLI wiring from the original PR #3 branch is intentionally excluded from this integration.

## Goal

Implement Gmail read-only shadow mode for EOS without Gmail mutations. The feature lists bounded Gmail messages, fetches safe metadata, normalizes classification-ready summaries, emits dry-run audit output, and can render a basic digest.

## Implemented Surface

No CLI surface is added in the PR #3/#4 integration branch. Gmail support is module-only in this round.

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

`run_gmail_auth_preflight` performs local preflight only. It checks explicit read-only scope evidence, `gog` availability, account configuration, optional token and credential path presence, and write-scope detection without importing credentials or calling Gmail.

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

The digest renderer adapts `MailSummary` metadata to `MailInput`, runs the PR #4 classifier, and groups into:

```text
critical
action_required
review_needed
finance
security
newsletter_high_signal
newsletter_normal
newsletter_low_signal
unknown
```

If the classifier is unavailable, digest output is marked `partial` with `classifier_unavailable` and falls back to metadata-only grouping.

## Failure Behavior

If Gmail credentials or scopes are missing, preflight returns a structured status or issue such as:

```text
auth_required
config_missing
provider_error
scope_not_verifiable
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
