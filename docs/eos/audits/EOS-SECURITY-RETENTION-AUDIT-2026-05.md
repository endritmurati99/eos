# EOS Security Retention Audit 2026-05

## Retention Policy Status

`EOS-DATA-RETENTION-POLICY-v1.md` ist erstellt. Die Policy definiert Class 0 bis Class 4, verbietet Class-4-Persistenz und blockiert dauerhafte Speicherung von Gmail raw bodies, Drive file content, Maps location history, OTPs und Reset-Links.

## Live Readiness Gates

`EOS-GOOGLE-LIVE-READINESS-POLICY-v1.md` ist erstellt. Gmail ist maximal G2 mit G3 pending. Drive, Maps und Calendar Travel-Time sind maximal G1 mit G2 pending. Live-Readiness ist standardmaessig blockiert.

## Gitignore Status

Root `.gitignore` wird um Env-, Credential-, Token-, Google-Workspace-, Runtime-Data- und SQLite-WAL/SHM-Regeln gehaertet. `data/eos_v2.db` wird nicht gesondert untracked.

## Env Example Status

Root `.env.example` enthaelt nur Platzhalter und Default-false Flags fuer Google Live Readiness. Echte Konten, Keys und Secrets sind nicht vorgesehen.

## Secret Pattern Tests

Tests decken Redaction und Detection fuer API Keys, OAuth Client Secrets, Telegram Chat IDs, OTPs, Reset-Links, Credential-Pfade und E-Mail-Adressen ab. Scanner-Ausgaben enthalten Labels und Counts, keine Rohwerte.

## Open Risks

- Gmail Live-Vertrag bleibt unverified.
- Gmail Live E2E bleibt unverified.
- Drive, Maps und Calendar Travel-Time haben nur vorbereitete Gates, keine Produktionsfreigabe.
- PR #16 bleibt bis zur finalen Runtime-Gate-Basis von PR #14 als Integration abhaengig zu pruefen.

## Required Before Production

- Explizite Freigabe fuer jedes Gate ab G3.
- Minimal-Scopes dokumentieren und pruefen.
- Redigierte Smoke-Ausgaben reviewen.
- Retention- und Loeschregeln fuer neue Runtime-State-Felder vor Merge bestaetigen.
- Rollback- und Disable-Switch-Verfahren einmal trocken durchspielen.
