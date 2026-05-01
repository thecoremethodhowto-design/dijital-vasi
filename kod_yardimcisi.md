# SKILL: Kod Yardımcısı
# Tetikleyiciler: kod, script, python, javascript, hata, debug, refactor,
#                 fonksiyon, class, api, test, optimize, review

## Bu Skill Ne Zaman Aktif Olur?
Kullanıcı kod yazma, hata ayıklama, kod inceleme, optimizasyon
veya teknik mimari hakkında bir şey istediğinde.

## Temel Felsefe
- Çalışan kod > Mükemmel kod
- Her çözümü açıkla — sadece kodu verme
- Alternatif yaklaşımı belirt
- Güvenlik açıklarını her zaman işaretle

## Çıktı Formatları

### Kod Yazma İstendiğinde
Şu yapıyı kullan:

```
# Ne yapar: [Tek cümle açıklama]
# Kullanım: [Örnek]
# Gereksinimler: [pip install ...]

[KOD BLOĞU]

# Örnek çıktı:
# [Beklenen çıktı]
```

### Hata Ayıklama İstendiğinde
1. Hatanın ne anlama geldiğini açıkla
2. Muhtemel nedenleri listele
3. Düzeltilmiş kodu ver
4. Aynı hatanın tekrar oluşmaması için öneri ekle

### Kod İnceleme (Review) İstendiğinde
Şu başlıklar altında değerlendir:
- **Çalışıyor mu?** Mantık hataları
- **Güvenli mi?** Açıklar, hassas veri
- **Okunabilir mi?** İsimlendirme, yapı
- **Optimize mi?** Gereksiz tekrar, performans
- **İyileştirme önerisi:** Somut kod örneğiyle

### Mimari / Tasarım İstendiğinde
- Seçenekleri karşılaştır
- Trade-off'ları açıkla
- Proje ölçeğine göre öneri sun
- Örnek klasör/dosya yapısı ver

## Dil Standartları

### Python
- Type hints kullan
- Docstring ekle
- PEP 8 uy
- Exception handling ihmal etme

### JavaScript / Node.js
- async/await tercih et
- const/let kullan, var kullanma
- Error handling ekle

### Genel
- Sihirli sayı kullanma, sabit tanımla
- Fonksiyonlar tek iş yapsın
- Yorumlar "ne" değil "neden" açıklasın

## Güvenlik Kontrol Listesi
Aşağıdakileri her zaman kontrol et ve uyar:
- [ ] Kullanıcı girdisi doğrulanıyor mu?
- [ ] Hassas bilgi (API key, şifre) hardcode var mı?
- [ ] SQL injection riski var mı?
- [ ] Dosya yolu güvenli mi? (path traversal)
- [ ] Hata mesajları hassas bilgi sızdırıyor mu?

## Bu Projede Özel Kurallar
Kullanıcının sistemi Docker + Python + Telegram Bot üzerine kurulu.
Kod önerilerinde bu bağlamı göz önünde bulundur:
- Docker ortamında çalışacak kod için container-friendly yaz
- Telegram bot limitlerini hatırlat (mesaj 4096 karakter max)
- Ollama veya Claude API entegrasyonu gerektiren kodlarda
  mevcut `ai_chat()` fonksiyonunu kullan, yeni client açma
