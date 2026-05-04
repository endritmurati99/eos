#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "${PYTHON_BIN} is not available." >&2
  exit 127
fi

is_docs_only_path() {
  local path="$1"
  case "${path}" in
    docs/*|README.md|AGENTS.md)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

is_code_path() {
  local path="$1"
  case "${path}" in
    src/*|tests/*|scripts/*|.github/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

derive_changed_code() {
  local changed_files=""
  local docs_only="true"
  local path

  if [ -n "${GITHUB_BASE_REF:-}" ]; then
    git fetch origin "${GITHUB_BASE_REF}" --depth=1 >/dev/null 2>&1
    changed_files="$(git diff --name-only "origin/${GITHUB_BASE_REF}...HEAD")"
  elif git rev-parse --verify origin/main >/dev/null 2>&1; then
    changed_files="$(git diff --name-only origin/main...HEAD)"
  else
    changed_files="$(git diff --name-only HEAD)"
  fi

  if [ -z "${changed_files}" ]; then
    echo "true"
    return
  fi

  while IFS= read -r path; do
    [ -z "${path}" ] && continue
    if is_code_path "${path}"; then
      echo "true"
      return
    fi
    if ! is_docs_only_path "${path}"; then
      docs_only="false"
    fi
  done <<EOF
${changed_files}
EOF

  if [ "${docs_only}" = "true" ]; then
    echo "false"
  else
    # Unknown/config-only changes are not docs-only; fail closed on no-test collection.
    echo "true"
  fi
}

derive_changed_files_count() {
  local changed_files=""
  if [ -n "${GITHUB_BASE_REF:-}" ]; then
    git fetch origin "${GITHUB_BASE_REF}" --depth=1 >/dev/null 2>&1
    changed_files="$(git diff --name-only "origin/${GITHUB_BASE_REF}...HEAD")"
  elif git rev-parse --verify origin/main >/dev/null 2>&1; then
    changed_files="$(git diff --name-only origin/main...HEAD)"
  else
    changed_files="$(git diff --name-only HEAD)"
  fi
  if [ -z "${changed_files}" ]; then
    echo "0"
  else
    printf '%s\n' "${changed_files}" | wc -l | tr -d ' '
  fi
}

validate_changed_code_value() {
  case "$1" in
    true|false)
      return 0
      ;;
    *)
      echo "PR_CHANGED_CODE must be true or false when set." >&2
      echo "true"
      return 1
      ;;
  esac
}

changed_code="${PR_CHANGED_CODE:-}"
if [ -z "${changed_code}" ]; then
  changed_code="$(derive_changed_code)"
else
  validate_changed_code_value "${changed_code}" >/dev/null
fi

compile_targets=()
for path in src scripts tests; do
  if [ -d "${path}" ]; then
    compile_targets+=("${path}")
  fi
done

if [ "${#compile_targets[@]}" -gt 0 ]; then
  "${PYTHON_BIN}" -m compileall -q "${compile_targets[@]}"
fi

set +e
"${PYTHON_BIN}" -m pytest -q
pytest_status=$?
set -e

if [ "${pytest_status}" -eq 5 ]; then
  if [ "${changed_code}" = "false" ]; then
    echo "pytest collected no tests; docs-only change classified as warning."
    exit 0
  fi
  changed_count="$(derive_changed_files_count)"
  echo "pytest collected no tests for a non-doc change; failing merge gate. changed_files=${changed_count}" >&2
  exit 5
fi

exit "${pytest_status}"
