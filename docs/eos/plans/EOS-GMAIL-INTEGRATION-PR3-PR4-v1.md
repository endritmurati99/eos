# EOS Gmail PR3/PR4 Integration v1

## 1. Goal

Integrate the Gmail classifier from PR #4 with the read-only Gmail shadow digest from PR #3. The result keeps Gmail in metadata-only shadow mode, uses deterministic classifier categories for digest grouping, and keeps all live provider work explicitly unverified.

## 2. Why PR #4 Before PR #3

PR #4 defines the classifier contract: `MailInput`, `MailClassification`, classifier rules, and synthetic corpus coverage. PR #3 can then adapt Gmail `MailSummary` metadata into that classifier contract instead of maintaining a separate heuristic digest taxonomy.

## 3. `__init__.py` Conflict Resolution

`src/eos_mail/__init__.py` exports both public API groups without initializing providers:

- Classifier: `MailInput`, `MailClassification`, `classify_mail`
- Read-only Gmail: `GogGmailReadOnlyClient`, `GmailClientError`, `GmailReadOnlyClient`, `MailSummary`, `MessageRef`, `render_shadow_digest`, `run_mail_audit`, `run_gmail_auth_preflight`

## 4. Classifier to Digest Flow

The digest maps `MailSummary` to `MailInput` using only message IDs, sender, subject, snippet, thread ID, and allowed metadata headers. `body_excerpt` is always `None`. Classifier output feeds the digest buckets: `critical`, `action_required`, `review_needed`, `finance`, `security`, `newsletter_high_signal`, `newsletter_normal`, `newsletter_low_signal`, and `unknown`.

If the classifier is unavailable, the digest returns `status: partial`, `issue: classifier_unavailable`, and falls back to metadata-only grouping.

## 5. Auth Preflight Strictness

`readonly_scope_configured` is true only when an explicit scope source contains `https://www.googleapis.com/auth/gmail.readonly` or provider auth status explicitly confirms read-only scope. Missing scope information yields `scope_not_verifiable` and warning readiness, not a false read-only success.

Write-scope detection is based on explicit scope sources only and flags `gmail.modify`, `gmail.send`, `gmail.compose`, and `https://mail.google.com/`.

## 6. Live Contract Status

The integration keeps these statuses separate:

- `config_readiness`
- `provider_contract_readiness`
- `live_e2e_readiness`

`provider_contract_verified`, `live_contract_verified`, and `live_e2e_verified` remain false. The bounded live provider contract is pending.

## 7. Tests

Coverage includes classifier digest integration, strict auth preflight behavior, write guard checks, metadata-only digest fallback, no body persistence, and the PR #4 synthetic classifier corpus.

## 8. Non-goals

This integration does not add Gmail labels, archive, delete, trash, send, compose, unsubscribe, CLI integration, OAuth login, live Gmail reads, tokens, credentials, or real Gmail data.

## 9. Next Step

Run a bounded live provider contract later with reviewed credentials, no secret output, metadata-only reads, and no write scopes.
