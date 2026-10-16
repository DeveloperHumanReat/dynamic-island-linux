#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
import subprocess
from typing import Callable


class SystemMonitor:
    def __init__(self, callback: Callable[[dict], None]) -> None:
        self.callback = callback
        self.previous: dict = {}

    @staticmethod
    def command(name: str, args: list[str]) -> str:
        if not shutil.which(name):
            return ""
        try:
            return subprocess.check_output([name, *args], text=True, stderr=subprocess.DEVNULL, timeout=1)
        except (OSError, subprocess.SubprocessError):
            return ""

    def snapshot(self) -> dict:
        data: dict = {}
        volume = self.command("wpctl", ["get-volume", "@DEFAULT_AUDIO_SINK@"]) or self.command("pactl", ["get-sink-volume", "@DEFAULT_SINK@"]) 
        match = re.search(r"(0?\.\d+|\d+)%?", volume)
        if match:
            value = float(match.group(1)); data["volume"] = int(value * 100) if value <= 1 else int(value)
        power = self.command("upower", ["-i", "/org/freedesktop/UPower/devices/DisplayDevice"])
        match = re.search(r"percentage:\s+(\d+)%", power)
        if match: data["battery"] = int(match.group(1))
        state = self.command("nmcli", ["-t", "-f", "GENERAL.STATE,GENERAL.CONNECTION", "device", "show"])
        data["network"] = "connected" if "connected" in state.lower() else ("offline" if state else "unknown")
        audio = self.command("pactl", ["list", "source-outputs"])
        data["mic_active"] = bool(audio.strip())
        lower = audio.lower()
        data["call"] = any(name in lower for name in ("discord", "zoom", "teams", "meet", "skype", "jitsi"))
        return data

    def poll(self) -> bool:
        current = self.snapshot()
        if current != self.previous:
            changed = {k: v for k, v in current.items() if self.previous.get(k) != v}
            self.previous = current
            self.callback({"state": current, "changed": changed})
        return True
