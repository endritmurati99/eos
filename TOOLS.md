# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Shared Claude Code → Codex Proxy - 2026-05-18

When Endrit wants Claude Code orchestration after Claude/Opus limits are exhausted, prefer the host-level launcher from the target project directory:

```bash
/data/.local/bin/claude-codex-here
```

Do not use plain `claude` for this path; plain `claude` is the direct Anthropic/Claude route and will still show Sonnet/Opus/Haiku in `/model`.

Before serious work, verify:

```bash
curl -fsS http://127.0.0.1:18765/healthz
claude-code-proxy codex auth status
/data/.local/bin/claude-codex-here -p 'Return exactly: OK-CODEX'
```

Current validated behavior: proxy routes to `https://chatgpt.com/backend-api/codex/responses` with `model=gpt-5.5`; tiny prompts took about 7-11s in tests. If Claude Code shows repeated attempts/retries or stalls, inspect `/data/.local/state/claude-code-proxy/proxy.log` before relying on it.

Shared details: `/data/.openclaw/workspaces/CLAUDE_CODE_CODEX_PROXY.md`.

