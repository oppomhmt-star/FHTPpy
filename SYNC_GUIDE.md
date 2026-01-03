# 🔄 Senkronizasyon Rehberi

Bu dokümanda yeni varlık türlerinin senkronizasyonunu nasıl yapacağınız açıklanır.

## 📋 İçindekiler

1. [Otomatik Senkronizasyon](#1-otomatik-senkronizasyon)
2. [Manuel Senkronizasyon](#2-manuel-senkronizasyon)
3. [Fiyat Güncellemesi](#3-fiyat-güncellemesi)
4. [Hata Yönetimi](#4-hata-yönetimi)

---

## 1. Otomatik Senkronizasyon

### Arka Planda Çalışan Senkronizasyon

Uygulamada **IntegrationManager** otomatik olarak başlatılır:

```python
# main.py
self.integration_manager = IntegrationManager(self.db)
```

### Kripto Fiyat Senkronizasyonu

**Zaman Aralığı**: Her 5 dakika (ayarlanabilir)

```python
# Otomatik
integration_manager.sync_crypto_prices(user_id)

# Manuel
integration_manager.sync_crypto_prices(
    user_id,
    callback=lambda: print("Kripto fiyatları güncellendi")
)
```

**Akış**:
```
1. assets tablosundan kripto'ları getir
2. Her kripto için CoinGecko API'ne istek gönder
3. Fiyat ve detay bilgilerini güncelle
4. Portföy değerini yeniden hesapla
```

### Emtia Fiyat Senkronizasyonu

```python
# Otomatik
integration_manager.sync_commodity_prices(user_id)

# Manuel
integration_manager.sync_commodity_prices(
    user_id,
    callback=lambda: print("Emtia fiyatları güncellendi")
)
```

### Fon Fiyat Senkronizasyonu

```python
# Otomatik
integration_manager.sync_fund_prices(user_id)

# Manuel
integration_manager.sync_fund_prices(
    user_id,
    callback=lambda: print("Fon fiyatları güncellendi")
)
```

---

## 2. Manuel Senkronizasyon

### Dashboard'dan Yenileme

AssetsPage'de "Yenile" butonu:

```python
# pages/assets_page.py
def refresh_assets(self):
    # Tüm varlıkları yeniden yükle
    self.parent.winfo_toplevel().integration_manager.sync_crypto_prices(
        self.current_user_id
    )
```

### Programatik Senkronizasyon

Başka yerden tetiklemek:

```python
# Kripto eklendikten sonra
crypto_integration.add_crypto_to_portfolio(user_id, crypto_data)
integration_manager.sync_crypto_prices(user_id)

# Fon eklendikten sonra
tefas_integration.add_fund_to_portfolio(user_id, fund_data)
integration_manager.sync_fund_prices(user_id)
```

---

## 3. Fiyat Güncellemesi

### Tek Varlığın Fiyatını Güncelleme

```python
# API'den fiyat çek
crypto_service.get_crypto_price('bitcoin', callback=lambda data: 
    update_asset_price(user_id, 'BTC', 'kripto', data)
)

# Veritabanında güncelle
asset = {
    'sembol': 'BTC',
    'tur': 'kripto',
    'ad': 'Bitcoin',
    'adet': 0.5,
    'ort_maliyet': 45000,
    'guncel_fiyat': 48500,  # ← Güncel fiyat
    'para_birimi': 'USD'
}
db.add_asset(asset, user_id)
```

### Toplu Fiyat Güncellemesi

```python
# Tüm kripto'ları güncelle
cryptos = db.get_assets_by_type('kripto', user_id)
for crypto in cryptos:
    crypto_service.get_crypto_price(
        crypto['sembol'].lower(),
        callback=lambda data, sym=crypto['sembol']: 
            update_crypto_price(user_id, sym, data)
    )

# Tüm emtia'ları güncelle
commodities = db.get_assets_by_type('emtia', user_id)
for commodity in commodities:
    commodity_service.get_commodity_price(
        commodity['sembol'],
        callback=lambda data, sym=commodity['sembol']: 
            update_commodity_price(user_id, sym, data)
    )
```

### Hisse Senkronizasyonu (Mevcut)

Hisseler zaten `main.py` içindeki `auto_update_prices()` ile güncellenmektedir:

```python
def auto_update_prices(self):
    """Otomatik fiyat güncelleme"""
    portfolio = self.db.get_portfolio(self.current_user_id)
    
    import yfinance as yf
    for stock in portfolio:
        t = yf.Ticker(f"{stock['sembol']}.IS")
        h = t.history(period="1d")
        if not h.empty:
            new_price = h['Close'].iloc[-1]
            # Veritabanında güncelle
            self.db.update_portfolio(
                stock['sembol'],
                stock['adet'],
                stock['ort_maliyet'],
                new_price,
                self.current_user_id
            )
```

---

## 4. Hata Yönetimi

### API Bağlantı Hatası

```python
try:
    crypto_service.get_crypto_price('bitcoin', callback=handle_data)
except ConnectionError:
    print("❌ CoinGecko API'sine bağlanılamadı")
    # Eski fiyatları kullan
except Exception as e:
    print(f"❌ Beklenmeyen hata: {e}")
```

### Rate Limiting Başarısız Olsa Da Devam Et

CoinGecko ücretsiz API'sinin limit'i aşılırsa:

```python
# Otomatik fallback: Cache kullan
if cached_data:
    use_cached_data()
else:
    retry_after_delay(5_minutes)
```

### Veri Tutarsızlığı

Kripto/Emtia USD, Hisse/Fon TRY cinsinden ise:

```python
# Para birimini kaydet
asset['para_birimi'] = 'USD'  # Kripto/Emtia
asset['para_birimi'] = 'TRY'  # Hisse/Fon

# Karşılaştırma yaparken dönüştür
def convert_to_try(value, currency):
    if currency == 'USD':
        return value * get_usd_try_rate()
    return value
```

### Ağ Bağlantı Yok

Offline modda yerel veri kullanılır:

```python
# Offline kontrol
if is_offline():
    use_last_known_prices()
    show_warning("Internet bağlantısı yok. Son bilinen fiyatlar kullanılıyor.")
else:
    fetch_fresh_data()
```

---

## 📊 Senkronizasyon Akışları

### Uygulama Başlatma

```
main.py: __init__()
  ├─ Database.init_db() → Tüm tablolar oluştur
  ├─ IntegrationManager(db) → Tüm servisleri başlat
  ├─ load_initial_market_data()
  │  ├─ api.get_currency_data() → Döviz kurlari
  │  └─ api.get_index_data() → Endeksleri
  └─ init_main_app()
     └─ [add_sample_data if first time]
```

### Sayfaya Girince

```
show_page('assets')
  ├─ AssetsPage.create()
  ├─ load_assets('hisse')
  │  └─ db.get_assets_by_type('hisse', user_id)
  └─ Tabloyu göster
```

### Varlık Ekleme

```
add_asset_dialog() → form doldur → [Kaydet]
  ├─ db.add_asset(asset_data, user_id)
  └─ Fiyat senkronize et
     ├─ crypto: sync_crypto_prices()
     ├─ fon: sync_fund_prices()
     └─ emtia: sync_commodity_prices()
```

### Otomatik Güncelleme Döngüsü

```
start_auto_update() [daemon thread]
  └─ while True:
     ├─ sleep(5 minutes)
     ├─ auto_update_prices() [hisseler]
     ├─ integration_manager.sync_crypto_prices()
     ├─ integration_manager.sync_commodity_prices()
     └─ refresh_current_page()
```

---

## 🔌 API Bağlantı Kontrolü

### Sağlayıcı Durumunu Kontrol Et

```python
# Main.py başlatılırken
def check_provider_status(self):
    """API sağlayıcılarının çalışıp çalışmadığını kontrol et"""
    
    # yfinance
    try:
        yf.Ticker("THYAO").info
        print("✅ yfinance: Çalışıyor")
    except:
        print("❌ yfinance: Çalışmıyor")
    
    # CoinGecko
    try:
        crypto_service.get_top_100_cryptos()
        print("✅ CoinGecko: Çalışıyor")
    except:
        print("❌ CoinGecko: Çalışmıyor")
```

### Fallback Mekanizması

Bir API başarısız olursa:

```python
def get_asset_price_safe(symbol, asset_type):
    """Güvenli fiyat alımı"""
    
    try:
        if asset_type == 'kripto':
            return get_from_coingecko(symbol)
        elif asset_type == 'emtia':
            return get_from_yfinance(symbol)
    except:
        # Fallback: Cache kullan
        cached = get_cached_price(symbol)
        if cached:
            return cached
        
        # Fallback: Son bilinen fiyat
        return get_last_known_price(symbol)
```

---

## 📈 Performans İpuçları

### Batch İşleme

Binlerce kripto/emtia varsa grup grup işle:

```python
def sync_all_with_batching(user_id, batch_size=10):
    assets = db.get_all_assets(user_id)
    
    for i in range(0, len(assets), batch_size):
        batch = assets[i:i+batch_size]
        
        for asset in batch:
            update_price(asset)
        
        time.sleep(0.5)  # Rate limit'e saygı göster
```

### Caching

Sık sorgulananlara cache ekle:

```python
cache = {}
cache_ttl = 300  # 5 dakika

def get_crypto_price_cached(symbol):
    if symbol in cache and not is_expired(cache[symbol]['time']):
        return cache[symbol]['price']
    
    price = fetch_from_api(symbol)
    cache[symbol] = {'price': price, 'time': now()}
    return price
```

### Paralel İşleme

Birden fazla API çağrısını paralel yap:

```python
import concurrent.futures

def sync_all_parallel(user_id):
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        cryptos = db.get_assets_by_type('kripto', user_id)
        futures = [
            executor.submit(update_crypto_price, c)
            for c in cryptos
        ]
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Sync hatası: {e}")
```

---

## ✅ Kontrol Listesi

Senkronizasyonun doğru çalıştığını doğrulamak için:

- [ ] `portfolio.db` oluşturuldu
- [ ] `assets` tablosu var
- [ ] `advanced_transactions` tablosu var
- [ ] Kripto eklenebiliyor
- [ ] Fon eklenebiliyor
- [ ] Emtia eklenebiliyor
- [ ] Fiyatlar otomatik güncelleniyor
- [ ] Stock Split uygulanabiliyor
- [ ] Rights Issue uygulanabiliyor
- [ ] Monte Carlo çalışıyor
- [ ] Hedef Analizi çalışıyor
- [ ] Vergi Optimizasyonu çalışıyor

---

**Son Güncelleme**: 2024-11  
**Sürüm**: 2.1.0
