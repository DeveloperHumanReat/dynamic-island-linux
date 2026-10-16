#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "dynamic-island-linux"
CONFIG_FILE = CONFIG_DIR / "settings.json"
DEFAULTS = {
    "theme": "dark",
    "scale": 1.0,
    "top_margin": 18,
    "auto_start": True,
    "notification_duration": 4200,
    "do_not_disturb": False,
    "enable_media": True,
    "enable_notifications": True,
    "enable_system": True,
    "enable_downloads": True,
    "enable_timer": True,
}


def load() -> dict:
    try:
        data = json.loads(CONFIG_FILE.read_text())
        return {**DEFAULTS, **data}
    except (OSError, ValueError):
        return DEFAULTS.copy()


def save(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({**DEFAULTS, **data}, indent=2, ensure_ascii=False))


def autostart_entry(launcher: Path) -> str:
    return ("[Desktop Entry]\nType=Application\nName=Dynamic Island for Linux\n"
            f"Exec={launcher}\nIcon=dynamic-island-linux\nX-GNOME-Autostart-enabled=true\nNoDisplay=true\n")
