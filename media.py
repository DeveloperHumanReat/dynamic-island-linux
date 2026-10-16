#!/usr/bin/env python3
"""Small MPRIS2 client for Wayland Dynamic Island."""
from __future__ import annotations

from typing import Callable

import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib


class MediaController:
    def __init__(self, on_update: Callable[[dict], None]) -> None:
        self.on_update = on_update
        self.connection = None
        self.proxy = None
        self.bus_name: str | None = None
        try:
            self.connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            GLib.timeout_add(1000, self.poll)
            self.poll()
        except Exception as exc:
            print(f"MPRIS kullanılamıyor: {exc}")

    def _names(self) -> list[str]:
        proxy = Gio.DBusProxy.new_sync(
            self.connection, Gio.DBusProxyFlags.NONE, None,
            "org.freedesktop.DBus", "/org/freedesktop/DBus",
            "org.freedesktop.DBus", None)
        result = proxy.call_sync("ListNames", None, Gio.DBusCallFlags.NONE, 1000, None)
        return list(result.unpack()[0])

    def _connect_player(self) -> None:
        names = [n for n in self._names() if n.startswith("org.mpris.MediaPlayer2.")]
        name = names[0] if names else None
        if name == self.bus_name and self.proxy is not None:
            return
        self.bus_name = name
        self.proxy = None
        if name:
            self.proxy = Gio.DBusProxy.new_sync(
                self.connection, Gio.DBusProxyFlags.NONE, None, name,
                "/org/mpris/MediaPlayer2", "org.mpris.MediaPlayer2.Player", None)

    @staticmethod
    def _value(value):
        return value.unpack() if hasattr(value, "unpack") else value

    def _metadata(self) -> tuple[str, str]:
        metadata = self.proxy.get_cached_property("Metadata")
        if not metadata:
            return "", ""
        data = metadata.unpack()
        title = self._value(data.get("xesam:title", ""))
        artists = self._value(data.get("xesam:artist", []))
        artist = artists[0] if isinstance(artists, (list, tuple)) and artists else str(artists or "")
        return str(title or ""), str(artist or "")

    def poll(self) -> bool:
        try:
            self._connect_player()
            if not self.proxy:
                self.on_update({"active": False})
                return True
            status = self._value(self.proxy.get_cached_property("PlaybackStatus"))
            title, artist = self._metadata()
            if status in ("Playing", "Paused") and title:
                self.on_update({"active": True, "playing": status == "Playing", "title": title, "artist": artist})
            else:
                self.on_update({"active": False})
        except Exception as exc:
            print(f"MPRIS güncellemesi başarısız: {exc}")
        return True

    def command(self, method: str) -> None:
        if self.proxy is None:
            return
        try:
            self.proxy.call_sync(method, None, Gio.DBusCallFlags.NONE, 1000, None)
            self.poll()
        except Exception as exc:
            print(f"MPRIS komutu başarısız: {exc}")

    def play_pause(self) -> None: self.command("PlayPause")
    def next(self) -> None: self.command("Next")
    def previous(self) -> None: self.command("Previous")
