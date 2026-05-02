# EOS Google Calendar Integration

## Goal
Use Google Calendar as the real calendar source for EOS, starting with read-only verification.

## Preferred Path
Use local `gog` CLI instead of the Maton gateway path.
Reason: cleaner architecture, direct Google OAuth, no additional Maton API dependency for calendar reads.

## Current Host State
- `gog` installed via Homebrew
- binary path expected in `/data/linuxbrew/.linuxbrew/bin/gog`
- OAuth not yet configured

## Setup Shape
1. Provide Google OAuth client credentials JSON
2. Run `gog auth credentials /path/to/client_secret.json`
3. Run `gog auth add <google-account> --services calendar`
4. Verify with `gog auth list`
5. Test read-only calendar fetch for a bounded time window
6. Only after successful reads, consider write actions

## EOS Policy
- Calendar sync starts read-only
- Local planning files remain usable fallback until live sync is validated
- No calendar writes until explicit confirmation

## Blocking Requirement
A Google OAuth client credentials JSON file is still required for `gog` auth setup.
