# 🦾 Dijital Vasi — Güvenli Yerel Yapay Zeka Asistanı

> **The Core Method** serisinin bir parçasıdır. │ [@THECOREMETHODHowTo](https://youtube.com/@THECOREMETHODHowTo)

Telefonunuzdan Telegram üzerinden komut verin, asistanınız evdeki bilgisayarınızda çalışsın. Veri dışarı çıkmaz, buluta bağımlılık yok, istediğiniz an tek komutla iz bırakmadan silinir.

---

## ⚠️ Önce Bunu Okuyun

> Bu proje **eğitim amaçlıdır.** Üçüncü taraf açık kaynak yazılımlar içerir.
> Sistemi ana bilgisayarınızda değil, mümkünse izole bir ortamda (Docker zaten bunu sağlar) test etmenizi öneririz.
> Olası veri kayıpları veya güvenlik açıklarından **The Core Method veya repo sahipleri sorumlu tutulamaz.**
> Tüm risk kullanıcıya aittir.

---

## Nasıl Çalışır?

```
Telefon (Telegram)
      │
      ▼
Docker Konteyneri  ←──  Ollama (Yerel Model)
      │
      ▼
  workspace/          ← Asistanın dokunabildiği tek yer
```

- **Docker** → Asistan izole bir konteyner içinde çalışır. Sisteminize dokunamaz.
- **Ollama** → Yapay zeka modeli yerel çalışır. Veri buluta gitmez.
- **Telegram** → Uzaktan komuta merkezi. Sadece sizin ID'nizden gelen komutlar kabul edilir.
- **workspace/** → Asistanın okuyup yazabildiği yegane klasör.

---

## Sistem Gereksinimleri

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| RAM | 16 GB | 32 GB+ |
| Disk | 40 GB boş | 80 GB+ boş |
| İşlemci | 8 çekirdek | 16 çekirdek+ |
| GPU | Yok (yavaş) | NVIDIA 8GB+ VRAM |

> **Model boyutları:** 5 modelin tamamı ~60–80 GB disk kaplar.
> Daha az RAM'iniz varsa `vasi.py` içindeki `MODELS` sözlüğünden sadece ihtiyacınız olan modeli bırakın, diğerlerini silin.
> Tek model öneri: `qwen3:8b` (hafif, makul performans).

---

## Kurulum

### Adım 0 — Gereksinimler

Bilgisayarınızda şunların kurulu olması gerekiyor:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com)
- [Git](https://git-scm.com/downloads)
- Telegram (telefon veya masaüstü)

Git kurulu mu? Terminalden kontrol edin:

```bash
git --version
```

`git version 2.x.x` gibi bir çıktı görüyorsanız hazırsınız.

---

### Adım 1 — Telegram Kimlik Bilgileri

**Bot Token:**
1. Telegram'da `@BotFather`'ı aratın
2. `/newbot` gönderin
3. Bot adı ve kullanıcı adı belirleyin (kullanıcı adı `_bot` ile bitmeli)
4. Verilen token'ı kopyalayın → `123456789:ABCxxx...`

**Kendi ID'niz:**
1. Telegram'da `@userinfobot`'a herhangi bir mesaj atın
2. Size verilen sayısal ID'yi kopyalayın → `987654321`

---

### Adım 2 — GitHub Repo'yu Kurun

> Git ve GitHub'ı ilk kez kullanıyorsanız önce [github.com](https://github.com) üzerinde ücretsiz hesap açın.

**2a — Bu repoyu fork edin (GitHub sitesinde):**

Sayfanın sağ üstündeki `Fork` butonuna tıklayın.
Bu, reponun bir kopyasını kendi hesabınıza oluşturur.

**2b — Fork'u bilgisayarınıza indirin:**

```bash
# KULLANICI_ADINIZ kısmını kendi GitHub kullanıcı adınızla değiştirin
git clone https://github.com/KULLANICI_ADINIZ/dijital-vasi.git
cd dijital-vasi
```

**2c — Klasör yapısını doğrulayın:**

```bash
ls -la
```

Şu dosyaları görmelisiniz:
```
.env.example
.gitignore
Dockerfile
README.md
DISCLAIMER.md
docker-compose.yml
requirements.txt
vasi.py
workspace/
```

---

### Adım 3 — Ortam Dosyasını Hazırlayın

`.env.example` şablonunu kopyalayıp `.env` adıyla kaydedin:

**Mac / Linux:**
```bash
cp .env.example .env
```

**Windows (CMD):**
```cmd
copy .env.example .env
```

Şimdi `.env` dosyasını bir metin editörüyle açıp kendi bilgilerinizi girin:

**Mac / Linux (nano ile):**
```bash
nano .env
```

**Windows (not defteri ile):**
```cmd
notepad .env
```

Dosya içeriği şöyle görünmeli:
```
TELEGRAM_BOT_TOKEN=123456789:ABCDefghIJKlmnOPQRstuVWxyz
MY_TELEGRAM_ID=987654321
WORKSPACE_DIR=./workspace
OLLAMA_HOST=http://host.docker.internal:11434
```

nano kullanıyorsanız kaydetmek için: `Ctrl + O` → `Enter` → `Ctrl + X`

> ⚠️ `.env` dosyasını **asla** GitHub'a push etmeyin. `.gitignore` otomatik olarak engelliyor ama yine de dikkatli olun.

---

### Adım 4 — Modelleri İndirin

Ollama'nın arka planda çalıştığından emin olun, ardından modelleri çekin.
Tamamını indirmek zorunda değilsiniz — sadece kullanacaklarınızı alın:

```bash
# Genel asistan (zorunlu — diğerleri yoksa bu devreye girer)
ollama pull qwen3:30b

# İçerik ve strateji
ollama pull command-r

# Teknik analiz
ollama pull gemma3:27b

# Kod yazma
ollama pull qwen3-coder:30b

# Dosya ve görsel analiz
ollama pull qwen3-vl:30b
```

İndirilen modelleri görmek için:
```bash
ollama list
```

> RAM kısıtınız varsa sadece `ollama pull qwen3:8b` çekip `vasi.py` içindeki tüm model değerlerini `qwen3:8b` yapın.

---

### Adım 5 — Sistemi Başlatın

```bash
docker compose up -d --build
```

İlk çalıştırmada Docker gerekli ortamı kurar (~2–3 dakika).
Sonraki başlatmalarda saniyeler içinde hazır olur.

Sistemin çalıştığını doğrulamak için:
```bash
docker ps
```

`vasi-sandbox-guard` adlı konteyneri `Up` olarak görmelisiniz.

Logları canlı izlemek için:
```bash
docker logs -f vasi-sandbox-guard
```

`Vasi basladi.` satırını görüyorsanız her şey hazır.
Telegram'dan botunuza `/start` yazarak test edin.

---

### Sorun Giderme

**Bot cevap vermiyorsa:**

Ollama'nın dışa açık çalışıp çalışmadığını kontrol edin:

```bash
# Mac / Linux
OLLAMA_HOST=0.0.0.0 ollama serve

# Windows (CMD)
set OLLAMA_HOST=0.0.0.0
ollama serve
```

**Konteyneri yeniden başlatmak için:**

```bash
docker compose restart
```

**Sıfırdan başlamak için:**

```bash
docker compose down
docker compose up -d --build
```

---

## Komutlar

| Komut | Açıklama |
|-------|----------|
| `/start` | Komut listesini göster |
| `/liste` | Workspace içindeki dosyaları listele |
| `/oku <dosya>` | Dosyayı oku, Telegram'a gönder |
| `/analiz <dosya>` | Dosyayı AI ile analiz et |
| `/rapor <konu>` | Konu hakkında rapor/makale yaz |
| `/kod <görev>` | Python kodu yaz |
| `/kaydet <dosya> <içerik>` | Metin dosyası oluştur |
| `/sil <dosya>` | Dosyayı sil (onay ister) |

Düz mesaj yazarak da sohbet edebilirsiniz. Mesajınızda bir dosya adı geçiyorsa (`rapor.md` gibi) sistem onu otomatik okuyup bağlam olarak ekler.

---

## Smart Router — Hangi Model Ne Zaman?

| Tetikleyici kelimeler | Seçilen model |
|----------------------|---------------|
| kod, script, python, docker, hata, debug | `qwen3-coder` |
| analiz, tablo, rapor, görsel, pdf | `qwen3-vl` |
| araştır, neden, hesapla, istatistik | `gemma3` |
| e-posta, yaz, makale, içerik, strateji | `command-r` |
| Diğer | `qwen3` (gatekeeper) |

---

## Güvenlik Mimarisi

**Path Traversal Koruması**
`/oku ../../etc/passwd` gibi workspace dışına çıkan her yol engellenir.

**Human-in-the-Loop**
Dosya yazma ve silme işlemleri Telegram'da onay butonu gösterir. Siz "Onayla" demeden hiçbir şey diske yazılmaz veya silinmez.

**Kimlik Doğrulama**
`MY_TELEGRAM_ID` dışındaki tüm mesajlar sessizce yok sayılır. Grup mesajları, yönlendirilen mesajlar ve 60 saniyeden eski mesajlar işlenmez.

**Docker İzolasyonu**
Konteyner yalnızca `workspace/` klasörüne erişebilir. Ana sisteminizin dosyaları görünmez.

---

## Sistemi Geliştirme

### Model Eklemek / Değiştirmek

`vasi.py` içindeki `MODELS` sözlüğünü düzenleyin:

```python
MODELS = {
    "gatekeeper": "qwen3:8b",      # Daha hafif versiyon
    "strateji":   "mistral",        # command-r yerine
    "teknik":     "gemma3:27b",
    "kod":        "qwen3-coder:30b",
    "gorsel":     "qwen3-vl:30b",
}
```

### Think Bloğunu Kapatmak

Qwen3 modelleri yanıt üretmeden önce İngilizce "düşünür" ve bunu bazen yanıta sızdırır.
`build_system_prompt` fonksiyonundaki `base` değişkeninin başına ekleyin:

```python
base = "/no_think\n" + f"Sen Vasi, ..."
```

### Yeni Anahtar Kelime Eklemek

`pick_model` fonksiyonundaki listelere kendi iş alanınıza uygun kelimeler ekleyin:

```python
if any(k in t for k in ["sözleşme", "madde", "hüküm", "dava"]):
    return MODELS["teknik"]
```

---

## Sistemi Silmek

Konteyner, image ve tüm paketler dahil iz bırakmadan silmek için:

```bash
docker compose down --rmi all -v
```

`workspace/` klasörünü de silmek isterseniz:

```bash
rm -rf ~/Desktop/CORE_WORKSPACE
```

---

## Lisans

MIT License — Serbestçe kullanabilir, değiştirebilir ve dağıtabilirsiniz.
Ancak orijinal kaynak belirtilmesi beklenir: **The Core Method / @THECOREMETHODHowTo**

---

## Video Serisi

| # | Başlık |
|---|--------|
| 1 | OpenClaw Nedir? Dijital Vasi Dönemi |
| 2 | Güvenlik Krizi: ClawJacked ve Moltbook Kaosu |
| 3 | Güvenli Kurulum: Docker ile Evcilleştirme *(bu repo)* |

[@THECOREMETHODHowTo](https://youtube.com/@THECOREMETHODHowTo) — Merakla kalın, profesyonel kalın.
