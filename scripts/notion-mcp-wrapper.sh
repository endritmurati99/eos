#!/usr/bin/env bash
set -euo pipefail
TOKEN_FILE="/data/.openclaw/secrets/notion.token"
if [[ ! -s "$TOKEN_FILE" ]]; then
  echo "Missing Notion token file: $TOKEN_FILE" >&2
  exit 1
fi
export NOTION_TOKEN="$(tr -d '\r\n' < "$TOKEN_FILE")"
exec npx -y @notionhq/notion-mcp-server
