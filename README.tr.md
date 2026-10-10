# SceneScout

**Hatırladığın sahneyi bul.** Google EmbeddingGemma 2 ile yerelde çalışan görsel video arama uygulaması.

[English README](README.md) · [Mimari](docs/architecture.md) · [Ölçülen örnek](docs/performance.md)

![SceneScout ile videoda Türkçe sahne arama](docs/scenescout-tr.jpg)

Video ekle, gördüğün sahneyi tarif et ve sonuçtan o ana git. İstersen örnek bir görselle benzer kareleri bul. Video, sorgu ve referans görselleri bir bulut çıkarım servisine gönderilmez.

## Kurulum

**Python 3.12 veya 3.13** ve [uv](https://docs.astral.sh/uv/getting-started/installation/) gerekir. Birkaç GB boş RAM ve disk alanı bırak.

```sh
git clone https://github.com/Fatih-Haslak/scenescout.git
cd scenescout
uv run --frozen scenescout --open-browser
```

Windows’ta **Start.cmd** dosyasına çift tıklayabilirsin. İlk açılışta bağımlılıklar, ilk videoda yaklaşık 1,5 GB model dosyası indirilir. Uygulamayı [http://127.0.0.1:8765](http://127.0.0.1:8765) adresinde kullan. Sunucuyu terminalinde Ctrl+C ile durdur.

1. **Video ekle** ile H.264 MP4 veya WebM seç.
2. İndeksleme bitip **Hazır** yazmasını bekle.
3. “Çimenlerde oturan bir tavşan” gibi bir sahne tarif et.
4. Sonuca tıkla; oynatıcı ilgili zaman koduna gider.

Görsel simgesiyle bir referans görsel yükleyebilir, zaman çizelgesinden videoyu gezebilir ve sonuçları JSON olarak dışa aktarabilirsin. Dil düğmesi Türkçe ve İngilizce arasında geçiş yapar.

## Örnek video

```sh
uv run --with imageio-ffmpeg python examples/create_demo.py
```

Oluşan `examples/demo.mp4` dosyasını 3 saniyelik kare aralığıyla ekle. Blender Foundation’ın *Big Buck Bunny* filminden 30 saniyelik sessiz bir kesittir. [Lisans ve kaynak](examples/ATTRIBUTION.md).

## Sınırlar

- Bu sürüm **videonun görüntüsünde** arama yapar. Sesi veya konuşmayı aramaz; hareketi takip etmez.
- Örnekleme kısa olayları kaçırabilir. Zaman kodları örneklenen karelere aittir.
- Video başına 512 MB, iki saat ve 2.000 kare sınırı vardır. Kare aralığını artırmak indeksleme maliyetini azaltır.
- Benzerlik puanı doğruluk yüzdesi değildir. İlgisiz sorgular da en yakın sonuçları getirir.
- Windows kurulumu CPU kullanır; GPU için uyumlu CUDA PyTorch kurulumu gerekir. GPU hızı ölçülmedi.
- Kopyalar ve indeks `.data/`, model dosyaları Hugging Face önbelleğindedir. Videoyu kaldırmak orijinalini silmez.
- İndirmeler tamamlandıktan sonra yerelde çalışır. Tam çevrimdışı model yüklemek için `HF_HUB_OFFLINE=1` kullanılabilir.

Tek kullanıcı için hazırlanmıştır. Sunucuyu internete açma. [Gizlilik ve güvenlik](SECURITY.md).

Kod lisansı MIT, model Apache 2.0, örnek film görüntüleri CC BY 3.0’dır.

[Fatih Haslak](https://github.com/Fatih-Haslak) tarafından geliştirildi.
