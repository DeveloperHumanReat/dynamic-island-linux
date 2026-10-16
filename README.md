# Dynamic Island for Linux

Bu sürüm yalnızca **Wayland** için geliştirilir. X11, XWayland ve Tkinter projeden çıkarılmıştır. Üstteki arayüz `GTK3 + gtk-layer-shell` ile Wayland compositor’ın overlay katmanında çalışır.

## Grafik kurulum

Wayland oturumunda `./install.sh` çalıştırın. Kurucu PyGObject, GTK3, gtk-layer-shell ve D-Bus araçlarını dağıtımın paket yöneticisiyle otomatik kurar. CachyOS dahil Arch türevleri, Debian/Ubuntu, Fedora/RHEL, openSUSE, Alpine ve Void aileleri desteklenir. Kurulum ayrıca uygulamayı otomatik başlatmak için `~/.config/autostart` girdisi oluşturur.

## Eklenen özellikler

**Sistem kontrolleri:** `wpctl`/PulseAudio üzerinden ses seviyesi, UPower üzerinden pil, NetworkManager üzerinden ağ ve PulseAudio/PipeWire kaynak akışları üzerinden mikrofon kullanımı izlenir. Aktif mikrofon veya Discord, Zoom, Teams, Meet, Skype ve Jitsi benzeri bir görüşme algılanırsa özel aktivite gösterilir.

**Dosya aktiviteleri:** `~/Downloads` klasörü izlenir. Yeni bir dosya geldiğinde dosya adı Dynamic Island’da indirme tamamlandı olayı olarak gösterilir.

**Zamanlayıcı/kronometre:** `T` ile beş dakikalık geri sayım başlatılır, `C` ile durdurulur. Kalan süre her saniye güncellenir ve tamamlanınca sonuç animasyonu gösterilir.

**Müzik çalar:** MPRIS2 üzerinden Spotify, VLC, Elisa, Amberol, Firefox ve diğer uyumlu oynatıcılar algılanır. Parça adı ve sanatçı gösterilir; Expanded görünümde önceki, oynat/duraklat ve sonraki kontrolleri çalışır.

**Bildirim merkezi:** D-Bus Notify çağrıları izlenir. Bildirim başlığı/gövdesi kısa süreli genişletilmiş aktiviteye dönüşür ve okunmamış sayısı tutulur. `B` okunmamış bildirim sayısını gösterip sayacı temizler.

**Görsel özelleştirme:** `S` ile açılan ayar penceresinden koyu/açık tema seçilebilir. Ayarlar `~/.config/dynamic-island-linux/settings.json` içinde saklanır.

**Birden fazla aktivite:** Medya, bildirim, indirme, timer ve sistem olayları öncelik sırasıyla aktivite kuyruğunda tutulur. `Space` veya `Enter` kuyruğun sonraki aktivitesine geçer.

**Otomatik başlatma:** Kurulum uygulama menüsü girdisinin yanında kullanıcı oturumunda otomatik başlatma girdisi oluşturur.

## Çalıştırma ve kontroller

```bash
~/.local/bin/dynamic-island-linux
```

- Tıklama: Compact/Expanded geçişi
- `Space` / `Enter`: aktivite kuyruğunda ilerle
- `T`: 5 dakikalık timer başlat
- `C`: timer’ı durdur
- `B`: okunmamış bildirim sayısını göster ve temizle
- `S`: tema ayarlarını aç
- `N`: demo bildirim olayı
- `Esc`: Compact görünüm
- `Q`: kapat

Başlatma hataları:

```bash
cat ~/.local/state/dynamic-island-linux/launcher.log
```

Wayland ve `wlr-layer-shell` destekli compositor gereklidir. X11 desteği yoktur.
