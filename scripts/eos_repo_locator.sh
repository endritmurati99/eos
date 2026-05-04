#!/usr/bin/env bash
set -euo pipefail

echo "== EOS Repo Locator =="

CANDIDATES=(
  "."
  "data/.openclaw/workspaces/personal-assistant"
  "/docker/openclaw-qt6t/data/.openclaw/workspaces/personal-assistant"
)

for dir in "${CANDIDATES[@]}"; do
  echo ""
  echo "-- candidate: $dir"
  if [ ! -d "$dir" ]; then
    echo "missing"
    continue
  fi

  (
    cd "$dir"
    echo "pwd=$(pwd)"
    git rev-parse --show-toplevel 2>/dev/null || true
    git status --short --branch 2>/dev/null || true
    git remote -v 2>/dev/null || true
    [ -f src/eos_cli.py ] && echo "has src/eos_cli.py"
    [ -d docs/eos ] && echo "has docs/eos"
    [ -f src/database/models.py ] && echo "has src/database/models.py"
  )
done
