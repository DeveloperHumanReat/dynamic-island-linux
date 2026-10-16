#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${PYTHON:-python3}"

if [ -z "${WAYLAND_DISPLAY:-}" ]; then
  echo "HATA: Bu sürüm yalnızca Wayland oturumlarında çalışır. X11 desteği kaldırıldı."
  echo "Wayland oturumuyla giriş yapıp kurulumu tekrar çalıştırın."
  exit 1
fi

exec "$PYTHON" "$ROOT_DIR/installer.py"
