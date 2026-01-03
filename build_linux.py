# build_linux.py - Linux için build scripti
import PyInstaller.__main__
import sys
import os

app_name = "HisseTakip"

# Linux için PyInstaller argümanları
args = [
    'main.py',
    '--name=' + app_name,
    '--onefile',  # Tek çalıştırılabilir dosya
    '--windowed',  # GUI modu (--noconsole Linux için)
    '--clean',
    '--add-data=config.py:.',  # Linux'ta ':' kullanılır
    '--add-data=pages:pages',
    '--add-data=utils:utils',
]

# Hidden imports
hidden_imports = [
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=PIL.ImageTk',
    '--hidden-import=customtkinter',
    '--hidden-import=yfinance',
    '--hidden-import=pandas',
    '--hidden-import=numpy',
    '--hidden-import=tkinter',
    '--hidden-import=_tkinter',
]

args.extend(hidden_imports)

# Linux'a özel optimizasyonlar
linux_specific = [
    '--strip',  # Debug sembollerini kaldır
    '--upx-dir=/usr/bin',  # UPX yolu (eğer yüklüyse)
]

args.extend(linux_specific)

print("🐧 Linux için build başlatılıyor...")
print(f"📦 Uygulama: {app_name}")
print(f"🔧 Platform: {sys.platform}")
print("-" * 50)

try:
    PyInstaller.__main__.run(args)
    print("\n✅ Build başarılı!")
    print(f"📂 Çalıştırılabilir dosya: dist/{app_name}")
    print(f"🚀 Çalıştırmak için: cd dist && ./{app_name}")
except Exception as e:
    print(f"\n❌ Build hatası: {e}")
    sys.exit(1)
