# EOS Roadmap

Status: Phase roadmap
Date: 2026-05

## Summary

EOS must grow in controlled phases. Gmail write actions, task writes, calendar writes, memory persistence, and autonomous actions are not safe starting points. The current roadmap prioritizes durable context, repository audit, and policies before adding Gmail intelligence.

## Phase 0: Context, Audit, and Policies

Goal:

- store the EOS direction in the repository
- audit the current architecture
- define authorization, mail, memory, calendar intelligence, habit, journal, and notification policies

Deliverables:

- `docs/eos/EOS-MASTER-CONTEXT.md`
- `docs/eos/EOS-ROADMAP.md`
- repository audit
- config and secrets handling notes in the repository audit
- policy documents

Non-Goals:

- no Gmail API integration
- no OAuth scope changes
- no label writes
- no database migration
- no scheduler change
- no autonomous actions

Dependencies:

- confirmed local repository and current codebase inspection

Exit Criteria:

- repo state is documented with code references
- security risks are documented without exposing secrets
- policies define what is allowed, suggested, approval-gated, and forbidden
- Phase 1 dependencies are explicit

Risks:

- documentation diverges from code
- future agents implement Gmail write actions too early
- existing tracked local state may become unsafe if mail data is added without review

## Phase 1: Gmail Read-Only Shadow Mode

Goal:

- read Gmail metadata and bounded message context
- classify mail in dry-run mode
- generate digests and label suggestions without changing Gmail

Deliverables:

- Gmail client design
- classifier design
- dry-run CLI contract
- synthetic test corpus
- audit logging design

Non-Goals:

- no label writes
- no archive
- no delete
- no send
- no unsubscribe
- no task or calendar writes

Dependencies:

- Phase 0 repository audit
- Phase 0 policy foundation
- Phase 0 config/secrets handling review

Exit Criteria:

- read-only OAuth strategy is defined
- no raw sensitive content is persisted by default
- synthetic tests cover risky categories
- digest output is useful without mutating Gmail

Risks:

- over-storing mail content
- false confidence in mock-only tests
- unbounded ingestion

## Phase 2: Safe Auto-Labeling

Goal:

- apply only low-risk reversible labels after shadow-mode validation

Deliverables:

- safe label apply flow
- review queue
- feedback loop
- read-after-write verification
- rollback procedure for labels applied by EOS

Non-Goals:

- no delete
- no send
- no archive for sensitive categories
- no unsubscribe without approval

Dependencies:

- successful Phase 1 dry-runs
- reviewed false-positive rates
- explicit label policy

Exit Criteria:

- high-confidence categories can be labeled safely
- sensitive categories remain conservative
- all label writes are auditable

Risks:

- incorrect labels on banking, legal, or security mail
- label drift without feedback

## Phase 3: Mail to Task and Calendar Suggestions

Goal:

- turn mail into task and calendar suggestions while keeping writes approval-aware

Deliverables:

- extraction of action requests, deadlines, and event candidates
- task suggestion contract
- calendar suggestion contract
- approval flow

Non-Goals:

- no autonomous calendar hard-event creation
- no task completion without strong evidence
- no mail send

Dependencies:

- Phase 1 and Phase 2 results
- action authorization policy

Exit Criteria:

- suggestions include source message IDs and confidence
- approval-gated writes are read-after-write verified
- ambiguous extraction asks one short clarification

Risks:

- creating duplicate tasks
- treating tentative dates as hard commitments

## Phase 4: Meeting Intelligence

Goal:

- answer meeting questions and prepare meeting briefs using calendar, mail, tasks, and vault sources

Deliverables:

- meeting brief generation
- conflict detection
- prep window suggestions
- follow-up detection
- source-backed meeting recall

Non-Goals:

- no automatic hard-event rescheduling
- no calendar update without approval

Dependencies:

- Phase 0 audit
- calendar intelligence policy
- optional Phase 1 mail context

Exit Criteria:

- meeting answers include evidence and uncertainty
- prep recommendations are bounded and actionable

Risks:

- hallucinated meeting context
- leaking sensitive mail or notes into broad summaries

## Phase 5: Personal Memory

Goal:

- answer personal operational questions with source-backed recall

Deliverables:

- memory source index
- retriever
- source link model
- uncertainty format

Non-Goals:

- no unsourced claims
- no broad raw-content hoarding
- no sensitive code or OTP storage

Dependencies:

- memory policy
- source-link storage model

Exit Criteria:

- answers cite calendar events, mail threads, tasks, or vault notes
- uncertain answers say what is uncertain
- sensitive content is minimized

Risks:

- memory becoming a second source of truth
- storing more personal data than needed

## Phase 6: Habit and Journal Coach

Goal:

- use a small set of signals for better planning without guilt-driven streak mechanics

Deliverables:

- morning prompt
- evening review
- mood and energy capture
- weekly pattern summary

Non-Goals:

- no therapy framing
- no unlimited tracking
- no moralizing missed habits

Dependencies:

- habit and journal policy
- existing habit engine review

Exit Criteria:

- 5 to 7 core signals are enough
- bad-day minimum versions are first-class
- daily planning uses energy and mood as planning context

Risks:

- notification fatigue
- overfitting daily plans to noisy signals

## Phase 7: Controlled Autopilot

Goal:

- allow constrained low-risk autonomous actions only after the earlier phases prove stable

Deliverables:

- action allowlist
- rollback and audit procedures
- review dashboards or CLI reports
- bounded autonomy rules

Non-Goals:

- no broad autonomous mail, calendar, or task control
- no destructive actions by default

Dependencies:

- stable Phases 1 through 6
- action authorization policy
- live E2E verification

Exit Criteria:

- allowed autonomous actions are narrow, reversible, and observable
- sensitive domains remain approval-gated

Risks:

- autonomy expanding without explicit policy
- failures becoming silent

## Parallelization Rules

Can run in parallel after Phase 0 planning:

- repository audit
- policy documents
- Gmail module design
- habit and journal concept
- calendar intelligence concept
- observability and audit concept

Must not start blindly in parallel:

- Gmail write actions
- auto-archive
- task writes
- calendar writes
- memory persistence
- autonomous actions

Reason: these mutate real systems or persist sensitive data.
