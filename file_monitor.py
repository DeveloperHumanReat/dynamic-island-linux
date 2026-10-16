#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Callable


class DownloadMonitor:
    def __init__(self, callback: Callable[[str], None]) -> None:
        self.callback = callback
        self.directory = Path.home() / "Downloads"
        self.known: set[str] = set()
        self.initialized = False

    def poll(self) -> bool:
        if not self.directory.exists():
            return True
        files = {str(path) for path in self.directory.iterdir() if path.is_file()}
        if not self.initialized:
            self.known = files; self.initialized = True; return True
        for path in sorted(files - self.known):
            self.callback(Path(path).name)
        self.known = files
        return True
