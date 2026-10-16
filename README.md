# Dynamic Island for Linux

Bu proje, iOS Dynamic Island davranış modelini Linux masaüstüne taşıyan ilk prototiptir. Üst merkezde kompakt kapsül, genişletilmiş görünüm, aktivite rotasyonu ve geçici olay animasyonu içerir.

## Grafik kurulum

Kurulum dosyasını çalıştırın:

```bash
chmod +x install.sh
./install.sh
```

`install.sh`, Python 3 ve Tkinter bileşenini kontrol eder. Tkinter eksikse dağıtımı algılayıp uygun paket yöneticisiyle otomatik kurar. Desteklenen paket yöneticileri Debian/Ubuntu (`apt`), Fedora/RHEL (`dnf` veya `yum`), Arch/Manjaro/CachyOS/Garuda/EndeavourOS (`pacman`), openSUSE (`zypper`), Alpine (`apk`) ve Void (`xbps`) aileleridir. Wayland backend’i için PyGObject, GTK3 ve `gtk-layer-shell` bağımlılıkları da aynı akışta otomatik kurulur. Ardından grafik kurucu açılır.

`installer.py` de artık doğrudan çalıştırılabilir. Tkinter eksikse dosyanın en başında bunu algılar, CachyOS dahil dağıtımı eşleştirir, `sudo pacman -S tk` komutunu otomatik çalıştırır ve kendisini yeniden başlatır. Böylece kullanıcı önce elle paket aramak zorunda kalmaz.

Grafik kurucu uygulamayı kullanıcı hesabına `~/.local/share/dynamic-island-linux` altına, başlatıcıyı `~/.local/bin` altına ve uygulama menüsü girdisini `~/.local/share/applications` altına yazar. Bu nedenle uygulama dosyalarını kopyalamak için root gerekmez; yalnızca eksik sistem paketini kurarken sudo yetkisi istenir.

Kaldırmak için:

```bash
./uninstall.sh
```

## Uygulamayı çalıştırma

Kurulumdan sonra uygulamalar menüsünden **Dynamic Island for Linux** seçilebilir veya şu komut kullanılabilir:

```bash
~/.local/bin/dynamic-island-linux
```

## Prototip kontrolleri

Tıklama veya Enter Compact ve Expanded görünümler arasında geçiş yapar. Space demo aktivitelerini değiştirir. N yeni bir indirme tamamlandı olayını gösterir. Esc Compact görünüme döner. Ctrl+Q uygulamayı kapatır.

## Wayland ve X11 backend’leri

Uygulama `WAYLAND_DISPLAY` değişkenini algıladığında GTK3 + `gtk-layer-shell` backend’ini seçer. Bu backend, uygulamayı Wayland compositor’a bildirilmiş gerçek `overlay` layer-shell yüzeyi olarak üst kenara yerleştirir. `wlr-layer-shell` desteklemeyen compositor’larda uygulama güvenli biçimde X11 backend’ine geri döner; bu durumda oturumun XWayland sağlaması gerekir.

X11 oturumlarında mevcut Tkinter backend’i kullanılır. Her iki backend aynı Compact, Expanded ve aktivite modeliyle çalışır. Wayland üzerinde pencereyi zorla en üstte tutmaya çalışmak yerine compositor’ın izin verdiği layer-shell protokolü kullanılır.

## Dağıtımlar arası uyumluluk planı

Bu sürüm X11 için Python 3/Tkinter, Wayland için Python 3/PyGObject/GTK3/gtk-layer-shell kullanır. Kurucu, bağımlılığı kullanıcıdan tek tek istemek yerine paket yöneticisi üzerinden tek işlemde kurar. Ancak tüm Linux dağıtımlarında aynı paket adı veya aynı compositor protokolü garanti edilemez.

Daha güçlü ürün sürümünde masaüstü bağımsız dağıtım için iki paket hedeflenecek:

1. **Flatpak:** GTK ve sistem bağımlılıklarını runtime içinde sabitler, modern Linux dağıtımlarında en tutarlı kurulum yoludur.
2. **AppImage:** Tek dosyalık taşınabilir dağıtım sağlar; X11 uyumluluk modunda kolay çalışır.

Wayland desteği için `wlr-layer-shell` tabanlı native backend eklenecek. GNOME gibi `wlr-layer-shell` sunmayan compositor’lar için compositor’a özgü bir adaptör veya masaüstü eklentisi gerekebilir. Bu kısıt, kurucuyla çözülemeyen bir protokol farkıdır.
