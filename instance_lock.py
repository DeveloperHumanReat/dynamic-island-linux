#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import os
from pathlib import Path


class SingleInstance:
    def __init__(self) -> None:
        runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
        runtime.mkdir(parents=True, exist_ok=True)
        self.path = runtime / "dynamic-island-linux.lock"
        self.handle = self.path.open("w")
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            self.handle.close()
            raise RuntimeError("Dynamic Island zaten çalışıyor.") from exc
        self.handle.write(str(os.getpid()))
        self.handle.flush()

    def close(self) -> None:
        try:
            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
            self.handle.close()
        except Exception:
            pass
