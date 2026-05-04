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
    docs/*|*.md)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

derive_changed_code() {
  local changed_files=""
  local path

  if [ -n "${GITHUB_BASE_REF:-}" ]; then
    git fetch origin "${GITHUB_BASE_REF}" --depth=1 >/dev/null 2>&1 || true
    changed_files="$(git diff --name-only "origin/${GITHUB_BASE_REF}...HEAD" 2>/dev/null || true)"
  elif git rev-parse --verify origin/main >/dev/null 2>&1; then
    changed_files="$(git diff --name-only origin/main...HEAD 2>/dev/null || true)"
  else
    changed_files="$(git diff --name-only HEAD 2>/dev/null || true)"
  fi

  if [ -z "${changed_files}" ]; then
    echo "true"
    return
  fi

  while IFS= read -r path; do
    [ -z "${path}" ] && continue
    if ! is_docs_only_path "${path}"; then
      echo "true"
      return
    fi
  done <<EOF
${changed_files}
EOF

  echo "false"
}

changed_code="${PR_CHANGED_CODE:-}"
if [ -z "${changed_code}" ]; then
  changed_code="$(derive_changed_code)"
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
  echo "pytest collected no tests for a non-doc change; failing merge gate." >&2
  exit 5
fi

exit "${pytest_status}"
