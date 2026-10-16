#!/usr/bin/env python3
"""Read desktop Notify calls from the session D-Bus monitor.

This avoids replacing the user's notification daemon. It observes Notify calls
and forwards summary/body data to the island when dbus-monitor is available.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import threading
from typing import Callable


_STRING = re.compile(r'^\s*string "(.*)"$')


class NotificationWatcher:
    def __init__(self, on_notification: Callable[[str, str, str], None]) -> None:
        self.on_notification = on_notification
        self.process = None
        self.thread = None
        if not shutil.which("dbus-monitor"):
            print("Bildirim watcher kapalı: dbus-monitor bulunamadı")
            return
        try:
            self.process = subprocess.Popen(
                ["dbus-monitor", "--session", "type='method_call',interface='org.freedesktop.Notifications',member='Notify'"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
            self.thread = threading.Thread(target=self._read, daemon=True)
            self.thread.start()
        except Exception as exc:
            print(f"Bildirim watcher başlatılamadı: {exc}")

    def _read(self) -> None:
        if not self.process or not self.process.stdout:
            return
        strings: list[str] = []
        for line in self.process.stdout:
            match = _STRING.match(line.strip())
            if match:
                strings.append(match.group(1).replace('\\"', '"'))
                # Notify arguments: app, replaces_id, icon, summary, body.
                if len(strings) == 5:
                    app, _replace_id, _icon, summary, body = strings
                    if summary or body:
                        self.on_notification(app, summary, body)
                    strings = []
            elif line.startswith("method call"):
                strings = []
