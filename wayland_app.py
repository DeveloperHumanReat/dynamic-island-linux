#!/usr/bin/env python3
"""Wayland backend using GTK3 + gtk-layer-shell."""
from __future__ import annotations

import math
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell, cairo
from media import MediaController
from notification_watcher import NotificationWatcher
from settings import load as load_settings, save as save_settings
from system_monitor import SystemMonitor
from file_monitor import DownloadMonitor


@dataclass
class Activity:
    icon: str
    title: str
    detail: str
    accent: tuple[float, float, float]
    progress: float | None = None


ACTIVITIES = [
    Activity("♪", "Now Playing", "Midnight City  ·  M83", (0.61, 0.55, 1.0)),
    Activity("↓", "Downloading", "dynamic-island-linux.tar.gz", (0.38, 0.84, 1.0), 0.68),
    Activity("◷", "Timer", "12:48 remaining", (1.0, 0.79, 0.41)),
]


class WaylandIsland:
    COMPACT = (188, 48)
    EXPANDED = (360, 142)

    def __init__(self) -> None:
        self.expanded = False
        self.activity_index = 0
        self.activity = ACTIVITIES[0]
        self.width, self.height = self.COMPACT
        self.target_width, self.target_height = self.COMPACT
        self.animating = False
        self.media_active = False
        self.notification_timeout = 0
        self.settings = load_settings()
        self.timer_remaining = 0
        self.timer_running = False
        self.activity_queue: list[Activity] = []
        self.unread_notifications = 0

        self.window = Gtk.Window()
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_app_paintable(True)
        self.window.set_visual(self.window.get_screen().get_rgba_visual())
        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("button-press-event", self.on_click)
        self.window.connect("key-press-event", self.on_key)
        self.window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        self.layer_shell_active = False
        try:
            GtkLayerShell.init_for_window(self.window)
            GtkLayerShell.set_layer(self.window, GtkLayerShell.Layer.OVERLAY)
            GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.TOP, True)
            GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.TOP, int(self.settings.get("top_margin", 18)))
            GtkLayerShell.set_exclusive_zone(self.window, 0)
            GtkLayerShell.set_keyboard_interactivity(self.window, GtkLayerShell.KeyboardMode.ON_DEMAND)
            self.layer_shell_active = True
        except Exception as exc:
            # Some Wayland compositors do not expose layer-shell. Keep the
            # island visible as a regular undecorated Wayland window instead
            # of exiting silently; it remains fully GTK/Wayland based.
            print(f"Layer-shell kullanılamıyor, görünür Wayland pencere fallback'i: {exc}")
            self.window.set_title("Dynamic Island for Linux")
            self.window.set_keep_above(True)

        self.area = Gtk.DrawingArea()
        self.area.connect("draw", self.draw)
        self.overlay = Gtk.Overlay()
        self.overlay.add(self.area)
        css = Gtk.CssProvider()
        css.load_from_data(b"label { color: #f2f1ff; font-weight: 600; }")
        Gtk.StyleContext.add_provider_for_screen(self.window.get_screen(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.icon_label = Gtk.Label(label="♪")
        self.icon_label.set_halign(Gtk.Align.START); self.icon_label.set_valign(Gtk.Align.START)
        self.icon_label.set_margin_start(18); self.icon_label.set_margin_top(12)
        self.overlay.add_overlay(self.icon_label)
        self.title_label = Gtk.Label(label="Dynamic Island")
        self.title_label.set_halign(Gtk.Align.START); self.title_label.set_valign(Gtk.Align.START)
        self.title_label.set_margin_start(50); self.title_label.set_margin_top(10)
        self.overlay.add_overlay(self.title_label)
        self.detail_label = Gtk.Label(label="Ready")
        self.detail_label.set_halign(Gtk.Align.START); self.detail_label.set_valign(Gtk.Align.START)
        self.detail_label.set_margin_start(50); self.detail_label.set_margin_top(30)
        self.detail_label.set_no_show_all(True)
        self.overlay.add_overlay(self.detail_label)
        self.window.add(self.overlay)
        self.window.set_default_size(*self.COMPACT)
        self.window.show_all()
        self.detail_label.hide()
        self.media = MediaController(self.on_media_update) if self.settings.get("enable_media", True) else None
        self.notifications = NotificationWatcher(self.on_notification) if self.settings.get("enable_notifications", True) else None
        self.system = SystemMonitor(self.on_system_update) if self.settings.get("enable_system", True) else None
        self.downloads = DownloadMonitor(self.on_download) if self.settings.get("enable_downloads", True) else None
        if self.system:
            GLib.timeout_add(2000, self.system.poll)
        if self.downloads:
            GLib.timeout_add(3000, self.downloads.poll)
        GLib.timeout_add(1000, self.tick_timer)
        GLib.timeout_add(4200, self.auto_collapse)

    @staticmethod
    def rounded_rectangle(ctx: cairo.Context, x: float, y: float, w: float, h: float, r: float) -> None:
        ctx.new_sub_path()
        ctx.arc(x + w - r, y + r, r, -math.pi / 2, 0)
        ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
        ctx.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
        ctx.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
        ctx.close_path()

    @staticmethod
    def text(ctx: cairo.Context, value: str, x: float, y: float, size: float,
             color: tuple[float, float, float], bold: bool = False) -> None:
        ctx.set_source_rgb(*color)
        ctx.select_font_face("DejaVu Sans", cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_BOLD if bold else cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(size)
        ctx.move_to(x, y)
        ctx.show_text(value)

    def draw(self, _area: Gtk.DrawingArea, ctx: cairo.Context) -> bool:
        w, h = self.width, self.height
        ctx.set_operator(cairo.Operator.CLEAR)
        ctx.paint()
        ctx.set_operator(cairo.Operator.OVER)
        background = (0.035, 0.035, 0.05) if self.settings.get("theme") == "dark" else (0.88, 0.88, 0.92)
        ctx.set_source_rgb(*background)
        self.rounded_rectangle(ctx, 4, 4, w - 8, h - 8, 22)
        ctx.fill()

        a = self.activity
        self.icon_label.set_text(a.icon)
        self.title_label.set_text(a.title)
        self.detail_label.set_text(a.detail)
        if self.expanded:
            self.icon_label.set_margin_start(24); self.icon_label.set_margin_top(22)
            self.title_label.set_margin_start(68); self.title_label.set_margin_top(15)
            self.detail_label.set_margin_start(68); self.detail_label.set_margin_top(38)
            self.detail_label.show()
        else:
            self.icon_label.set_margin_start(18); self.icon_label.set_margin_top(12)
            self.title_label.set_margin_start(50); self.title_label.set_margin_top(10)
            self.detail_label.hide()

        if not self.expanded:
            if a.progress is not None:
                ctx.set_source_rgb(*a.accent)
                ctx.set_line_width(3)
                ctx.arc(w - 26, 24, 10, -math.pi / 2, -math.pi / 2 + 2 * math.pi * a.progress)
                ctx.stroke()
                self.text(ctx, str(int(a.progress * 100)), w - 31, 27, 7, (0.95, 0.95, 0.98), True)
            else:
                ctx.set_source_rgb(*a.accent)
                ctx.arc(w - 26, 24, 5, 0, 2 * math.pi)
                ctx.fill()
            return True

        if a.progress is not None:
            ctx.set_source_rgb(0.16, 0.16, 0.20)
            self.rounded_rectangle(ctx, 22, 78, w - 44, 5, 3)
            ctx.fill()
            ctx.set_source_rgb(*a.accent)
            self.rounded_rectangle(ctx, 22, 78, (w - 44) * a.progress, 5, 3)
            ctx.fill()
        for label, x in (("‹", 82), ("Ⅱ", 128), ("›", 174)):
            ctx.set_source_rgb(0.11, 0.11, 0.15)
            ctx.arc(x + 16, 112, 16, 0, 2 * math.pi)
            ctx.fill()
            self.text(ctx, label, x + 10, 118, 12, (0.94, 0.94, 0.97), True)
        return True

    def on_click(self, _widget: Gtk.Widget, _event: Gdk.EventButton) -> bool:
        if self.expanded and _event.y >= 94:
            if 76 <= _event.x <= 122:
                if self.media: self.media.previous()
                return True
            if 122 <= _event.x <= 170:
                if self.media: self.media.play_pause()
                return True
            if 170 <= _event.x <= 220:
                if self.media: self.media.next()
                return True
        self.set_expanded(not self.expanded)
        return True

    def on_media_update(self, data: dict) -> None:
        if not data.get("active"):
            if self.media_active:
                self.media_active = False
                self.activity = ACTIVITIES[0]
                self.area.queue_draw()
            return
        self.media_active = True
        title = str(data.get("title", "Music"))[:32]
        artist = str(data.get("artist", ""))[:36]
        self.activity = Activity("♪", title, artist or "Music", (0.61, 0.55, 1.0))
        self.push_activity(self.activity)
        self.area.queue_draw()

    def on_notification(self, app: str, summary: str, body: str) -> None:
        def show() -> bool:
            self.unread_notifications += 1
            title = (summary or app or "Notification")[:42]
            detail = (body or app or "New notification").replace("\n", " ")[:48]
            if self.unread_notifications > 1:
                detail = f"{detail}  ·  {self.unread_notifications} unread"
            self.activity = Activity("•", title, detail, (0.44, 0.88, 0.63))
            self.push_activity(self.activity)
            self.set_expanded(True)
            if self.notification_timeout:
                GLib.source_remove(self.notification_timeout)
            self.notification_timeout = GLib.timeout_add(4200, self.auto_collapse)
            return False
        if self.settings.get("do_not_disturb", False):
            return
        GLib.idle_add(show)

    def on_download(self, filename: str) -> None:
        self.activity = Activity("↓", "Download ready", filename[:42], (0.38, 0.84, 1.0))
        self.push_activity(self.activity)
        self.set_expanded(True)
        GLib.timeout_add(3200, self.auto_collapse)
        self.area.queue_draw()

    def on_system_update(self, payload: dict) -> None:
        changed = payload.get("changed", {})
        state = payload.get("state", {})
        if state.get("call"):
            self.activity = Activity("☎", "Active call", "Microphone in use", (0.42, 0.9, 0.62))
        elif state.get("mic_active"):
            self.activity = Activity("●", "Microphone active", "Audio input is in use", (1.0, 0.45, 0.45))
        elif "battery" in changed and state.get("battery", 100) <= 20:
            self.activity = Activity("▰", "Low battery", f"{state['battery']}% remaining", (1.0, 0.55, 0.38))
        elif "volume" in changed:
            self.activity = Activity("◖", "Volume", f"{state.get('volume', 0)}%", (0.45, 0.78, 1.0))
        elif "network" in changed:
            label = "Network connected" if state.get("network") == "connected" else "Network offline"
            self.activity = Activity("⌁", label, "System status changed", (0.45, 0.78, 1.0))
        else:
            return
        self.push_activity(self.activity)
        self.set_expanded(True)
        GLib.timeout_add(2600, self.auto_collapse)
        self.area.queue_draw()

    def push_activity(self, activity: Activity) -> None:
        self.activity_queue = [item for item in self.activity_queue if item.title != activity.title]
        self.activity_queue.insert(0, activity)
        self.activity_queue = self.activity_queue[:6]

    def tick_timer(self) -> bool:
        if self.timer_running and self.timer_remaining > 0:
            self.timer_remaining -= 1
            minutes, seconds = divmod(self.timer_remaining, 60)
            self.activity = Activity("◷", "Timer", f"{minutes:02d}:{seconds:02d} remaining", (1.0, 0.79, 0.41))
            self.push_activity(self.activity)
            self.area.queue_draw()
            if self.timer_remaining == 0:
                self.timer_running = False
                self.activity = Activity("✓", "Timer finished", "Time is up", (0.44, 0.88, 0.63))
                self.set_expanded(True)
        return True

    def show_settings(self) -> None:
        dialog = Gtk.Dialog(title="Dynamic Island Settings", transient_for=self.window, flags=0)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL); dialog.add_button("Save", Gtk.ResponseType.OK)
        box = dialog.get_content_area(); box.set_spacing(10); box.set_margin_top(16); box.set_margin_bottom(16); box.set_margin_start(16); box.set_margin_end(16)
        theme = Gtk.ComboBoxText(); theme.append("dark", "Dark"); theme.append("light", "Light"); theme.set_active_id(self.settings.get("theme", "dark"))
        box.pack_start(Gtk.Label(label="Theme", xalign=0), False, False, 0); box.pack_start(theme, False, False, 0)
        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            self.settings["theme"] = theme.get_active_id() or "dark"; save_settings(self.settings); self.area.queue_draw()
        dialog.destroy()

    def on_key(self, _widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        key = Gdk.keyval_name(event.keyval)
        if key in ("Escape",):
            self.set_expanded(False)
        elif key in ("space", "Return"):
            if self.activity_queue:
                self.activity = self.activity_queue[(self.activity_index + 1) % len(self.activity_queue)]
                self.activity_index += 1
            else:
                self.activity_index = (self.activity_index + 1) % len(ACTIVITIES)
                self.activity = ACTIVITIES[self.activity_index]
            self.set_expanded(True)
        elif key == "t":
            if self.settings.get("enable_timer", True):
                self.timer_remaining = 300; self.timer_running = True; self.set_expanded(True)
        elif key == "c":
            self.timer_remaining = 0; self.timer_running = False; self.set_expanded(False)
        elif key == "s":
            self.show_settings()
        elif key == "p":
            panel = Path(__file__).with_name("control_panel.py")
            if panel.exists():
                subprocess.Popen([sys.executable, str(panel)])
            else:
                subprocess.Popen([str(Path.home() / ".local/bin/dynamic-island-linux-control")])
        elif key == "n":
            self.activity = Activity("✓", "Download complete", "File is ready", (0.44, 0.88, 0.63))
            self.set_expanded(True)
            GLib.timeout_add(2200, self.auto_collapse)
        elif key == "b":
            self.activity = Activity("•", "Notifications", f"{self.unread_notifications} unread", (0.44, 0.88, 0.63))
            self.unread_notifications = 0
            self.set_expanded(True)
        elif key == "q":
            Gtk.main_quit()
        return True

    def set_expanded(self, expanded: bool) -> None:
        self.expanded = expanded
        self.target_width, self.target_height = self.EXPANDED if expanded else self.COMPACT
        if not self.animating:
            self.animating = True
            GLib.timeout_add(16, self.animate)

    def animate(self) -> bool:
        self.width += (self.target_width - self.width) * 0.23
        self.height += (self.target_height - self.height) * 0.23
        if abs(self.target_width - self.width) < 1 and abs(self.target_height - self.height) < 1:
            self.width, self.height = self.target_width, self.target_height
            self.animating = False
            self.window.set_default_size(self.width, self.height)
            self.area.queue_draw()
            return False
        self.window.set_default_size(int(self.width), int(self.height))
        self.area.queue_draw()
        return True

    def auto_collapse(self) -> bool:
        if not self.expanded:
            return True
        self.set_expanded(False)
        return False


def main() -> None:
    WaylandIsland()
    Gtk.main()


if __name__ == "__main__":
    main()
