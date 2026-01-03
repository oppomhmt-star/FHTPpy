# 🎉 HisseTakip Uygulaması - Exe Derleme Başarılı!

## ✅ Derleme Tamamlandı

Uygulamanız başarıyla taşınabilir bir **`.exe`** dosyası olarak derlenmiştir.

---

## 📦 Derlenen Dosya

**Konum:** `dist/HisseTakip.exe`  
**Boyut:** ~172 MB  
**Platform:** Windows (x64)

---

## 🚀 NASIL ÇALIŞTIRILIR?

### Seçenek 1: Doğrudan Başlatın
```
dist/ klasöründe HisseTakip.exe dosyasını çift tıklayın
```

### Seçenek 2: Komut Satırından
```cmd
dist\HisseTakip.exe
```

---

## 📁 VERİ DEPOLAMASı

**ÖNEMLİ:** Veritabanı dosyası (`portfolio.db`) **HisseTakip.exe dosyasının yanında** oluşturulur.

```
dist/
├── HisseTakip.exe          ← Ana uygulama
├── portfolio.db             ← Verileriniz burada (otomatik oluşturulur)
├── README.txt               ← Kullanıcı rehberi
└── NOT_OKUNUZ.txt          ← Önemli notlar
```

---

## 💾 VERILERI AKTARMA

### Uygulamayı Başka Bilgisayara Taşımak

1. **dist/** klasörünün tamamını kopyalayın (HisseTakip.exe + portfolio.db)
2. Başka bilgisayara yapıştırın
3. HisseTakip.exe'yi çalıştırın - Verileriniz otomatik olarak yüklenecek

### Mevcut Verilerinizi Yedeklemek

- `portfolio.db` dosyasını güvenli bir yere kopyalayın
- Herhangi bir zaman geri yüklemek için dosyayı `dist/` klasörüne yapıştırın

---

## 🔧 TEKNIK DETAYLAR

### Database Yönetimi
Database dosyasının otomatik olarak exe'nin çalıştığı yerde oluşturulmasını sağlayan kodlar:

**database.py**
```python
if getattr(sys, 'frozen', False):
    # PyInstaller ile derlenmiş exe
    app_dir = sys._MEIPASS
else:
    # Normal Python ortamı
    app_dir = os.path.dirname(os.path.abspath(__file__))

self.db_name = os.path.join(app_dir, db_name)
self.json_file = os.path.join(app_dir, json_file)
```

### Derleme Yapılandırması
- **Tool:** PyInstaller 6.16.0
- **Python:** 3.13.7
- **Spec:** build_exe.spec

---

## 📋 DOSYA YAPISI

```
HisseTakip(YENI)/
├── dist/                      ← Taşınabilir uygulama
│   ├── HisseTakip.exe         ← ANA DOSYA
│   ├── portfolio.db           ← Veritabanı (kullanıcı oluşturur)
│   ├── README.txt
│   └── NOT_OKUNUZ.txt
│
├── build_exe.spec            ← PyInstaller yapılandırması
├── build.bat                 ← Derleme scripti
├── database.py               ← Dinamik path desteği
├── main.py
├── config.py
└── [diğer dosyalar]
```

---

## 🔄 YENIDEN DERLEME İsTE

Kodda değişiklik yaptıysanız, yeniden derlemek için:

### Windows CMD/PowerShell'de:
```cmd
cd dist'in_üst_klasörü
python -m PyInstaller build_exe.spec
```

---

## ✨ ÖZELLİKLER

✅ **Taşınabilir** - Kurulum gerekmez  
✅ **Kendi Kendine Çalışan** - Tüm bağımlılıklar dahil  
✅ **Yerel Veri Depolama** - Verileriniz bilgisayarınızda kalır  
✅ **Güncellenebilir** - Yeniden derleyerek güncelleyin  
✅ **Güvenli** - Hiçbir internet verisi aktarımı yok  

---

## ⚠️ HATALAR GIDERIM

### Exe başlamıyor:
1. Python 3.7+ yüklü olduğundan emin olun (geliştirme sırasında)
2. Windows Defender/Antivirus'u geçici devre dışı bırakın
3. Dosya adında özel karakter olmadığından emin olun

### Database dosyası oluşturulmuyor:
- `dist/` klasörüne yazma izniniz olduğundan emin olun
- Klasörün salt okunur olmadığını kontrol edin

### Veriler yüklenmedi:
- `portfolio.db` dosyasının `dist/` klasöründe olduğundan emin olun
- Veritabanı dosyasının bozuk olmadığını kontrol edin

---

## 📞 İLETİŞİM

Sorun yaşarsanız:
1. README.txt dosyasını okuyun
2. portfolio.db dosyasını yedekleyin
3. Gerekirse veritabanını silin (veriler kaybedilir)

---

## 🎯 HAZIRLANMIŞ!

Uygulamanız artık **profesyonel bir taşınabilir programı** olarak dağıtıma hazırdır!

**dist/ klasörünü bir zip dosyası olarak sıkıştırıp paylaşabilirsiniz.**
