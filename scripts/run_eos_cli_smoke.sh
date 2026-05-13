#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
SUMMARY_SCRIPT="${SUMMARY_SCRIPT:-scripts/eos_safe_smoke_summary.py}"
SMOKE_FAILED=0
if [[ -z "${EOS_DB_PATH:-}" ]]; then
  EOS_DB_PATH="$(mktemp -t eos-cli-safe-smoke-db.XXXXXX)"
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
run_safe cli_help "${PYTHON_BIN}" -m src.eos_cli --help
run_safe health "${PYTHON_BIN}" -m src.eos_cli --json-only health
run_safe cron_audit "${PYTHON_BIN}" -m src.eos_cli --json-only cron-audit
run_safe model_audit "${PYTHON_BIN}" -m src.eos_cli --json-only model-audit
run_safe daily_plan "${PYTHON_BIN}" -m src.eos_cli --json-only daily-plan --date "$(date +%F)" --dry-run
run_safe weekly_plan "${PYTHON_BIN}" -m src.eos_cli --json-only weekly-plan --week-start "$(date +%F)" --dry-run
run_safe assistant_home "${PYTHON_BIN}" -m src.eos_cli --json-only assistant home --date "$(date +%F)" --dry-run
run_safe assistant_status "${PYTHON_BIN}" -m src.eos_cli --json-only assistant status --dry-run
run_safe assistant_heute "${PYTHON_BIN}" -m src.eos_cli --json-only assistant heute --date "$(date +%F)" --dry-run
run_safe assistant_jetzt "${PYTHON_BIN}" -m src.eos_cli --json-only assistant jetzt --date "$(date +%F)" --dry-run
run_safe assistant_abend "${PYTHON_BIN}" -m src.eos_cli --json-only assistant abend --date "$(date +%F)" --dry-run
run_safe assistant_mail "${PYTHON_BIN}" -m src.eos_cli --json-only assistant mail --date "$(date +%F)" --limit 5 --dry-run
echo "- sensitive_output_printed: no"

exit "${SMOKE_FAILED}"
