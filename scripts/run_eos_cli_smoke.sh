#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
SUMMARY_SCRIPT="${SUMMARY_SCRIPT:-scripts/eos_safe_smoke_summary.py}"
SMOKE_FAILED=0
TEMP_DB_CREATED=0
READONLY_DATABASE_HARD="${EOS_DB_RECOVERY_FIXED:-${EOS_RUNTIME_LIVE_GATE:-false}}"

if [ -z "${EOS_DB_PATH:-}" ]; then
  EOS_DB_PATH="$(mktemp -t eos-cli-safe-smoke-db.XXXXXX)"
  export EOS_DB_PATH
  TEMP_DB_CREATED=1
fi

cleanup() {
  if [ "${TEMP_DB_CREATED}" = "1" ]; then
    rm -f "${EOS_DB_PATH}" "${EOS_DB_PATH}-wal" "${EOS_DB_PATH}-shm" "${EOS_DB_PATH}-journal"
  fi
}
trap cleanup EXIT

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "EOS_SAFE_SMOKE"
  echo "- smoke_runner: failed exit_code=127 error_class=missing_python_alias stdout_lines=0 stderr_lines=0 sensitive_output_detected=no secret_output_detected=no raw_output_printed=no"
  echo "- sensitive_output_printed: no"
  echo "- raw_output_printed: no"
  exit 1
fi

run_safe() {
  local command_name="$1"
  shift
  local stdout_file
  local stderr_file
  local exit_code
  local line
  local readonly_flag=()

  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"

  set +e
  "$@" >"${stdout_file}" 2>"${stderr_file}"
  exit_code=$?
  set -e

  if [ "${READONLY_DATABASE_HARD}" = "true" ]; then
    readonly_flag=(--readonly-database-hard)
  fi

  line="$("${PYTHON_BIN}" "${SUMMARY_SCRIPT}" \
    --command-name "${command_name}" \
    --exit-code "${exit_code}" \
    --stdout-file "${stdout_file}" \
    --stderr-file "${stderr_file}" \
    --format line \
    "${readonly_flag[@]}")"
  rm -f "${stdout_file}" "${stderr_file}"

  echo "${line}"
  if [[ "${line}" == *": failed"* ]]; then
    SMOKE_FAILED=1
  fi
}

echo "EOS_SAFE_SMOKE"
run_safe cli_help "${PYTHON_BIN}" -m src.eos_cli --help
run_safe health bash -lc "${PYTHON_BIN} -m src.eos_cli --json-only health >/dev/null"
run_safe cron_audit "${PYTHON_BIN}" -m src.eos_cli --json-only cron-audit
run_safe model_audit bash -lc "${PYTHON_BIN} -m src.eos_cli --json-only model-audit >/dev/null"
run_safe daily_plan bash -lc "${PYTHON_BIN} -m src.eos_cli --json-only daily-plan --date $(date +%F) --dry-run >/dev/null"
run_safe weekly_plan bash -lc "${PYTHON_BIN} -m src.eos_cli --json-only weekly-plan --week-start $(date +%F) --dry-run >/dev/null"
echo "- sensitive_output_printed: no"
echo "- raw_output_printed: no"

exit "${SMOKE_FAILED}"
