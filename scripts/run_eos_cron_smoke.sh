#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
SUMMARY_SCRIPT="${SUMMARY_SCRIPT:-scripts/eos_safe_smoke_summary.py}"
SMOKE_FAILED=0
if [[ -z "${EOS_DB_PATH:-}" ]]; then
  EOS_DB_PATH="$(mktemp -t eos-cron-safe-smoke-db.XXXXXX)"
  export EOS_DB_PATH
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "EOS_SAFE_SMOKE"
  echo "- smoke_runner: failed exit_code=127 error_class=missing_python_alias stdout_lines=0 stderr_lines=0 sensitive_output_detected=no raw_output_printed=no"
  echo "- sensitive_output_printed: no"
  exit 1
fi

run_safe() {
  local command_name="$1"
  shift
  local stdout_file
  local stderr_file
  local exit_code
  local line

  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"

  set +e
  "$@" >"${stdout_file}" 2>"${stderr_file}"
  exit_code=$?
  set -e

  line="$("${PYTHON_BIN}" "${SUMMARY_SCRIPT}" \
    --command-name "${command_name}" \
    --exit-code "${exit_code}" \
    --stdout-file "${stdout_file}" \
    --stderr-file "${stderr_file}" \
    --format line)"
  rm -f "${stdout_file}" "${stderr_file}"

  echo "${line}"
  if [[ "${line}" == *": failed"* ]]; then
    SMOKE_FAILED=1
  fi
}

echo "EOS_SAFE_SMOKE"
run_safe cron_files bash -lc "find ops -maxdepth 3 -type f | sort | wc -l"
run_safe cron_audit "${PYTHON_BIN}" -m src.eos_cli --json-only cron-audit
if command -v systemctl >/dev/null 2>&1; then
  run_safe systemd_timers bash -lc "systemctl list-timers --all | grep -i eos || true"
else
  run_safe systemd_timers bash -lc "echo systemctl unavailable; exit 127"
fi
echo "- sensitive_output_printed: no"

exit "${SMOKE_FAILED}"
