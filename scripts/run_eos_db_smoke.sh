#!/usr/bin/env bash
set -euo pipefail

choose_python() {
  if [ -n "${EOS_PYTHON:-}" ] && [ -x "$EOS_PYTHON" ]; then
    echo "$EOS_PYTHON"
    return
  fi
  if [ -x ".venv/bin/python" ]; then
    echo ".venv/bin/python"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    command -v python
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi
  echo "ERROR: no Python interpreter found." >&2
  return 1
}

classify_output() {
  local output_file="$1"
  if grep -qi "attempt to write a readonly database" "$output_file"; then
    echo "readonly_db"
  elif grep -qiE "ModuleNotFoundError|No module named" "$output_file"; then
    echo "missing_dependency"
  elif grep -qi "gog" "$output_file"; then
    echo "missing_gog_or_google_runtime"
  elif grep -qiE "permission denied|readonly database" "$output_file"; then
    echo "permission_or_readonly_db"
  elif grep -qiE "credential|token|auth|secret" "$output_file"; then
    echo "missing_or_degraded_auth"
  else
    echo "unknown_failure"
  fi
}

run_checked() {
  local label="$1"
  shift
  local output_file
  output_file="$(mktemp)"

  set +e
  "$@" >"$output_file" 2>&1
  local exit_code=$?
  set -e

  if [ "${EOS_DB_SMOKE_VERBOSE:-false}" = "true" ]; then
    echo "== $label output =="
    cat "$output_file"
  fi

  local error_class="none"
  if [ "$exit_code" -ne 0 ]; then
    error_class="$(classify_output "$output_file")"
    SMOKE_FAILURES=$((SMOKE_FAILURES + 1))
  fi

  echo "$label: exit_code=$exit_code error_class=$error_class"
  rm -f "$output_file"
}

run_safe_summary() {
  local label="$1"
  shift
  local stdout_file
  local stderr_file
  local exit_code
  stdout_file="$(mktemp)"
  stderr_file="$(mktemp)"

  set +e
  "$@" >"$stdout_file" 2>"$stderr_file"
  exit_code=$?
  set -e

  "$PYTHON_BIN" scripts/eos_safe_smoke_summary.py \
    --command-name "$label" \
    --exit-code "$exit_code" \
    --stdout-file "$stdout_file" \
    --stderr-file "$stderr_file" \
    --format line
  if [ "$exit_code" -ne 0 ]; then
    SMOKE_FAILURES=$((SMOKE_FAILURES + 1))
  fi
  rm -f "$stdout_file" "$stderr_file"
}

PYTHON_BIN="$(choose_python)"
TODAY="$(date +%F)"
SMOKE_FAILURES=0

echo "EOS_DB_SAFE_SMOKE"
run_safe_summary "db_doctor" "$PYTHON_BIN" scripts/eos_db_doctor.py

run_safe_summary "cli_help" "$PYTHON_BIN" -m src.eos_cli --help
run_safe_summary "daily_dry_run" "$PYTHON_BIN" -m src.eos_cli --json-only daily-plan --date "$TODAY" --dry-run
run_safe_summary "weekly_dry_run" "$PYTHON_BIN" -m src.eos_cli --json-only weekly-plan --week-start "$TODAY" --dry-run
run_safe_summary "run_job_daily_morning_dry_run" "$PYTHON_BIN" -m src.eos_cli --json-only run-job daily_morning --date "$TODAY" --dry-run
run_safe_summary "run_job_weekly_sync_dry_run" "$PYTHON_BIN" -m src.eos_cli --json-only run-job weekly_sync --week-start "$TODAY" --dry-run
run_safe_summary "assistant_home" "$PYTHON_BIN" -m src.eos_cli --json-only assistant home --date "$TODAY" --dry-run
run_safe_summary "assistant_status" "$PYTHON_BIN" -m src.eos_cli --json-only assistant status --dry-run

if [ "$SMOKE_FAILURES" -ne 0 ]; then
  echo "EOS DB smoke completed with $SMOKE_FAILURES failing step(s)."
  exit 1
fi

echo "EOS DB smoke completed successfully."
