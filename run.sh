#!/usr/bin/env bash
set -u
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/dynamic-island-linux"
LOG_FILE="$LOG_DIR/launcher.log"
mkdir -p "$LOG_DIR"
cd "$ROOT_DIR" || exit 1

PYTHON="${PYTHON:-python3}"
"$PYTHON" "$ROOT_DIR/app.py" >>"$LOG_FILE" 2>&1
STATUS=$?

if [ "$STATUS" -ne 0 ]; then
  MESSAGE="Dynamic Island başlatılamadı. Ayrıntılar: $LOG_FILE"
  if command -v notify-send >/dev/null 2>&1; then
    notify-send -u critical "Dynamic Island for Linux" "$MESSAGE"
  elif command -v zenity >/dev/null 2>&1; then
    zenity --error --title="Dynamic Island for Linux" --text="$MESSAGE" 2>/dev/null || true
  elif command -v kdialog >/dev/null 2>&1; then
    kdialog --error "$MESSAGE" --title "Dynamic Island for Linux" 2>/dev/null || true
  fi
  printf '%s\n' "$MESSAGE" >&2
fi
exit "$STATUS"
