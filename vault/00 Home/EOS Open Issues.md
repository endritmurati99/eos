# EOS Open Issues

Critical blockers, known limitations, and outstanding decisions.

**Binding architectural decisions:**
- [[ADR - Calendar as Source of Truth]] — Google Calendar is the single source of truth for hard time.
- [[ADR - Tasks as Source of Truth]] — Google Tasks is the single source of truth for active open tasks.

---

## Phase 1 Blockers (Pilot Cannot Start)

### [BLK-001] gog CLI Keyring Password

**Severity**: HIGH  
**Impact**: Calendar read unavailable — Phase 1 pilot blocked  
**Status**: Pending configuration

The `gog` file-keyring password is not set in the OpenClaw container environment.

```
Error: read token for endrit.murati99@gmail.com: no TTY available for keyring file backend password prompt
```

**Fix**: Set `GOG_KEYRING_PASSWORD` environment variable in docker-compose.yml or `.env`  
**Related**: [vault/14 Knowledge/EOS-RUNTIME-FIX-INSTRUCTIONS.txt](../14%20Knowledge/EOS-RUNTIME-FIX-INSTRUCTIONS.txt)

---

### [BLK-002] gog Keyring File Permissions

**Severity**: HIGH  
**Impact**: Calendar read unavailable — Phase 1 pilot blocked  
**Status**: Pending fix

Files under `/data/.config/gogcli/keyring/` are not readable by the OpenClaw process.

```
Error: permission denied
```

**Fix**: Adjust ownership/permissions or re-authenticate `gog`  
**Related**: [.learnings/ERRORS.md](../../.learnings/ERRORS.md) (ERR-20260421-002)

---

## Phase 2 Blockers (Integration Not Started)

### [PEND-001] Google Tasks Architecture

**Status**: ✓ RESOLVED — formalized via [[ADR - Tasks as Source of Truth]]
**Impact**: Role of Google Tasks as primary source of truth is now decided. Integration implementation path (auth + v1 scope) still needs to be executed.

Role decision (binding): Google Tasks is the single source of truth for active open tasks. See [[ADR - Tasks as Source of Truth]].

Still open at the implementation level:
- finalize headless-safe OAuth2 path with refresh tokens
- implement Tasks v1 minimal scope (read, create, complete, fixed list structure)
- live E2E verification

**Target spec**: [docs/EOS-TASKS-INTEGRATION-v1.md](../../docs/EOS-TASKS-INTEGRATION-v1.md)

---

### [PEND-002] Vault Live Mount

**Status**: PLANNED, NOT YET VERIFIED  
**Impact**: Vault is file-based only; not yet a live persistent backend

**Target**: Obsidian Vault as mounted filesystem  
**Spec**: [docs/EOS-VAULT-v1.md](../../docs/EOS-VAULT-v1.md)

---

### [PEND-003] Scheduler Implementation

**Status**: DESIGN COMPLETE, IMPLEMENTATION PENDING  
**Impact**: No automation, no reminders, no scheduled jobs running

**Specs complete**:
- [EOS-SCHEDULER-POLICY-v1.md](../../docs/EOS-SCHEDULER-POLICY-v1.md)
- [EOS-SCHEDULER-IMPLEMENTATION-v1.md](../../docs/EOS-SCHEDULER-IMPLEMENTATION-v1.md)
- [EOS-SCHEDULER-JOBS-v1.md](../../docs/EOS-SCHEDULER-JOBS-v1.md)

**Pending**: Runtime integration, Python implementation, state idempotency tests

---

### [PEND-004] Evening Reset and Weekly Review Workflows

**Status**: SPECIFIED, NOT YET IMPLEMENTED  
**Impact**: No evening or weekly automation

**Specs available**:
- [docs/EOS-EVENING-RESET-v1.md](../../docs/EOS-EVENING-RESET-v1.md)
- [docs/EOS-REVIEW-ENGINE-v1.md](../../docs/EOS-REVIEW-ENGINE-v1.md)

**Pending**: Scheduler integration

---

## Calendar Write Operational Status

**Google Calendar WRITE**: Technically verified (E2E spec exists and path is defined).  
**Operational status**: Not yet enabled — no production writes have been executed.  
This is not a blocker for Phase 1 (read-only baseline), but must be validated before any write-path automation is enabled.

---

## Architectural Decisions

### Decided

| Decision | Outcome | Reference |
|----------|---------|-----------|
| **Source of truth for hard time** | Google Calendar | [[ADR - Calendar as Source of Truth]] |
| **Source of truth for active tasks** | Google Tasks | [[ADR - Tasks as Source of Truth]] |

### Still Pending

| Decision | Options | Target |
|----------|---------|--------|
| **Google Tasks auth path** | Maton vs. direct OAuth | Direct OAuth (verify) |
| **Vault mount strategy** | Single path vs. multi-mount | Single persistent mount |
| **Scheduler backend** | Redis vs. file-based state | TBD (idempotency requirement) |
| **Skill visibility** | Minimal vs. all available | Minimal (least-privilege) |

---

## Reference Materials

- **Errors log**: [.learnings/ERRORS.md](../../.learnings/ERRORS.md)
- **Runtime fixes**: [vault/14 Knowledge/](../14%20Knowledge/)
- **Technical specs**: [docs/INDEX.md](../../docs/INDEX.md)
- **Architecture**: [MOC - Architecture.md](../01%20Maps%20of%20Content/MOC%20-%20Architecture.md)

---

## Last Updated

**2026-04-22** — Added [[ADR - Calendar as Source of Truth]] and [[ADR - Tasks as Source of Truth]]; PEND-001 now resolved at the decision level, implementation still pending. Phase 1 pilot still blocked on keyring fix (BLK-001, BLK-002).
