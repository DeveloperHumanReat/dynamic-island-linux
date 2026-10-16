# Dynamic Island for Linux

Bu sürüm yalnızca **Wayland** için geliştirilir. X11, XWayland ve Tkinter projeden çıkarılmıştır. Üstteki arayüz `GTK3 + gtk-layer-shell` ile Wayland compositor’ın onayladığı overlay katmanında çalışır.

## Grafik kurulum

Wayland oturumunda:

```bash
chmod +x install.sh
./install.sh
```

Kurucu; PyGObject, GTK3, gtk-layer-shell ve D-Bus araçlarını dağıtımın paket yöneticisiyle otomatik kurar. Debian/Ubuntu, Fedora/RHEL, Arch/Manjaro/CachyOS/Garuda/EndeavourOS/Artix, openSUSE, Alpine ve Void aileleri desteklenir.

## Müzik çalar entegrasyonu

Uygulama oturum D-Bus’ındaki **MPRIS2** oyuncularını otomatik bulur. Spotify, VLC, Elisa, Amberol, Firefox medya oturumu ve MPRIS destekleyen diğer oynatıcılar çalışırken Dynamic Island’da parça adı ve sanatçı görünür. Aktivite, oyuncunun `PlaybackStatus` ve `Metadata` alanlarını yaklaşık saniyede bir günceller.

Expanded görünümdeki kontroller MPRIS üzerinden çalışır:

- Sol düğme: önceki parça
- Orta düğme: oynat/duraklat
- Sağ düğme: sonraki parça

## Bildirim desteği

Bildirim watcher, oturum D-Bus’ındaki `org.freedesktop.Notifications.Notify` çağrılarını izler ve mevcut bildirim daemon’ını değiştirmez. Yeni bildirim geldiğinde başlık ve gövde Dynamic Island’da kısa süreli Expanded görünümde gösterilir. `dbus-monitor` bulunamazsa müzik entegrasyonu çalışmaya devam eder ve watcher açık bir log mesajıyla devre dışı kalır.

## Çalıştırma

Kurulumdan sonra uygulamalar menüsünden **Dynamic Island for Linux** seçin veya:

```bash
~/.local/bin/dynamic-island-linux
```

Başlatma hataları:

```bash
cat ~/.local/state/dynamic-island-linux/launcher.log
```

Wayland ve `wlr-layer-shell` destekli compositor gereklidir. X11 desteği yoktur.

## Kontroller

Tıklama Compact ve Expanded görünümler arasında geçiş yapar. Expanded görünümde medya düğmeleri MPRIS komutları gönderir. Space veya Enter demo aktivitelerini değiştirir. N demo bildirim olayı gösterir. Esc Compact görünüme döner. Q uygulamayı kapatır.

## Mimari

`main.py` Wayland giriş noktasıdır. `wayland_app.py` GTK layer-shell arayüzünü içerir. `media.py` MPRIS2 D-Bus istemcisidir. `notification_watcher.py` mevcut bildirim daemon’ını bozmadan Notify çağrılarını izler. `installer.py` GTK grafik kurucusudur. `run.sh` Wayland kontrolü yapar ve başlatma hatalarını loglar.
