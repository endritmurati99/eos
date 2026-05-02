# EOS Action Authorization Policy v1

Status: Phase 0 policy

## Purpose

This policy defines what EOS may read, summarize, suggest, write, or do autonomously. The default posture is conservative: read first, dry-run first, reversible actions before irreversible actions, and approval for sensitive writes.

## Authorization Levels

```text
L0: Read only
L1: Summarize
L2: Suggest
L3: Low-risk reversible action
L4: Draft for approval
L5: Autonomous constrained action
```

## Level Definitions

L0 Read only:

- read bounded source data
- no mutation
- no user-visible external action

L1 Summarize:

- produce summaries or digests from read data
- cite or identify sources when relevant
- no source mutation

L2 Suggest:

- recommend labels, tasks, calendar blocks, replies, or follow-ups
- no external writes unless separately approved

L3 Low-risk reversible action:

- write only when action is low-risk, reversible, policy-allowed, and audited
- examples may include safe labels after validation

L4 Draft for approval:

- prepare a draft action that the user must approve
- examples include mail replies, calendar changes, or sensitive task creation

L5 Autonomous constrained action:

- narrow, pre-approved, low-risk automation only
- requires tests, audit, rollback, and explicit allowlist

## Defaults

```text
Mail read: L0
Mail digest: L1
Mail label suggestion: L2
Safe label apply: L3 after validation
Newsletter archive: L3 only after training
Mail delete: forbidden by default
Mail send: forbidden by default
Calendar hard event update: forbidden by default
Task create: L2 or L3 depending confidence and user policy
Task complete: only with strong evidence
Memory answer: L1 with sources
Notification digest: L1
Urgent escalation: L2 unless already allowlisted
```

## Approval Required

Approval is required for:

- sending mail
- deleting mail
- unsubscribing
- archiving sensitive mail
- changing hard calendar events
- completing tasks without clear user command
- storing raw sensitive content
- broad memory persistence from new sources
- any action involving money, legal, security, or health unless explicitly allowlisted

## Forbidden by Default

EOS must not:

- delete mail
- send mail
- move money
- click links in suspected phishing mail
- open attachments without explicit purpose
- persist OTPs
- persist password reset links
- silently change hard calendar commitments
- silently mark tasks complete based on weak evidence

## Write Preconditions

Any external write requires:

- policy allows the action
- action level is known
- source IDs are recorded
- dry-run behavior exists or was explicitly waived
- confidence is sufficient
- idempotency strategy exists where repeated execution is possible
- result is auditable
- read-after-write verification exists for important writes

## Audit Requirements

Each action record should include:

- action ID
- authorization level
- source system
- target system
- source IDs
- user command or trigger
- confidence
- dry-run flag
- approval status
- result status
- timestamp
- error class

## Rollback Requirements

L3 and above need rollback or compensation where feasible.

Examples:

- label write: remove label applied by EOS
- archive: unarchive if EOS applied the archive
- task create: mark EOS-created task as canceled or delete only with approval
- calendar create: remove EOS-created event only with approval

Irreversible or destructive actions should stay forbidden unless explicitly approved for a single action.
