# Notion Setup for Bayern Trip

## Recommended path
Use a Notion internal integration / PAT with access only to the Bayern Trip parent page.

Do NOT share your normal Notion password.

## What Endrit needs to create
1. Open Notion developer portal: https://www.notion.so/developers
2. Create either:
   - Personal access token (fastest for personal workspace), or
   - Internal connection (clean bot-style integration)
3. Capabilities: Read content, Insert content, Update content. No delete needed.
4. Create an empty Notion parent page: `EOS / Bayern Trip`.
5. Share/connect that page with the integration/token if required.
6. Provide EOS:
   - token, preferably only once
   - parent page URL or page ID

## Local files prepared
- scripts/notion-mcp-wrapper.sh reads token from /data/.openclaw/secrets/notion.token
- data/bayern_trip/create_notion_page.mjs can create the first page via API
- data/bayern_trip/participants.csv can be imported/used for database rows
- data/bayern_trip/notion-template.md is the manual fallback template

## OpenClaw MCP config snippet, once token file exists
{
  "mcp": {
    "servers": {
      "notionApi": {
        "command": "/data/.openclaw/workspaces/personal-assistant/scripts/notion-mcp-wrapper.sh",
        "args": []
      }
    }
  }
}
