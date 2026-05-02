# EOS Subagent Protocol v1

## Purpose
EOS can use specialist agents as advisors, but the main `personal-assistant`
agent remains the only orchestrator and the only writer of operational state.

## Roles
- `personal-assistant`: user interface, orchestration, final decisions, state writes
- `aurelius`: review, priorities, overload checks, tradeoff analysis
- `solara`: sport, recovery, habits, physical load
- `photon`: automation, code, tests, integration work
- `pharos`: research and external context
- `lucent`: communication drafts and wording
- `lux`: quick utility checks and small operational lookups

## Write Rules
- Subagents do not write `data/eos_state.json`.
- Subagents do not write Google Calendar or Google Tasks directly.
- Subagents return recommendations with evidence, uncertainty, and proposed action.
- The orchestrator validates state against `data/eos_state.schema.json` before any state write.

## Operating Rules
- Use subagents only after EOS Core has loaded and validated state.
- Ask one specialist for one bounded question.
- Do not let multiple subagents independently rank the same task list.
- Prefer deterministic EOS Core results over agent opinion when they conflict.
- Implementation subagents must also follow `docs/eos/policies/EOS-GLOBAL-AGENT-RULES-v1.md` for branching, safety, verification, and reporting.
