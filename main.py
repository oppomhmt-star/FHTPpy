# main.py

import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime
import threading
import sys
import os
import time

def get_app_path():
    """Uygulama çalışma dizinini belirle"""
    if getattr(sys, 'frozen', False):
        # PyInstaller ile paketlenmiş
        return os.path.dirname(sys.executable)
    else:
        # Normal Python ortamı
        return os.path.dirname(os.path.abspath(__file__))

def ensure_directories():
    """Gerekli dizinleri oluştur"""
    app_dir = get_app_path()
    
    # Ana dizin
    os.makedirs(app_dir, exist_ok=True)
    
    # Alt dizinler
    subdirs = ['backups', 'cache', 'logs']
    for subdir in subdirs:
        os.makedirs(os.path.join(app_dir, subdir), exist_ok=True)
    
    return app_dir

# Uygulama başlangıcında çağır
app_dir = ensure_directories()

# Database ve diğer dosya yollarını ayarla
DB_PATH = os.path.join(app_dir, "portfolio.db")
BACKUP_DIR = os.path.join(app_dir, "backups")
CACHE_DIR = os.path.join(app_dir, "cache")
LOG_DIR = os.path.join(app_dir, "logs")

from database import Database
from api_service import APIService
from auth_service import AuthService
from cloud_sync import CloudSync
from credentials_manager import CredentialsManager
from config import COLORS, DEFAULT_SETTINGS, FONT_SIZES
from ui_utils import showinfo, showerror, askyesno
from integration_manager import IntegrationManager

# Settings ve Backup Manager
try:
    from utils.settings_manager import SettingsManager
    from utils.backup_manager import BackupManager
except ImportError as e:
    print(f"Modül import hatası: {e}")
    SettingsManager = None
    BackupManager = None

# Price Alert Manager - YENİ
try:
    from utils.price_alert_manager import PriceAlertManager
except ImportError as e:
    print(f"Price Alert Manager import hatası: {e}")
    PriceAlertManager = None

# Sayfalar
from pages.auth_page import AuthPage
from pages.dashboard_page import DashboardPage
from pages.portfolio_page import PortfolioPage
from pages.transactions_page import TransactionsPage
from pages.analysis_page import AnalysisPage
from pages.settings_page import SettingsPage
from pages.financials_page import FinancialsPage
from pages.stock_history_page import StockHistoryPage
from pages.advanced_transactions_page import AdvancedTransactionsPage
from pages.advanced_analysis_page import AdvancedAnalysisPage

# Price Alert Page - YENİ
try:
    from pages.price_alert_page import PriceAlertPage
except ImportError as e:
    print(f"Price Alert Page import hatası: {e}")
    PriceAlertPage = None


class HisseTakipProgrami(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Hisse Senedi Takip Programı")
        self.geometry("1450x850")
        
        # Veritabanı ve Servisler
        self.db = Database()
        self.auth = AuthService(self.db)
        self.api = APIService()
        self.cloud_sync = CloudSync(self.db)
        self.integration_manager = IntegrationManager(self.db)
        self.credentials_manager = CredentialsManager()
        
        # Kullanıcı oturumu
        self.current_user_id = None
        self.current_token = None
        
        # Settings Manager
        if SettingsManager:
            self.settings_manager = SettingsManager(self.db)
        else:
            self.settings_manager = None
        
        # Backup Manager
        if BackupManager and self.settings_manager:
            self.backup_manager = BackupManager(self.db, self.settings_manager)
        else:
            self.backup_manager = None
        
        # Price Alert Manager - YENİ
        if PriceAlertManager:
            self.alert_manager = PriceAlertManager(self.db, self.settings_manager)
        else:
            self.alert_manager = None
        
        # Cache ve event'ler
        self.currency_cache = []
        self.index_cache = []
        self.data_loaded_event = threading.Event()
        
        # Auto-update kontrolü için flag
        self.auto_update_running = False
        
        # Grid yapılandırması
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Auth sayfasını göster
        self.show_auth_page()
        
        # Kapatma protokolü
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def show_auth_page(self):
        """Auth sayfasını göster"""
        # Mevcut widgetleri temizle
        for widget in self.winfo_children():
            widget.destroy()
        
        # Auth frame
        self.auth_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.auth_frame.grid(row=0, column=0, sticky="nsew")
        
        auth_page = AuthPage(self.auth_frame, self.auth)
        auth_page.on_login_success = self.on_login_success
        auth_page.create()
    
    def on_login_success(self, result):
        """Başarılı giriş sonrası"""
        self.current_user_id = result['user_id']
        self.current_token = result['token']
        
        print(f"✅ {result['username']} olarak giriş yapıldı")
        
        # Cloud sync ayarla
        self.cloud_sync.set_credentials(self.current_user_id, self.current_token)
        
        # Ana uygulamayı başlat
        self.init_main_app()
    
    def init_main_app(self):
        """Ana uygulamayı başlat"""
        # Auth frame'i temizle
        for widget in self.winfo_children():
            widget.destroy()
        
        # Grid yapılandırması
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)  # Sidebar - sabit genişlik
        self.grid_columnconfigure(1, weight=1)  # Main frame - esnek
        
        # Örnek veri varsa ekle
        if not self.db.get_portfolio(self.current_user_id):
            self.db.add_sample_data(self.current_user_id)
        
        # Ayarları uygula
        self.apply_settings()
        
        # Otomatik yedekleme kontrolü
        if self.backup_manager:
            self.check_auto_backup()
        
        # Sidebar ve main frame oluştur
        self.create_sidebar()
        
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Loading ekranı
        font_size = self.get_font_size("normal")
        self.loading_label = ctk.CTkLabel(
            self.main_frame, 
            text="⏳ Başlangıç verileri yükleniyor...", 
            font=ctk.CTkFont(size=font_size)
        )
        self.loading_label.pack(expand=True)
        
        # Verileri yükle
        threading.Thread(target=self.load_initial_market_data, daemon=True).start()
        
        # Otomatik fiyat güncelleme
        if self.should_auto_update():
            self.start_auto_update()
        
        # Fiyat alarmı izleme - YENİ
        if self.alert_manager:
            self.start_price_alert_monitoring()
        
        # Cloud sync başlat (eğer etkin ise)
        if self.settings_manager and self.settings_manager.get("cloud_sync_enabled", False):
            self.cloud_sync.start_auto_sync()

        # KLAVYE KIŞAYOLLARINI AYARLA - YENİ DOĞRU YER
        self.setup_keyboard_shortcuts()
        
        # Verilerin yüklenmesini bekle ve ilk sayfayı göster
        self.check_data_loaded()
        
    def check_data_loaded(self):
        """Verilerin yüklenip yüklenmediğini kontrol et"""
        if self.data_loaded_event.is_set():
            # Loading label'ı kaldır
            if self.loading_label:
                self.loading_label.destroy()
                self.loading_label = None
            
            # Başlangıç sayfasını göster
            if self.settings_manager:
                start_page = self.settings_manager.get("start_page", "dashboard")
            else:
                start_page = "dashboard"
            
            self.show_page(start_page)
        else:
            # Tekrar kontrol et
            self.after(100, self.check_data_loaded)
    
    # ========== YENİ: FİYAT ALARMI İZLEME ==========
    
    def start_price_alert_monitoring(self):
        """Fiyat alarm izlemeyi başlat"""
        if not self.alert_manager:
            return
        
        class PriceProvider:
            """Fiyat sağlayıcı"""
            def __init__(self, api_service, db, user_id):
                self.api = api_service
                self.db = db
                self.user_id = user_id
            
            def get_current_prices(self, symbols):
                """Güncel fiyatları al"""
                prices = {}
                
                import yfinance as yf
                for symbol in symbols:
                    try:
                        stock = yf.Ticker(symbol + ".IS")
                        hist = stock.history(period="1d")
                        
                        if not hist.empty:
                            prices[symbol] = float(hist['Close'].iloc[-1])
                    except Exception as e:
                        print(f"Fiyat alma hatası ({symbol}): {e}")
                
                return prices
        
        # Provider oluştur
        provider = PriceProvider(self.api, self.db, self.current_user_id)
        
        # İzlemeyi başlat (30 saniyede bir kontrol)
        interval = 30
        if self.settings_manager:
            interval = self.settings_manager.get("alert_check_interval", 30)
        
        self.alert_manager.start_monitoring(provider, interval=interval)
        
        print(f"✅ Fiyat alarm izleme başlatıldı (interval: {interval}s)")
    
    # ========== YARDIMCI METODLAR ==========
    
    def get_font_size(self, size_type="normal"):
        """Font boyutunu al (güvenli)"""
        if self.settings_manager:
            return self.settings_manager.get_font_size(size_type)
        
        # Fallback
        return FONT_SIZES.get("normal", {}).get(size_type, 13)

    def should_auto_update(self):
        """Otomatik güncelleme kontrolü (güvenli)"""
        if self.settings_manager:
            return self.settings_manager.should_auto_update()
        return True

    def apply_settings(self):
        """Ayarları uygula"""
        if self.settings_manager:
            self.current_theme = self.settings_manager.get("tema", "dark")
        else:
            self.current_theme = "dark"
        
        ctk.set_appearance_mode(self.current_theme)

    def check_auto_backup(self):
        """Otomatik yedekleme kontrolü"""
        try:
            if self.backup_manager:
                backup_path = self.backup_manager.check_and_auto_backup()
                if backup_path:
                    print(f"✅ Otomatik yedek oluşturuldu: {backup_path}")
        except Exception as e:
            print(f"Otomatik yedekleme hatası: {e}")

    def start_auto_update(self):
        """Otomatik fiyat güncellemeyi başlat"""
        self.auto_update_running = True
        
        def update_loop():
            while self.auto_update_running:
                try:
                    # Güncelleme aralığını al
                    if self.settings_manager:
                        interval = self.settings_manager.get_update_interval()
                    else:
                        interval = 300
                    
                    # Güvenlik kontrolü
                    if not isinstance(interval, (int, float)) or interval <= 0:
                        interval = 300
                    
                    # Bekle (her 1 saniyede kontrol et - durdurma için)
                    for _ in range(int(interval)):
                        if not self.auto_update_running:
                            return
                        time.sleep(1)
                    
                    if not self.auto_update_running:
                        return
                    
                    # Piyasa saatleri kontrolü
                    if self.settings_manager:
                        update_after_hours = self.settings_manager.get("update_after_hours", False)
                        if isinstance(update_after_hours, str):
                            update_after_hours = update_after_hours.lower() in ['true', '1', 'yes', 'on']
                    else:
                        update_after_hours = False
                    
                    if not update_after_hours:
                        now = datetime.now()
                        # Hafta sonu veya piyasa saatleri dışı
                        if now.weekday() >= 5 or now.hour < 10 or now.hour >= 18:
                            continue
                    
                    # Fiyatları güncelle
                    self.after(0, self.auto_update_prices)
                
                except Exception as e:
                    print(f"Güncelleme döngüsü hatası: {e}")
                    time.sleep(60)  # Hata durumunda 1 dakika bekle
        
        # Thread başlat
        threading.Thread(target=update_loop, daemon=True).start()
        print("✅ Otomatik fiyat güncelleme başlatıldı")
    
    def auto_update_prices(self):
        """Otomatik fiyat güncelleme"""
        try:
            portfolio = self.db.get_portfolio(self.current_user_id)
            if not portfolio:
                return
            
            import yfinance as yf
            updated_count = 0
            
            for stock in portfolio:
                try:
                    ticker = yf.Ticker(f"{stock['sembol']}.IS")
                    hist = ticker.history(period="1d")
                    
                    if not hist.empty:
                        new_price = float(hist['Close'].iloc[-1])
                        
                        # Veritabanını güncelle
                        with self.db.get_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE portfolios 
                                SET guncel_fiyat = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE sembol = ? AND user_id = ?
                            ''', (new_price, stock['sembol'], self.current_user_id))
                        
                        updated_count += 1
                
                except Exception as e:
                    print(f"Fiyat güncellemesi hatası ({stock['sembol']}): {e}")
            
            # Sayfayı yenile
            if updated_count > 0:
                self.refresh_current_page()
                print(f"✅ {updated_count} hisse fiyatı güncellendi")
        
        except Exception as e:
            print(f"Otomatik fiyat güncelleme hatası: {e}")
    
    def refresh_current_page(self):
        """Mevcut sayfayı yenile"""
        if hasattr(self, 'active_page'):
            try:
                self.show_page(self.active_page)
            except Exception as e:
                print(f"Sayfa yenileme hatası: {e}")
            
    
    # ================== KLAVYE KISAYOLLARI ==================    
    def setup_keyboard_shortcuts(self):
        """Klavye kısayollarını ayarla - Dinamik"""
        
        # Ayarlardan kısayolları al
        shortcuts = self.settings_manager.settings.get("keyboard_shortcuts", {
            "new_stock": "Control-n",
            "backup": "Control-s",
            "search": "Control-f",
            "refresh_prices": "Control-r",
            "refresh_page": "F5",
            "quit_app": "Control-q",
            "page_dashboard": "Control-Key-1",
            "page_portfolio": "Control-Key-2",
            "page_transactions": "Control-Key-3",
            "page_settings": "Control-Key-4",
            "help": "F1",
            "escape": "Escape"
        })
        
        # Önceki binding'leri temizle (varsa)
        if hasattr(self, '_shortcut_bindings'):
            for binding in self._shortcut_bindings:
                try:
                    self.unbind_all(binding)
                except:
                    pass
        
        self._shortcut_bindings = []
        
        # Kısayolları bind et
        shortcut_map = {
            "new_stock": self.shortcut_new_stock,
            "backup": self.shortcut_backup,
            "search": self.shortcut_search,
            "refresh_prices": self.shortcut_refresh_prices,
            "refresh_page": self.shortcut_refresh_page,
            "quit_app": self.shortcut_quit,
            "page_dashboard": lambda: self.show_page("dashboard"),
            "page_portfolio": lambda: self.show_page("portfolio"),
            "page_transactions": lambda: self.show_page("transactions"),
            "page_settings": lambda: self.show_page("settings"),
            "help": self.show_shortcuts_help,
            "escape": self.shortcut_escape
        }
        
        for action, callback in shortcut_map.items():
            if action in shortcuts:
                binding = f"<{shortcuts[action]}>"
                self.bind_all(binding, lambda e, c=callback: c())
                self._shortcut_bindings.append(binding)
        
        print(f"[INFO] {len(self._shortcut_bindings)} klavye kısayolu yüklendi")
    
    def shortcut_new_stock(self):
        """Yeni hisse ekle kısayolu"""
        if hasattr(self, 'active_page') and self.active_page == "portfolio":
            if hasattr(self, 'portfolio_page'):
                self.portfolio_page.add_stock_dialog()
        else:
            self.show_page("portfolio")
            self.after(100, lambda: self.portfolio_page.add_stock_dialog())
    
    def shortcut_backup(self):
        """Yedek al kısayolu"""
        try:
            backup_path = self.backup_manager.create_backup(auto=False)
            if backup_path:
                import os
                backup_name = os.path.basename(backup_path)
                showinfo("Başarılı", f"✅ Yedekleme tamamlandı!\n\n📁 {backup_name}")
        except Exception as e:
            showerror("Hata", f"Yedekleme hatası:\n{str(e)}")
    
    def shortcut_search(self):
        """Arama kısayolu"""
        if hasattr(self, 'active_page') and self.active_page == "portfolio":
            if hasattr(self, 'portfolio_page') and hasattr(self.portfolio_page, 'search_entry'):
                self.portfolio_page.search_entry.focus_set()
    
    def shortcut_refresh_prices(self):
        """Fiyatları güncelle kısayolu"""
        if hasattr(self, 'portfolio_page'):
            self.portfolio_page.update_all_prices()
    
    def shortcut_refresh_page(self):
        """Sayfayı yenile kısayolu"""
        current_page = getattr(self, 'active_page', 'dashboard')
        self.show_page(current_page)
    
    def shortcut_quit(self):
        """Çıkış kısayolu"""
        if askyesno("Çıkış", "Uygulamadan çıkmak istediğinizden emin misiniz?"):
            self.quit()
    
    def shortcut_escape(self):
        """Escape - Dialog kapat"""
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkToplevel):
                widget.destroy()
                break
    
    def show_shortcuts_help(self):
        """Klavye kısayolları yardımı"""
        help_window = ctk.CTkToplevel(self)
        help_window.title("⌨️ Klavye Kısayolları")
        help_window.geometry("550x650")
        help_window.transient(self)
        help_window.grab_set()
        
        # Pencereyi ortala
        help_window.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - (help_window.winfo_width() // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (help_window.winfo_height() // 2)
        help_window.geometry(f"+{x}+{y}")
        
        # Başlık
        ctk.CTkLabel(help_window, text="⌨️ Klavye Kısayolları", 
                    font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)
        
        # Scroll frame
        scroll_frame = ctk.CTkScrollableFrame(help_window, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Mevcut kısayolları al
        shortcuts_settings = self.settings_manager.settings.get("keyboard_shortcuts", {})
        
        def format_key(key_binding):
            """Kısayolu formatla"""
            formatted = key_binding.replace("Control-", "Ctrl+")
            formatted = formatted.replace("Shift-", "Shift+")
            formatted = formatted.replace("Alt-", "Alt+")
            formatted = formatted.replace("Key-", "")
            parts = formatted.split('+')
            if len(parts) > 1:
                parts[-1] = parts[-1].upper()
                return '+'.join(parts)
            return formatted.upper()
        
        # Kısayollar listesi
        shortcuts = [
            ("Genel", [
                ("help", "Bu yardım penceresini göster"),
                ("refresh_page", "Sayfayı yenile"),
                ("quit_app", "Uygulamadan çıkış"),
                ("escape", "Açık pencereyi kapat"),
            ]),
            ("Sayfa Geçişleri", [
                ("page_dashboard", "Dashboard'a git"),
                ("page_portfolio", "Portföy'e git"),
                ("page_transactions", "İşlemler'e git"),
                ("page_settings", "Ayarlar'a git"),
            ]),
            ("İşlemler", [
                ("new_stock", "Yeni hisse ekle"),
                ("backup", "Yedek al"),
                ("search", "Portföyde ara"),
                ("refresh_prices", "Fiyatları güncelle"),
            ]),
        ]
        
        for category, items in shortcuts:
            # Kategori başlığı
            category_frame = ctk.CTkFrame(scroll_frame, fg_color=("gray85", "gray20"))
            category_frame.pack(fill="x", pady=(10, 5))
            
            ctk.CTkLabel(category_frame, text=category, 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=8)
            
            # Kısayollar
            for key_id, description in items:
                row = ctk.CTkFrame(scroll_frame, fg_color=("gray90", "gray13"), corner_radius=6)
                row.pack(fill="x", pady=3)
                
                content = ctk.CTkFrame(row, fg_color="transparent")
                content.pack(fill="x", padx=15, pady=10)
                
                # Kısayol tuşu - Ayarlardan al
                key_binding = shortcuts_settings.get(key_id, "")
                key_display = format_key(key_binding) if key_binding else "Atanmamış"
                
                key_label = ctk.CTkLabel(content, text=key_display, 
                                        font=ctk.CTkFont(size=13, weight="bold", family="Consolas"),
                                        text_color=COLORS["cyan"],
                                        width=140)
                key_label.pack(side="left")
                
                # Açıklama
                desc_label = ctk.CTkLabel(content, text=description, 
                                         font=ctk.CTkFont(size=12),
                                         anchor="w")
                desc_label.pack(side="left", fill="x", expand=True, padx=10)
        
        # Alt bilgi
        info_frame = ctk.CTkFrame(help_window, fg_color=("gray85", "gray17"))
        info_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(info_frame, 
                    text="💡 Kısayolları özelleştirmek için Ayarlar > Klavye Kısayolları",
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack(padx=15, pady=10)
        
        # Kapat butonu
        ctk.CTkButton(help_window, text="Kapat", command=help_window.destroy,
                     width=150, height=40).pack(pady=(0, 15))

    def load_initial_market_data(self, callback=None):
        """İlk veri yüklemesi"""
        self.data_loaded_event.clear()
        finished_tasks = 0
        lock = threading.Lock()
        
        def task_finished():
            nonlocal finished_tasks
            with lock:
                finished_tasks += 1
                if finished_tasks == 2:
                    print("✅ API verileri yüklendi.")
                    self.data_loaded_event.set()
                    if callback:
                        self.after(0, callback)
        
        def currency_callback(data):
            self.currency_cache = data
            task_finished()
        
        def index_callback(data):
            self.index_cache = data
            task_finished()
        
        # Verileri paralel yükle
        self.api.get_currency_data(callback=currency_callback)
        self.api.get_index_data(callback=index_callback)

    def create_sidebar(self):
        """Sidebar oluştur"""
        # Sidebar genişliği
        if self.settings_manager:
            sidebar_width = self.settings_manager.get("sidebar_width", 240)
        else:
            sidebar_width = 240
        
        self.sidebar = ctk.CTkFrame(self, width=sidebar_width, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(11, weight=1)  # 10 -> 11 (yeni buton için)
        
        # Logo
        font_size = self.get_font_size("title")
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="📊 Portföy Takip", 
            font=ctk.CTkFont(size=font_size, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)
        
        # Menü butonları
        self.menu_buttons = {}
        menu_items = [
            ("dashboard", "📈 Dashboard"),
            ("portfolio", "💼 Portföy"),
            ("transactions", "💰 İşlemler"),
            ("analysis", "📊 Analiz"),
            ("price_alerts", "🔔 Fiyat Alarmları"),  # YENİ
            ("adv_analysis", "🔬 Gelişmiş Analiz"),
            ("adv_transactions", "⚙️ Gelişmiş İşlemler"),
            ("financial", "📑 Finansal Tablolar"),
            ("history", "📜 Hisse Geçmişi"),
            ("settings", "⚙️ Ayarlar")
        ]
        
        button_font_size = self.get_font_size("normal")
        
        for i, (page_id, text) in enumerate(menu_items, start=1):
            btn = ctk.CTkButton(
                self.sidebar, 
                text=text, 
                command=lambda p=page_id: self.show_page(p), 
                font=ctk.CTkFont(size=button_font_size), 
                height=40, 
                anchor="w", 
                fg_color="transparent", 
                text_color=("gray10", "gray90"), 
                hover_color=("gray70", "gray30")
            )
            btn.grid(row=i, column=0, padx=20, pady=5, sticky="ew")
            self.menu_buttons[page_id] = btn

    def show_page(self, page_name):
        """Sayfayı göster"""
        self.active_page = page_name
        self.update_active_menu()
        
        # Mevcut sayfayı temizle (loading label hariç)
        for widget in self.main_frame.winfo_children():
            if widget != self.loading_label:
                widget.destroy()
        
        # Veriler yüklenmemişse loading göster
        if not self.data_loaded_event.is_set():
            if not self.loading_label or not self.loading_label.winfo_exists():
                self.loading_label = ctk.CTkLabel(
                    self.main_frame, 
                    text="⏳ Veriler yükleniyor...", 
                    font=ctk.CTkFont(size=self.get_font_size("normal"))
                )
                self.loading_label.pack(expand=True)
            return

        page_instance = None
        
        try:
            if page_name == "dashboard":
                page_instance = DashboardPage(
                    self.main_frame, self.db, self.api, self.current_theme, 
                    self.currency_cache, self.index_cache
                )
            
            elif page_name == "portfolio":
                page_instance = PortfolioPage(
                    self.main_frame, self.db, self.api, self.current_theme
                )
                # Portfolio page referansını sakla (kısayollar için)
                self.portfolio_page = page_instance
            
            elif page_name == "transactions":
                page_instance = TransactionsPage(
                    self.main_frame, self.db, self.api, self.current_theme
                )
            
            elif page_name == "analysis":
                page_instance = AnalysisPage(
                    self.main_frame, self.db, self.api, self.current_theme
                )
            
            elif page_name == "price_alerts":  # YENİ
                if PriceAlertPage and self.alert_manager:
                    app_callbacks = {
                        'get_settings_manager': lambda: self.settings_manager,
                        'get_backup_manager': lambda: self.backup_manager,
                        'reload_app': self.reload_app,
                        'toggle_theme': self.toggle_theme,
                        'show_shortcuts_help': self.show_shortcuts_help,
                        'reload_shortcuts': self.setup_keyboard_shortcuts
                    }
                    page_instance = PriceAlertPage(
                        self.main_frame, self.db, app_callbacks
                    )
                else:
                    # Fallback mesajı
                    error_label = ctk.CTkLabel(
                        self.main_frame, 
                        text="⚠️ Fiyat Alarm modülü yüklenemedi\n\nLütfen gerekli dosyaların yüklü olduğundan emin olun.", 
                        font=ctk.CTkFont(size=14),
                        text_color=COLORS["warning"]
                    )
                    error_label.pack(expand=True)
                    return
            
            elif page_name == "financial":
                page_instance = FinancialsPage(
                    self.main_frame, self.db, self.api, self.current_theme
                )
            
            elif page_name == "history":
                page_instance = StockHistoryPage(
                    self.main_frame, self.db, self.api, self.current_theme
                )
            
            elif page_name == "adv_transactions":
                page_instance = AdvancedTransactionsPage(
                    self.main_frame, self.db, self.current_theme
                )
            
            elif page_name == "adv_analysis":
                page_instance = AdvancedAnalysisPage(
                    self.main_frame, self.db, self.current_theme
                )
            
            elif page_name == "settings":
                app_callbacks = {
                    'toggle_theme': self.toggle_theme,
                    'reload_app': self.reload_app,
                    'get_settings_manager': lambda: self.settings_manager,
                    'get_backup_manager': lambda: self.backup_manager,
                    'get_cloud_sync': lambda: self.cloud_sync,
                    'get_api_service': lambda: self.api,
                    'user_id': self.current_user_id
                }
                page_instance = SettingsPage(self.main_frame, self.db, app_callbacks)
            
            # Sayfayı oluştur
            if page_instance:
                page_instance.create()
        
        except Exception as e:
            print(f"Sayfa oluşturma hatası ({page_name}): {e}")
            import traceback
            traceback.print_exc()
            
            error_label = ctk.CTkLabel(
                self.main_frame, 
                text=f"⚠️ Sayfa yüklenirken hata oluştu:\n\n{str(e)}", 
                font=ctk.CTkFont(size=14),
                text_color=COLORS["danger"]
            )
            error_label.pack(expand=True)

    # main.py veya app.py - Ana uygulama sınıfına ekle


    def refresh_all_pages(self):
        """Tüm sayfaları refresh et"""
        try:
            # Portföy sayfasını refresh et
            if hasattr(self, 'portfolio_page') and self.portfolio_page:
                if hasattr(self.portfolio_page, 'refresh_ui'):
                    self.portfolio_page.refresh_ui()
                    print("[INFO] Portföy sayfası yenilendi")
            
            # Dashboard'ı refresh et
            if hasattr(self, 'dashboard_page') and self.dashboard_page:
                # Dashboard zaten kendini yeniliyor
                pass
            
            # Diğer sayfaları da refresh edebilirsiniz
            if hasattr(self, 'transactions_page') and self.transactions_page:
                if hasattr(self.transactions_page, 'display_transactions'):
                    self.transactions_page.display_transactions()
                    print("[INFO] İşlemler sayfası yenilendi")
            
        except Exception as e:
            print(f"[ERROR] Sayfa yenileme hatası: {e}")
    
    def toggle_theme(self, theme=None):
        """Tema değiştir"""
        if theme:
            self.current_theme = theme
        else:
            # Toggle between dark and light
            self.current_theme = "light" if self.current_theme == "dark" else "dark"
        
        ctk.set_appearance_mode(self.current_theme)
        
        # Ayarlara kaydet
        if self.settings_manager:
            self.settings_manager.set("tema", self.current_theme)
        
        # Sayfayı yenile
        self.show_page(self.active_page)
    
    def reload_app(self):
        """Uygulamayı yeniden başlat"""
        try:
            # Auto-update'i durdur
            self.auto_update_running = False
            
            # Alarm izlemeyi durdur
            if self.alert_manager:
                self.alert_manager.stop_monitoring()
            
            # Python yorumlayıcısını yeniden başlat
            python = sys.executable
            os.execl(python, python, *sys.argv)
        
        except Exception as e:
            print(f"Yeniden başlatma hatası: {e}")
            showerror("Hata", "Uygulama yeniden başlatılamadı.\n\nLütfen manuel olarak yeniden başlatın.")

    

    def update_active_menu(self):
        """Aktif menüyü vurgula"""
        font_size = self.get_font_size("normal")
        
        for page_id, btn in self.menu_buttons.items():
            if page_id == self.active_page:
                btn.configure(
                    fg_color=("gray75", "gray25"), 
                    text_color=("#1f538d", "#14b8a6"), 
                    font=ctk.CTkFont(size=font_size, weight="bold")
                )
            else:
                btn.configure(
                    fg_color="transparent", 
                    text_color=("gray10", "gray90"), 
                    font=ctk.CTkFont(size=font_size, weight="normal")
                )
    
    def on_closing(self):
        """Uygulama kapatılırken"""
        try:
            # Auto-update'i durdur
            self.auto_update_running = False
            
            # Alarm izlemeyi durdur
            if self.alert_manager:
                self.alert_manager.stop_monitoring()
                print("✅ Alarm izleme durduruldu")
            
            # Yedekleme kontrolü
            if self.backup_manager and self.settings_manager:
                if self.settings_manager.backup_needed():
                    if askyesno("Yedekleme", "Çıkmadan önce yedek almak ister misiniz?"):
                        backup_path = self.backup_manager.create_backup(auto=False)
                        if backup_path:
                            showinfo("Başarılı", f"Yedek alındı:\n{os.path.basename(backup_path)}")
        
        except Exception as e:
            print(f"Kapatma işlemi hatası: {e}")
        
        finally:
            self.destroy()


if __name__ == "__main__":
    try:
        app = HisseTakipProgrami()
        app.mainloop()
    
    except Exception as e:
        print(f"❌ Uygulama başlatma hatası: {e}")
        import traceback
        traceback.print_exc()
        
        # Hata penceresi
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Başlatma Hatası",
                f"Uygulama başlatılamadı:\n\n{str(e)}\n\nDetaylar için konsolu kontrol edin."
            )
            root.destroy()
        except:
            pass