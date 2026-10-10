# SceneScout

**Hatırladığın sahneyi bul.** Google EmbeddingGemma 2 ile yerelde çalışan görsel video arama uygulaması.

[English README](README.md) · [Mimari](docs/architecture.md) · [Ölçülen örnek](docs/performance.md)

## Windows'ta kur ve kullan

**[Windows x64 kurulum dosyasını indir](https://github.com/Fatih-Haslak/scenescout/releases/latest/download/SceneScout-Setup-Windows-x64.exe)** · [Tüm indirmeler ve doğrulama özetleri](https://github.com/Fatih-Haslak/scenescout/releases/latest)

1. İndirilen `SceneScout-Setup-Windows-x64.exe` dosyasını aç, **Türkçe** seç ve kurulumu tamamla.
2. Masaüstündeki **SceneScout** kısayoluna çift tıkla. Python ve gerekli paketler otomatik hazırlanır; elle Python kurman veya API anahtarı alman gerekmez.
3. Tarayıcı açılınca video yükle ya da herkese açık YouTube/X video bağlantısı yapıştır. **Hazır** yazınca sahneyi tarif et, sonucu aç.

Windows 10/11 x64 içindir. **İlk açılış internet ve birkaç GB boş alan gerektirir. İlk videoda yaklaşık 1,5 GB model indirilir.** İndirme sırasında açılış penceresini açık tut; uygulamayı durdurmak için o pencerede Ctrl+C kullan. Varsayılan CPU'dur; isteğe bağlı NVIDIA GPU kısayolu Başlat menüsündedir.

Paket Türkçe/İngilizce başlangıç rehberi, kısayollar ve kaldırıcı içerir. Güncellemeler video arşivini korur. Kurulum dosyası dijital imzalı değildir; Windows yayıncı uyarısı gösterebilir. [Kurulum ayrıntıları ve sorun giderme](docs/installation.tr.md).

![SceneScout ile videoda Türkçe sahne arama](docs/scenescout-tr.jpg)

Video ekle, gördüğün sahneyi tarif et ve sonuçtan o ana git. İstersen örnek bir görselle benzer kareleri bul. Video, sorgu ve referans görselleri bir bulut çıkarım servisine gönderilmez.

### Taşınabilir ZIP veya kaynak kod

Kurulum dosyası yerine ZIP istersen sürüm sayfasından `SceneScout-0.4.0-Windows-x64.zip` indir. **Önce klasöre çıkart**, sonra `Start.cmd` dosyasını aç. `QUICKSTART.html` rehberi internet olmadan okunabilir. ZIP içindeki dosyayı doğrudan çalıştırma.

Kaynak koddan kurmak için Python 3.12/3.13 ve [uv](https://docs.astral.sh/uv/getting-started/installation/) kullan:

```sh
git clone https://github.com/Fatih-Haslak/scenescout.git
cd scenescout
uv run --frozen --extra cpu scenescout --open-browser
```

Windows’ta **Start.cmd** dosyasına çift tıklayabilirsin. İlk açılışta bağımlılıklar, ilk videoda yaklaşık 1,5 GB model dosyası indirilir. Uygulamayı [http://127.0.0.1:8765](http://127.0.0.1:8765) adresinde kullan. Sunucuyu terminalinde Ctrl+C ile durdur.

1. **Video ekle** ile H.264 MP4 veya WebM seç; ya da **Bağlantıdan ekle** ile herkese açık YouTube/Shorts veya X/Twitter video adresi yapıştır.
2. İndeksleme bitip **Hazır** yazmasını bekle.
3. “Çimenlerde oturan bir tavşan” gibi bir sahne tarif et.
4. Sonuca tıkla; oynatıcı ilgili zaman koduna gider.

Görsel simgesiyle bir referans görsel yükleyebilir, zaman çizelgesinden videoyu gezebilir ve sonuçları JSON olarak dışa aktarabilirsin. Dil düğmesi Türkçe ve İngilizce arasında geçiş yapar.

**En az benzerlik** filtresi zayıf sonuçları gizler. Filtreyi geçen kare bulunamazsa uygulama bunu açıkça gösterir. Eşik doğruluk yüzdesi değildir; yüksek bir eşik doğru sahneleri de gizleyebilir. Varsayılan seçenek en yakın sahneleri gösterir.

v0.3.1, YouTube 403 hatasından sonra herkese açık alternatif akışı bir kez dener. İndirme boyutu ses ve görüntü akışlarının toplamında denetlenir; Windows ilerleme dosyasındaki geçici kilitler yeniden denenir. Kitaplık yenilemelerinin birden fazla sorgulama döngüsü başlatması da giderildi.

v0.3.2, takılı kalan video/HTTP bağlantıları için kapanış beklemesini 10 saniyeyle sınırlar. Ardından bağlantılar iptal edilir ve işçilerin güvenli kapanışı yapılır; eski önizleme bağlantıları sunucuyu süresiz açık tutmaz.

Yarım kalan indeksler kayıtlı kareleri korur. Kitaplıktaki **İndekslemeye devam et** düğmesiyle yeniden yüklemeden devam edebilirsin. Silme sırasında uygulama kapanırsa temizlik sonraki açılışta tamamlanır.

## Doğrulama ve ölçümler

76 davranış testi; Windows/Linux ve Python 3.12/3.13 için otomatik kontroller. Gerçek model ayrıca CPU ve RTX 4060 Ti GPU üzerinde çalıştırıldı. Üç filmden 55 kare ve 36 Türkçe/İngilizce sorgudan oluşan küçük geliştirme setinde doğru sahne 24 sorguda ilk sırada, 36 sorgunun tamamında ilk beşte bulundu. Isınmış metin aramasında ortanca süre CPU’da 66 ms, GPU’da 32 ms ölçüldü.

Bağlantı indirmeleri arka planda çalışır; iptal edilebilir ve yarım kalırsa baştan yeniden denenebilir. İndirilen kopya H.264 MP4’e dönüştürülür. **Kaynağı aç** düğmesi orijinal paylaşımı gösterir. Tekil, herkese açık videolar desteklenir; canlı yayın, hesap girişi ve konuşma/özet üretimi yoktur. Platform erişimi engellerse hata gösterilir. [Bağlantı desteği ve gerçek örnekler](docs/link-imports.md).

Bu küçük set genel doğruluk garantisi değildir. Beklenen sahneler aramalardan önce kaydedildi; ilk sonucu kaçıran sorgular da raporda yer alır. [Ham sonuçlar, yöntem ve tekrar çalıştırma](docs/evaluation.md).

## Örnek video

```sh
uv run --with imageio-ffmpeg python examples/create_demo.py
```

Oluşan `examples/demo.mp4` dosyasını 3 saniyelik kare aralığıyla ekle. Blender Foundation’ın *Big Buck Bunny* filminden 30 saniyelik sessiz bir kesittir. [Lisans ve kaynak](examples/ATTRIBUTION.md).

## Sınırlar

- Bu sürüm **videonun görüntüsünde** arama yapar. Sesi veya konuşmayı aramaz; hareketi takip etmez.
- Örnekleme kısa olayları kaçırabilir. Zaman kodları örneklenen karelere aittir.
- Video başına 512 MB, iki saat ve 2.000 kare sınırı vardır. Kare aralığını artırmak indeksleme maliyetini azaltır.
- Benzerlik puanı doğruluk yüzdesi değildir. Filtre kapalıyken ilgisiz sorgular da en yakın sonuçları getirir. Filtre tüm yanlış eşleşmeleri otomatik saptama garantisi vermez.
- CPU için `--extra cpu`, uyumlu NVIDIA GPU için `--extra cuda` seçilir. GPU ölçümü RTX 4060 Ti ile yapıldı.
- Kurulum paketinde kopyalar ve indeks `%LOCALAPPDATA%\SceneScout\Data`, ZIP/kaynak kod kullanımında `.data/` klasöründedir; model dosyaları Hugging Face önbelleğindedir. Videoyu kaldırmak orijinalini silmez.
- İndirmeler tamamlandıktan sonra yerelde çalışır. Tam çevrimdışı model yüklemek için `HF_HUB_OFFLINE=1` kullanılabilir.

Tek kullanıcı için hazırlanmıştır. Sunucuyu internete açma. [Gizlilik ve güvenlik](SECURITY.md).

Kod lisansı MIT, model Apache 2.0, örnek film görüntüleri CC BY 3.0’dır.

[Fatih Haslak](https://github.com/Fatih-Haslak) tarafından geliştirildi.
