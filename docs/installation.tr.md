# Windows kurulumu

## Önerilen yol: kurulum dosyası

[SceneScout kurulum dosyasını indir](https://github.com/Fatih-Haslak/scenescout/releases/latest/download/SceneScout-Setup-Windows-x64.exe), aç, **Türkçe** seç ve kurulumu tamamla. Masaüstündeki **SceneScout** kısayoluna çift tıkla. Yönetici izni, elle Python kurulumu veya API anahtarı gerekmez. Windows 10/11 x64 desteklenir.

| Aşama | Ne olur? |
| --- | --- |
| Kurulum dosyası | Uygulama, rehber ve kısayollar bilgisayarına kopyalanır. |
| İlk açılış | Uyumlu Python ve sürümleri sabitlenmiş paketler internetten hazırlanır. |
| İlk video | Yaklaşık 1,5 GB EmbeddingGemma 2 modeli indirilir; video kareleri indekslenir. |
| Sonraki açılışlar | Hazır ortam ve önbellekteki model kullanılır. |

Diskte birkaç GB boş alan ve yeterli RAM bırak. Sabit bir kurulum süresi yoktur; internet ve donanım hızına bağlıdır. Açılış penceresini açık tut, uygulamayı kapatmak için **Ctrl+C** kullan. Tarayıcı sekmesini kapatmak sunucuyu durdurmaz. İlerleme tamamlanıp videoda **Hazır** yazınca arama yap.

Başlat menüsündeki **Başlangıç rehberi**, internet gerektirmeyen Türkçe/İngilizce rehberi açar. Varsayılan CPU'dur. Uyumlu NVIDIA GPU/sürücü varsa ayrı **NVIDIA GPU** kısayolu kullanılabilir; daha büyük paketler indirir. CPU ve GPU ortamları birbirinden ayrıdır.

## Veriler ve güncelleme

| Dosyalar | Varsayılan konum |
| --- | --- |
| Uygulama | `%LOCALAPPDATA%\Programs\SceneScout` |
| Video kopyaları ve indeksler | `%LOCALAPPDATA%\SceneScout\Data` |
| Python ve CPU/GPU ortamları | `%LOCALAPPDATA%\SceneScout\Runtime` ve `Environments` |
| Açılış kayıtları | `%LOCALAPPDATA%\SceneScout\Logs\setup-cpu.log` / `setup-cuda.log` |
| Model ve paket önbellekleri | Hugging Face ve uv'nin kullanıcı önbellekleri |

Güncellemeden önce uygulamayı Ctrl+C ile durdur ve yeni kurulum dosyasını aç. Arşiv kurulum klasörünün dışında kaldığından korunur. Windows Ayarlar → Uygulamalar üzerinden kaldırma, arşivi ve indirilen ortamları korur. Bunları kalıcı silmek için önce yedekle, sonra ilgili veri klasörünü kendin kaldır.

Eski ZIP/kaynak kod arşivi otomatik taşınmaz: uygulamayı durdur ve eski `.data` klasörünün **içeriğini**, yeni kurulumu başlatmadan önce `%LOCALAPPDATA%\SceneScout\Data` içine kopyala. Mevcut bir arşivin üzerine yazma; önce yedek al.

## Sorun giderme

- **İndirme yarım kaldı:** interneti/boş alanı kontrol et, kısayolu yeniden aç. Tamamlanan önbellek indirmeleri yeniden kullanılır. Kurulum hatasının ayrıntıları yukarıdaki kayıt dosyasındadır.
- **Tarayıcı açılmadı:** açılış penceresindeki hataya bak. Sunucu hazırsa [yerel uygulama adresini](http://127.0.0.1:8765) aç.
- **Adres zaten kullanılıyor:** diğer SceneScout kopyasını Ctrl+C ile durdur. Gelişmiş kullanımda `Start.ps1 -Port 8877` seçilebilir.
- **GPU açılmadı:** CPU kısayolunu kullan; NVIDIA sürücüsü ve CUDA 13.0 PyTorch uyumluluğunu kontrol et.
- **Bağlantı indirilmiyor:** yalnızca tekil, herkese açık videolar desteklenir. Özel, giriş isteyen, canlı veya platformca engellenen içerikler için elindeki dosyayı yükle.
- **Windows yayıncı uyarısı:** paket henüz dijital imzalı değildir. Resmî sürüm sayfasını ve `SHA256SUMS.txt` özetlerini kontrol et. Kurulum sistemin güvenlik ayarlarını değiştirmez.

Sorun bildirirken kullanılan sürümü ve ilgili hatayı paylaş; kişisel yolları, video adreslerini ve özel bilgileri kayıttan çıkar.

## ZIP ve geliştirici kurulumu

Taşınabilir ZIP'i **önce çıkart**, `QUICKSTART.html` rehberini aç, sonra `Start.cmd` dosyasını çalıştır. Video arşivi bu klasörün `.data` altındadır. Yeni ZIP'e geçerken bunu koru. CPU ve GPU ortamları `.venv-cpu` ve `.venv-cuda` klasörlerinde ayrıdır.

Kaynak kod kurulumu için [English installation guide](installation.md) içindeki geliştirici bölümünü kullan. Windows paketleri resmî, doğrulanmış uv ve Deno çalışma araçlarını içerir; Python, paketler ve model ilk kullanımda internetten indirilir. Paket tamamen çevrimdışı kurulum değildir.
