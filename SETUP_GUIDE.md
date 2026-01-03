# Kurulum ve Yapılandırma Rehberi

## ⚡ Hızlı Başlangıç

### 1. Gereklilikler
Python 3.8+ ve pip

### 2. Paketleri Yükle
```bash
pip install -r requirements.txt
```

### 3. Ana Uygulamayı Başlat
```bash
python main.py
```

---

## 📋 Detaylı Kurulum

### Windows
```bash
# Python yüklü mü kontrol et
python --version

# Sanal ortam oluştur
python -m venv venv
venv\Scripts\activate

# Paketleri yükle
pip install -r requirements.txt

# Çalıştır
python main.py
```

### Mac/Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

## 🔐 Auth Sistemi Kurulumu

### Veritabanı
- SQLite otomatik oluşturulur: `portfolio.db`
- İlk başlangıçta boş başlar
- Giriş yapıp ürün eklenince veriler kaydedilir

### Örnek Hesaplar
```
Kullanıcı Adı: demo
Şifre: demo123
Email: demo@example.com

(Uygulamada yeni hesap oluşturabilirsiniz)
```

---

## ☁️ Cloud Sync Kurulumu (Opsiyonel)

### Backend Serverini Başlat

#### Windows
```bash
python server.py
```

#### Mac/Linux
```bash
python3 server.py
```

Server başlayacak:
```
📊 HisseTakip Cloud Server başlıyor...
============================================================
URL: http://localhost:5000
```

### Uygulamada Etkinleştir
1. Ayarlar → Cloud Sync
2. Server URL: `http://localhost:5000` (default)
3. "Cloud Sync'i Etkinleştir" toggle
4. Manual sync veya otomatik sync seçeneği

---

## 📡 API Sağlayıcıları Kurulumu

### 1. yfinance (Varsayılan)
✅ Zaten entegre, API anahtarı gereksiz

### 2. Finnhub
```bash
# 1. Hesap oluştur: https://finnhub.io/
# 2. API anahtarını al
# 3. Uygulamada:
#    Ayarlar → API Sağlayıcısı → Finnhub
#    API Anahtarı girin
```

### 3. Alpha Vantage
```bash
# 1. Hesap oluştur: https://www.alphavantage.co/
# 2. API anahtarını al (free: "demo" kullanabilirsiniz)
# 3. Uygulamada:
#    Ayarlar → API Sağlayıcısı → Alpha Vantage
#    API Anahtarı girin
```

### 4. IEX Cloud
```bash
# 1. Hesap oluştur: https://iexcloud.io/
# 2. Publishable Key al
# 3. Uygulamada:
#    Ayarlar → API Sağlayıcısı → IEX Cloud
#    API Anahtarı girin
```

---

## 🗄️ Veritabanı Yönetimi

### Dosyaların Konumu
```
HisseTakip(YENI)/
├── portfolio.db           # Ana SQLite veritabanı
├── cloud_portfolio.db     # Backend veritabanı (eğer server çalışıyorsa)
└── portfoy_data_backup_*.json  # JSON yedekleri
```

### Veri İçe/Dışa Aktarma

#### JSON olarak Dışa Aktar
```
Ayarlar → Yedekleme → Verileri JSON olarak Dışa Aktar
```

#### JSON'dan İçe Aktar
```
Ayarlar → Yedekleme → Verileri JSON'dan İçe Aktar
```

### Backup Alma
```
Ayarlar → Yedekleme → Manuel Yedek Al
```

Otomatik yedekleme: `Ayarlar → Yedekleme → Otomatik Yedekleme` (varsayılan: Haftalık)

---

## 🔧 Yapılandırma Dosyaları

### config.py
```python
# Endeksler
INDICES = {
    "XU100": "XU100.IS",
    "NASDAQ": "^IXIC",
    "S&P 500": "^GSPC"
}

# Dövizler
CURRENCIES = {
    "DOLAR": "TRY=X",
    "EURO": "EURTRY=X",
    "ALTIN": "GC=F",
    "BTC": "BTC-USD"
}

# Varsayılan ayarlar
DEFAULT_SETTINGS = {
    "api_provider": "yfinance",
    "tema": "dark",
    "otomatik_guncelleme": True,
    "cloud_sync_enabled": False,
    # ... daha fazla ayar
}
```

### .env (Backend için)
```
SECRET_KEY=your_secret_key_here
DATABASE_FILE=cloud_portfolio.db
FLASK_ENV=development
FLASK_DEBUG=True
```

---

## 🐛 Sorun Giderme

### "ModuleNotFoundError: No module named 'customtkinter'"
```bash
pip install customtkinter>=5.0.0
```

### "ModuleNotFoundError: No module named 'yfinance'"
```bash
pip install yfinance
```

### Database hataları
```bash
# Veritabanını sıfırla
rm portfolio.db
# Uygulamayı yeniden başlat
python main.py
```

### Cloud sync bağlantısı başarısız
1. Backend'in çalışıp çalışmadığını kontrol et: `python server.py`
2. URL doğru mu: `http://localhost:5000`
3. Firewall 5000 portunu açmış mı
4. Backend loglarında hata var mı

### API hataları
1. API anahtarı doğru mu
2. API rate limit aşıldı mı
3. İnternet bağlantısı var mı
4. Sağlayıcı website'i çalışıyor mu

---

## 📊 Performans İyileştirmeleri

### Veritabanı
- SQLite kullanıldığı için JSON'dan ~50x daha hızlı
- İndeksler otomatik oluşturulur
- Bağlantı pooling ile optimize edilir

### API Çağrıları
- 5 dakikalık cache
- Asenkron çağrılar (UI freezing yok)
- Thread-safe operasyonlar

### UI
- CustomTkinter ile modern arayüz
- Lazy loading (sayfalar açılırken yüklenir)
- Threading ile responsive arayüz

---

## 🔒 Güvenlik

### Şifre Güvenliği
- PBKDF2-SHA256 hashing
- 100,000 iteration
- Unique salt per password

### Token Güvenliği
- JWT tokens (RS256 veya HS256)
- 7 gün expiry
- Token refresh endpoint

### Veri Koruma
- SQL injection prevention
- XSS protection
- CORS enabled (backend)
- HTTPS recommended (production)

---

## 📞 Destek

### Sık Sorulan Sorular

**S: Verilerim kurtarılabilir mi?**
A: Evet, `portfoy_data_backup_*.json` dosyaları otomatik yedeklenir.

**S: Başka bir bilgisayardan erişebilir miyim?**
A: Cloud Sync ile evet. Backend'i internet-accessible yap ve firewall'u açıtır.

**S: İnternet olmadan çalışabilir mi?**
A: Evet, tüm veriler yerel olarak saklanır. Cloud sync sadece opsiyonel.

**S: Kaç kullanıcı desteklenebilir?**
A: Sınırı yok. Her kullanıcı kendi verisine sahip.

---

## 🚀 Sonraki Adımlar

1. **Settings'i özelleştir**
   - Tema seç (dark/light)
   - API sağlayıcısı kur
   - Auto-update aralığını ayarla

2. **Portföy oluştur**
   - Hisse senedi ekle
   - İşlemler kaydet
   - Temettüleri takip et

3. **Cloud'u etkinleştir** (opsiyonel)
   - Backend serverini başlat
   - Cloud sync'i aç
   - Otomatik senkronizasyon kullan

4. **Mobil sürümü bek**
   - Yakında React Native uygulaması geliyor
