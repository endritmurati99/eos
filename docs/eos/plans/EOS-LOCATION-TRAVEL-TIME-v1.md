# EOS Location Travel Time v1

## Goal

Prepare deterministic location and travel-time intelligence for daily planning without live Maps calls, Calendar writes, real addresses, or location history.

## Architecture

Calendar-like events enter `eos_location_intelligence` as synthetic `CalendarLocationEvent` values. A route client estimates travel time. In this phase the route client is `FakeRoutesClient`.

## Location Rules

- Missing location returns no estimate and risk `unknown`.
- Same origin and destination returns zero minutes and low risk.
- First located event uses `Home` as origin.
- Consecutive located events estimate travel from the previous event location.

## Travel-Time Risk

- Unknown route estimate means medium risk.
- Travel time plus configured buffer overlapping the next event start means high risk.
- A route that fits before the event with buffer means low risk.

## Privacy Boundary

Do not store real addresses, latitude/longitude history, route history, live location, API keys, tokens, Calendar writes, Gmail writes, or Drive document content.

## Next Phase

After the database P0 blocker and read-only PR sequence are resolved, wire this module into calendar planning as a read-only advisory layer.
