# 🆕 Yeni Özellikler Rehberi

Bu dokümanda, Hisse Takip Programı'na eklenen yeni özellikleri öğrenebilirsiniz.

## 📚 İçindekiler

1. [Daha Fazla Varlık Türü Desteği](#1-daha-fazla-varlık-türü-desteği)
2. [Gelişmiş Portföy Analizi](#2-gelişmiş-portföy-analizi)
3. [Gelişmiş İşlem Türleri](#3-gelişmiş-işlem-türleri)
4. [Teknik Altyapı](#4-teknik-altyapı)

---

## 1. Daha Fazla Varlık Türü Desteği

### 📈 Hisseler (Mevcut)
- BIST hisse senetleri
- Fiyat takibi
- Alım/Satım işlemleri

### 💰 Yatırım Fonları (YENİ)
**TEFAS Entegrasyonu ile Özellikler:**
- Türkiye'deki tüm yatırım fonlarına erişim
- Fon fiyatları ve performans verisi
- Fon kategorileri: Hisse, Borçlanma Aracı, Karma, Döviz, Endeks vb.
- Aylık/Yıllık getiri takibi

**Kullanımı:**
```python
from tefas_integration import TEFASIntegration

tefas = TEFASIntegration(db)
tefas.get_popular_funds()  # Popüler fonları getir
tefas.add_fund_to_portfolio(user_id, fund_data)  # Fonu portföye ekle
```

### ₿ Kripto Paralar (YENİ)
**CoinGecko API ile Özellikler:**
- İlk 100 kripto parayı ekleyebilme
- Bitcoin, Ethereum, vb. tüm kripto paralar
- Real-time fiyat güncellemeleri
- 24 saatlik değişim takibi
- Pazar değeri ve hacim verisi

**Desteklenen Kriptolar:**
- BTC (Bitcoin)
- ETH (Ethereum)
- USDT (Tether)
- BNB (Binance Coin)
- XRP (Ripple)
- ...ve 95 daha

**Kullanımı:**
```python
from crypto_integration import CryptoIntegration

crypto = CryptoIntegration(db)
crypto.get_top_100_cryptos()  # Top 100 kripto
crypto.add_crypto_to_portfolio(user_id, crypto_data)  # Portföye ekle
```

### ⚡ Emtialar (YENİ)
**Desteklenen Emtialar:**
- 🥇 Altın (Gold)
- 🥈 Gümüş (Silver)
- 🛢️ Petrol (WTI, Brent)
- 🔥 Doğalgaz (Natural Gas)
- 🟧 Bakır (Copper)
- 🪛 Alüminyum (Aluminum)
- ⚙️ Nikel (Nickel)
- 🧪 Çinko (Zinc)
- 🔒 Kurşun (Lead)

**Kullanımı:**
```python
from commodity_integration import CommodityIntegration

commodity = CommodityIntegration(db)
commodity.get_commodity_price('GOLD')  # Altın fiyatı
commodity.add_commodity_to_portfolio(user_id, commodity_data)  # Ekle
```

### 🏦 Varlık Yönetimi Sayfası
**Sidebar:** 🏦 Varlıklar

Tüm varlık türlerini tek bir yerde yönetin:
- Varlık ekleme/düzenleme/silme
- Türe göre filtreleme (Hisse/Fon/Kripto/Emtia)
- Maliyet ve güncel fiyat takibi
- Toplam portföy değeri hesaplaması

---

## 2. Gelişmiş Portföy Analizi

### 🎲 Monte Carlo Simülasyonu
**Portföyün gelecekteki olası değer aralığını tahmin edin**

**Nedir?**
Binlerce farklı senaryo simülasyonu yaparak portföyün 1 yıl sonra ne olabileceğini gösterir.

**Parametreler:**
- Portföy Değeri: Güncel toplam değer
- Günlük Ortalama Getiri: Beklenen günlük getiri (%)
- Günlük Standart Sapma: Volatilite (risklilik)
- Simülasyon Günü: 252 = 1 yıl
- Simülasyon Sayısı: 10,000 (önerilen)

**Sonuçlar:**
- Ortalama son değer
- Medyan değer
- En kötü/En iyi senaryo
- Güven aralıkları (5%, 25%, 75%, 95. persentil)

**Örnek:**
```
Başlangıç: 100,000₺
Ortalama Sonuç: 120,500₺
5. Persentil (Kötü senaryo): 95,000₺
95. Persentil (İyi senaryo): 145,000₺
```

### 🎯 Hedef Yönelik Analiz
**"Aylık 5.000 TL yatırımla 10 yıl sonra portföyüm ne olur?"**

**Parametreler:**
- Başlangıç Portföy Değeri
- Aylık Yatırım Miktarı
- Yıllık Beklenen Getiri (%)
- Projeksiyon Yılı Sayısı

**Çıktı:**
Yıl yıl breakdown:
- Portföy Değeri
- Toplam Yatırım
- Kazanç (getiri)

**Örnek:**
```
Yıl 1: 65,500₺ (Yatırım: 60,000₺, Kazanç: 5,500₺)
Yıl 5: 385,000₺ (Yatırım: 300,000₺, Kazanç: 85,000₺)
Yıl 10: 885,000₺ (Yatırım: 600,000₺, Kazanç: 285,000₺)
```

### 💰 Vergi Optimizasyonu
**Satış stratejilerinizi optimize edin**

**Türkiye Vergi Oranları:**
- Kısa vadeli (1 yıldan kısa): %20
- Uzun vadeli (1 yıldan uzun): %10
- Vergi muaf tutar: 13,000₺

**Önerilen Senaryolar:**
1. **Mevcut Durum:** Hiçbir satış yapılmıyor
2. **Zarar Offseti:** Zararlı pozisyonları satıp kazançları azalt
3. **1 Yıl Üzeri Tutma:** Pozisyonları 1 yıldan uzun tutup vergiyi azalt

**Çıktı:**
```
Toplam Kazanç: 50,000₺
Vergilendirilebilir: 37,000₺

Senaryo 1: Vergi = 7,400₺
Senaryo 3: Vergi = 3,700₺ (Tasarruf: 3,700₺)
```

**Sidebar:** 🔬 Gelişmiş Analiz

---

## 3. Gelişmiş İşlem Türleri

### 📊 Hisse Bölünmesi (Stock Split)
**Bedelsiz sermaye artırımı sonrası otomatik ayarlama**

**Ne olur?**
- Bir hisse 2'ye bölünürse: 100 hisse × 50₺ = 10,000₺
- Sonra: 200 hisse × 25₺ = 10,000₺ (toplam maliyet aynı)

**Uygulama:**
```
Hisse Seç: THYAO
Bölünme Oranı: 2
[Hesapla]
→ 100 × 250₺ → 200 × 125₺
[Uygula]
```

**İşlem Kaydı:** Otomatik olarak advanced_transactions tablosuna kaydedilir

### 💼 Rüçhan Hakkı (Rights Issue)
**Bedelli sermaye artırımının otomatik hesaplanması**

**Ne olur?**
Şirket "Her 4 hisse'ye 1 yeni hisse, 40₺'ye" diyorsa:
- Eski: 100 hisse × 250₺ = 25,000₺
- Yeni: 25 hisse × 40₺ = 1,000₺
- Toplam: 125 hisse × yeni ortalama maliyet

**Uygulama:**
```
Hisse Seç: AKBNK
Rüçhan Oranı: 0.25
Yeni Hisse Fiyatı: 40
[Hesapla]
→ Yeni Adet: 500, Yeni Ort.Maliyet: 46.50₺
[Uygula]
```

**Sidebar:** ⚙️ Gelişmiş İşlemler

---

## 4. Teknik Altyapı

### Veritabanı Yapısı

**Yeni Tablolar:**

#### `assets`
```sql
CREATE TABLE assets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    sembol TEXT NOT NULL,
    tur TEXT NOT NULL,  -- 'hisse', 'fon', 'kripto', 'emtia'
    ad TEXT NOT NULL,
    adet REAL NOT NULL,
    ort_maliyet REAL NOT NULL,
    guncel_fiyat REAL NOT NULL,
    para_birimi TEXT DEFAULT 'TRY',
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(user_id, sembol, tur)
)
```

#### `advanced_transactions`
```sql
CREATE TABLE advanced_transactions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    sembol TEXT NOT NULL,
    tip TEXT NOT NULL,  -- 'StockSplit', 'RightsIssue'
    adet REAL NOT NULL,
    fiyat REAL NOT NULL,
    toplam REAL NOT NULL,
    komisyon REAL DEFAULT 0,
    otkome TEXT,  -- Açıklama
    tarih TIMESTAMP NOT NULL,
    created_at TIMESTAMP
)
```

#### `portfolio_goals`
```sql
CREATE TABLE portfolio_goals (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    hedef_ad TEXT NOT NULL,
    hedef_tutar REAL NOT NULL,
    hedef_tarihi TEXT NOT NULL,
    aylik_yatirim REAL,
    notlar TEXT,
    created_at TIMESTAMP
)
```

#### `tax_records`
```sql
CREATE TABLE tax_records (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    yil INTEGER NOT NULL,
    satig_gelirleri REAL DEFAULT 0,
    satig_zararlar REAL DEFAULT 0,
    temettü REAL DEFAULT 0,
    faiz REAL DEFAULT 0,
    vergi_serbest REAL DEFAULT 0,
    notlar TEXT,
    created_at TIMESTAMP,
    UNIQUE(user_id, yil)
)
```

### Yeni Modüller

#### `advanced_api_service.py`
- **TEFASService**: Yatırım fonu API'si
- **CryptoService**: CoinGecko kripto API'si
- **CommodityService**: Emtia fiyatları (Yahoo Finance)
- **AdvancedAnalysisService**: Analiz hesaplamaları
- **StockSplitCalculator**: Hisse bölünmesi
- **RightsIssueCalculator**: Rüçhan hakkı

#### `integration_manager.py`
Tüm entegrasyonları merkezi yerde yönet

#### `crypto_integration.py`
Kripto para entegrasyonu

#### `tefas_integration.py`
Yatırım fonu entegrasyonu

#### `commodity_integration.py`
Emtia entegrasyonu

### Yeni Sayfalar

#### `pages/assets_page.py`
Varlık yönetimi UI

#### `pages/advanced_transactions_page.py`
Stock Split ve Rights Issue UI

#### `pages/advanced_analysis_page.py`
Monte Carlo, Hedef Analizi, Vergi Optimizasyonu UI

---

## 📖 Kullanım Örnekleri

### Kripto Portföye Eklemek
```python
crypto_data = {
    'sembol': 'BTC',
    'ad': 'Bitcoin',
    'adet': 0.5,
    'ort_maliyet': 45000,
    'guncel_fiyat': 48000
}
crypto_integration.add_crypto_to_portfolio(user_id, crypto_data)
```

### Fon Eklemek
```python
fund_data = {
    'kod': 'FXUSZ',
    'ad': 'Garanti Dolar Fonu',
    'adet': 1000,
    'ort_maliyet': 1.25,
    'guncel_fiyat': 1.30
}
tefas_integration.add_fund_to_portfolio(user_id, fund_data)
```

### Stock Split Uygulamak
```python
db.apply_stock_split('THYAO', 2, user_id)  # 2'ye bölünme
```

### Monte Carlo Çalıştırmak
```python
result = AdvancedAnalysisService.monte_carlo_simulation(
    current_value=100000,
    daily_return=0.05,
    std_dev=2.0,
    days=252,
    simulations=10000
)
```

---

## 🔧 Kurulum

### Requirements
```bash
pip install -r requirements.txt
```

requirements.txt'te şunlar var:
- numpy (Monte Carlo simülasyonu için)
- yfinance (Emtia fiyatları için)
- requests (API çağrıları için)

### Veritabanı Güncelleme
Database otomatik olarak yeni tabloları oluştururken ilk kez bağlanılırken.

```python
db = Database()  # Yeni tablolar otomatik oluşturulur
```

---

## 📊 Senkronizasyon

### Otomatik Fiyat Güncellemesi
IntegrationManager, arka planda varlık fiyatlarını günceller:

```python
# Kripto fiyatlarını senkronize et
integration_manager.sync_crypto_prices(user_id)

# Emtia fiyatlarını senkronize et
integration_manager.sync_commodity_prices(user_id)

# Fon fiyatlarını senkronize et
integration_manager.sync_fund_prices(user_id)
```

---

## ⚠️ Önemli Notlar

### Vergi Bilgisi
Vergi Optimizasyonu modülü, Türkiye'nin 2024 yılı vergisini esas alır:
- Kısa vadeli: %20
- Uzun vadeli: %10
- Muaf tutar: 13,000₺

**Gerçek vergi beyannameleri için mali müşavir danışınız.**

### Kripto Fiyatları
CoinGecko API kullanan kriptolar USD cinsinden gelir. TRY'ye çevrilmesi sizin sorumluluk alınır.

### Emtia Fiyatları
Emtialar USD cinsindendir. Gerçek ticaret fiyatlarıyla farklılık gösterebilir.

### Fon Fiyatları
TEFAS fiyatları gerçek zamanlı olmayabilir. Güncel fiyatlar için TEFAS.com.tr ziyaret edin.

---

## 🐛 Hata Raporlaması
Herhangi bir sorun olursa, CHANGELOG.md ve ERROR_LOG dosyalarını kontrol edin.

---

**Versiyon:** 2.0.0  
**Son Güncelleme:** 2024  
**Geliştiren:** Portföy Takip Ekibi
