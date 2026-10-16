# Dynamic Island for Linux

Bu sürüm yalnızca **Wayland** için geliştirilir. X11, XWayland, Tkinter ve X11 fallback kodu projeden çıkarılmıştır. Üstteki arayüz `GTK3 + gtk-layer-shell` kullanarak Wayland compositor’ın onayladığı `overlay` katmanında çalışır.

## Grafik kurulum

Wayland oturumunda:

```bash
chmod +x install.sh
./install.sh
```

Kurulum betiği önce Wayland oturumunu kontrol eder, sonra grafik GTK kurucuyu açar. Kurucu gerekli PyGObject, GTK3 ve gtk-layer-shell paketlerini dağıtımın paket yöneticisiyle otomatik kurar. Debian/Ubuntu, Fedora/RHEL, Arch/Manjaro/CachyOS/Garuda/EndeavourOS/Artix, openSUSE, Alpine ve Void aileleri desteklenir.

Kurulum uygulamayı `~/.local/share/dynamic-island-linux` altına, başlatıcıyı `~/.local/bin/dynamic-island-linux` altına ve uygulama menüsü girdisini `~/.local/share/applications` altına yerleştirir. Uygulama dosyalarını kopyalamak için root gerekmez; yalnızca eksik sistem paketlerini kurarken sudo istenir.

## Çalıştırma

Kurulumdan sonra uygulamalar menüsünden **Dynamic Island for Linux** seçin veya:

```bash
~/.local/bin/dynamic-island-linux
```

Uygulama başlamazsa hata ayrıntısı burada bulunur:

```bash
cat ~/.local/state/dynamic-island-linux/launcher.log
```

Wayland oturumu yoksa launcher açıkça hata verir. X11 desteği bu sürümde yoktur.

## Kontroller

Tıklama Compact ve Expanded görünümler arasında geçiş yapar. Space veya Enter demo aktivitelerini değiştirir. N yeni bir indirme tamamlandı olayını gösterir. Esc Compact görünüme döner. Q uygulamayı kapatır.

## Mimari

`main.py` Wayland giriş noktasıdır. `wayland_app.py` GTK layer-shell yüzeyini, animasyonları ve Dynamic Island arayüzünü içerir. `installer.py` de GTK ile yazılmıştır; Tkinter kullanılmaz. `run.sh` çalışma dizinini ayarlar, Wayland kontrolü yapar ve başlatma hatalarını loglar.

Wayland compositor’ın `wlr-layer-shell` protokolünü desteklemesi gerekir. Desteklenmeyen compositor’larda bu uygulama pencereyi başka bir protokole gizlice düşürmez; açık hata verir. Bu davranış X11’e sessizce dönmekten daha güvenlidir.
