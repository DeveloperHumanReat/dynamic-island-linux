#!/usr/bin/env bash
set -u
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/dynamic-island-linux"
LOG_FILE="$LOG_DIR/launcher.log"
mkdir -p "$LOG_DIR"
cd "$ROOT_DIR" || exit 1

if [ -z "${WAYLAND_DISPLAY:-}" ]; then
  printf '%s\n' "Dynamic Island: Wayland oturumu bulunamadı; X11 desteği kaldırıldı." | tee -a "$LOG_FILE" >&2
  if command -v notify-send >/dev/null 2>&1; then notify-send -u critical "Dynamic Island" "Wayland oturumu gerekli."; fi
  exit 1
fi

python3 "$ROOT_DIR/main.py" >>"$LOG_FILE" 2>&1
STATUS=$?
if [ "$STATUS" -ne 0 ]; then
  MESSAGE="Dynamic Island başlatılamadı. Ayrıntılar: $LOG_FILE"
  if command -v notify-send >/dev/null 2>&1; then notify-send -u critical "Dynamic Island for Linux" "$MESSAGE"; fi
  printf '%s\n' "$MESSAGE" >&2
fi
exit "$STATUS"
