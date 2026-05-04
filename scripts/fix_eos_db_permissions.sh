#!/usr/bin/env bash
set -euo pipefail

DB_PATH="${EOS_DB_PATH:-data/eos_v2.db}"
TARGET_USER="${EOS_DB_OWNER_USER:-$(id -un)}"
TARGET_GROUP="${EOS_DB_OWNER_GROUP:-$(id -gn)}"
APPLY="${EOS_APPLY_DB_PERMISSION_FIX:-false}"
PARENT_DIR="$(dirname "$DB_PATH")"

run_privileged() {
  if [ "$(id -u)" = "0" ]; then
    "$@"
    return
  fi
  if command -v sudo >/dev/null 2>&1; then
    sudo "$@"
    return
  fi
  echo "ERROR: sudo is required when not running as root." >&2
  return 1
}

show_path() {
  local path="$1"
  if [ -e "$path" ]; then
    ls -ld "$path"
  else
    echo "missing: $path"
  fi
}

fix_path() {
  local path="$1"
  if [ ! -e "$path" ]; then
    return
  fi
  run_privileged chown "$TARGET_USER:$TARGET_GROUP" "$path"
  if [ -d "$path" ]; then
    chmod u+rwx "$path"
  else
    chmod u+rw "$path"
  fi
}

echo "EOS DB permission fixer"
echo "CURRENT_USER=$(id -un)"
echo "CURRENT_GROUP=$(id -gn)"
echo "DB_PATH=$DB_PATH"
echo "TARGET_USER=$TARGET_USER"
echo "TARGET_GROUP=$TARGET_GROUP"
echo "APPLY=$APPLY"

if ! id -u "$TARGET_USER" >/dev/null 2>&1; then
  echo "ERROR: target user does not exist: $TARGET_USER" >&2
  exit 2
fi

if ! getent group "$TARGET_GROUP" >/dev/null 2>&1; then
  echo "ERROR: target group does not exist: $TARGET_GROUP" >&2
  exit 2
fi

echo "Before:"
show_path "$PARENT_DIR"
show_path "$DB_PATH"
for suffix in "-wal" "-shm" "-journal"; do
  show_path "${DB_PATH}${suffix}"
done

if [ "$APPLY" != "true" ]; then
  echo "Dry-run only. Set EOS_APPLY_DB_PERMISSION_FIX=true to apply."
  exit 0
fi

if [ ! -d "$PARENT_DIR" ]; then
  echo "ERROR: parent directory does not exist: $PARENT_DIR" >&2
  exit 3
fi

fix_path "$PARENT_DIR"
fix_path "$DB_PATH"
for suffix in "-wal" "-shm" "-journal"; do
  fix_path "${DB_PATH}${suffix}"
done

echo "After:"
show_path "$PARENT_DIR"
show_path "$DB_PATH"
for suffix in "-wal" "-shm" "-journal"; do
  show_path "${DB_PATH}${suffix}"
done
echo "Done."
