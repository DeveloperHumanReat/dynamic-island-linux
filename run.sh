#!/usr/bin/env bash
set -u
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/dynamic-island-linux"
LOG_FILE="$LOG_DIR/launcher.log"
mkdir -p "$LOG_DIR"
cd "$ROOT_DIR" || exit 1
printf 'WAYLAND_DISPLAY=%s XDG_CURRENT_DESKTOP=%s\n' "${WAYLAND_DISPLAY:-}" "${XDG_CURRENT_DESKTOP:-}" >>"$LOG_FILE"

stop_instances() {
  pkill -u "$(id -u)" -f '/dynamic-island-linux/(main\.py|wayland_app\.py)' 2>/dev/null || true
  pkill -u "$(id -u)" -f 'wayland_app\.py' 2>/dev/null || true
  rm -f "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/dynamic-island-linux.lock"
}

case "${1:-}" in
  --stop)
    stop_instances
    echo "Dynamic Island durduruldu."
    exit 0
    ;;
  --restart)
    stop_instances
    sleep 0.3
    ;;
esac

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
  if command -v kdialog >/dev/null 2>&1; then kdialog --error "$MESSAGE" --title "Dynamic Island for Linux" 2>/dev/null || true; fi
  if command -v zenity >/dev/null 2>&1; then zenity --error --title="Dynamic Island for Linux" --text="$MESSAGE" 2>/dev/null || true; fi
  printf '%s\n' "$MESSAGE" >&2
fi
exit "$STATUS"
