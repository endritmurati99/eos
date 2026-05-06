# EOS Mail Policy v1

Status: Phase 0 policy

## Purpose

EOS may use Gmail only to improve personal operations: detect important mail, answer needs, waiting loops, receipts, security signals, deadlines, meeting context, and digests.

EOS must not treat Gmail as a playground for autonomous actions. Mail starts read-only.

## Phase Defaults

Phase 1:

- read-only ingestion
- dry-run classification
- digest generation
- label suggestions
- no Gmail mutation

Phase 2:

- safe auto-labeling only after validation
- reversible label writes only
- no delete, send, or sensitive archive

Future phases:

- mail to task and calendar suggestions
- approval-gated writes
- constrained low-risk automation only after explicit policy review

## Label Taxonomy

Recommended labels:

```text
_EOS/Action Required
_EOS/Waiting For Reply
_EOS/Review Needed
_EOS/Read Later
_EOS/Done

_Priority/Critical
_Priority/Important
_Priority/Low

_Money/Banking
_Money/Credit Card
_Money/Invoice
_Money/Receipt
_Money/Tax
_Money/Subscription

_Security/Login Alert
_Security/Password Reset
_Security/OTP
_Security/Suspicious

_Newsletter/High Signal
_Newsletter/Normal
_Newsletter/Low Signal
_Newsletter/Unsubscribe Candidate

_Personal
_Work
_University
_Health
_Travel
_Shopping
_Legal

_Risk/Spam Review
_Risk/Phishing Suspected
_Risk/Unknown Sender
```

## Confidence Thresholds

Default thresholds:

```text
>= 0.95: eligible for future safe auto-label
0.80 to 0.95: label suggestion and digest review
0.60 to 0.80: review only
< 0.60: Review Needed
```

Sensitive categories require stricter treatment:

- banking
- credit card
- tax
- security
- legal
- health
- phishing
- spam

For sensitive categories, high confidence may still mean suggestion-only until Phase 2 review explicitly allows more.

## Safe Actions

At the start:

- list bounded messages
- read metadata and headers
- read snippets or excerpts only as needed
- classify in dry-run mode
- produce digest
- store classification metadata with confidence and reason
- store Gmail message ID and thread ID
- produce label suggestions

## Review Actions

Require later policy and test approval:

- applying labels
- archiving newsletters
- creating tasks from mail
- creating calendar suggestions from mail
- storing body excerpts
- indexing sender profiles
- opening or summarizing attachments

Review-only categories include:

- low-confidence classification
- ambiguous sender identity
- banking, credit card, tax, security, legal, or health signals
- suspected spam or phishing
- any case where suggested action and detected category conflict

## Forbidden Actions

EOS must not do these by default:

- delete mail
- send mail
- archive banking mail
- archive credit card mail
- archive security mail
- archive legal mail
- unsubscribe without approval
- store OTPs
- store password reset links
- store full raw mail bodies without explicit purpose
- classify attachment contents without explicit scope

## Newsletter Policy

- high, normal, low signal, and unsubscribe candidate can be classified
- archive requires training, high confidence, and rollback
- unsubscribe always requires approval
- newsletter quality feedback should update future classification

## Banking/Credit Card Policy

- conservative by default
- never auto-archive in early phases
- label suggestion is allowed
- digest should avoid account numbers, card numbers, balances, and transaction identifiers
- invoice, receipt, tax, and subscription classification is allowed only as metadata and short reason

## Security Mail Policy

- login alerts, password resets, OTPs, and suspicious access are never low risk
- no body persistence for codes or reset links
- suspicious mail should go to review
- never click links or open attachments from suspected security mail without explicit user approval

## Legal and Health Policy

- review-first
- no automatic archive
- no broad summaries without source links
- avoid storing raw content unless explicitly approved for a defined purpose

## Spam/Phishing Policy

- mark as suspected or review
- do not click links
- do not open attachments
- do not unsubscribe from suspected phishing
- do not train safe-sender rules from suspected phishing mail

## Storage Rules

Prefer storing:

- Gmail message ID
- thread ID
- sender domain
- timestamp
- labels suggested
- classification
- confidence
- short reason
- audit run ID

Avoid storing:

- raw full body
- OTPs
- reset links
- account numbers
- full attachment content
- unnecessary personal content

## Audit Logging Requirements

Every mail run must record:

- run ID
- timestamp
- command or job name
- account identifier or alias
- query window
- message count
- classification count
- suggestion count
- write action count
- dry-run flag
- error class

Any future write must also record:

- action type
- message ID
- previous labels if available
- applied labels
- result status
- rollback handle where feasible

## Feedback Loop

EOS should support user feedback for:

- wrong category
- missing action required
- false priority
- safe sender
- risky sender
- newsletter quality

Feedback must update future decisions without rewriting past audit facts.
