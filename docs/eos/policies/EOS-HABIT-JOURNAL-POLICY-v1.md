# EOS Habit and Journal Policy v1

Status: Phase 0 policy

## Purpose

Habit and journal features should improve daily steering without creating guilt, noise, or excessive tracking. EOS should use a small number of signals to help choose realistic plans.

## Core Signals

Start with no more than 5 to 7 signals:

- sleep quality
- training or sport
- deep work
- study or work progress
- mood or energy
- basic nutrition
- evening shutdown

Do not add more signals unless a concrete planning decision depends on them.

## Tone Rules

EOS must avoid:

- streak guilt
- moralizing
- long lectures
- therapy framing
- pressure language
- over-analysis after missed habits

EOS should use:

- short prompts
- minimum versions
- practical reflection
- realistic next step framing

## Minimum Versions

Every habit that matters should have a minimum version for bad days.

Minimum version is not failure. It is the continuity path when the day is constrained.

Examples:

- short mobility instead of full routine
- one reflection question instead of a long journal
- one focused work block instead of a full deep-work plan

## Morning Prompt

Morning prompt should be short and operational.

It may ask for:

- sleep quality
- energy
- major constraint today
- one must-do
- whether the plan needs to be lighter

It should not become a long intake form.

## Evening Review

Evening review should capture:

- what was done
- what was skipped or minimized
- energy and mood trend
- one adjustment for tomorrow
- open loop if important

It should not create shame or a large retrospective burden.

## Planning Use

Habit and journal data can influence:

- task load
- focus block count
- recovery recommendation
- reminder timing
- next-day warning
- weekly pattern review

It must not override hard calendar events or become a second task system.

## Storage Rules

Prefer storing:

- date
- signal name
- bounded value
- short notes
- source
- timestamp

Avoid storing:

- long private journal text by default
- sensitive health details unless explicitly useful
- speculative psychological conclusions

## Future Implementation Requirements

Before extending habit or journal code:

- define exact signal set
- define CLI or Telegram input shape
- define storage table or JSON field
- define weekly review output
- add tests for bad-day minimum behavior
- add tests that missed habits are not treated as moral failure
