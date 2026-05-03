#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
EOS_DB_PATH="${EOS_DB_PATH:-$(mktemp -t eos-cron-smoke-db.XXXXXX)}"
export EOS_DB_PATH

run_masked() {
  "${@}" 2>&1 | "${PYTHON_BIN}" -c 'import re, sys
data = sys.stdin.read()
data = re.sub(r"telegram:[0-9]+", "telegram:<masked>", data)
data = re.sub(r"(?i)(token|secret|password|api[_-]?key)([\"'"'"' ]*[:=][\"'"'"' ]*)[^\"'"'"'\n,} ]+", r"\1\2<masked>", data)
print(data, end="")'
  return "${PIPESTATUS[0]}"
}

echo "== Cron/Systemd Files =="
find ops -maxdepth 3 -type f | sort || true

echo "== EOS cron audit =="
run_masked "${PYTHON_BIN}" -m src.eos_cli --json-only cron-audit || true

echo "== systemd timers if available =="
if command -v systemctl >/dev/null 2>&1; then
  run_masked systemctl list-timers --all | grep -i eos || true
else
  echo "systemctl unavailable"
fi
