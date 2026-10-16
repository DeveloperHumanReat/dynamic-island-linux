#!/usr/bin/env python3
"""GTK control panel for Dynamic Island for Linux."""
from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from settings import load, save


class ControlPanel(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="Dynamic Island — Control Panel")
        self.set_default_size(620, 620)
        self.set_border_width(22)
        self.settings = load()
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.add(root)
        title = Gtk.Label(label="Dynamic Island Control Panel")
        title.set_xalign(0); title.get_style_context().add_class("title-1")
        root.pack_start(title, False, False, 0)
        subtitle = Gtk.Label(label="Wayland overlay özelliklerini ve davranışını buradan yönetin.")
        subtitle.set_xalign(0); root.pack_start(subtitle, False, False, 0)

        notebook = Gtk.Notebook(); root.pack_start(notebook, True, True, 0)
        notebook.append_page(self.feature_page(), Gtk.Label(label="Features"))
        notebook.append_page(self.appearance_page(), Gtk.Label(label="Appearance"))
        notebook.append_page(self.behavior_page(), Gtk.Label(label="Behavior"))

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        root.pack_end(actions, False, False, 0)
        reset = Gtk.Button(label="Reset defaults"); reset.connect("clicked", self.reset)
        actions.pack_start(reset, False, False, 0)
        save_button = Gtk.Button(label="Save settings"); save_button.connect("clicked", self.save_settings)
        actions.pack_end(save_button, False, False, 0)
        close = Gtk.Button(label="Close"); close.connect("clicked", lambda *_: self.destroy())
        actions.pack_end(close, False, False, 0)

    def row(self, box: Gtk.Box, label: str, key: str) -> Gtk.Switch:
        line = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        text = Gtk.Label(label=label); text.set_xalign(0); line.pack_start(text, True, True, 0)
        switch = Gtk.Switch(); switch.set_active(bool(self.settings.get(key, True))); line.pack_end(switch, False, False, 0)
        box.pack_start(line, False, False, 8)
        setattr(self, f"switch_{key}", switch)
        return switch

    def feature_page(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8); box.set_border_width(18)
        self.row(box, "Music player / MPRIS", "enable_media")
        self.row(box, "Desktop notifications", "enable_notifications")
        self.row(box, "System status", "enable_system")
        self.row(box, "Downloads and file activities", "enable_downloads")
        self.row(box, "Timer and stopwatch", "enable_timer")
        self.row(box, "Do Not Disturb", "do_not_disturb")
        return box

    def appearance_page(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); box.set_border_width(18)
        box.pack_start(Gtk.Label(label="Theme", xalign=0), False, False, 0)
        self.theme = Gtk.ComboBoxText(); self.theme.append("dark", "Dark"); self.theme.append("light", "Light")
        self.theme.set_active_id(self.settings.get("theme", "dark")); box.pack_start(self.theme, False, False, 0)
        box.pack_start(Gtk.Label(label="Top margin (pixels)", xalign=0), False, False, 0)
        self.margin = Gtk.SpinButton.new_with_range(0, 120, 1); self.margin.set_value(self.settings.get("top_margin", 18)); box.pack_start(self.margin, False, False, 0)
        box.pack_start(Gtk.Label(label="Scale", xalign=0), False, False, 0)
        self.scale = Gtk.SpinButton.new_with_range(0.75, 1.5, 0.05); self.scale.set_value(self.settings.get("scale", 1.0)); box.pack_start(self.scale, False, False, 0)
        return box

    def behavior_page(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12); box.set_border_width(18)
        self.row(box, "Launch automatically at login", "auto_start")
        box.pack_start(Gtk.Label(label="Notification duration (milliseconds)", xalign=0), False, False, 0)
        self.duration = Gtk.SpinButton.new_with_range(1000, 30000, 500); self.duration.set_value(self.settings.get("notification_duration", 4200)); box.pack_start(self.duration, False, False, 0)
        info = Gtk.Label(label="Keyboard: P opens this panel, S opens quick theme settings, T starts a timer.")
        info.set_xalign(0); info.set_line_wrap(True); box.pack_start(info, False, False, 20)
        return box

    def collect(self) -> dict:
        data = dict(self.settings)
        for key in ("enable_media", "enable_notifications", "enable_system", "enable_downloads", "enable_timer", "do_not_disturb", "auto_start"):
            data[key] = getattr(self, f"switch_{key}").get_active()
        data.update({"theme": self.theme.get_active_id() or "dark", "top_margin": int(self.margin.get_value()), "scale": self.scale.get_value(), "notification_duration": int(self.duration.get_value())})
        return data

    def save_settings(self, _button=None) -> None:
        save(self.collect())

    def reset(self, _button) -> None:
        self.settings = load(); self.settings.update({"theme": "dark", "top_margin": 18, "scale": 1.0, "auto_start": True, "do_not_disturb": False})
        self.destroy(); ControlPanel().show_all()


def main() -> None:
    if not __import__("os").environ.get("WAYLAND_DISPLAY"):
        raise RuntimeError("Control Panel yalnızca Wayland oturumlarında çalışır.")
    window = ControlPanel(); window.connect("destroy", Gtk.main_quit); window.show_all(); Gtk.main()


if __name__ == "__main__":
    main()
