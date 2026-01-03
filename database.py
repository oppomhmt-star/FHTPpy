"""
SQLite Veritabanı Modülü - JSON'dan geçiş ile uyumlu
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from config import DEFAULT_SETTINGS
from contextlib import contextmanager

class Database:
    def __init__(self, db_name="portfolio.db", json_file="portfoy_data.json"):
        # Exe'nin çalıştığı dizini belirle
        if getattr(sys, 'frozen', False):
            # PyInstaller ile derlenmiş exe - exe dosyasının konumunu kullan
            app_dir = os.path.dirname(sys.executable)
        else:
            # Normal Python ortamı
            app_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Klasörü oluştur (eğer yoksa)
        try:
            os.makedirs(app_dir, exist_ok=True)
        except Exception as e:
            print(f"[ERROR] Klasör oluşturma hatası: {e}")
            app_dir = os.path.expanduser("~")
        
        # Database ve JSON dosyalarını app dizininde oluştur
        self.db_name = os.path.join(app_dir, db_name)
        self.json_file = os.path.join(app_dir, json_file)
        self.connection = None
        
        print(f"[DB] Database konumu: {self.db_name}")
        
        # Veritabanını başlat
        try:
            self.init_db()
        except Exception as e:
            print(f"[ERROR] Veritabanı başlatma hatası (yeniden deneniyor): {e}")
            import time
            time.sleep(1)
            self.init_db()
        
        # JSON'dan SQLite'a geçiş varsa otomatik yap
        try:
            if os.path.exists(self.json_file) and not self._db_has_data():
                print(f"[INFO] JSON dosyası bulundu, geçiş başlıyor...")
                self.migrate_from_json()
        except Exception as e:
            print(f"[WARN] JSON geçişi başarısız: {e}")
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def init_db(self):
        """Veritabanını başlat - tüm tabloları oluştur"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Kullanıcılar Tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Portföyler Tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS portfolios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        sembol TEXT NOT NULL,
                        adet INTEGER NOT NULL,
                        ort_maliyet REAL NOT NULL,
                        guncel_fiyat REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        UNIQUE(user_id, sembol)
                    )
                ''')
                
                # İşlemler Tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        sembol TEXT NOT NULL,
                        tip TEXT NOT NULL,
                        adet INTEGER NOT NULL,
                        fiyat REAL NOT NULL,
                        toplam REAL NOT NULL,
                        komisyon REAL DEFAULT 0,
                        tarih TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                ''')
                
                # Temettüler Tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dividends (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        sembol TEXT NOT NULL,
                        tutar REAL NOT NULL,
                        adet INTEGER NOT NULL,
                        hisse_basi_tutar REAL NOT NULL,
                        tarih TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                ''')
                
                # Ayarlar Tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        setting_key TEXT NOT NULL,
                        setting_value TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        UNIQUE(user_id, setting_key)
                    )
                ''')
                
                # Session/Token Tablosu (Cloud sync için)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        token TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                ''')
                
                # Varlık Türleri Tablosu (Hisse, Fon, Kripto, Emtia)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS assets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        sembol TEXT NOT NULL,
                        tur TEXT NOT NULL,
                        ad TEXT NOT NULL,
                        adet REAL NOT NULL,
                        ort_maliyet REAL NOT NULL,
                        guncel_fiyat REAL NOT NULL,
                        para_birimi TEXT DEFAULT 'TRY',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        UNIQUE(user_id, sembol, tur)
                    )
                ''')
                
                # Gelişmiş İşlemler Tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS advanced_transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        sembol TEXT NOT NULL,
                        tip TEXT NOT NULL,
                        adet REAL NOT NULL,
                        fiyat REAL NOT NULL,
                        toplam REAL NOT NULL,
                        komisyon REAL DEFAULT 0,
                        otkome TEXT,
                        tarih TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                ''')
                
                # Portföy Hedefleri
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS portfolio_goals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        hedef_ad TEXT NOT NULL,
                        hedef_tutar REAL NOT NULL,
                        hedef_tarihi TEXT NOT NULL,
                        aylik_yatirim REAL,
                        notlar TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                ''')
                
                # Vergi Kayıtları
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tax_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        yil INTEGER NOT NULL,
                        satig_gelirleri REAL DEFAULT 0,
                        satig_zararlar REAL DEFAULT 0,
                        temettü REAL DEFAULT 0,
                        faiz REAL DEFAULT 0,
                        vergi_serbest REAL DEFAULT 0,
                        notlar TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        UNIQUE(user_id, yil)
                    )
                ''')
                
                # ========== YENİ: FİYAT ALARMLARI TABLOSU ==========
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS price_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL DEFAULT 1,
                        symbol TEXT NOT NULL,
                        target_price REAL NOT NULL,
                        condition TEXT NOT NULL CHECK(condition IN ('above', 'below')),
                        note TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        active BOOLEAN DEFAULT 1,
                        triggered BOOLEAN DEFAULT 0,
                        triggered_at TIMESTAMP,
                        triggered_price REAL,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                ''')
                
                # Index'ler ekle (performans için)
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_price_alerts_user_active 
                    ON price_alerts(user_id, active)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_price_alerts_symbol 
                    ON price_alerts(symbol)
                ''')
                
                conn.commit()
                print(f"[OK] Veritabanı başarıyla oluşturuldu: {self.db_name}")
        except Exception as e:
            print(f"[ERROR] Veritabanı oluşturma hatası: {e}")
            print(f"   Database path: {self.db_name}")
            raise
    
    def _db_has_data(self):
        """Veritabanında veri olup olmadığını kontrol et"""
        try:
            # Eğer dosya yoksa False dön
            if not os.path.exists(self.db_name):
                return False
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                # Portfolios tablosundaki veri sayısını kontrol et
                cursor.execute("SELECT COUNT(*) FROM portfolios WHERE user_id = 1")
                count = cursor.fetchone()
                return count and count[0] > 0
        except Exception as e:
            print(f"[WARN] Database veri kontrol hatası: {e}")
            return False
    
    def migrate_from_json(self):
        """JSON dosyasından SQLite'a veri geçişi"""
        print("\n" + "="*60)
        print("📊 JSON'dan SQLite'a veri geçişi başlıyor...")
        print("="*60)
        
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Varsayılan kullanıcı oluştur
                default_username = "default_user"
                try:
                    cursor.execute('''
                        INSERT INTO users (username, email, password_hash)
                        VALUES (?, ?, ?)
                    ''', (default_username, "user@local.dev", "hashed_pwd"))
                    user_id = cursor.lastrowid
                except sqlite3.IntegrityError:
                    cursor.execute("SELECT id FROM users WHERE username = ?", (default_username,))
                    user_id = cursor.fetchone()[0]
                
                # Portföy verileri
                for stock in json_data.get('portfoy', []):
                    cursor.execute('''
                        INSERT OR REPLACE INTO portfolios 
                        (user_id, sembol, adet, ort_maliyet, guncel_fiyat)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, stock['sembol'], stock['adet'], 
                          stock['ort_maliyet'], stock['guncel_fiyat']))
                
                # İşlem verileri
                for trans in json_data.get('islemler', []):
                    cursor.execute('''
                        INSERT INTO transactions 
                        (user_id, sembol, tip, adet, fiyat, toplam, tarih)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (user_id, trans['sembol'], trans['tip'], 
                          trans['adet'], trans['fiyat'], trans['toplam'], 
                          trans['tarih']))
                
                # Temettü verileri
                for div in json_data.get('temettüler', []):
                    cursor.execute('''
                        INSERT INTO dividends 
                        (user_id, sembol, tutar, adet, hisse_basi_tutar, tarih)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user_id, div['sembol'], div['tutar'], 
                          div['adet'], div['hisse_basi_tutar'], div['tarih']))
                
                # Ayarlar
                for key, value in json_data.get('ayarlar', DEFAULT_SETTINGS).items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO settings 
                        (user_id, setting_key, setting_value)
                        VALUES (?, ?, ?)
                    ''', (user_id, key, json.dumps(value)))
                
                conn.commit()
                
                # Yedek JSON dosyasını oluştur
                backup_name = f"portfoy_data_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                import shutil
                shutil.copy(self.json_file, backup_name)
                
                print(f"✅ {len(json_data.get('portfoy', []))} hisse başarıyla geçirildi")
                print(f"✅ {len(json_data.get('islemler', []))} işlem başarıyla geçirildi")
                print(f"✅ JSON yedek: {backup_name}")
                print("="*60 + "\n")
        
        except Exception as e:
            print(f"❌ Geçiş hatası: {e}")
    
    # ========== KULLANICI İŞLEMLERİ ==========
    
    def create_user(self, username, email, password_hash):
        """Yeni kullanıcı oluştur"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT INTO users (username, email, password_hash)
                    VALUES (?, ?, ?)
                ''', (username, email, password_hash))
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                print(f"Kullanıcı zaten var: {username}")
                return None
    
    def get_user(self, username):
        """Kullanıcı bilgisi getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    # ========== PORTFÖY İŞLEMLERİ ==========
    
    def get_portfolio(self, user_id=1):
        """Portföy getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sembol, adet, ort_maliyet, guncel_fiyat 
                FROM portfolios 
                WHERE user_id = ?
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_portfolio(self, symbol, adet, ort_maliyet, guncel_fiyat, user_id=1):
        """Portföy hissesini güncelle"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO portfolios 
                (user_id, sembol, adet, ort_maliyet, guncel_fiyat)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, symbol, adet, ort_maliyet, guncel_fiyat))
            conn.commit()
            return True
    
    def delete_portfolio(self, symbol, user_id=1):
        """Hisseyi portföyden ve ilgili işlemlerini sil"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Hisseyi portföyden sil
            cursor.execute("DELETE FROM portfolios WHERE user_id = ? AND sembol = ?", (user_id, symbol))
            # İlgili işlemleri sil
            cursor.execute("DELETE FROM transactions WHERE user_id = ? AND sembol = ?", (user_id, symbol))
            # İlgili temettüleri sil
            cursor.execute("DELETE FROM dividends WHERE user_id = ? AND sembol = ?", (user_id, symbol))
            conn.commit()
            return True
    

    def recalculate_portfolio_from_transactions(self, user_id=1):
        """Portföyü işlemlerden yeniden hesapla - SATIŞ DÜZELTİLMİŞ"""
        print("\n" + "="*60)
        print("Portföy yeniden hesaplanıyor (komisyon dahil)...")
        print("="*60)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            settings = self.get_settings(user_id)
            commission_rate = settings.get("komisyon_orani", 0.0004)
            
            try:
                if isinstance(commission_rate, str):
                    commission_rate = commission_rate.replace(',', '.')
                commission_rate = float(commission_rate)
            except:
                commission_rate = 0.0004
            
            # Mevcut fiyatları al
            cursor.execute('''
                SELECT sembol, guncel_fiyat FROM portfolios WHERE user_id = ?
            ''', (user_id,))
            current_prices = {row['sembol']: row['guncel_fiyat'] for row in cursor.fetchall()}
            
            # Portföyü temizle
            cursor.execute("DELETE FROM portfolios WHERE user_id = ?", (user_id,))
            
            # İşlemleri tarihe göre getir
            cursor.execute('''
                SELECT sembol, tip, adet, fiyat, komisyon, tarih FROM transactions 
                WHERE user_id = ? 
                ORDER BY tarih ASC
            ''', (user_id,))
            
            temp_portfolio = {}
            
            for row in cursor.fetchall():
                # SQLite Row nesnesini dict'e dönüştür
                row_dict = dict(row)
                
                symbol = row_dict['sembol']
                adet = row_dict['adet']
                fiyat = row_dict['fiyat']
                tip = row_dict['tip']
                
                # Komisyon değerini kontrol et
                stored_komisyon = row_dict.get('komisyon', 0)
                
                if symbol not in temp_portfolio:
                    temp_portfolio[symbol] = {'adet': 0, 'toplam_maliyet': 0}
                
                if tip == 'Alım':
                    islem_tutari = adet * fiyat
                    komisyon = stored_komisyon if stored_komisyon and stored_komisyon > 0 else islem_tutari * commission_rate
                    toplam_maliyet = islem_tutari + komisyon
                    
                    temp_portfolio[symbol]['adet'] += adet
                    temp_portfolio[symbol]['toplam_maliyet'] += toplam_maliyet
                    
                    print(f"  ✅ {symbol} ALIM: {adet} x {fiyat:.2f}₺ + {komisyon:.2f}₺ kom. = {toplam_maliyet:.2f}₺")
                
                elif tip == 'Satış':
                    # ✅ SATIŞ KONTROLÜ GÜÇLENDİRİLDİ
                    if symbol not in temp_portfolio:
                        print(f"  ⚠️ {symbol} SATIŞ HATASI: Portföyde bu hisse yok!")
                        continue
                        
                    if temp_portfolio[symbol]['adet'] < adet:
                        print(f"  ⚠️ {symbol} SATIŞ HATASI: Yetersiz adet! (Portföyde: {temp_portfolio[symbol]['adet']}, Satış: {adet})")
                        continue
                    
                    # ✅ SATIŞ İŞLEMİ
                    ortalama_maliyet = temp_portfolio[symbol]['toplam_maliyet'] / temp_portfolio[symbol]['adet']
                    satis_maliyeti = adet * ortalama_maliyet
                    
                    temp_portfolio[symbol]['toplam_maliyet'] -= satis_maliyeti
                    temp_portfolio[symbol]['adet'] -= adet
                    
                    print(f"  ❌ {symbol} SATIŞ: {adet} adet x {ortalama_maliyet:.2f}₺ = {satis_maliyeti:.2f}₺")
                    print(f"     → Kalan: {temp_portfolio[symbol]['adet']} adet, Maliyet: {temp_portfolio[symbol]['toplam_maliyet']:.2f}₺")
            
            # Portföyü kaydet
            for symbol, data in temp_portfolio.items():
                if data['adet'] > 0:
                    ort_maliyet = data['toplam_maliyet'] / data['adet']
                    guncel_fiyat = current_prices.get(symbol, ort_maliyet)
                    
                    cursor.execute('''
                        INSERT INTO portfolios 
                        (user_id, sembol, adet, ort_maliyet, guncel_fiyat)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (user_id, symbol, data['adet'], ort_maliyet, guncel_fiyat))
                    
                    print(f"  💼 {symbol}: {data['adet']} adet, Ort.Maliyet: {ort_maliyet:.2f}₺")
                else:
                    print(f"  🗑️ {symbol}: Portföyden çıkarıldı (adet: 0)")
            
            conn.commit()
            print("="*60 + "\n")
    
    # ========== İŞLEM İŞLEMLERİ ==========
    
    def get_transactions(self, user_id=1):
        """İşlemleri getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sembol, tip, adet, fiyat, toplam, komisyon, tarih 
                FROM transactions 
                WHERE user_id = ?
                ORDER BY tarih DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== İŞLEM İŞLEMLERİ - DÜZELTİLMİŞ ==========

    def add_transaction(self, *args, **kwargs):
        """
        İşlem ekle - Esnek format desteği
        
        Format 1 (Dictionary):
            add_transaction(transaction_data, user_id=1)
        
        Format 2 (Pozisyonel argümanlar):
            add_transaction(user_id, sembol, tip, adet, fiyat, tarih, komisyon, notlar)
        
        Format 3 (Keyword argümanlar):
            add_transaction(user_id=1, sembol="THYAO", tip="Alış", ...)
        """
        
        # Format 1: Dictionary (eski format)
        if len(args) == 1 and isinstance(args[0], dict):
            transaction_data = args[0]
            user_id = kwargs.get('user_id', 1)
            
            sembol = transaction_data['sembol']
            tip = transaction_data['tip']
            adet = transaction_data['adet']
            fiyat = transaction_data['fiyat']
            toplam = transaction_data.get('toplam', adet * fiyat)
            komisyon = transaction_data.get('komisyon', 0)
            tarih = transaction_data['tarih']
        
        # Format 2: Pozisyonel argümanlar (yeni - dashboard için)
        elif len(args) >= 7:
            user_id = args[0]
            sembol = args[1]
            tip = args[2]
            adet = args[3]
            fiyat = args[4]
            tarih = args[5]
            komisyon = args[6] if len(args) > 6 else 0
            notlar = args[7] if len(args) > 7 else None
            
            # Toplam hesapla
            toplam = adet * fiyat
        
        # Format 3: Keyword argümanlar
        elif kwargs:
            user_id = kwargs.get('user_id', 1)
            sembol = kwargs.get('sembol') or kwargs.get('symbol')
            tip = kwargs.get('tip') or kwargs.get('transaction_type')
            adet = kwargs.get('adet') or kwargs.get('amount')
            fiyat = kwargs.get('fiyat') or kwargs.get('price')
            tarih = kwargs.get('tarih') or kwargs.get('date')
            komisyon = kwargs.get('komisyon', 0) or kwargs.get('commission', 0)
            notlar = kwargs.get('notlar') or kwargs.get('notes') or kwargs.get('aciklama')
            
            # Toplam hesapla
            toplam = kwargs.get('toplam', adet * fiyat)
        
        else:
            raise ValueError("Geçersiz add_transaction formatı!")
        
        # Validasyon
        if not all([sembol, tip, adet, fiyat, tarih]):
            raise ValueError("Eksik işlem bilgisi!")
        
        # Database'e kaydet
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions 
                (user_id, sembol, tip, adet, fiyat, toplam, komisyon, tarih)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, sembol, tip, adet, fiyat, toplam, komisyon, tarih))
            conn.commit()
            return cursor.lastrowid
    
    # ========== TEMETTÜ İŞLEMLERİ ==========
    
    def get_dividends(self, user_id=1):
        """Temettüleri getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT sembol, tutar, adet, hisse_basi_tutar, tarih 
                FROM dividends 
                WHERE user_id = ?
                ORDER BY tarih DESC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def add_dividend(self, *args, **kwargs):
        """
        Temettü ekle - Esnek format desteği
        
        Format 1 (Dictionary):
            add_dividend(dividend_data, user_id=1)
        
        Format 2 (Pozisyonel):
            add_dividend(user_id, sembol, tutar, tarih, aciklama)
        
        Format 3 (Keyword):
            add_dividend(user_id=1, sembol="THYAO", tutar=100, ...)
        """
        
        # Format 1: Dictionary
        if len(args) == 1 and isinstance(args[0], dict):
            dividend_data = args[0]
            user_id = kwargs.get('user_id', 1)
            
            sembol = dividend_data['sembol']
            tutar = dividend_data['tutar']
            adet = dividend_data.get('adet', 0)
            hisse_basi_tutar = dividend_data.get('hisse_basi_tutar', 0)
            tarih = dividend_data['tarih']
        
        # Format 2: Pozisyonel argümanlar
        elif len(args) >= 4:
            user_id = args[0]
            sembol = args[1]
            tutar = args[2]
            tarih = args[3]
            aciklama = args[4] if len(args) > 4 else None
            
            # Portföyden adet bilgisini al
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT adet FROM portfolios 
                    WHERE user_id = ? AND sembol = ?
                ''', (user_id, sembol))
                
                result = cursor.fetchone()
                adet = result['adet'] if result else 0
            
            hisse_basi_tutar = tutar / adet if adet > 0 else 0
        
        # Format 3: Keyword argümanlar
        elif kwargs:
            user_id = kwargs.get('user_id', 1)
            sembol = kwargs.get('sembol') or kwargs.get('symbol')
            tutar = kwargs.get('tutar') or kwargs.get('amount')
            tarih = kwargs.get('tarih') or kwargs.get('date')
            aciklama = kwargs.get('aciklama') or kwargs.get('notlar') or kwargs.get('note')
            
            # Portföyden adet bilgisini al
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT adet FROM portfolios 
                    WHERE user_id = ? AND sembol = ?
                ''', (user_id, sembol))
                
                result = cursor.fetchone()
                adet = result['adet'] if result else kwargs.get('adet', 0)
            
            hisse_basi_tutar = kwargs.get('hisse_basi_tutar', tutar / adet if adet > 0 else 0)
        
        else:
            raise ValueError("Geçersiz add_dividend formatı!")
        
        # Validasyon
        if not all([sembol, tutar, tarih]):
            raise ValueError("Eksik temettü bilgisi!")
        
        # Database'e kaydet
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO dividends 
                (user_id, sembol, tutar, adet, hisse_basi_tutar, tarih)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, sembol, tutar, adet, hisse_basi_tutar, tarih))
            conn.commit()
            return cursor.lastrowid
    
    # ========== AYAR İŞLEMLERİ ==========
    
    def get_settings(self, user_id=1):
        """Ayarları getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT setting_key, setting_value 
                FROM settings 
                WHERE user_id = ?
            ''', (user_id,))
            
            settings = DEFAULT_SETTINGS.copy()
            for row in cursor.fetchall():
                try:
                    settings[row['setting_key']] = json.loads(row['setting_value'])
                except:
                    settings[row['setting_key']] = row['setting_value']
            
            return settings
    
    def update_settings(self, new_settings, user_id=1):
        """Ayarları güncelle"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for key, value in new_settings.items():
                cursor.execute('''
                    INSERT OR REPLACE INTO settings 
                    (user_id, setting_key, setting_value)
                    VALUES (?, ?, ?)
                ''', (user_id, key, json.dumps(value)))
            conn.commit()
            return True
    
    # ========== FİYAT ALARMLARI İŞLEMLERİ ==========
    
    def add_price_alert(self, alert_data, user_id=1):
        """Fiyat alarmı ekle"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO price_alerts 
                    (user_id, symbol, target_price, condition, note, created_at, active, triggered)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id,
                    alert_data['symbol'],
                    alert_data['target_price'],
                    alert_data['condition'],
                    alert_data.get('note', ''),
                    alert_data.get('created_at', datetime.now()),
                    alert_data.get('active', True),
                    alert_data.get('triggered', False)
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            print(f"Alarm ekleme hatası: {e}")
            return None
    
    def get_price_alerts(self, active_only=False, user_id=1):
        """Tüm fiyat alarmlarını getir"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM price_alerts WHERE user_id = ?'
                params = [user_id]
                
                if active_only:
                    query += ' AND active = 1'
                
                query += ' ORDER BY created_at DESC'
                
                cursor.execute(query, params)
                columns = [description[0] for description in cursor.description]
                
                alerts = []
                for row in cursor.fetchall():
                    alert = dict(zip(columns, row))
                    
                    # Datetime dönüşümleri
                    if alert.get('created_at'):
                        try:
                            alert['created_at'] = datetime.fromisoformat(alert['created_at'])
                        except:
                            pass
                    
                    if alert.get('triggered_at'):
                        try:
                            alert['triggered_at'] = datetime.fromisoformat(alert['triggered_at'])
                        except:
                            pass
                    
                    alerts.append(alert)
                
                return alerts
        except Exception as e:
            print(f"Alarm getirme hatası: {e}")
            return []
    
    def get_price_alert(self, alert_id, user_id=1):
        """Tek bir alarmı getir"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM price_alerts 
                    WHERE id = ? AND user_id = ?
                ''', (alert_id, user_id))
                
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    alert = dict(zip(columns, row))
                    
                    # Datetime dönüşümleri
                    if alert.get('created_at'):
                        try:
                            alert['created_at'] = datetime.fromisoformat(alert['created_at'])
                        except:
                            pass
                    
                    if alert.get('triggered_at'):
                        try:
                            alert['triggered_at'] = datetime.fromisoformat(alert['triggered_at'])
                        except:
                            pass
                    
                    return alert
        except Exception as e:
            print(f"Alarm getirme hatası: {e}")
        
        return None
    
    def update_price_alert(self, alert_id, user_id=1, **kwargs):
        """Fiyat alarmını güncelle"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                allowed_fields = [
                    'target_price', 'condition', 'note', 'active', 
                    'triggered', 'triggered_at', 'triggered_price'
                ]
                
                updates = []
                values = []
                
                for key, value in kwargs.items():
                    if key in allowed_fields:
                        updates.append(f"{key} = ?")
                        values.append(value)
                
                if not updates:
                    return False
                
                values.extend([alert_id, user_id])
                
                query = f'''
                    UPDATE price_alerts 
                    SET {', '.join(updates)} 
                    WHERE id = ? AND user_id = ?
                '''
                
                cursor.execute(query, values)
                conn.commit()
                
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Alarm güncelleme hatası: {e}")
            return False
    
    def delete_price_alert(self, alert_id, user_id=1):
        """Fiyat alarmını sil"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM price_alerts 
                    WHERE id = ? AND user_id = ?
                ''', (alert_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Alarm silme hatası: {e}")
            return False
    
    # ========== VARLIK TÜRÜ İŞLEMLERİ ==========
    
    def add_asset(self, asset_data, user_id=1):
        """Yeni varlık ekle (Hisse, Fon, Kripto, Emtia)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO assets 
                    (user_id, sembol, tur, ad, adet, ort_maliyet, guncel_fiyat, para_birimi)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, asset_data['sembol'], asset_data['tur'], 
                      asset_data['ad'], asset_data['adet'], asset_data['ort_maliyet'],
                      asset_data['guncel_fiyat'], asset_data.get('para_birimi', 'TRY')))
                conn.commit()
                return cursor.lastrowid
            except Exception as e:
                print(f"Asset ekleme hatası: {e}")
                return None
    
    def get_assets_by_type(self, asset_type, user_id=1):
        """Türe göre varlıkları getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM assets 
                WHERE user_id = ? AND tur = ?
                ORDER BY ad ASC
            ''', (user_id, asset_type))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_all_assets(self, user_id=1):
        """Tüm varlıkları getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM assets 
                WHERE user_id = ?
                ORDER BY tur, ad
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_asset(self, symbol, asset_type, user_id=1):
        """Varlığı sil"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM assets 
                WHERE user_id = ? AND sembol = ? AND tur = ?
            ''', (user_id, symbol, asset_type))
            conn.commit()
            return True
    
    # ========== GELİŞMİŞ İŞLEMLER ==========
    
    def apply_stock_split(self, symbol, split_ratio, user_id=1):
        """Hisse bölünmesi uygula"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Portföyden hisseyi getir
            cursor.execute('''
                SELECT adet, ort_maliyet FROM portfolios 
                WHERE user_id = ? AND sembol = ?
            ''', (user_id, symbol))
            
            stock = cursor.fetchone()
            if not stock:
                return False
            
            old_adet = stock['adet']
            old_cost = stock['ort_maliyet']
            
            # Yeni değerleri hesapla
            new_adet = old_adet * split_ratio
            new_cost = old_cost / split_ratio
            
            # Portföyü güncelle
            cursor.execute('''
                UPDATE portfolios 
                SET adet = ?, ort_maliyet = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND sembol = ?
            ''', (new_adet, new_cost, user_id, symbol))
            
            # İşlem kaydı ekle
            cursor.execute('''
                INSERT INTO advanced_transactions 
                (user_id, sembol, tip, adet, fiyat, toplam, otkome, tarih)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, symbol, 'StockSplit', split_ratio, new_cost, 
                  new_adet * new_cost, 
                  f'Hisse Bölünmesi: {old_adet} x {old_cost:.2f}₺ -> {int(new_adet)} x {new_cost:.2f}₺',
                  datetime.now().isoformat()))
            
            conn.commit()
            return True
    
    def apply_rights_issue(self, symbol, rights_ratio, new_share_price, user_id=1):
        """Rüçhan hakkı uygula (bedelli sermaye artırımı)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Portföyden hisseyi getir
            cursor.execute('''
                SELECT adet, ort_maliyet, guncel_fiyat FROM portfolios 
                WHERE user_id = ? AND sembol = ?
            ''', (user_id, symbol))
            
            stock = cursor.fetchone()
            if not stock:
                return False
            
            old_adet = stock['adet']
            old_cost = stock['ort_maliyet']
            old_price = stock['guncel_fiyat']
            
            # Yeni hisse adeti hesapla
            new_shares = old_adet / rights_ratio
            
            # Yeni ortalama maliyet hesapla
            total_investment = old_adet * old_cost + new_shares * new_share_price
            new_avg_cost = total_investment / (old_adet + new_shares)
            
            # Portföyü güncelle
            cursor.execute('''
                UPDATE portfolios 
                SET adet = ?, ort_maliyet = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND sembol = ?
            ''', (old_adet + new_shares, new_avg_cost, user_id, symbol))
            
            # İşlem kaydı ekle
            cursor.execute('''
                INSERT INTO advanced_transactions 
                (user_id, sembol, tip, adet, fiyat, toplam, otkome, tarih)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, symbol, 'RightsIssue', new_shares, new_share_price,
                  new_shares * new_share_price,
                  f'Bedelli Sermaye Artırımı: {new_shares:.0f} hisse x {new_share_price:.2f}₺',
                  datetime.now().isoformat()))
            
            conn.commit()
            return True
    
    # ========== PORTFÖY HEDEFLERİ ==========
    
    def add_goal(self, goal_data, user_id=1):
        """Portföy hedefi ekle"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO portfolio_goals 
                (user_id, hedef_ad, hedef_tutar, hedef_tarihi, aylik_yatirim, notlar)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, goal_data['hedef_ad'], goal_data['hedef_tutar'],
                  goal_data['hedef_tarihi'], goal_data.get('aylik_yatirim'),
                  goal_data.get('notlar')))
            conn.commit()
            return cursor.lastrowid
    
    def get_goals(self, user_id=1):
        """Hedefleri getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM portfolio_goals 
                WHERE user_id = ?
                ORDER BY hedef_tarihi ASC
            ''', (user_id,))
            return [dict(row) for row in cursor.fetchall()]
    
    def delete_goal(self, goal_id, user_id=1):
        """Hedefi sil"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM portfolio_goals 
                WHERE id = ? AND user_id = ?
            ''', (goal_id, user_id))
            conn.commit()
            return True
    
    # ========== VERGİ KAYITLARI ==========
    
    def update_tax_record(self, year, tax_data, user_id=1):
        """Vergi kaydı ekle/güncelle"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO tax_records 
                (user_id, yil, satig_gelirleri, satig_zararlar, temettü, faiz, vergi_serbest, notlar)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, year, tax_data.get('satig_gelirleri', 0),
                  tax_data.get('satig_zararlar', 0), tax_data.get('temettü', 0),
                  tax_data.get('faiz', 0), tax_data.get('vergi_serbest', 0),
                  tax_data.get('notlar')))
            conn.commit()
            return True
    
    def get_tax_records(self, year=None, user_id=1):
        """Vergi kayıtlarını getir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if year:
                cursor.execute('''
                    SELECT * FROM tax_records 
                    WHERE user_id = ? AND yil = ?
                ''', (user_id, year))
            else:
                cursor.execute('''
                    SELECT * FROM tax_records 
                    WHERE user_id = ?
                    ORDER BY yil DESC
                ''', (user_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # ========== VERİ YÖNETİMİ ==========
    
    def export_data(self, filename, user_id=1):
        """Verileri JSON olarak dış aktar"""
        try:
            export_data = {
                "portfoy": self.get_portfolio(user_id),
                "islemler": self.get_transactions(user_id),
                "temettüler": self.get_dividends(user_id),
                "ayarlar": self.get_settings(user_id),
                "price_alerts": self.get_price_alerts(user_id=user_id)
            }
            
            # Datetime nesnelerini string'e çevir
            def convert_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime(i) for i in obj]
                return obj
            
            export_data = convert_datetime(export_data)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Export hatası: {e}")
            return False
    
    def import_data(self, filename, user_id=1):
        """JSON'dan veri aktar"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for trans in data.get('islemler', []):
                self.add_transaction(trans, user_id)
            
            for div in data.get('temettüler', []):
                self.add_dividend(div, user_id)
            
            # Price alerts varsa ekle
            for alert in data.get('price_alerts', []):
                self.add_price_alert(alert, user_id)
            
            self.update_settings(data.get('ayarlar', {}), user_id)
            self.recalculate_portfolio_from_transactions(user_id)
            return True
        except Exception as e:
            print(f"Import hatası: {e}")
            return False
    
    def clear_all_data(self, user_id=1):
        """Kullanıcı verilerini sil"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM portfolios WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM dividends WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM settings WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM price_alerts WHERE user_id = ?", (user_id,))
            conn.commit()
            return True
    
    # ========== ÖRNEK VERİ ==========
    
    def add_sample_data(self, user_id=1):
        """Örnek veri ekle"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM portfolios WHERE user_id = ?", (user_id,))
            
            if cursor.fetchone()[0] > 0:
                return False
            
            sample_transactions = [
                ("THYAO", "Alım", 100, 250.50, 25050, "2024-01-15 10:30:00"),
                ("AKBNK", "Alım", 500, 45.75, 22875, "2024-01-20 14:15:00"),
                ("EREGL", "Alım", 200, 38.20, 7640, "2024-02-01 11:00:00"),
                ("GARAN", "Alım", 300, 95.30, 28590, "2024-02-10 09:45:00"),
                ("THYAO", "Satış", 50, 265.00, 13250, "2024-03-05 13:20:00"),
            ]
            
            for sembol, tip, adet, fiyat, toplam, tarih in sample_transactions:
                cursor.execute('''
                    INSERT INTO transactions 
                    (user_id, sembol, tip, adet, fiyat, toplam, tarih)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (user_id, sembol, tip, adet, fiyat, toplam, tarih))
            
            cursor.execute('''
                INSERT INTO dividends 
                (user_id, sembol, tutar, adet, hisse_basi_tutar, tarih)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, "AKBNK", 1250.00, 500, 2.50, "2024-03-15 10:00:00"))
            
            # Örnek alarm ekle
            cursor.execute('''
                INSERT INTO price_alerts 
                (user_id, symbol, target_price, condition, note)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, "THYAO", 275.00, "above", "Kar al seviyesi"))
            
            conn.commit()
            self.recalculate_portfolio_from_transactions(user_id)
            return True