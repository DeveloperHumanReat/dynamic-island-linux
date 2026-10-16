#!/usr/bin/env python3
"""Wayland-only GTK installer with automatic distro dependency setup."""
from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import threading
from pathlib import Path


def distro_id() -> str:
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if line.startswith("ID="):
                return line.split("=", 1)[1].strip().strip('"').lower()
    except OSError:
        pass
    return "linux"


def root_command(command: list[str]) -> None:
    if os.geteuid() == 0:
        subprocess.run(command, check=True)
        return
    sudo = shutil.which("sudo")
    if not sudo:
        raise RuntimeError("Eksik Wayland bağımlılıkları için sudo bulunamadı.")
    subprocess.run([sudo, *command], check=True)


def install_wayland_dependencies() -> None:
    distro = distro_id()
    arch = {"arch", "manjaro", "endeavouros", "cachyos", "garuda", "artix"}
    if distro in {"ubuntu", "debian", "linuxmint", "pop", "elementary", "zorin"}:
        root_command(["apt-get", "update"])
        root_command(["apt-get", "install", "-y", "python3-gi", "gir1.2-gtk-3.0", "gir1.2-gtklayershell-0.1", "libgtk-layer-shell0", "dbus"])
    elif distro in {"fedora", "rhel", "centos", "rocky", "almalinux"}:
        manager = "dnf" if shutil.which("dnf") else "yum"
        root_command([manager, "install", "-y", "python3-gobject", "gtk3", "gtk-layer-shell", "dbus"])
    elif distro in arch:
        root_command(["pacman", "-Sy", "--needed", "--noconfirm", "python-gobject", "gtk3", "gtk-layer-shell", "dbus"])
    elif distro.startswith("opensuse") or distro == "suse":
        root_command(["zypper", "--non-interactive", "install", "python3-gobject", "gtk3", "gtk-layer-shell", "dbus-1"])
    elif distro == "alpine":
        root_command(["apk", "add", "py3-gobject3", "gtk+3.0", "gtk-layer-shell", "dbus"])
    elif distro == "void":
        root_command(["xbps-install", "-Sy", "python3-gobject", "gtk+3", "gtk-layer-shell", "dbus"])
    else:
        raise RuntimeError(f"Desteklenmeyen dağıtım: {distro}. GTK3, PyGObject ve gtk-layer-shell paketlerini kurun.")


def ensure_gtk() -> None:
    try:
        import gi  # noqa: F401
    except (ImportError, ModuleNotFoundError):
        print("GTK/PyGObject eksik; Wayland bağımlılıkları otomatik kuruluyor…")
        install_wayland_dependencies()
        os.execv(sys.executable, [sys.executable, __file__, *sys.argv[1:]])


ensure_gtk()
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk
from settings import autostart_entry, load as load_settings

APP_ID = "dynamic-island-linux"
APP_NAME = "Dynamic Island for Linux"
SOURCE_DIR = Path(__file__).resolve().parent
INSTALL_DIR = Path.home() / ".local" / "share" / APP_ID
BIN_DIR = Path.home() / ".local" / "bin"
DESKTOP_DIR = Path.home() / ".local" / "share" / "applications"


class Installer(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title=f"{APP_NAME} — Kurulum")
        self.set_default_size(600, 470)
        self.set_resizable(False)
        self.connect("destroy", Gtk.main_quit)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        outer.set_margin_top(28); outer.set_margin_bottom(28)
        outer.set_margin_start(32); outer.set_margin_end(32)
        self.add(outer)
        title = Gtk.Label(label=APP_NAME)
        title.set_xalign(0); title.get_style_context().add_class("title-1")
        outer.pack_start(title, False, False, 0)
        subtitle = Gtk.Label(label="Wayland overlay kurulumu — X11 desteği kullanılmaz.")
        subtitle.set_xalign(0); outer.pack_start(subtitle, False, False, 0)
        info = Gtk.Label(label=f"Algılanan sistem: {platform.platform()} ({distro_id()})")
        info.set_xalign(0); outer.pack_start(info, False, False, 6)
        self.status = Gtk.Label(label="Kuruluma hazır.")
        self.status.set_xalign(0); outer.pack_start(self.status, False, False, 8)
        self.progress = Gtk.ProgressBar(); outer.pack_start(self.progress, False, False, 0)
        self.log = Gtk.TextView(); self.log.set_editable(False); self.log.set_monospace(True)
        scroll = Gtk.ScrolledWindow(); scroll.set_min_content_height(190); scroll.add(self.log)
        outer.pack_start(scroll, True, True, 0)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        outer.pack_end(row, False, False, 0)
        close = Gtk.Button(label="Kapat"); close.connect("clicked", lambda *_: self.destroy())
        row.pack_end(close, False, False, 0)
        self.install_button = Gtk.Button(label="Kur")
        self.install_button.connect("clicked", self.start_install)
        row.pack_end(self.install_button, False, False, 0)

    def write_log(self, text: str) -> None:
        buffer = self.log.get_buffer()
        buffer.insert(buffer.get_end_iter(), text.rstrip() + "\n")

    def set_status(self, text: str, fraction: float | None = None) -> None:
        self.status.set_text(text)
        if fraction is not None: self.progress.set_fraction(fraction)

    def start_install(self, _button: Gtk.Button) -> None:
        self.install_button.set_sensitive(False)
        threading.Thread(target=self.install, daemon=True).start()

    def install(self) -> None:
        try:
            INSTALL_DIR.mkdir(parents=True, exist_ok=True); BIN_DIR.mkdir(parents=True, exist_ok=True); DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
            for name in ("main.py", "wayland_app.py", "media.py", "notification_watcher.py", "system_monitor.py", "file_monitor.py", "settings.py", "control_panel.py", "run.sh", "README.md"):
                shutil.copy2(SOURCE_DIR / name, INSTALL_DIR / name)
            (INSTALL_DIR / "run.sh").chmod(0o755)
            GLib.idle_add(self.set_status, "Dosyalar kuruldu…", 0.45)
            launcher = BIN_DIR / APP_ID
            launcher.write_text(f"#!/bin/sh\nexec {INSTALL_DIR / 'run.sh'} \"$@\"\n"); launcher.chmod(0o755)
            panel_launcher = BIN_DIR / f"{APP_ID}-control"
            panel_launcher.write_text(f"#!/bin/sh\nexec {sys.executable} {INSTALL_DIR / 'control_panel.py'} \"$@\"\n"); panel_launcher.chmod(0o755)
            desktop = DESKTOP_DIR / f"{APP_ID}.desktop"
            desktop.write_text(f"[Desktop Entry]\nType=Application\nName={APP_NAME}\nComment=Wayland Dynamic Island overlay\nExec={launcher}\nTerminal=false\nCategories=Utility;\nStartupNotify=true\n")
            panel_desktop = DESKTOP_DIR / f"{APP_ID}-control.desktop"
            panel_desktop.write_text(f"[Desktop Entry]\nType=Application\nName=Dynamic Island Control Panel\nComment=Configure Dynamic Island\nExec={panel_launcher}\nTerminal=false\nCategories=Settings;Utility;\nStartupNotify=true\n")
            autostart = Path.home() / ".config" / "autostart"
            autostart.mkdir(parents=True, exist_ok=True)
            autostart_file = autostart / f"{APP_ID}.desktop"
            if load_settings().get("auto_start", True):
                autostart_file.write_text(autostart_entry(launcher))
            elif autostart_file.exists():
                autostart_file.unlink()
            GLib.idle_add(self.set_status, "Uygulama menüsü güncelleniyor…", 0.8)
            if shutil.which("update-desktop-database"):
                subprocess.run(["update-desktop-database", str(DESKTOP_DIR)], check=False)
            GLib.idle_add(self.write_log, f"Kuruldu: {INSTALL_DIR}")
            GLib.idle_add(self.set_status, "Kurulum tamamlandı. Uygulamalar menüsünden açabilirsiniz.", 1.0)
            GLib.idle_add(self.install_button.set_label, "Tamamlandı")
        except Exception as exc:
            GLib.idle_add(self.write_log, f"HATA: {exc}")
            GLib.idle_add(self.set_status, "Kurulum başarısız oldu; ayrıntı logda.")
            GLib.idle_add(self.install_button.set_sensitive, True)


def main() -> None:
    if not os.environ.get("WAYLAND_DISPLAY"):
        raise RuntimeError("Bu sürüm yalnızca Wayland oturumlarında çalışır. X11 desteği kaldırıldı.")
    window = Installer(); window.show_all(); Gtk.main()


if __name__ == "__main__":
    main()
