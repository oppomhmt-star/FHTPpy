# CachyOS/Linux Build Rehberi

## 🐧 Linux'ta Tek Çalıştırılabilir Dosya Oluşturma

### 1. Sistem Hazırlığı

```bash
# CachyOS'ta gerekli paketleri yükle
sudo pacman -S python python-pip tk

# Python sanal ortam oluştur (önerilen)
python -m venv venv
source venv/bin/activate
```

### 2. Bağımlılıkları Yükle

```bash
# Linux için requirements
pip install customtkinter Pillow yfinance requests pandas python-dotenv cryptography pyinstaller

# Not: winotify Windows-only, Linux'ta notify-send kullanacağız
```

### 3. Build Script'i Çalıştır

```bash
# Linux için build
python build_linux.py
```

### 4. Çalıştırma

```bash
# Build sonrası dist klasöründe olacak
cd dist
./HisseTakip

# İsteğe bağlı: çalıştırılabilir yapma
chmod +x HisseTakip
```

### 5. Sistem Entegrasyonu (Opsiyonel)

Desktop entry oluşturmak için:

```bash
# ~/.local/share/applications/hissetakip.desktop
[Desktop Entry]
Type=Application
Name=HisseTakip
Comment=Portföy Takip Uygulaması
Exec=/tam/yol/dist/HisseTakip
Icon=/tam/yol/icon.png
Terminal=false
Categories=Office;Finance;
```

## 🔧 Sorun Giderme

### TK/TCL Hatası
```bash
sudo pacman -S tk
```

### Bildirim Sorunu
Linux'ta `notify-send` kullanılır (winotify yerine):
```bash
sudo pacman -S libnotify
```

### Font Sorunu
```bash
sudo pacman -S ttf-dejavu
```

## 📦 Taşınabilir Kullanım

Build edilen `HisseTakip` dosyası tek başına çalışır:
- Başka bir CachyOS/Linux sistemine kopyalayabilirsiniz
- USB'den çalıştırabilirsiniz
- `chmod +x HisseTakip` komutu ile çalıştırılabilir yapın

## 🎯 Performans İpuçları

1. UPX ile sıkıştırma:
```bash
sudo pacman -S upx
# build_linux.py içinde upx=True zaten aktif
```

2. Boyutu küçültme:
- Gereksiz kütüphaneleri kaldırın
- `--exclude-module` ile kullanılmayan modülleri hariç tutun

## ⚠️ Önemli Notlar

- Linux build'i **sadece Linux'ta** çalışır (CachyOS, Arch, Ubuntu vb.)
- Windows .exe ile cross-compile edilemez
- Her platform için o platformda build yapılmalı
