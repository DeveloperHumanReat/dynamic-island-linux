#!/usr/bin/env bash
set -euo pipefail
rm -rf "$HOME/.local/share/dynamic-island-linux"
rm -f "$HOME/.local/bin/dynamic-island-linux"
rm -f "$HOME/.local/share/applications/dynamic-island-linux.desktop"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi
echo "Dynamic Island kaldırıldı."
