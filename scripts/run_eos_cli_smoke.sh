#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
EOS_DB_PATH="${EOS_DB_PATH:-$(mktemp -t eos-cli-smoke-db.XXXXXX)}"
export EOS_DB_PATH

run_masked() {
  "${@}" 2>&1 | "${PYTHON_BIN}" -c 'import re, sys
data = sys.stdin.read()
data = re.sub(r"telegram:[0-9]+", "telegram:<masked>", data)
data = re.sub(r"(?i)(token|secret|password|api[_-]?key)([\"'"'"' ]*[:=][\"'"'"' ]*)[^\"'"'"'\n,} ]+", r"\1\2<masked>", data)
print(data, end="")'
  return "${PIPESTATUS[0]}"
}

echo "== EOS CLI Smoke =="

run_masked "${PYTHON_BIN}" -m src.eos_cli --help

echo "== health =="
run_masked "${PYTHON_BIN}" -m src.eos_cli --json-only health || true

echo "== cron-audit =="
run_masked "${PYTHON_BIN}" -m src.eos_cli --json-only cron-audit || true

echo "== model-audit =="
run_masked "${PYTHON_BIN}" -m src.eos_cli --json-only model-audit || true

echo "== daily-plan dry-run =="
run_masked "${PYTHON_BIN}" -m src.eos_cli --json-only daily-plan --date "$(date +%F)" --dry-run || true

echo "== weekly-plan dry-run =="
run_masked "${PYTHON_BIN}" -m src.eos_cli --json-only weekly-plan --week-start "$(date +%F)" --dry-run || true
