# EOS Mail Task Proposal Engine v1

## 1. Ziel

The Mail Task Proposal Engine turns mail metadata and mail classification labels into safe task proposals. It does not read Gmail, write Google Tasks, change labels, archive mail, delete mail, send mail, or integrate with the CLI.

The v1 flow is:

```text
Mail metadata + categories
-> deterministic action extraction
-> deadline extraction
-> safety filtering and redaction
-> TaskProposal objects for later approval-aware task write
```

## 2. Architektur

The engine lives in `src/eos_mail_actions/` and is intentionally independent from pending Gmail classifier and Gmail read-only PRs.

Core modules:

- `types.py`: standalone DTOs for input, extraction results, and task proposals.
- `deadline_extractor.py`: deterministic relative and explicit date parsing.
- `action_extractor.py`: deterministic mail-action recognition.
- `safety.py`: sensitive-category approval rules, no-task suppression, list mapping, and note redaction.
- `task_proposal.py`: conversion from action extractions into task proposals.

## 3. Input/Output

Input is a `MailActionInput` with message IDs, sender, subject, snippet, optional body excerpt, categories, priority, and optional received timestamp.

Output is a list of `TaskProposal` objects:

```text
source
source_message_id
title
notes
due
list_name
confidence
requires_approval
reason
risk_flags
```

The engine stores nothing. Callers decide whether and where to persist proposals.

## 4. Safety Rules

Sensitive categories always require approval:

```text
_Money/Banking
_Money/Credit Card
_Security/*
_Legal
_Health
```

Suppressed categories produce no task by default:

```text
_Newsletter/*
_Money/Receipt
_Security/OTP
_Security/Password Reset
_Risk/Spam Review
_Risk/Phishing Suspected
```

Normal reply tasks may skip approval only when the request is clear, nonsensitive, and confidence is at least `0.85`.

Task proposal notes are redacted for code-like values, reset/login links, IBAN/account/card-like numbers, and long token-like identifiers.

## 5. Deadline Extraction

Supported deterministic deadline signals:

```text
today / heute
tomorrow / morgen
by Friday / bis Freitag
until Monday / bis Montag
due on 2026-05-10
faellig am 10.05.2026
within 3 days
bis Ende der Woche
```

Deadline output is ISO `YYYY-MM-DD`. The base date is `received_at`, then explicit `reference_date`, then local today.

Uncertain deadline phrases such as `soon`, `asap`, `next week`, or bare `deadline` produce:

```text
due=None
requires_approval=True
risk_flags=["deadline_uncertain"]
```

## 6. Task Mapping

Default mapping:

```text
reply_required      -> Inbox
confirm_required    -> Inbox
send_document       -> Inbox
review_invoice      -> Inbox
pay_invoice         -> Inbox
check_bank_alert    -> Review
review_security_alert -> Review
review_legal_notice -> Review
prepare_meeting     -> Next
schedule_followup   -> Next
waiting_for_reply   -> Waiting
```

Any sensitive category overrides the target list to `Review`.

## 7. Synthetic Tests

The synthetic fixture set covers at least:

```text
reply_by_friday
confirm_appointment
send_document
invoice_due_date
receipt_no_action
bank_alert_review
credit_card_charge_review
security_login_alert_review
password_reset_no_task
legal_notice_review
health_appointment_confirm
meeting_prepare
meeting_followup
waiting_for_reply
newsletter_no_task
spam_no_task
phishing_no_task
ambiguous_deadline_review
```

The tests use no real mail data, no credentials, and no external APIs.

## 8. Nicht-Ziele

This phase does not implement:

- Gmail API access
- Gmail OAuth changes
- Gmail label writes
- Gmail archive/delete/send/unsubscribe
- Google Tasks writes
- CLI integration
- persistence
- live mail processing

## 9. Grenzen

The engine is deterministic and intentionally conservative. It may miss subtle action requests and should prefer review over automation for ambiguous or sensitive mail. It does not infer facts from complete threads, attachments, calendars, or task history.

## 10. Nächste Phase: Task Write mit Approval

The next phase may connect proposals to an approval-aware task writer. That phase must add:

- explicit user approval for sensitive proposals
- idempotency keys for task creation
- audit logging for proposed and accepted writes
- rollback/reconciliation behavior
- contract tests against the Google Tasks gateway
