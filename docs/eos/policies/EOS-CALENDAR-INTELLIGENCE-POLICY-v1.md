# EOS Calendar Intelligence Policy v1

Status: Phase 0 policy

## Purpose

Calendar intelligence helps EOS understand hard events, meetings, conflicts, prep needs, and follow-ups. Google Calendar remains the source of truth for hard time commitments.

## Hard Events First

EOS must treat confirmed calendar events as hard constraints unless the user says otherwise.

Rules:

- aggregate at least `primary` and `sport` where configured
- use `Europe/Berlin` for planning display and trigger decisions
- fail closed for send-worthy planning if live calendar read fails
- do not invent events from tasks or mail

## Meeting Briefs

Meeting briefs may include:

- event title
- time and timezone
- attendees
- event description
- related mail threads
- related tasks
- related vault notes
- prior meeting briefs
- open follow-ups

Meeting briefs must label each source and avoid unsourced assertions.

## Conflict Detection

EOS may detect:

- overlapping hard events
- overloaded days
- missing prep windows
- insufficient recovery windows
- travel or transition gaps
- meetings next to fixed sport or work blocks

EOS may suggest resolutions but must not move hard events autonomously.

## Prep Windows

EOS may suggest prep windows for:

- important meetings
- travel
- sport
- paperwork or admin
- deadlines

Prep suggestions are planning advice unless the user approves a write.

## Follow-Up Detection

EOS may detect follow-ups from:

- event descriptions
- mail threads
- tasks
- vault notes
- prior brief outputs

Follow-up extraction must keep source IDs and confidence.

## Calendar Writes

Forbidden by default:

- automatic hard-event move
- automatic hard-event delete
- automatic attendee changes
- automatic meeting creation from weak mail signals

Approval required:

- creating hard events
- moving events
- deleting events
- changing attendees
- changing meeting descriptions

Allowed as suggestion:

- propose focus blocks
- propose prep windows
- propose follow-up reminders
- propose conflict resolutions

## Audit Requirements

Every future calendar intelligence run should record:

- run ID
- date window
- calendars read
- event count
- source status
- conflict count
- suggestions made
- write actions attempted
- dry-run flag
- error class

## Exit Criteria for Future Writes

Before any calendar write feature:

- action authorization policy is enforced
- user approval path exists
- read-after-write verification exists
- idempotency or duplicate prevention exists
- live E2E test is defined
