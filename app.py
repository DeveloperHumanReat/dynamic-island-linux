#!/usr/bin/env python3
"""Dynamic Island for Linux - dependency-free X11 prototype.

This first milestone focuses on the interaction model:
- compact pill at the top center
- expanded state on click
- auto-collapsing temporary event
- demo activity rotation with keyboard shortcuts

A future Wayland backend can keep the same Activity model and replace only
OverlayWindow with a layer-shell implementation.
"""

from __future__ import annotations

import math
import tkinter as tk
from dataclasses import dataclass
from typing import Callable


@dataclass
class Activity:
    icon: str
    title: str
    detail: str
    accent: str
    progress: float | None = None
    persistent: bool = True


ACTIVITIES = [
    Activity("♪", "Now Playing", "Midnight City  ·  M83", "#9b8cff"),
    Activity("↓", "Downloading", "dynamic-island-linux.tar.gz", "#62d6ff", 0.68),
    Activity("◷", "Timer", "12:48 remaining", "#ffca68"),
]


class DynamicIsland:
    COMPACT_W = 188
    COMPACT_H = 48
    EXPANDED_W = 360
    EXPANDED_H = 142
    TOP_MARGIN = 18
    ANIMATION_MS = 16

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.expanded = False
        self.activity_index = 0
        self.activity = ACTIVITIES[0]
        self.target_w = self.COMPACT_W
        self.target_h = self.COMPACT_H
        self.current_w = self.COMPACT_W
        self.current_h = self.COMPACT_H
        self._animating = False
        self._hide_job: str | None = None

        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.98)
        root.configure(bg="#000001")
        try:
            root.wm_attributes("-transparentcolor", "#000001")
        except tk.TclError:
            # Some compositors do not expose transparentcolor; the black
            # window still remains usable as a prototype.
            pass

        self.canvas = tk.Canvas(root, bg="#000001", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.toggle)
        self.canvas.bind("<Enter>", lambda _event: self._cancel_hide())
        self.canvas.bind("<Leave>", self._schedule_hide)

        root.bind("<Escape>", lambda _event: self.collapse())
        root.bind("<space>", lambda _event: self.next_activity())
        root.bind("<Return>", lambda _event: self.toggle())
        root.bind("<Control-q>", lambda _event: root.destroy())

        self._position()
        self._draw()
        self._schedule_hide()

    def _position(self) -> None:
        screen_w = self.root.winfo_screenwidth()
        x = max(0, int((screen_w - self.current_w) / 2))
        self.root.geometry(f"{int(self.current_w)}x{int(self.current_h)}+{x}+{self.TOP_MARGIN}")

    def _rounded_rect(self, x1: float, y1: float, x2: float, y2: float,
                      radius: float, fill: str, outline: str = "") -> None:
        c = self.canvas
        c.create_arc((x1, y1, x1 + radius * 2, y1 + radius * 2), start=180, extent=90,
                     fill=fill, outline=outline)
        c.create_arc((x2 - radius * 2, y1, x2, y1 + radius * 2), start=90, extent=90,
                     fill=fill, outline=outline)
        c.create_arc((x1, y2 - radius * 2, x1 + radius * 2, y2), start=180, extent=-90,
                     fill=fill, outline=outline)
        c.create_arc((x2 - radius * 2, y2 - radius * 2, x2, y2), start=0, extent=90,
                     fill=fill, outline=outline)
        c.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline=outline)
        c.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline=outline)

    def _draw(self) -> None:
        self.canvas.delete("all")
        w, h = self.current_w, self.current_h
        pad = 4
        self._rounded_rect(pad, pad, w - pad, h - pad, 22, "#09090d")

        a = self.activity
        if not self.expanded:
            self.canvas.create_oval(16, 14, 38, 36, fill=a.accent, outline="")
            self.canvas.create_text(27, 25, text=a.icon, fill="#111119", font=("DejaVu Sans", 12, "bold"))
            self.canvas.create_text(50, 24, text=a.title, anchor="w", fill="#f3f3f7",
                                    font=("DejaVu Sans", 11, "bold"))
            if a.progress is not None:
                self.canvas.create_arc(w - 37, 13, w - 15, 35, start=90,
                                       extent=-360 * a.progress, style="arc", outline=a.accent, width=3)
                self.canvas.create_text(w - 26, 24, text=f"{int(a.progress * 100)}",
                                        fill="#f3f3f7", font=("DejaVu Sans", 7, "bold"))
            else:
                self.canvas.create_oval(w - 31, 18, w - 21, 28, fill=a.accent, outline="")
            return

        # Expanded content keeps the compact identity in the same relative area.
        self.canvas.create_oval(22, 20, 54, 52, fill=a.accent, outline="")
        self.canvas.create_text(38, 36, text=a.icon, fill="#111119", font=("DejaVu Sans", 16, "bold"))
        self.canvas.create_text(68, 28, text=a.title, anchor="w", fill="#f7f7fb",
                                font=("DejaVu Sans", 13, "bold"))
        self.canvas.create_text(68, 49, text=a.detail, anchor="w", fill="#a6a6b2",
                                font=("DejaVu Sans", 10))

        if a.progress is not None:
            x1, x2, y = 22, w - 22, 78
            self._rounded_rect(x1, y, x2, y + 5, 3, "#282832")
            self._rounded_rect(x1, y, x1 + (x2 - x1) * a.progress, y + 5, 3, a.accent)

        # Small, intentionally simple controls for the first milestone.
        buttons = [("‹", 82), ("Ⅱ", 128), ("›", 174)]
        for label, x in buttons:
            self.canvas.create_oval(x, 96, x + 32, 128, fill="#1c1c25", outline="")
            self.canvas.create_text(x + 16, 112, text=label, fill="#f0f0f4",
                                    font=("DejaVu Sans", 12, "bold"))
        self.canvas.create_text(w - 22, 112, text="×", fill="#7f7f8c",
                                font=("DejaVu Sans", 15), anchor="e")

    def _animate(self) -> None:
        dw = self.target_w - self.current_w
        dh = self.target_h - self.current_h
        if abs(dw) < 1 and abs(dh) < 1:
            self.current_w, self.current_h = self.target_w, self.target_h
            self._position()
            self._draw()
            self._animating = False
            return
        # Smooth, spring-like interpolation without extra dependencies.
        self.current_w += dw * 0.23
        self.current_h += dh * 0.23
        self._position()
        self._draw()
        self.root.after(self.ANIMATION_MS, self._animate)

    def _resize(self, expanded: bool) -> None:
        self.expanded = expanded
        self.target_w = self.EXPANDED_W if expanded else self.COMPACT_W
        self.target_h = self.EXPANDED_H if expanded else self.COMPACT_H
        if not self._animating:
            self._animating = True
            self._animate()

    def toggle(self, _event: tk.Event | None = None) -> None:
        self._cancel_hide()
        self._resize(not self.expanded)
        if not self.expanded:
            self._schedule_hide()

    def collapse(self) -> None:
        self._resize(False)
        self._schedule_hide()

    def next_activity(self) -> None:
        self.activity_index = (self.activity_index + 1) % len(ACTIVITIES)
        self.activity = ACTIVITIES[self.activity_index]
        self._cancel_hide()
        self._draw()
        self._resize(True)
        self.root.after(1700, self.collapse)

    def show_event(self, icon: str, title: str, detail: str, accent: str = "#70e1a1") -> None:
        self.activity = Activity(icon, title, detail, accent, persistent=False)
        self._cancel_hide()
        self._resize(True)
        self.root.after(2200, self.collapse)

    def _schedule_hide(self, _event: tk.Event | None = None) -> None:
        self._cancel_hide()
        if not self.expanded:
            self._hide_job = self.root.after(4200, self.collapse)

    def _cancel_hide(self) -> None:
        if self._hide_job is not None:
            self.root.after_cancel(self._hide_job)
            self._hide_job = None


def main() -> None:
    root = tk.Tk()
    island = DynamicIsland(root)
    # Demo shortcut: press N to simulate a fresh system event.
    root.bind("n", lambda _event: island.show_event("✓", "Download complete", "File is ready", "#70e1a1"))
    root.mainloop()


if __name__ == "__main__":
    main()
