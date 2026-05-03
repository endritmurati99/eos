#!/usr/bin/env bash
set -euo pipefail

if command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "Neither python nor python3 is available." >&2
  exit 127
fi

"${PYTHON_BIN}" -m src.eos_cli --help >/dev/null

"${PYTHON_BIN}" -m src.eos_cli --json-only health || true
"${PYTHON_BIN}" -m src.eos_cli --json-only cron-audit || true
"${PYTHON_BIN}" -m src.eos_cli --json-only model-audit || true
