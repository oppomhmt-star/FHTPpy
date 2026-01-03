# HisseTakip Sürüm 2.0 - Büyük İyileştirmeler

## 1️⃣ SQLite Veritabanı Yükseltmesi ✅

### Özellikler
- **JSON'dan SQLite'a Geçiş**: Otomatik veri göçü ilk çalıştırmada
- **Güvenli Veri Yönetimi**: Context manager ile bağlantı yönetimi
- **Multi-Kullanıcı Destek**: Her kullanıcının kendi verisi izole
- **Performans**: Geniş veri setlerde ~50x daha hızlı

### Dosyalar
- `database.py` - Yeni SQLite API'si
- Tablolar: `users`, `portfolios`, `transactions`, `dividends`, `settings`, `sessions`

### Kullanım
```python
from database import Database

db = Database()  # Otomatik olarak SQLite oluşturur

# Mevcut kullanıcılar
portfolio = db.get_portfolio(user_id=1)
transactions = db.get_transactions(user_id=1)

# Veri ekleme
db.add_transaction({
    'sembol': 'THYAO',
    'tip': 'Alım',
    'adet': 100,
    'fiyat': 250.50,
    'toplam': 25050,
    'tarih': '2024-01-15 10:30:00'
}, user_id=1)
```

### Geçiş Süreci
1. `portfolio.db` otomatik oluşturulur
2. `portfoy_data.json` bulunursa veriler aktarılır
3. JSON dosyasının yedeği alınır: `portfoy_data_backup_YYYYMMDD_HHMMSS.json`
4. Eski JSON dosyası uygulamada kullanılmaz

---

## 2️⃣ Profesyonel API Entegrasyonu ✅

### Desteklenen Sağlayıcılar

| Sağlayıcı | Durum | Avantajlar |
|-----------|-------|-----------|
| **yfinance** | ✅ Varsayılan | Ücretsiz, geniş veritabanı |
| **Finnhub** | ✅ Entegre | Hızlı, real-time, mum grafikleri |
| **Alpha Vantage** | ✅ Entegre | Teknik göstergeler, günlük veriler |
| **IEX Cloud** | ✅ Entegre | Profesyonel, düşük latensi |

### Dosya
- `api_service.py` - Multi-provider API

### Kullanım

#### API Anahtarı Ayarla
```python
from api_service import APIService

api = APIService()

# Finnhub API anahtarı
api.set_api_key("finnhub", "pk_xxxxxxxxxxxx")

# Alpha Vantage API anahtarı
api.set_api_key("alpha_vantage", "demo")

# IEX Cloud API anahtarı
api.set_api_key("iex", "pk_xxxxxxxxxxxx")
```

#### Sağlayıcı Seçimi
```python
# Sağlayıcıyı değiştir
api.switch_provider("finnhub")

# Hisse fiyatı getir
price = api.get_stock_price("THYAO")

# Geçmiş verisi getir
history = api.get_stock_history("THYAO", period="1y")

# Sağlayıcıyı test et
is_working = api.test_provider("finnhub")
```

### Settings'de Ayar
Ayarlar sayfasında API seçeneği:
1. Sağlayıcı seçimi dropdown
2. API anahtarı girişi
3. Bağlantı testi

---

## 3️⃣ Kullanıcı Hesapları & Auth Sistemi ✅

### Özellikler
- **JWT Token Based Auth**: Secure token-based authentication
- **PBKDF2 Hashing**: Güvenli şifre depolaması
- **Giriş/Kayıt Sayfaları**: Profesyonel UI
- **Şifre Değiştirme**: Kullanıcı hesap yönetimi

### Dosyalar
- `auth_service.py` - Kimlik doğrulama servisi
- `pages/auth_page.py` - Giriş/Kayıt UI

### Kullanım

#### Kayıt
```python
from auth_service import AuthService
from database import Database

db = Database()
auth = AuthService(db)

result = auth.register_user(
    username="ahmet",
    email="ahmet@example.com",
    password="secure_password_123"
)

if result['success']:
    print(f"Kullanıcı ID: {result['user_id']}")
```

#### Giriş
```python
result = auth.login_user("ahmet", "secure_password_123")

if result['success']:
    print(f"Token: {result['token']}")
    print(f"User ID: {result['user_id']}")
```

#### Token Doğrulama
```python
result = auth.verify_token(token)

if result['success']:
    user_id = result['user_id']
```

### Güvenlik
- ✅ PBKDF2 SHA256 hashing (100,000 iterations)
- ✅ JWT token expiry (7 gün)
- ✅ SQL injection prevention
- ✅ XSS protection (HTML escaping)

---

## 4️⃣ Bulut Senkronizasyonu ✅

### Özellikler
- **Otomatik Sync**: 5 dakika aralıkla (yapılandırılabilir)
- **Selective Sync**: Portfolio, işlemler, temettüler, ayarlar ayrı ayrı
- **Offline Support**: İnternet yoksa veriler kaydedilir
- **Conflict Resolution**: Cloud-first veya local-first seçeneği

### Dosyalar
- `cloud_sync.py` - Senkronizasyon motoru
- `server.py` - Flask backend API

### Backend API

#### Auth Endpoints
```
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me
POST   /api/auth/change-password
```

#### Data Sync Endpoints
```
POST   /api/sync/portfolio
POST   /api/sync/transactions
POST   /api/sync/dividends
POST   /api/sync/settings
```

#### Data Pull Endpoints
```
GET    /api/pull/portfolio
GET    /api/pull/transactions
GET    /api/pull/dividends
GET    /api/pull/settings
GET    /api/pull/all
```

### Kullanım

#### Backend'i Başlat
```bash
python server.py
# http://localhost:5000
```

#### Client'ta Cloud Sync Etkinleştir
```python
from cloud_sync import CloudSync
from database import Database

db = Database()
cloud = CloudSync(db, cloud_url="http://localhost:5000")

# Kimlik bilgilerini ayarla
cloud.set_credentials(user_id=1, token="jwt_token_here")

# Tüm verileri senkronize et
result = cloud.sync_all_data()

# Otomatik senkronizasyonu başlat
cloud.start_auto_sync()
```

### Settings'de Entegrasyon
- Cloud sync on/off toggle
- Server URL ayarı
- Manual sync butonu
- Last sync timestamp gösterimi
- Connection test

---

## 🚀 Başlangıç

### Kurulum
```bash
# Gereklilikler yükle
pip install -r requirements.txt

# Ana uygulama başlat
python main.py

# (Opsiyonel) Backend serverini başlat
python server.py
```

### İlk Çalıştırma
1. Giriş/Kayıt sayfası belirir
2. Yeni hesap oluştur veya mevcut hesapla giriş yap
3. Otomatik olarak ana uygulamaya geçer
4. Veritabanı ve API'ler başlatılır
5. Dashboard açılır

---

## 📊 Veri Akışı

```
┌─────────────────────────────────────────────────────────────┐
│                   HisseTakip Ana Uygulama                   │
│                       (main.py)                             │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─── 🔐 Auth Page (pages/auth_page.py)
             │        │
             │        ├─ Register → AuthService.register_user()
             │        └─ Login    → AuthService.login_user()
             │
             ├─── 📊 Dashboard, Portfolio, Transactions, ...
             │        │
             │        └─ Database.get_*() [User ID ile izole]
             │
             ├─── 📡 API Service (api_service.py)
             │        ├─ yfinance (varsayılan)
             │        ├─ Finnhub
             │        ├─ Alpha Vantage
             │        └─ IEX Cloud
             │
             └─── ☁️  Cloud Sync (cloud_sync.py)
                      │
                      └─ Flask API Server (server.py)
                           ├─ /api/auth/*
                           ├─ /api/sync/*
                           └─ /api/pull/*
```

---

## 🔧 Yapılandırma

### config.py
```python
# API Seçimi
DEFAULT_SETTINGS = {
    "api_provider": "yfinance",  # yfinance, finnhub, alpha_vantage, iex
    "finnhub_key": "",
    "alpha_vantage_key": "",
    "iex_key": "",
    
    # Cloud Sync
    "cloud_sync_enabled": False,
    "cloud_url": "http://localhost:5000",
    
    # Diğer ayarlar...
}
```

### .env (Backend)
```
SECRET_KEY=your_secret_key_here
DATABASE_FILE=cloud_portfolio.db
FLASK_ENV=production
```

---

## 📝 Notlar

### Veritabanı Depolama
- `portfolio.db` - SQLite veritabanı (all data)
- `portfoy_data_backup_*.json` - JSON yedekleri
- `cloud_portfolio.db` - Backend veritabanı (server.py çalıştırıldığında)

### İnternet Kesintileri
- Cloud sync devre dışı kalırsa veriler yerel olarak kaydedilir
- Bağlantı kurulduktan sonra otomatik senkronizasyon başlar
- Manual sync butonu her zaman mevcut

### Güvenlik Tavsiyeleri
- Backend'i production'da HTTPS ile çalıştır
- `SECRET_KEY` değiştir
- Database dosyalarına erişim kısıtla
- Firewall kuralları ekle

---

## 🎯 Gelecek Planı

- [ ] Mobil uygulama (React Native)
- [ ] Versiyon kontrol (GitHub sync)
- [ ] Veri şifrelemesi
- [ ] 2FA (İki faktörlü doğrulama)
- [ ] WebSocket real-time sync
- [ ] Offline-first PWA
