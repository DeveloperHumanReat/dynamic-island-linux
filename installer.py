#!/usr/bin/env python3
"""Graphical installer for Dynamic Island for Linux.

The bootstrap shell script installs tkinter only when the current Python lacks
it. This GUI then performs a user-local installation, so no root is needed for
copying the application itself.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

APP_NAME = "Dynamic Island for Linux"
APP_ID = "dynamic-island-linux"
SOURCE_DIR = Path(__file__).resolve().parent
INSTALL_DIR = Path.home() / ".local" / "share" / APP_ID
BIN_DIR = Path.home() / ".local" / "bin"
DESKTOP_DIR = Path.home() / ".local" / "share" / "applications"


def distro_info() -> tuple[str, str]:
    data: dict[str, str] = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                data[key] = value.strip().strip('"')
    except OSError:
        pass
    return data.get("ID", "linux"), data.get("PRETTY_NAME", platform.system())


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def desktop_entry() -> str:
    launcher = BIN_DIR / APP_ID
    return f"""[Desktop Entry]\nType=Application\nName={APP_NAME}\nComment=iOS Dynamic Island inspired Linux overlay\nExec={launcher}\nIcon=preferences-desktop-notification\nTerminal=false\nCategories=Utility;\nStartupNotify=false\n"""


class Installer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"{APP_NAME} — Kurulum")
        self.geometry("560x440")
        self.resizable(False, False)
        self.configure(bg="#f4f4f7")
        self._build_ui()

    def _build_ui(self) -> None:
        outer = tk.Frame(self, bg="#f4f4f7", padx=28, pady=24)
        outer.pack(fill="both", expand=True)
        tk.Label(outer, text="Dynamic Island for Linux", bg="#f4f4f7", fg="#111119",
                 font=("DejaVu Sans", 20, "bold")).pack(anchor="w")
        tk.Label(outer, text="Tüm dosyaları kullanıcı hesabınıza kurar; uygulama menüsüne ekler.",
                 bg="#f4f4f7", fg="#5b5b68", font=("DejaVu Sans", 10)).pack(anchor="w", pady=(5, 20))

        distro_id, distro_name = distro_info()
        self.info = tk.Label(outer, text=f"Algılanan sistem: {distro_name} ({distro_id})",
                             bg="#e9e9ef", fg="#30303a", anchor="w", padx=12, pady=9,
                             font=("DejaVu Sans", 10))
        self.info.pack(fill="x")

        self.status = tk.Label(outer, text="Kuruluma hazır.", bg="#f4f4f7", fg="#30303a",
                               anchor="w", justify="left", wraplength=500,
                               font=("DejaVu Sans", 10))
        self.status.pack(fill="x", pady=(18, 8))
        self.progress = ttk.Progressbar(outer, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(0, 20))

        self.log = tk.Text(outer, height=8, width=62, state="disabled", bg="#17171c", fg="#d7d7e2",
                           relief="flat", padx=10, pady=8, font=("DejaVu Sans Mono", 9))
        self.log.pack(fill="both", expand=True)

        bottom = tk.Frame(outer, bg="#f4f4f7")
        bottom.pack(fill="x", pady=(18, 0))
        self.install_button = tk.Button(bottom, text="Kur", command=self.start_install,
                                        bg="#111119", fg="white", activebackground="#30303a",
                                        activeforeground="white", relief="flat", padx=24, pady=10,
                                        font=("DejaVu Sans", 10, "bold"), cursor="hand2")
        self.install_button.pack(side="right")
        tk.Button(bottom, text="Kapat", command=self.destroy, relief="flat", padx=14, pady=10,
                  bg="#f4f4f7", fg="#44444e", font=("DejaVu Sans", 10)).pack(side="right", padx=(0, 8))

    def write_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def update_status(self, text: str, progress: int | None = None) -> None:
        self.status.configure(text=text)
        if progress is not None:
            self.progress.configure(value=progress)

    def start_install(self) -> None:
        self.install_button.configure(state="disabled")
        threading.Thread(target=self.install, daemon=True).start()

    def install(self) -> None:
        try:
            self.after(0, lambda: self.update_status("Dosyalar hazırlanıyor…", 20))
            INSTALL_DIR.mkdir(parents=True, exist_ok=True)
            BIN_DIR.mkdir(parents=True, exist_ok=True)
            DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SOURCE_DIR / "app.py", INSTALL_DIR / "app.py")
            shutil.copy2(SOURCE_DIR / "wayland_app.py", INSTALL_DIR / "wayland_app.py")
            shutil.copy2(SOURCE_DIR / "README.md", INSTALL_DIR / "README.md")
            self.write_log(f"Uygulama dizini: {INSTALL_DIR}")

            launcher = BIN_DIR / APP_ID
            launcher.write_text(f"#!/bin/sh\nexec {sys.executable} {INSTALL_DIR / 'app.py'} \"$@\"\n")
            launcher.chmod(0o755)
            self.after(0, lambda: self.update_status("Başlatıcı oluşturuluyor…", 55))
            self.write_log(f"Başlatıcı: {launcher}")

            desktop = DESKTOP_DIR / f"{APP_ID}.desktop"
            desktop.write_text(desktop_entry())
            desktop.chmod(0o644)
            self.write_log(f"Uygulama menüsü girdisi: {desktop}")
            self.after(0, lambda: self.update_status("Uygulama menüsü güncelleniyor…", 80))
            if command_exists("update-desktop-database"):
                subprocess.run(["update-desktop-database", str(DESKTOP_DIR)], check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            self.after(0, lambda: self.update_status("Kurulum tamamlandı.", 100))
            self.after(0, lambda: messagebox.showinfo(
                "Kurulum tamamlandı", "Dynamic Island kuruldu. Uygulamalar menüsünden açabilir veya terminalde 'dynamic-island-linux' çalıştırabilirsiniz."))
            self.after(0, lambda: self.install_button.configure(text="Tamamlandı", state="disabled"))
        except Exception as exc:
            self.write_log(f"HATA: {exc}")
            self.after(0, lambda: self.update_status("Kurulum başarısız oldu."))
            self.after(0, lambda: messagebox.showerror("Kurulum hatası", str(exc)))
            self.after(0, lambda: self.install_button.configure(state="normal"))


def main() -> None:
    Installer().mainloop()


if __name__ == "__main__":
    main()
