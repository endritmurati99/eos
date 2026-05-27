# Notion Agent Setup Guide

## Current status

Configured and tested:

- Notion token stored locally at `/data/.openclaw/secrets/notion.token` with `0600` permissions.
- OpenClaw MCP server saved as `notionApi`.
- Claude Code MCP server saved as `notionApi` in user scope.
- Codex MCP server saved as `notionApi` in global Codex config.
- Notion CLI `ntn` installed: `ntn 0.14.0`.
- Official Notion MCP package available: `@notionhq/notion-mcp-server`.
- API smoke test works against `/v1/users/me`.

## Why this setup

We use a wrapper script instead of storing the token directly in Claude/Codex/OpenClaw config.

Wrapper:

```bash
/data/.openclaw/workspaces/personal-assistant/scripts/notion-mcp-wrapper.sh
```

It reads the token from:

```bash
/data/.openclaw/secrets/notion.token
```

Then starts:

```bash
npx -y @notionhq/notion-mcp-server
```

## Commands used

OpenClaw:

```bash
openclaw mcp set notionApi '{"command":"/data/.openclaw/workspaces/personal-assistant/scripts/notion-mcp-wrapper.sh","args":[]}'
openclaw mcp show notionApi --json
```

Claude Code:

```bash
claude mcp add -s user notionApi -- /data/.openclaw/workspaces/personal-assistant/scripts/notion-mcp-wrapper.sh
claude mcp list
claude mcp get notionApi
```

Codex:

```bash
codex mcp add notionApi -- /data/.openclaw/workspaces/personal-assistant/scripts/notion-mcp-wrapper.sh
codex mcp list
codex mcp get notionApi
```

Notion CLI:

```bash
npm install --global ntn
ntn --version
NOTION_API_TOKEN="$(cat /data/.openclaw/secrets/notion.token)" ntn api /v1/users/me --notion-version 2022-06-28
```

## Manual setup if repeated later

1. Create a Notion token or integration.
2. Create/share the target Notion page with that integration.
3. Save token locally only:

```bash
umask 077
mkdir -p /data/.openclaw/secrets
printf '%s\n' '<TOKEN>' > /data/.openclaw/secrets/notion.token
chmod 600 /data/.openclaw/secrets/notion.token
```

4. Add MCP server to OpenClaw, Claude Code, and Codex using the wrapper script.
5. Run smoke tests.

## Security note

Because the token was pasted in chat once, rotate it later after setup is stable: create a new Notion token, replace `/data/.openclaw/secrets/notion.token`, then revoke the old one in Notion.
