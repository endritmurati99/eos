# EOS Docs — Technical Specifications Index

Canonical technical specifications for EOS (`personal-assistant`).
These documents define system behaviour, contracts, and policies.
All paths in `SOUL.md` and agent config reference this layer.

## Quick Navigation

→ **[Start with vault dashboard](../vault/00%20Home/EOS%20Dashboard.md)** — System overview & status  
→ **[Vault maps of content](../vault/01%20Maps%20of%20Content/)** — Topic guides to navigate this index  
→ **Vault README**: [vault/README.md](../vault/README.md) — Folder structure & workflows

---

## Durable EOS Context

| File | Description |
|------|-------------|
| [eos/EOS-MASTER-CONTEXT.md](eos/EOS-MASTER-CONTEXT.md) | Durable project memory, scope, architecture rules, and phase baseline |
| [eos/EOS-ROADMAP.md](eos/EOS-ROADMAP.md) | Controlled rollout from Phase 0 through controlled autopilot |
| [eos/audits/EOS-REPO-AUDIT-2026-05.md](eos/audits/EOS-REPO-AUDIT-2026-05.md) | Phase 0 repository audit and current-state findings |
| [eos/audits/EOS-SECURITY-SECRETS-AUDIT-2026-05.md](eos/audits/EOS-SECURITY-SECRETS-AUDIT-2026-05.md) | Metadata-only security, secrets, and OAuth audit |
| [eos/policies/EOS-MAIL-POLICY-v1.md](eos/policies/EOS-MAIL-POLICY-v1.md) | Gmail read-only, labeling, storage, and sensitive-category policy |
| [eos/policies/EOS-ACTION-AUTHORIZATION-POLICY-v1.md](eos/policies/EOS-ACTION-AUTHORIZATION-POLICY-v1.md) | L0-L5 authorization model for reads, suggestions, writes, and autonomy |
| [eos/policies/EOS-MEMORY-POLICY-v1.md](eos/policies/EOS-MEMORY-POLICY-v1.md) | Source-backed personal memory and retention policy |
| [eos/policies/EOS-CALENDAR-INTELLIGENCE-POLICY-v1.md](eos/policies/EOS-CALENDAR-INTELLIGENCE-POLICY-v1.md) | Meeting briefs, conflicts, prep, follow-ups, and calendar write limits |
| [eos/policies/EOS-HABIT-JOURNAL-POLICY-v1.md](eos/policies/EOS-HABIT-JOURNAL-POLICY-v1.md) | Habit and journal signal limits, tone, and minimum-version policy |
| [eos/policies/EOS-NOTIFICATION-BUDGET-v1.md](eos/policies/EOS-NOTIFICATION-BUDGET-v1.md) | Telegram-first notification budget and escalation rules |
| [eos/policies/EOS-GLOBAL-AGENT-RULES-v1.md](eos/policies/EOS-GLOBAL-AGENT-RULES-v1.md) | Branching, safety, verification, and reporting rules for all implementation agents |

---

## Core Architecture

| File | Description |
|------|-------------|
| [EOS-ARCHITECTURE-v1.md](EOS-ARCHITECTURE-v1.md) | Confirmed vs. target vs. open — authoritative system overview |
| [EOS-CAPABILITY-MAP.md](EOS-CAPABILITY-MAP.md) | Live capabilities, integration status, data access rules |
| [EOS-OPERATING-CONTRACT-v1.md](EOS-OPERATING-CONTRACT-v1.md) | Agent operating contract and hard constraints |
| [EOS-SUBAGENT-PROTOCOL-v1.md](EOS-SUBAGENT-PROTOCOL-v1.md) | Specialist-agent roles and write boundaries |
| [EOS-V2-TECHNICAL-SPEC.md](EOS-V2-TECHNICAL-SPEC.md) | V2 target state specification |
| [EOS-V2-STATE-MODEL-v1.md](EOS-V2-STATE-MODEL-v1.md) | V2 state model |

---

## Planning

| File | Description |
|------|-------------|
| [EOS-PLANNING-POLICY-v1.md](EOS-PLANNING-POLICY-v1.md) | Daily and weekly planning rules (active policy) |
| [EOS-ACTION-CONTRACT-v1.md](EOS-ACTION-CONTRACT-v1.md) | Action classification and execution contract |
| [EOS-ALIASES-v1.md](EOS-ALIASES-v1.md) | Alias normalization rules |

---

## Calendar

| File | Description |
|------|-------------|
| [EOS-CALENDAR-WRITE-E2E-v1.md](EOS-CALENDAR-WRITE-E2E-v1.md) | Calendar write path, verification, and edge cases |

---

## Tasks

| File | Description |
|------|-------------|
| [EOS-TASKS-INTEGRATION-v1.md](EOS-TASKS-INTEGRATION-v1.md) | Google Tasks integration spec |
| [EOS-TASKS-ACTION-CONTRACT-v1.md](EOS-TASKS-ACTION-CONTRACT-v1.md) | Task action contract |

---

## Scheduler

| File | Description |
|------|-------------|
| [EOS-SCHEDULER-POLICY-v1.md](EOS-SCHEDULER-POLICY-v1.md) | Scheduler rules and dry-run policy |
| [EOS-SCHEDULER-JOBS-v1.md](EOS-SCHEDULER-JOBS-v1.md) | Job definitions |
| [EOS-SCHEDULER-IMPLEMENTATION-v1.md](EOS-SCHEDULER-IMPLEMENTATION-v1.md) | Implementation spec |
| [EOS-SCHEDULER-TIMEBASE-v1.md](EOS-SCHEDULER-TIMEBASE-v1.md) | Time base and timezone rules |
| [EOS-SCHEDULER-STATE-IDEMPOTENCY-v1.md](EOS-SCHEDULER-STATE-IDEMPOTENCY-v1.md) | State idempotency contract |

---

## Engines & Workflows

| File | Description |
|------|-------------|
| [EOS-BRAIN-DUMP-v1.md](EOS-BRAIN-DUMP-v1.md) | Brain dump intake and routing |
| [EOS-EVENING-RESET-v1.md](EOS-EVENING-RESET-v1.md) | Evening reset workflow |
| [EOS-REVIEW-ENGINE-v1.md](EOS-REVIEW-ENGINE-v1.md) | Weekly review engine |
| [EOS-COACHING-ENGINE-v1.md](EOS-COACHING-ENGINE-v1.md) | Planning coaching engine |
| [EOS-PREP-REMINDER-POLICY-v1.md](EOS-PREP-REMINDER-POLICY-v1.md) | Prep reminder policy |
| [EOS-PREP-REMINDER-TRIGGER-PATH-v1.md](EOS-PREP-REMINDER-TRIGGER-PATH-v1.md) | Prep reminder trigger path |
| [EOS-PREP-CHECKLIST-MAPPINGS-v1.md](EOS-PREP-CHECKLIST-MAPPINGS-v1.md) | Prep checklist per event type |

---

## Vault

| File | Description |
|------|-------------|
| [EOS-VAULT-v1.md](EOS-VAULT-v1.md) | Vault structure, note types, naming, linking rules |

---

## V2 Foundation

| File | Description |
|------|-------------|
| [EOS-V2-FOUNDATION-IMPLEMENTATION-v1.md](EOS-V2-FOUNDATION-IMPLEMENTATION-v1.md) | V2 foundation implementation |
| [EOS-V2-TIMERS-v1.md](EOS-V2-TIMERS-v1.md) | V2 timer system |
| [EOS-INTEGRATION-ROLLOUT-PLAN.md](EOS-INTEGRATION-ROLLOUT-PLAN.md) | Integration rollout order |

---

## E2E Test Records

| File | Description |
|------|-------------|
| [EOS-LIVE-E2E-TESTS-v1.md](EOS-LIVE-E2E-TESTS-v1.md) | General live E2E tests |
| [EOS-CALENDAR-WRITE-E2E-v1.md](EOS-CALENDAR-WRITE-E2E-v1.md) | Calendar write E2E |
| [EOS-TASKS-LIVE-E2E-v1.md](EOS-TASKS-LIVE-E2E-v1.md) | Tasks E2E |
| [EOS-SCHEDULER-LIVE-E2E-v1.md](EOS-SCHEDULER-LIVE-E2E-v1.md) | Scheduler E2E |
| [EOS-PREP-REMINDER-LIVE-E2E-v1.md](EOS-PREP-REMINDER-LIVE-E2E-v1.md) | Prep reminder E2E |
| [EOS-V2-LIVE-E2E-v1.md](EOS-V2-LIVE-E2E-v1.md) | V2 foundation E2E |
