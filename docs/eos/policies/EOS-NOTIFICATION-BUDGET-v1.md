# EOS Notification Budget v1

Status: Phase 0 policy

## Purpose

EOS notifications should reduce operational load, not create interruption load. Telegram is the main delivery channel, but it must be budgeted.

## Default Channel

Primary channel:

- Telegram

Other channels may be added later only with explicit routing policy.

## Notification Principles

EOS should notify only when:

- a decision is needed
- a digest was scheduled
- a real risk is detected
- a user-requested reminder is due
- a job has useful output

EOS should avoid:

- constant status pings
- repeated low-value reminders
- verbose explanations in notifications
- sending when source data is missing and the output would be speculative

## Digest First

Prefer bundled digests over scattered messages.

Useful digest types:

- morning plan
- evening review
- weekly sync
- mail digest
- meeting prep digest
- habit check-in

## Escalation

Escalation should be rare.

Allowed escalation reasons:

- imminent hard calendar conflict
- high-confidence security risk
- critical deadline detected
- user-requested reminder
- failed important automation that requires manual action

Not escalation-worthy by default:

- ordinary newsletter
- low-priority shopping update
- weak classifier guess
- non-urgent FYI

## Budget Rules

Default rules:

- batch where practical
- do not send duplicate messages for one job run
- do not send if live source read failed for a source-critical message
- include only the actionable summary
- keep source details available in logs or follow-up views

## Sensitive Notifications

For sensitive categories:

- avoid exposing account numbers, OTPs, reset links, or legal details
- prefer "review needed" wording
- include minimal source identifiers
- do not forward raw mail content into Telegram by default

## Audit Requirements

Notification sends should record:

- job or command
- run ID
- channel
- target alias, not raw secret
- message digest
- status
- error class
- timestamp
- idempotency key where applicable

## Future Implementation Requirements

Before adding new notification flows:

- define trigger
- define max frequency
- define suppression rules
- define source-read requirements
- define idempotency key
- define failure behavior
