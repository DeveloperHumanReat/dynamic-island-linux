#!/usr/bin/env python3
"""Wayland backend using GTK3 + gtk-layer-shell."""
from __future__ import annotations

import math
import tkinter  # noqa: F401  # keeps the same Python runtime requirement as X11
from dataclasses import dataclass

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gtk, Gdk, GLib, GtkLayerShell, cairo


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

        self.window = Gtk.Window()
        self.window.set_decorated(False)
        self.window.set_resizable(False)
        self.window.set_app_paintable(True)
        self.window.set_visual(self.window.get_screen().get_rgba_visual())
        self.window.connect("destroy", Gtk.main_quit)
        self.window.connect("button-press-event", self.on_click)
        self.window.connect("key-press-event", self.on_key)
        self.window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)

        GtkLayerShell.init_for_window(self.window)
        GtkLayerShell.set_layer(self.window, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_anchor(self.window, GtkLayerShell.Edge.TOP, True)
        GtkLayerShell.set_margin(self.window, GtkLayerShell.Edge.TOP, 18)
        GtkLayerShell.set_exclusive_zone(self.window, 0)
        GtkLayerShell.set_keyboard_interactivity(self.window, GtkLayerShell.KeyboardMode.ON_DEMAND)

        self.area = Gtk.DrawingArea()
        self.area.connect("draw", self.draw)
        self.window.add(self.area)
        self.window.set_default_size(*self.COMPACT)
        self.window.show_all()
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
        ctx.set_operator(cairo.OPERATOR_CLEAR)
        ctx.paint()
        ctx.set_operator(cairo.OPERATOR_OVER)
        ctx.set_source_rgb(0.035, 0.035, 0.05)
        self.rounded_rectangle(ctx, 4, 4, w - 8, h - 8, 22)
        ctx.fill()

        a = self.activity
        self.text(ctx, a.icon, 18 if not self.expanded else 24, 31 if not self.expanded else 44,
                  14 if not self.expanded else 20, a.accent, True)
        self.text(ctx, a.title, 50 if not self.expanded else 68, 30 if not self.expanded else 32,
                  11 if not self.expanded else 13, (0.95, 0.95, 0.98), True)

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

        self.text(ctx, a.detail, 68, 53, 10, (0.65, 0.65, 0.71))
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
        self.set_expanded(not self.expanded)
        return True

    def on_key(self, _widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        key = Gdk.keyval_name(event.keyval)
        if key in ("Escape",):
            self.set_expanded(False)
        elif key in ("space", "Return"):
            self.activity_index = (self.activity_index + 1) % len(ACTIVITIES)
            self.activity = ACTIVITIES[self.activity_index]
            self.set_expanded(True)
        elif key == "n":
            self.activity = Activity("✓", "Download complete", "File is ready", (0.44, 0.88, 0.63))
            self.set_expanded(True)
            GLib.timeout_add(2200, self.auto_collapse)
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
