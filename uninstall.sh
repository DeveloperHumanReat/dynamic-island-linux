#!/usr/bin/env bash
set -e
pkill -u "$(id -u)" -f 'wayland_app\.py' 2>/dev/null || true
pkill -u "$(id -u)" -f 'control_panel\.py' 2>/dev/null || true
rm -rf "$HOME/.local/share/dynamic-island-linux"
rm -f "$HOME/.local/bin/dynamic-island-linux"
rm -f "$HOME/.local/bin/dynamic-island-linux-control"
rm -f "$HOME/.local/share/applications/dynamic-island-linux.desktop"
rm -f "$HOME/.local/share/applications/dynamic-island-linux-control.desktop"
rm -f "$HOME/.config/autostart/dynamic-island-linux.desktop"
rm -f "$HOME/.config/dynamic-island-linux/settings.json"
rm -f "$HOME/.local/share/icons/hicolor/scalable/apps/dynamic-island-linux.svg"
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi
echo "Dynamic Island kaldırıldı."
