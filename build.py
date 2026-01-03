# build.py
import PyInstaller.__main__
import sys
import os

# Exe'nin adı
app_name = "HisseTakip"

# Icon dosyası (varsa)
icon_path = "icon.ico"  # Eğer ikonunuz varsa

# Tüm gerekli dosyaları ve klasörleri belirt
additional_files = [
    ('config.py', '.'),
    ('pages/*.py', 'pages'),
    ('utils/*.py', 'utils'),
    ('assets/*', 'assets'),  # Eğer assets klasörünüz varsa
]

# PyInstaller argümanları
args = [
    'main.py',  # Ana Python dosyası
    '--name=' + app_name,
    '--onefile',  # Tek exe dosyası
    '--noconsole',  # Konsol penceresi gösterme
    '--clean',  # Temiz build
    '--add-data=config.py;.',  # Config dosyası
    '--add-data=pages;pages',  # Pages klasörü
    '--add-data=utils;utils',  # Utils klasörü
    #'--add-data=assets;assets',  # Assets klasörü (varsa)
]

# Icon varsa ekle
if os.path.exists(icon_path):
    args.append('--icon=' + icon_path)

# Hidden imports (gerekli olabilecek gizli modüller)
hidden_imports = [
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=customtkinter',
    '--hidden-import=yfinance',
    '--hidden-import=pandas',
    '--hidden-import=numpy',
]

args.extend(hidden_imports)

# PyInstaller'ı çalıştır
PyInstaller.__main__.run(args)