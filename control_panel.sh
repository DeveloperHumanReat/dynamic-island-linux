#!/usr/bin/env bash
set -u
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/dynamic-island-linux"
LOG_FILE="$LOG_DIR/control-panel.log"
mkdir -p "$LOG_DIR"
cd "$ROOT_DIR" || exit 1
python3 "$ROOT_DIR/control_panel.py" >>"$LOG_FILE" 2>&1
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
  MESSAGE="Kontrol paneli açılamadı. Ayrıntılar: $LOG_FILE"
  command -v kdialog >/dev/null 2>&1 && kdialog --error "$MESSAGE" --title "Dynamic Island" 2>/dev/null || true
  command -v notify-send >/dev/null 2>&1 && notify-send -u critical "Dynamic Island" "$MESSAGE" || true
  printf '%s\n' "$MESSAGE" >&2
fi
exit "$STATUS"
