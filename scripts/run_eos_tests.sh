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

set +e
"${PYTHON_BIN}" -m pytest -q
pytest_status=$?
set -e

if [ "${pytest_status}" -eq 5 ]; then
  echo "pytest collected no tests; treating as bootstrap warning."
  exit 0
fi

exit "${pytest_status}"
