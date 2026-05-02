# Personal Assistant / EOS Coding Agent Plan (2026-04-25)

## Audience
This document is for Claude Code, Codex, or another coding agent working directly in `/data/.openclaw/workspaces/personal-assistant`.

## Mission
Stabilize the personal assistant into an open-beta-ready EOS implementation with four immediate priorities:
1. remove production stub leakage
2. harden live integration degradation behavior
3. add local-first TTS pipeline
4. make Google Tasks production-ready

## Known Confirmed Problem
The user received fabricated-looking daily priorities such as:
- `Steuerunterlagen vorsortieren`
- `Mit Max Rücksprache halten`

These came from local stub/example data in `data/tasks.json`, not from the model inventing them from scratch.
The actual production failure chain was:
1. live Google Tasks failed with `403 accessNotConfigured`
2. production planning path fell back to stub task data
3. user-facing briefing presented stub tasks as if they were real

This must never happen again.

## Product Invariants
- Production output must never present `data/tasks.json` as real tasks.
- Production output must never present `data/calendar.json` as real calendar truth.
- Integration failures must be surfaced as degraded availability, not filled by plausible guesses.
- Text briefing and audio delivery must be decoupled.
- Audio failure must not be appended to the briefing body.
- Local TTS should be preferred or at least available as a reliable fallback.
- Google Tasks must be treated as the real task source for open beta, not a loose optional add-on.

---

# Section 1: Immediate code fixes

## 1.1 Patch daily capacity defaults
File:
- `src/jobs/daily_capacity.py`

Change `run_daily_capacity()` defaults to:
```python
allow_stub_calendar: bool = False
allow_stub_tasks: bool = False
prefer_live_calendar: bool = True
prefer_live_tasks: bool = True
```

Why:
- default call path should behave like production
- tests can still opt into stub behavior explicitly

Also review these functions in the same file:
- `_load_calendar_blocks`
- `_load_tasks`
- `_capacity_status`
- `_recommendation`

Desired behavior:
- if live tasks fail and stubs are disabled, the result should still be structured and useful
- recommendation should explicitly reflect weak task basis without inventing substitute work

## 1.2 Strengthen Google Tasks error semantics
File:
- `src/gateways/google_tasks.py`

Tasks:
- normalize `403 accessNotConfigured` into a stable semantic status
- preserve raw error text internally for diagnostics
- ensure upstream code can distinguish between:
  - auth missing
  - provider disabled
  - config missing
  - temporary provider error

Desired outcome:
- downstream prompts/templates can say, in effect, "Live tasks are currently unavailable" without ambiguity

## 1.3 Search for other stub leaks
Audit at minimum:
- `src/jobs/evening_reset.py`
- `templates/daily-output.md`
- `templates/weekly-output.md`
- any future planning helper that reads `data/tasks.json` or `data/calendar.json`

Rules:
- test fixture use is allowed only with explicit opt-in
- production path must be live-only or explicitly degraded
- any test-only fallback should be commented as test-only

---

# Section 2: Template and prompt behavior

## 2.1 Daily output template
File:
- `templates/daily-output.md`

Update requirements:
- distinguish verified facts from unavailable integrations
- if no hard calendar events exist, say that briefly
- if tasks are unavailable, say that briefly
- never invite the model to infer tasks from context-free patterns
- keep wording short, operational, and direct

The template should force this behavior:
- calendar block section = factual only
- task section = live verified tasks only
- recommendation = tactical advice based on verified state, not guessed backlog

## 2.2 Weekly output template
File:
- `templates/weekly-output.md`

Same principles as daily output.
Weekly planning must never convert missing tasks into guessed weekly priorities.

## 2.3 Audio-related user text
Wherever the briefing text is assembled:
- do not append phrases like "Audio für Telegram konnte ich diesmal leider nicht erzeugen..."
- audio delivery failures belong in logs/result metadata, not in the briefing body

---

# Section 3: TTS pipeline implementation

## 3.1 Target architecture
Introduce a small TTS subsystem instead of embedding TTS ad hoc into planning jobs.

Suggested files:
- `src/gateways/tts_provider.py`
- `src/gateways/tts_local.py`
- `src/gateways/tts_pipeline.py`

Suggested API shape:
```python
def synthesize_briefing_audio(
    text: str,
    target: str,
    voice: str | None = None,
    prefer_local: bool = True,
) -> dict[str, Any]:
    ...
```

Return structure should include:
- `status`
- `provider`
- `audio_path`
- `mime_type`
- `duration_estimate`
- `error`

## 3.2 Piper local fallback
Known working shared assets outside this workspace:
- `/data/.openclaw/workspace/vendor/piper`
- `/data/.openclaw/workspace/tts/piper/de_DE-eva_k-x_low.onnx`
- `/data/.openclaw/workspace/tts/piper/de_DE-eva_k-x_low.onnx.json`

Implementation guidance:
- use `PYTHONPATH=/data/.openclaw/workspace/vendor/piper` or a cleaner packaging approach
- generate audio into a deterministic output directory inside this workspace or a configured shared runtime path
- support WAV generation first
- optionally transcode to MP3 for delivery convenience

Potential new config keys:
- `EOS_TTS_MODE=local_first`
- `EOS_TTS_PIPER_MODEL_PATH`
- `EOS_TTS_PIPER_CONFIG_PATH`
- `EOS_TTS_OUTPUT_DIR`

## 3.3 Delivery target separation
The TTS subsystem should not know Telegram internals.
It should only generate audio.
A separate delivery layer should decide whether to:
- attach/send to Telegram
- store/log only

## 3.4 TTS fallback strategy
Recommended order:
1. small configured primary provider if explicitly enabled
2. local Piper
3. structured failure result

Do not:
- switch to large expensive model paths implicitly
- leak raw TTS failure text into user-facing briefing body

---

# Section 4: Google Tasks production readiness

## 4.1 Product goal
After the planning stack is stabilized, Google Tasks should be dependable enough that EOS can use it as the default operational task source during open beta.

## 4.2 Auth and API readiness
Focus areas:
- GCP API enablement
- OAuth client setup
- refresh-token persistence
- account/config discovery
- operator-visible status reporting

The system should make it obvious whether the problem is:
- API disabled
- auth missing
- credentials missing
- account mismatch
- provider failure

## 4.3 Canonical list handling
The system should consistently understand and use:
- `Inbox`
- `Next`
- `Waiting`
- `This Week`

If one list fails:
- return structured partial state
- do not silently zero it out without explanation

If all lists fail:
- degrade explicitly
- do not use stub tasks as replacement in production

## 4.4 Operator setup and smoke verification
Add or improve a human-runnable verification flow that checks:
1. auth/config status
2. canonical list discovery
3. live read success
4. degraded-state reporting when unavailable

This should be simple enough that a human can run one or two commands and know what is broken.

## 4.5 Docs to update
Likely docs:
- `docs/EOS-TASKS-INTEGRATION-v1.md`
- `docs/EOS-INTEGRATION-ROLLOUT-PLAN.md`
- `PLAN.md`
- relevant learning files under `.learnings/`

The docs should explain:
- why fake tasks appeared before
- why stubs are now test-only
- what degraded states mean
- how to restore live Google Tasks

---

# Section 5: Tests and verification

## 5.1 Existing tests to preserve
Review:
- `tests/verify_daily_capacity.py`
- `tests/verify_eos_core.py`
- `tests/verify_eos_state.py`
- `tests/verify_v2_foundation.py`

## 5.2 Add or update tests
Add at minimum:
- `tests/verify_tts_pipeline.py`
- Google Tasks smoke verification script or focused test coverage

Needed coverage:
- `run_daily_capacity()` default path is live-only
- explicit stub flags still work in tests
- live task failure produces degraded but honest result
- TTS failure does not contaminate briefing text

## 5.3 Suggested smoke checks
Examples, adapt to actual runtime:
```bash
python tests/verify_daily_capacity.py
python -m src.jobs.daily_capacity
python tests/verify_tts_pipeline.py
```

And one live operator smoke flow:
- simulate or observe unavailable Google Tasks
- generate daily briefing
- confirm no stub task titles appear
- run local Piper generation

---

# Section 6: Docs and rollout updates

## 6.1 Update project docs after code changes
Likely docs to update:
- `PLAN.md`
- `docs/EOS-INTEGRATION-ROLLOUT-PLAN.md`
- `docs/EOS-TASKS-INTEGRATION-v1.md`
- `docs/EOS-SCHEDULER-JOBS-v1.md`
- `docs/EOS-CAPABILITY-MAP.md`

## 6.2 Record lessons learned
Update:
- `.learnings/ERRORS.md`
- `.learnings/FEATURE_REQUESTS.md`
- `.learnings/LEARNINGS.md`

Must capture:
- confirmed root cause of fake tasks in production output
- why live-only defaults are necessary
- TTS fallback chain design
- Google Tasks setup assumptions and degraded-state semantics

---

# Section 7: Recommended work sequence for the coding agent

## Step 1
Patch `src/jobs/daily_capacity.py` defaults and keep tests passing.

## Step 2
Improve Google Tasks error semantics and audit for stub leakage elsewhere.

## Step 3
Tighten templates so unavailable data stays unavailable instead of becoming invented content.

## Step 4
Implement TTS abstraction and Piper local fallback.

## Step 5
Add live Google Tasks verification and operator-facing setup docs.

## Step 6
Add tests, smoke checks, and doc updates.

---

# Definition of Done
This workspace is in the right state when:
- production daily planning does not use stub tasks/calendar by default
- Google Tasks outage yields an explicit degraded state
- no hallucinated or borrowed stub tasks appear in daily/weekly briefings
- audio generation is available through at least one local path
- Google Tasks setup and degraded behavior are documented cleanly
- daily text output remains clean even when audio fails
- coding agents can continue implementation from this file without guessing the intended architecture
