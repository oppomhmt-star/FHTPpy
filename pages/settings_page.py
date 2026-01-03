import customtkinter as ctk
from tkinter import filedialog
from config import COLORS, DEFAULT_SETTINGS
from ui_utils import showinfo, showerror, askyesno
import os
import sys
import shutil
import threading
from datetime import datetime
from typing import Optional, Dict, Any
import traceback

# Utility imports
try:
    from utils.secure_settings import SecureSettings
    from utils.api_manager import APIManager
    from utils.settings_validator import SettingsValidator
    from utils.rate_limiter import RateLimiter, RateLimitException
except ImportError as e:
    print(f"Warning: Could not import utilities: {e}")
    SecureSettings = None
    APIManager = None
    SettingsValidator = None
    RateLimiter = None


# ================== HELPER FUNCTIONS ==================

def format_rate(value):
    """Float rate'i düzgün formatta string'e çevir (bilimsel gösterim olmadan)"""
    if value == 0:
        return "0"
    
    # Bilimsel gösterim yerine normal format
    formatted = "{:.10f}".format(float(value))
    
    # Sondaki gereksiz sıfırları temizle
    formatted = formatted.rstrip('0').rstrip('.')
    
    return formatted


# ================== ERROR HANDLING DECORATOR ==================

def handle_errors(show_error=True):
    """Hata yakalama decorator'ı"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_msg = f"{func.__name__} hatası:\n{str(e)}"
                print(error_msg)
                traceback.print_exc()
                if show_error:
                    showerror("Hata", error_msg)
                return None
        return wrapper
    return decorator


# ================== LOADING DIALOG - FIXED ==================

class LoadingDialog(ctk.CTkToplevel):
    """Thread-safe loading dialog"""
    
    def __init__(self, parent, message="İşlem yapılıyor..."):
        super().__init__(parent)
        self.title("")
        self.geometry("350x120")
        self.resizable(False, False)
        
        # Center window
        self.transient(parent)
        self.grab_set()
        
        # Icon/Emoji
        ctk.CTkLabel(self, text="⏳", font=ctk.CTkFont(size=32)).pack(pady=(20, 5))
        
        # Message
        self.message_label = ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=14))
        self.message_label.pack(pady=5)
        
        # Progress bar
        self.progress = ctk.CTkProgressBar(self, mode="indeterminate", width=300)
        self.progress.pack(pady=10)
        self.progress.start()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        self._destroyed = False
        self._destroy_lock = threading.Lock()
    
    def safe_destroy(self):
        """Thread-safe destroy with proper error handling"""
        with self._destroy_lock:
            if self._destroyed:
                return
            
            self._destroyed = True
            
            try:
                # Progress bar'ı durdur
                if hasattr(self, 'progress') and self.progress.winfo_exists():
                    self.progress.stop()
            except Exception as e:
                print(f"Progress stop error: {e}")
            
            try:
                # Grab'i serbest bırak
                if self.winfo_exists():
                    self.grab_release()
            except Exception as e:
                print(f"Grab release error: {e}")
            
            try:
                # Pencereyi kapat
                if self.winfo_exists():
                    # Withdraw before destroy to prevent deiconify issues
                    self.withdraw()
                    self.update_idletasks()
                    self.destroy()
            except Exception as e:
                print(f"Window destroy error: {e}")
    
    def update_message(self, message):
        """Mesajı güncelle"""
        if not self._destroyed:
            try:
                if self.winfo_exists() and hasattr(self, 'message_label'):
                    self.message_label.configure(text=message)
                    self.update_idletasks()
            except Exception as e:
                print(f"Message update error: {e}")


# ================== SETTING WIDGET WRAPPER ==================

class SettingWidget:
    """Tutarlı widget yönetimi için wrapper sınıfı"""
    
    def __init__(self, var, widget_type, **metadata):
        self.var = var
        self.type = widget_type  # 'switch', 'combo', 'entry', 'rate', 'api_key'
        self.metadata = metadata
    
    def get_value(self):
        """Widget'ın değerini al"""
        if self.type == 'switch':
            return self.var.get() == "on"
        
        elif self.type == 'combo':
            display_value = self.var.get()
            try:
                idx = self.metadata['display_values'].index(display_value)
                return self.metadata['values'][idx]
            except (ValueError, IndexError):
                return self.var.get()
        
        elif self.type == 'rate':
            # Oran değerleri (komisyon, vergi) - onbinde/binde formatında
            value = self.var.get().replace(',', '.').strip()
            try:
                rate = float(value)
                if 0 <= rate <= 1:  # 0 ile 1 arasında olmalı
                    return rate
                else:
                    raise ValueError(f"Oran 0-1 arasında olmalı, {rate} geçersiz")
            except ValueError as e:
                raise ValueError(f"Geçersiz oran formatı: {value}")
        
        elif self.type == 'entry':
            return self.var.get()
        
        elif self.type == 'api_key':
            # API anahtarları - şifrelenecek
            return self.var.get().strip()
        
        else:
            return self.var.get()
    
    def set_value(self, value):
        """Widget'a değer ata"""
        if self.type == 'switch':
            self.var.set("on" if value else "off")
        
        elif self.type == 'combo':
            try:
                idx = self.metadata['values'].index(value)
                self.var.set(self.metadata['display_values'][idx])
            except (ValueError, IndexError):
                self.var.set(str(value))
        
        elif self.type == 'rate':
            # Rate değerlerini formatla
            self.var.set(format_rate(value))
        
        else:
            self.var.set(str(value))


# ================== SETTINGS PAGE ==================

class SettingsPage:
    def __init__(self, parent, db, app_callbacks):
        self.parent = parent
        self.db = db
        self.app_callbacks = app_callbacks
        
        # Ayar ve Yedekleme yöneticilerini al
        if 'get_settings_manager' in app_callbacks:
            self.settings_manager = app_callbacks['get_settings_manager']()
        else:
            from utils.settings_manager import SettingsManager
            self.settings_manager = SettingsManager(db)
        
        if 'get_backup_manager' in app_callbacks:
            self.backup_manager = app_callbacks['get_backup_manager']()
        else:
            from utils.backup_manager import BackupManager
            self.backup_manager = BackupManager(db, self.settings_manager)
        
        # Credentials yöneticisini al
        try:
            from credentials_manager import CredentialsManager
            self.credentials_manager = CredentialsManager()
        except:
            self.credentials_manager = None
        
        # Security ve API yöneticileri
        self.secure_settings = SecureSettings() if SecureSettings else None
        self.api_manager = APIManager(self.settings_manager) if APIManager else None
        self.validator = SettingsValidator() if SettingsValidator else None
        
        self.settings = self.settings_manager.settings
        
        # Widget yönetimi - kategorilere göre ayrılmış
        self.settings_widgets = {
            'general': {},
            'appearance': {},
            'data': {},
            'notifications': {},
            'portfolio': {},
            'charts': {},
            'backup': {},
            'advanced': {},
            'shortcuts': {},
            'security': {},
            'about': {}
        }
        
        self.temp_settings = self.settings.copy()
        self.active_category = None
        self.category_buttons = {}
        self.api_status_labels = {}
        
        # Search
        self.search_var = None
    
    def create(self):
        """Gelişmiş ayarlar sayfasını oluşturur."""
        self.main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)
        
        # Başlık
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        # Sol: Başlık
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")
        
        ctk.CTkLabel(title_frame, text="⚙️ Ayarlar", 
                     font=ctk.CTkFont(size=32, weight="bold")).pack(side="left")
        
        # Orta: Arama
        search_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        search_frame.pack(side="left", padx=40)
        
        self.search_var = ctk.StringVar()
        self.search_var.trace("w", lambda *args: self.filter_categories())
        
        search_entry = ctk.CTkEntry(search_frame, 
                                   placeholder_text="🔍 Ayarlarda ara...",
                                   textvariable=self.search_var, 
                                   width=300,
                                   height=35)
        search_entry.pack()
        
        # Sağ: Butonlar
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="💾 Kaydet", command=self.save_all_settings,
                     width=100, height=35, fg_color=COLORS["success"]).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="↺ Sıfırla", command=self.reset_to_defaults,
                     width=100, height=35, fg_color=COLORS["warning"]).pack(side="left", padx=5)
        
        # Ana içerik - iki bölmeli
        content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=5)
        
        content_frame.grid_columnconfigure(0, weight=0, minsize=200)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Sol panel - Kategori menüsü
        self.create_category_menu(content_frame)
        
        # Sağ panel - Ayar içeriği
        self.settings_container = ctk.CTkScrollableFrame(content_frame, fg_color="transparent")
        self.settings_container.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Varsayılan olarak Genel ayarları göster
        self.show_category("general")
    
    def create_category_menu(self, parent):
        """Sol taraftaki kategori menüsü"""
        menu_frame = ctk.CTkFrame(parent, fg_color=("gray85", "gray17"), 
                                 corner_radius=10, width=200)
        menu_frame.grid(row=0, column=0, sticky="nsew")
        menu_frame.grid_propagate(False)
        
        ctk.CTkLabel(menu_frame, text="Kategoriler", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)
        
        self.categories = [
            ("general", "🏠 Genel", ["başlangıç", "dil", "tarih", "para birimi"]),
            ("appearance", "🎨 Görünüm", ["tema", "renk", "font", "yazı", "kompakt"]),
            ("data", "📊 Veri & Güncelleme", ["otomatik", "güncelleme", "cache", "önbellek"]),
            ("notifications", "🔔 Bildirimler", ["bildirim", "alarm", "ses", "uyarı"]),
            ("portfolio", "💼 Portföy", ["komisyon", "vergi", "hedef"]),
            ("charts", "📈 Grafikler", ["grafik", "mum", "çizgi", "hacim", "gösterge"]),
            ("backup", "💾 Yedekleme", ["yedek", "backup", "geri yükleme"]),
            ("advanced", "⚡ Gelişmiş", ["api", "cloud", "senkronizasyon", "export", "import"]),
            ("shortcuts", "⌨️ Klavye Kısayolları", ["kısayol", "tuş", "keyboard"]),
            ("security", "🔐 Güvenlik", ["giriş", "şifre", "oturum", "çıkış"]),
            ("about", "ℹ️ Hakkında", ["versiyon", "bilgi", "sistem"])
        ]
        
        for cat_id, cat_name, keywords in self.categories:
            btn = ctk.CTkButton(
                menu_frame,
                text=cat_name,
                command=lambda c=cat_id: self.show_category(c),
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                anchor="w",
                height=40,
                font=ctk.CTkFont(size=14)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.category_buttons[cat_id] = {
                "button": btn,
                "name": cat_name,
                "keywords": keywords
            }
    
    def filter_categories(self):
        """Arama sorgusuna göre kategorileri filtrele"""
        query = self.search_var.get().lower().strip()
        
        if not query:
            # Tüm kategorileri göster
            for cat_data in self.category_buttons.values():
                cat_data["button"].configure(state="normal")
            return
        
        # Kategorileri filtrele
        for cat_id, cat_data in self.category_buttons.items():
            # Kategori adı veya anahtar kelimelerde ara
            name_match = query in cat_data["name"].lower()
            keyword_match = any(query in keyword for keyword in cat_data["keywords"])
            
            if name_match or keyword_match:
                cat_data["button"].configure(state="normal")
            else:
                cat_data["button"].configure(state="disabled")
    
    def show_category(self, category_id):
        """Seçilen kategoriyi göster"""
        self.active_category = category_id
        
        # Kategori butonlarını güncelle
        for cat_id, cat_data in self.category_buttons.items():
            btn = cat_data["button"]
            if cat_id == category_id:
                btn.configure(fg_color=("gray75", "gray25"), 
                            text_color=COLORS["cyan"],
                            font=ctk.CTkFont(size=14, weight="bold"))
            else:
                btn.configure(fg_color="transparent",
                            text_color=("gray10", "gray90"),
                            font=ctk.CTkFont(size=14))
        
        # Container'ı temizle
        for widget in self.settings_container.winfo_children():
            widget.destroy()
        
        # Başlık
        title_map = {
            "general": "🏠 Genel Ayarlar",
            "appearance": "🎨 Görünüm Ayarları",
            "data": "📊 Veri ve Güncelleme",
            "notifications": "🔔 Bildirim Ayarları",
            "portfolio": "💼 Portföy Tercihleri",
            "charts": "📈 Grafik Ayarları",
            "backup": "💾 Yedekleme",
            "advanced": "⚡ Gelişmiş Ayarlar",
            "shortcuts": "⌨️ Klavye Kısayolları",
            "security": "🔐 Güvenlik Ayarları",
            "about": "ℹ️ Uygulama Hakkında"
        }
        
        ctk.CTkLabel(self.settings_container, 
                    text=title_map.get(category_id, "Ayarlar"),
                    font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", pady=(0, 20))
        
        # Kategori içeriğini oluştur
        method_name = f"create_{category_id}_settings"
        if hasattr(self, method_name):
            getattr(self, method_name)()
    
    # ================== KATEGORİ İÇERİKLERİ ==================
    
    def create_general_settings(self):
        """Genel ayarlar"""
        self.create_setting_group("Başlangıç Ayarları")
        
        self.create_combobox_setting(
            "general",
            "Başlangıç Sayfası",
            "start_page",
            ["dashboard", "portfolio", "transactions", "analysis"],
            self.temp_settings.get("start_page", "dashboard"),
            "Uygulama açıldığında gösterilecek sayfa",
            display_values=["📈 Dashboard", "💼 Portföy", "💰 İşlemler", "📊 Analiz"]
        )
        
        self.create_setting_group("Dil ve Bölge")
        
        self.create_combobox_setting(
            "general",
            "Tarih Formatı",
            "date_format",
            ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"],
            self.temp_settings.get("date_format", "DD/MM/YYYY"),
            "Tarihlerin gösterim formatı"
        )
        
        self.create_combobox_setting(
            "general",
            "Para Birimi Formatı",
            "currency_format",
            ["₺", "TRY", "TL"],
            self.temp_settings.get("currency_format", "₺"),
            "Para birimi gösterimi"
        )
    
    def create_appearance_settings(self):
        """Görünüm ayarları"""
        self.create_setting_group("Tema")
        
        theme_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        theme_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(theme_frame, text="Renk Teması:", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        theme_var = ctk.StringVar(value=self.temp_settings.get("tema", "dark"))
        self.settings_widgets["appearance"]["tema"] = SettingWidget(theme_var, "entry")
        
        theme_options = ctk.CTkFrame(theme_frame, fg_color="transparent")
        theme_options.pack(fill="x", pady=(5, 0))
        
        ctk.CTkRadioButton(theme_options, text="🌙 Koyu", variable=theme_var, 
                          value="dark", font=ctk.CTkFont(size=13),
                          command=lambda: self.preview_theme("dark")).pack(side="left", padx=(0, 15))
        
        ctk.CTkRadioButton(theme_options, text="☀️ Açık", variable=theme_var, 
                          value="light", font=ctk.CTkFont(size=13),
                          command=lambda: self.preview_theme("light")).pack(side="left")
        
        self.create_setting_group("Yazı Boyutu")
        
        self.create_combobox_setting(
            "appearance",
            "Font Boyutu",
            "font_size",
            ["small", "normal", "large", "xlarge"],
            self.temp_settings.get("font_size", "normal"),
            "Arayüzdeki yazı boyutu (Yeniden başlatma gerekli)",
            display_values=["Küçük", "Normal", "Büyük", "Çok Büyük"]
        )
        
        self.create_setting_group("Diğer Görünüm Seçenekleri")
        
        self.create_switch_setting(
            "appearance",
            "Kompakt Mod",
            "compact_mode",
            self.temp_settings.get("compact_mode", False),
            "Daha az boşluk, daha fazla veri (Yeniden başlatma gerekli)"
        )
    
    def create_data_settings(self):
        """Veri ve güncelleme ayarları"""
        self.create_setting_group("Otomatik Güncelleme")
        
        self.create_switch_setting(
            "data",
            "Otomatik Fiyat Güncelleme",
            "otomatik_guncelleme",
            self.temp_settings.get("otomatik_guncelleme", True),
            "Fiyatları otomatik olarak güncelle"
        )
        
        self.create_combobox_setting(
            "data",
            "Güncelleme Sıklığı",
            "guncelleme_suresi",
            [1, 5, 15, 30, 60],
            self.temp_settings.get("guncelleme_suresi", 5),
            "Fiyatlar ne sıklıkla güncellensin (dakika)",
            display_values=["1 Dakika", "5 Dakika", "15 Dakika", "30 Dakika", "1 Saat"]
        )
        
        self.create_switch_setting(
            "data",
            "Piyasa Saatleri Dışında Güncelleme",
            "update_after_hours",
            self.temp_settings.get("update_after_hours", False),
            "Piyasa kapandıktan sonra da güncelle"
        )
        
        self.create_setting_group("Performans")
        
        cache_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        cache_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(cache_frame, text="🗑️ Önbelleği Temizle",
                     command=self.clear_cache, width=200, height=40).pack(anchor="w")
        
        # Cache boyutu göster
        cache_size = self._get_cache_size()
        if cache_size > 0:
            size_mb = cache_size / (1024 * 1024)
            ctk.CTkLabel(cache_frame, 
                        text=f"Mevcut önbellek boyutu: {size_mb:.2f} MB",
                        font=ctk.CTkFont(size=11),
                        text_color=("gray50", "gray70")).pack(anchor="w", pady=(5, 0))
    
    def create_notifications_settings(self):
        """Bildirim ayarları"""
        self.create_setting_group("Genel Bildirimler")
        
        self.create_switch_setting(
            "notifications",
            "Bildirimleri Etkinleştir",
            "notifications_enabled",
            self.temp_settings.get("notifications_enabled", True),
            "Tüm bildirimleri aç/kapat"
        )
        
        self.create_switch_setting(
            "notifications",
            "Sesli Uyarılar",
            "sound_alerts",
            self.temp_settings.get("sound_alerts", True),
            "Bildirimler için ses çal"
        )
        
        self.create_setting_group("Fiyat Alarmları")
        
        self.create_entry_setting(
            "notifications",
            "Değişim Eşiği (%)",
            "price_change_threshold",
            str(self.temp_settings.get("price_change_threshold", 5)),
            "Bu değerin üzerindeki değişimlerde bildir"
        )
        
        self.create_setting_group("Portföy Uyarıları")
        
        self.create_entry_setting(
            "notifications",
            "Günlük Değişim Eşiği (%)",
            "daily_change_threshold",
            str(self.temp_settings.get("daily_change_threshold", 3)),
            "Portföy bu kadar değiştiğinde bildir"
        )
    
    def create_portfolio_settings(self):
        """Portföy tercihleri"""
        self.create_setting_group("Varsayılan Değerler")
        
        # Komisyon Oranı - ONBİNDE FORMATI
        commission_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        commission_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(commission_frame, text="Komisyon Oranı", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        ctk.CTkLabel(commission_frame, 
                    text="Onbinde/Binde cinsinden girin. Örnek: 0.0004 (onbinde 4) veya 0.001 (binde 1)", 
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack(anchor="w", pady=(0, 5))
        
        # Mevcut değeri al ve formatla
        current_commission = self.temp_settings.get("commission_rate", 0.0004)
        formatted_commission = format_rate(current_commission)
        
        commission_var = ctk.StringVar(value=formatted_commission)
        commission_entry = ctk.CTkEntry(commission_frame, textvariable=commission_var, width=200)
        commission_entry.pack(anchor="w")
        
        format_label = ctk.CTkLabel(commission_frame, text="", 
                                    font=ctk.CTkFont(size=11),
                                    text_color=COLORS["cyan"])
        format_label.pack(anchor="w", pady=(3, 0))
        
        def update_commission_preview(*args):
            """Girilen değerin önizlemesini göster"""
            try:
                val = commission_var.get().replace(',', '.').strip()
                rate = float(val)
                
                if not 0 <= rate <= 1:
                    format_label.configure(
                        text="⚠ Oran 0-1 arasında olmalı (örn: 0.0004)", 
                        text_color=COLORS["warning"]
                    )
                    return
                
                # Onbinde ve binde hesapla
                onbinde = rate * 10000
                binde = rate * 1000
                yuzde = rate * 100
                
                if rate >= 0.001:  # Binde 1 veya daha büyük
                    info_text = f"✓ Binde {binde:.2f} | Yüzde {yuzde:.3f}"
                else:  # Onbinde göster
                    info_text = f"✓ Onbinde {onbinde:.2f} | Binde {binde:.3f}"
                
                # Örnek hesaplama göster
                ornek_fiyat = 100
                ornek_komisyon = ornek_fiyat * rate
                info_text += f" | Örnek: {ornek_fiyat}₺'lik işlemde {ornek_komisyon:.4f}₺ komisyon"
                
                format_label.configure(text=info_text, text_color=COLORS["success"])
                
            except:
                format_label.configure(
                    text="⚠ Geçersiz format (örn: 0.0004)", 
                    text_color=COLORS["warning"]
                )
        
        commission_var.trace("w", update_commission_preview)
        update_commission_preview()
        
        self.settings_widgets["portfolio"]["commission_rate"] = SettingWidget(
            commission_var, "rate"
        )
        
        # Vergi Oranı - ONBİNDE FORMATI
        tax_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        tax_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(tax_frame, text="Vergi Oranı (Stopaj)", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        ctk.CTkLabel(tax_frame, 
                    text="Onbinde/Binde cinsinden girin. Örnek: 0.001 (binde 1) veya 0.015 (yüzde 1.5)", 
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack(anchor="w", pady=(0, 5))
        
        current_tax = self.temp_settings.get("tax_rate", 0)
        formatted_tax = format_rate(current_tax)
        
        tax_var = ctk.StringVar(value=formatted_tax)
        tax_entry = ctk.CTkEntry(tax_frame, textvariable=tax_var, width=200)
        tax_entry.pack(anchor="w")
        
        tax_format_label = ctk.CTkLabel(tax_frame, text="", 
                                        font=ctk.CTkFont(size=11),
                                        text_color=COLORS["cyan"])
        tax_format_label.pack(anchor="w", pady=(3, 0))
        
        def update_tax_preview(*args):
            """Vergi oranı önizlemesi"""
            try:
                val = tax_var.get().replace(',', '.').strip()
                rate = float(val)
                
                if not 0 <= rate <= 1:
                    tax_format_label.configure(
                        text="⚠ Oran 0-1 arasında olmalı (örn: 0.001)", 
                        text_color=COLORS["warning"]
                    )
                    return
                
                binde = rate * 1000
                yuzde = rate * 100
                
                if rate >= 0.01:  # Yüzde 1 veya daha büyük
                    info_text = f"✓ Yüzde {yuzde:.2f} | Binde {binde:.1f}"
                else:
                    info_text = f"✓ Binde {binde:.2f} | Yüzde {yuzde:.3f}"
                
                # Örnek hesaplama
                ornek_kar = 1000
                ornek_vergi = ornek_kar * rate
                info_text += f" | Örnek: {ornek_kar}₺ karda {ornek_vergi:.2f}₺ vergi"
                
                tax_format_label.configure(text=info_text, text_color=COLORS["success"])
                
            except:
                tax_format_label.configure(
                    text="⚠ Geçersiz format (örn: 0.001)", 
                    text_color=COLORS["warning"]
                )
        
        tax_var.trace("w", update_tax_preview)
        update_tax_preview()
        
        self.settings_widgets["portfolio"]["tax_rate"] = SettingWidget(
            tax_var, "rate"
        )
        
        # Portföy Hedefi
        self.create_entry_setting(
            "portfolio",
            "Portföy Hedefi (₺)",
            "portfolio_target",
            str(self.temp_settings.get("portfolio_target", 100000)),
            "Hedeflenen portföy değeri"
        )
    
    def create_charts_settings(self):
        """Grafik ayarları"""
        self.create_setting_group("Varsayılan Grafik Türü")
        
        self.create_combobox_setting(
            "charts",
            "Grafik Türü",
            "default_chart_type",
            ["line", "candle", "ohlc", "area"],
            self.temp_settings.get("default_chart_type", "line"),
            "Varsayılan grafik görünümü",
            display_values=["Çizgi Grafiği", "Mum Grafiği", "OHLC Grafiği", "Alan Grafiği"]
        )
        
        self.create_combobox_setting(
            "charts",
            "Zaman Aralığı",
            "default_time_range",
            ["1mo", "3mo", "6mo", "1y", "5y", "max"],
            self.temp_settings.get("default_time_range", "1y"),
            "Varsayılan zaman aralığı",
            display_values=["1 Ay", "3 Ay", "6 Ay", "1 Yıl", "5 Yıl", "Tümü"]
        )
        
        self.create_setting_group("Göstergeler")
        
        self.create_switch_setting(
            "charts",
            "SMA (Basit Hareketli Ortalama)",
            "show_sma",
            self.temp_settings.get("show_sma", True),
            "SMA çizgilerini göster"
        )
        
        self.create_switch_setting(
            "charts",
            "Hacim Grafiği",
            "show_volume",
            self.temp_settings.get("show_volume", True),
            "İşlem hacmi grafiğini göster"
        )
    
    def create_backup_settings(self):
        """Yedekleme ayarları"""
        self.create_setting_group("Otomatik Yedekleme")
        
        self.create_switch_setting(
            "backup",
            "Otomatik Yedekleme",
            "auto_backup",
            self.temp_settings.get("auto_backup", True),
            "Düzenli aralıklarla otomatik yedek al"
        )
        
        self.create_combobox_setting(
            "backup",
            "Yedekleme Sıklığı",
            "backup_frequency",
            ["daily", "weekly", "monthly"],
            self.temp_settings.get("backup_frequency", "weekly"),
            "Yedekleme aralığı",
            display_values=["Günlük", "Haftalık", "Aylık"]
        )
        
        # Yedekleme Konumu
        location_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        location_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(location_frame, text="Yedekleme Konumu:", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        location_entry_frame = ctk.CTkFrame(location_frame, fg_color="transparent")
        location_entry_frame.pack(fill="x", pady=(5, 0))
        
        current_location = self.temp_settings.get("backup_location", "")
        if not current_location:
            current_location = os.path.join(os.getcwd(), "backups")
        
        location_var = ctk.StringVar(value=current_location)
        location_entry = ctk.CTkEntry(location_entry_frame, textvariable=location_var, width=400)
        location_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(location_entry_frame, text="📁 Seç", width=80, 
                     command=lambda: self.select_backup_location(location_var)).pack(side="left")
        
        self.settings_widgets["backup"]["backup_location"] = SettingWidget(location_var, "entry")
        
        self.create_setting_group("Manuel İşlemler")
        
        backup_buttons = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        backup_buttons.pack(fill="x", pady=10)
        
        ctk.CTkButton(backup_buttons, text="💾 Şimdi Yedekle",
                     command=self.backup_now, width=180, height=40,
                     fg_color=COLORS["success"]).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(backup_buttons, text="📥 Yedeği Geri Yükle",
                     command=self.restore_backup, width=180, height=40,
                     fg_color=COLORS["primary"]).pack(side="left")
        
        self.create_setting_group("Yedek Geçmişi")
        
        self.create_backup_history_list()
    
    def create_backup_history_list(self):
        """Yedek geçmişi listesi"""
        history_frame = ctk.CTkFrame(self.settings_container, 
                                    fg_color=("gray90", "gray13"), 
                                    corner_radius=10)
        history_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(history_frame, text="Son Yedekler", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        try:
            backups = self.backup_manager.get_backup_list()
        except:
            backups = []
        
        if not backups:
            ctk.CTkLabel(history_frame, text="Henüz yedek bulunamadı",
                        text_color="gray").pack(pady=20)
        else:
            for backup in backups[:5]:
                backup_row = ctk.CTkFrame(history_frame, fg_color=("gray85", "gray17"), corner_radius=6)
                backup_row.pack(fill="x", padx=15, pady=3)
                
                content = ctk.CTkFrame(backup_row, fg_color="transparent")
                content.pack(fill="x", padx=10, pady=8)
                
                name_label = ctk.CTkLabel(content, text=backup.get("name", "backup"), 
                                         font=ctk.CTkFont(size=12, weight="bold"))
                name_label.pack(side="left")
                
                if "created" in backup:
                    date_str = backup["created"].strftime("%d/%m/%Y %H:%M")
                    date_label = ctk.CTkLabel(content, text=date_str, 
                                             font=ctk.CTkFont(size=11),
                                             text_color=("gray50", "gray70"))
                    date_label.pack(side="left", padx=10)
                
                if "size" in backup:
                    size_mb = backup["size"] / (1024 * 1024)
                    size_label = ctk.CTkLabel(content, text=f"{size_mb:.2f} MB", 
                                             font=ctk.CTkFont(size=11))
                    size_label.pack(side="right")
                
                if "path" in backup:
                    restore_btn = ctk.CTkButton(content, text="↺", width=30, height=24,
                                              command=lambda p=backup["path"]: self.restore_specific_backup(p))
                    restore_btn.pack(side="right", padx=(0, 10))
    
    def create_advanced_settings(self):
        """Gelişmiş ayarlar"""
        # API Sağlayıcı Seçimi
        self.create_setting_group("API Sağlayıcı Seçimi")
        
        self.create_combobox_setting(
            "advanced",
            "Tercih Edilen API Sağlayıcısı",
            "api_provider",
            ["yfinance", "iex_cloud", "finnhub", "alpha_vantage"],
            self.temp_settings.get("api_provider", "yfinance"),
            "Fiyat verilerini hangi kaynaktan al",
            display_values=["Yahoo Finance (Ücretsiz)", "IEX Cloud", "Finnhub", "Alpha Vantage"]
        )
        
        # API Anahtarları
        self.create_setting_group("API Anahtarları")
        
        api_info_frame = ctk.CTkFrame(self.settings_container, 
                                     fg_color=("gray90", "gray13"), 
                                     corner_radius=10)
        api_info_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(api_info_frame, 
                    text="ℹ️ API anahtarları şifrelenmiş olarak saklanır",
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack(padx=15, pady=10)
        
        # IEX Cloud
        self.create_entry_setting(
            "advanced",
            "IEX Cloud API Anahtarı",
            "iex_cloud_api_key",
            self._get_decrypted_api_key("iex_cloud_api_key"),
            "IEX Cloud API servisine erişim anahtarı",
            sensitive=True,
            widget_type="api_key"
        )
        
        # Finnhub
        self.create_entry_setting(
            "advanced",
            "Finnhub API Anahtarı",
            "finnhub_api_key",
            self._get_decrypted_api_key("finnhub_api_key"),
            "Finnhub API anahtarı",
            sensitive=True,
            widget_type="api_key"
        )
        
        # Alpha Vantage
        self.create_entry_setting(
            "advanced",
            "Alpha Vantage API Anahtarı",
            "alpha_vantage_api_key",
            self._get_decrypted_api_key("alpha_vantage_api_key"),
            "Alpha Vantage API anahtarı",
            sensitive=True,
            widget_type="api_key"
        )
        
        # API Doğrulama
        self.create_setting_group("API Doğrulama")
        
        validation_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        validation_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(validation_frame, text="API Anahtarlarını Test Et", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        ctk.CTkLabel(validation_frame, 
                    text="Girilen API anahtarlarının geçerli olup olmadığını kontrol edin", 
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack(anchor="w", pady=(0, 10))
        
        btn_frame = ctk.CTkFrame(validation_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(btn_frame, text="✓ Tüm API'leri Test Et",
                     command=self.validate_all_apis, width=200, height=40,
                     fg_color=COLORS["success"]).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(btn_frame, text="🔄 Seçili API'yi Test Et",
                     command=self.validate_selected_api, width=200, height=40,
                     fg_color=COLORS["primary"]).pack(side="left")
        
        # API Status Dashboard
        if self.api_manager:
            self.create_api_status_dashboard()
        
        # Cloud Sync Ayarları
        self.create_setting_group("Bulut Senkronizasyonu")
        
        cloud_info = ctk.CTkFrame(self.settings_container, 
                                 fg_color=("gray90", "gray13"), 
                                 corner_radius=10)
        cloud_info.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(cloud_info, 
                    text="ℹ️ Cloud Sync özelliği yakında kullanıma sunulacak",
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack(padx=15, pady=10)
        
        self.create_switch_setting(
            "advanced",
            "Cloud Sync Etkinleştir (Yakında)",
            "cloud_sync_enabled",
            False,
            "Portföy verilerinizi bulutla senkronize et"
        )
        
        # Veri Yönetimi
        self.create_setting_group("Veri Yönetimi")
        
        data_buttons = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        data_buttons.pack(fill="x", pady=10)
        
        ctk.CTkButton(data_buttons, text="📤 Tüm Veriyi Dışa Aktar",
                     command=self.export_data, width=180, height=40).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(data_buttons, text="📥 Veriyi İçe Aktar",
                     command=self.import_data, width=180, height=40).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(data_buttons, text="🗑️ Tüm Verileri Sil",
                     command=self.clear_all_data, width=180, height=40,
                     fg_color=COLORS["danger"]).pack(side="left")
        
        self.create_setting_group("Ayar Yönetimi")
        
        settings_buttons = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        settings_buttons.pack(fill="x", pady=10)
        
        ctk.CTkButton(settings_buttons, text="📤 Ayarları Dışa Aktar",
                     command=self.export_settings, width=180, height=40).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(settings_buttons, text="📥 Ayarları İçe Aktar",
                     command=self.import_settings, width=180, height=40).pack(side="left")
    
    def create_api_status_dashboard(self):
        """API durumlarını gösteren dashboard"""
        self.create_setting_group("API Durum Göstergesi")
        
        status_frame = ctk.CTkFrame(self.settings_container, 
                                   fg_color=("gray90", "gray13"), 
                                   corner_radius=10)
        status_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(status_frame, text="API Durumları", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        apis = [
            ("yfinance", "Yahoo Finance", "Ücretsiz, sınırsız"),
            ("iex_cloud", "IEX Cloud", "Ücretli, 50k/ay ücretsiz"),
            ("finnhub", "Finnhub", "Ücretli, 60 call/dk ücretsiz"),
            ("alpha_vantage", "Alpha Vantage", "Ücretli, 5 call/dk ücretsiz")
        ]
        
        for api_id, api_name, api_info in apis:
            row = ctk.CTkFrame(status_frame, fg_color=("gray85", "gray17"), corner_radius=6)
            row.pack(fill="x", padx=15, pady=3)
            
            content = ctk.CTkFrame(row, fg_color="transparent")
            content.pack(fill="x", padx=10, pady=8)
            
            # İsim
            name_label = ctk.CTkLabel(content, text=api_name, 
                                     font=ctk.CTkFont(size=12, weight="bold"))
            name_label.pack(side="left")
            
            # Info
            info_label = ctk.CTkLabel(content, text=api_info, 
                                     font=ctk.CTkFont(size=10),
                                     text_color=("gray50", "gray70"))
            info_label.pack(side="left", padx=10)
            
            # Status indicator
            status_label = ctk.CTkLabel(content, text="●", 
                                       text_color="gray",
                                       font=ctk.CTkFont(size=16))
            status_label.pack(side="right")
            
            # Test button
            test_btn = ctk.CTkButton(content, text="Test", width=60, height=24,
                                   command=lambda aid=api_id, sl=status_label: self._test_and_update_status(aid, sl))
            test_btn.pack(side="right", padx=5)
            
            self.api_status_labels[api_id] = status_label
    
    def create_shortcuts_settings(self):
        """Klavye kısayolları ayarları"""
        
        # Bilgi
        info_frame = ctk.CTkFrame(self.settings_container, 
                                 fg_color=("gray85", "gray17"), 
                                 corner_radius=10)
        info_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(info_frame, 
                    text="ℹ️ Klavye kısayollarını özelleştirin. Değişiklikleri kaydetmeyi unutmayın.",
                    font=ctk.CTkFont(size=12),
                    text_color=("gray50", "gray70")).pack(padx=15, pady=12)
        
        # Varsayılan kısayollar
        default_shortcuts = {
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
        }
        
        # Mevcut ayarları al
        current_shortcuts = self.temp_settings.get("keyboard_shortcuts", default_shortcuts.copy())
        
        # Kısayol tanımları
        shortcut_definitions = [
            ("Genel İşlemler", [
                ("new_stock", "Yeni Hisse Ekle", "Control-n"),
                ("backup", "Yedek Al", "Control-s"),
                ("search", "Ara (Portföyde)", "Control-f"),
                ("refresh_prices", "Fiyatları Güncelle", "Control-r"),
                ("refresh_page", "Sayfayı Yenile", "F5"),
                ("help", "Yardım", "F1"),
                ("escape", "İptal/Kapat", "Escape"),
                ("quit_app", "Çıkış", "Control-q"),
            ]),
            ("Sayfa Geçişleri", [
                ("page_dashboard", "Dashboard", "Control-Key-1"),
                ("page_portfolio", "Portföy", "Control-Key-2"),
                ("page_transactions", "İşlemler", "Control-Key-3"),
                ("page_settings", "Ayarlar", "Control-Key-4"),
            ])
        ]
        
        for category, shortcuts in shortcut_definitions:
            self.create_setting_group(category)
            
            for key, label, default_key in shortcuts:
                self.create_shortcut_setting(key, label, 
                                            current_shortcuts.get(key, default_key))
        
        # Sıfırla butonu
        reset_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        reset_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(reset_frame, 
                     text="🔄 Varsayılana Sıfırla", 
                     command=self.reset_shortcuts,
                     width=200, height=40,
                     fg_color=COLORS["warning"]).pack(anchor="w")
        
        # Yardım
        help_frame = ctk.CTkFrame(self.settings_container, 
                                 fg_color=("gray85", "gray17"), 
                                 corner_radius=10)
        help_frame.pack(fill="x", pady=(20, 0))
        
        help_content = ctk.CTkFrame(help_frame, fg_color="transparent")
        help_content.pack(fill="x", padx=15, pady=12)
        
        ctk.CTkLabel(help_content, 
                    text="💡 İpucu: Kısayol değiştirmek için 'Değiştir' butonuna tıklayın ve yeni tuş kombinasyonuna basın.",
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70"),
                    wraplength=600,
                    justify="left").pack(anchor="w")
    
    def create_shortcut_setting(self, key, label, current_value):
        """Kısayol ayar satırı"""
        frame = ctk.CTkFrame(self.settings_container, 
                            fg_color=("gray90", "gray13"), 
                            corner_radius=8)
        frame.pack(fill="x", pady=5)
        
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)
        
        # Label
        ctk.CTkLabel(content, text=label, 
                    font=ctk.CTkFont(size=13),
                    anchor="w",
                    width=200).pack(side="left")
        
        # Mevcut kısayol gösterimi
        display_value = self._format_shortcut_display(current_value)
        shortcut_var = ctk.StringVar(value=display_value)
        
        # Gerçek değeri saklayan gizli variable
        real_value_var = ctk.StringVar(value=current_value)
        
        shortcut_display = ctk.CTkLabel(content, 
                                       textvariable=shortcut_var,
                                       font=ctk.CTkFont(size=13, family="Consolas", weight="bold"),
                                       text_color=COLORS["cyan"],
                                       width=150)
        shortcut_display.pack(side="left", padx=20)
        
        # Değiştir butonu
        def change_shortcut():
            self.edit_shortcut_dialog(key, label, shortcut_var, real_value_var)
        
        ctk.CTkButton(content, text="✏️ Değiştir", 
                     command=change_shortcut,
                     width=100, height=32).pack(side="right")
        
        # Gerçek değeri sakla
        self.settings_widgets["shortcuts"][key] = SettingWidget(real_value_var, "entry")
    
    def _format_shortcut_display(self, shortcut):
        """Kısayolu güzel formatta göster"""
        if not shortcut:
            return "Atanmamış"
        
        # Control-n -> Ctrl+N
        shortcut = shortcut.replace("Control-", "Ctrl+")
        shortcut = shortcut.replace("Shift-", "Shift+")
        shortcut = shortcut.replace("Alt-", "Alt+")
        shortcut = shortcut.replace("Key-", "")
        
        # Son karakteri büyük yap
        parts = shortcut.split('+')
        if len(parts) > 1:
            parts[-1] = parts[-1].upper()
            return '+'.join(parts)
        
        return shortcut.upper()
    
    def edit_shortcut_dialog(self, key, label, display_var, real_var):
        """Kısayol düzenleme dialogu"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"Kısayol Değiştir: {label}")
        dialog.geometry("450x320")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Ortala
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (225)
        y = (dialog.winfo_screenheight() // 2) - (160)
        dialog.geometry(f"+{x}+{y}")
        
        main = ctk.CTkFrame(dialog, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(main, text=f"🎹 {label}",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 10))
        
        ctk.CTkLabel(main, text="Yeni kısayol ataması",
                    font=ctk.CTkFont(size=13),
                    text_color=("gray50", "gray70")).pack(pady=(0, 20))
        
        # Bilgi
        info = ctk.CTkFrame(main, fg_color=("gray85", "gray17"), corner_radius=8)
        info.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(info, 
                    text="Aşağıdaki alana tıklayın ve\nyeni tuş kombinasyonuna basın",
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack(padx=15, pady=12)
        
        # Kısayol yakalama alanı
        capture_frame = ctk.CTkFrame(main, fg_color=("gray90", "gray20"), 
                                    corner_radius=10, height=80)
        capture_frame.pack(fill="x", pady=(0, 20))
        capture_frame.pack_propagate(False)
        
        captured_key_display = ctk.StringVar(value="Bir tuşa basın...")
        key_label = ctk.CTkLabel(capture_frame, 
                                textvariable=captured_key_display,
                                font=ctk.CTkFont(size=16, family="Consolas", weight="bold"),
                                text_color=COLORS["primary"])
        key_label.pack(expand=True)
        
        new_shortcut = [None]  # Gerçek değer
        
        def on_key_press(event):
            """Tuş basımını yakala"""
            modifiers = []
            
            if event.state & 0x4:  # Control
                modifiers.append("Control")
            if event.state & 0x1:  # Shift
                modifiers.append("Shift")
            if event.state & 0x20000:  # Alt
                modifiers.append("Alt")
            
            # Tuş adını al
            key_name = event.keysym
            
            # Özel tuşlar - sadece modifier ise atla
            if key_name in ["Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"]:
                return
            
            # Sayı tuşları için özel format
            if key_name.isdigit():
                key_name = f"Key-{key_name}"
            
            # Kısayolu oluştur (Tkinter formatında)
            if modifiers:
                shortcut_real = "-".join(modifiers) + "-" + key_name
            else:
                shortcut_real = key_name
            
            new_shortcut[0] = shortcut_real
            captured_key_display.set(self._format_shortcut_display(shortcut_real))
        
        # Bind
        dialog.bind("<KeyPress>", on_key_press)
        capture_frame.bind("<Button-1>", lambda e: dialog.focus_set())
        
        # Butonlar
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        def save_shortcut():
            if new_shortcut[0]:
                # Çakışma kontrolü
                conflict = self._check_shortcut_conflict(key, new_shortcut[0])
                if conflict:
                    if not askyesno("Uyarı", 
                                   f"Bu kısayol '{conflict}' için zaten kullanılıyor.\n\n"
                                   f"Değiştirmek ister misiniz?"):
                        return
                
                # Gösterim değerini güncelle
                display_var.set(self._format_shortcut_display(new_shortcut[0]))
                
                # Gerçek değeri güncelle
                real_var.set(new_shortcut[0])
                
                showinfo("Başarılı", 
                        f"✅ Kısayol atandı!\n\n"
                        f"{self._format_shortcut_display(new_shortcut[0])}\n\n"
                        f"💡 Değişiklikleri kaydetmeyi unutmayın!")
                dialog.destroy()
            else:
                showerror("Hata", "Lütfen bir tuşa basın!")
        
        ctk.CTkButton(btn_frame, text="💾 Kaydet", command=save_shortcut,
                     height=40).pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        ctk.CTkButton(btn_frame, text="❌ İptal", command=dialog.destroy,
                     height=40, fg_color=("gray60", "gray40")).pack(side="left", expand=True, fill="x", padx=(5, 0))
    
    def _check_shortcut_conflict(self, current_key, new_shortcut):
        """Kısayol çakışması kontrolü"""
        if "shortcuts" not in self.settings_widgets:
            return None
        
        for key, widget in self.settings_widgets["shortcuts"].items():
            if key != current_key:
                if widget.var.get() == new_shortcut:
                    # Açıklama bul
                    labels = {
                        "new_stock": "Yeni Hisse Ekle",
                        "backup": "Yedek Al",
                        "search": "Ara",
                        "refresh_prices": "Fiyatları Güncelle",
                        "refresh_page": "Sayfayı Yenile",
                        "help": "Yardım",
                        "escape": "İptal/Kapat",
                        "quit_app": "Çıkış",
                        "page_dashboard": "Dashboard",
                        "page_portfolio": "Portföy",
                        "page_transactions": "İşlemler",
                        "page_settings": "Ayarlar"
                    }
                    return labels.get(key, key)
        return None
    
    def reset_shortcuts(self):
        """Kısayolları varsayılana sıfırla"""
        if askyesno("Onay", "Tüm klavye kısayollarını varsayılan değerlere sıfırlamak istiyor musunuz?"):
            # Varsayılan değerler
            default_shortcuts = {
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
            }
            
            # Temp ayarları güncelle
            self.temp_settings["keyboard_shortcuts"] = default_shortcuts
            
            showinfo("Başarılı", 
                    "✅ Klavye kısayolları varsayılan değerlere sıfırlandı!\n\n"
                    "💡 Değişiklikleri uygulamak için 'Kaydet' butonuna basın.")
            
            # Sayfayı yenile
            self.show_category("shortcuts")
     
    
    def create_security_settings(self):
        """Güvenlik ayarları"""
        self.create_setting_group("Giriş Bilgileri")
        
        if self.credentials_manager and self.credentials_manager.has_saved_credentials():
            info_frame = ctk.CTkFrame(self.settings_container, 
                                     fg_color=("gray90", "gray13"), 
                                     corner_radius=10)
            info_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(info_frame, text="💾 Kaydedilmiş Giriş Bilgileri", 
                        font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
            
            ctk.CTkLabel(info_frame, text="Giriş bilgileriniz şifrelenmiş olarak saklanıyor.", 
                        font=ctk.CTkFont(size=11),
                        text_color=("gray50", "gray70")).pack(anchor="w", padx=15, pady=(0, 10))
            
            button_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            button_frame.pack(fill="x", padx=15, pady=(0, 15))
            
            ctk.CTkButton(button_frame, text="🗑️ Kaydedilmiş Bilgileri Sil",
                         command=self.clear_saved_credentials, 
                         width=200, height=40,
                         fg_color=COLORS["danger"]).pack(side="left", padx=(0, 10))
            
            ctk.CTkButton(button_frame, text="🔄 Yeniden Giriş Yap",
                         command=self.logout, 
                         width=200, height=40,
                         fg_color=COLORS["warning"]).pack(side="left")
        else:
            ctk.CTkLabel(self.settings_container, text="Henüz hiçbir giriş bilgisi kaydedilmemiş.", 
                        text_color=("gray50", "gray70"),
                        font=ctk.CTkFont(size=12)).pack(anchor="w", pady=10)
            
            ctk.CTkButton(self.settings_container, text="🔄 Yeniden Giriş Yap",
                         command=self.logout, 
                         width=200, height=40,
                         fg_color=COLORS["warning"]).pack(anchor="w", pady=10)
        
        self.create_setting_group("Oturum")
        
        logout_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        logout_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(logout_frame, text="🚪 Çıkış Yap",
                     command=self.logout, 
                     width=200, height=45,
                     fg_color=COLORS["danger"],
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
    
    def create_shortcuts_settings(self):
        """Klavye kısayolları ayarları"""
        
        # Bilgi
        info_frame = ctk.CTkFrame(self.settings_container, 
                                 fg_color=("gray85", "gray17"), 
                                 corner_radius=10)
        info_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(info_frame, 
                    text="ℹ️ Klavye kısayollarını özelleştirin. Değişiklikler hemen etkili olur.",
                    font=ctk.CTkFont(size=12),
                    text_color=("gray50", "gray70")).pack(padx=15, pady=12)
        
        # Varsayılan kısayollar
        default_shortcuts = {
            "new_stock": "Control-n",
            "backup": "Control-s",
            "search": "Control-f",
            "refresh_prices": "Control-r",
            "refresh_page": "F5",
            "quit_app": "Control-q",
            "page_dashboard": "Control-1",
            "page_portfolio": "Control-2",
            "page_transactions": "Control-3",
            "page_settings": "Control-4",
            "help": "F1",
            "escape": "Escape"
        }
        
        # Mevcut ayarları al
        current_shortcuts = self.temp_settings.get("keyboard_shortcuts", default_shortcuts.copy())
        
        # Kısayol tanımları
        shortcut_definitions = [
            ("Genel İşlemler", [
                ("new_stock", "Yeni Hisse Ekle", "Control-n"),
                ("backup", "Yedek Al", "Control-s"),
                ("search", "Ara", "Control-f"),
                ("refresh_prices", "Fiyatları Güncelle", "Control-r"),
                ("refresh_page", "Sayfayı Yenile", "F5"),
                ("help", "Yardım", "F1"),
                ("escape", "İptal/Kapat", "Escape"),
                ("quit_app", "Çıkış", "Control-q"),
            ]),
            ("Sayfa Geçişleri", [
                ("page_dashboard", "Dashboard", "Control-1"),
                ("page_portfolio", "Portföy", "Control-2"),
                ("page_transactions", "İşlemler", "Control-3"),
                ("page_settings", "Ayarlar", "Control-4"),
            ])
        ]
        
        for category, shortcuts in shortcut_definitions:
            self.create_setting_group(category)
            
            for key, label, default_key in shortcuts:
                self.create_shortcut_setting(key, label, 
                                            current_shortcuts.get(key, default_key))
        
        # Sıfırla butonu
        reset_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        reset_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(reset_frame, 
                     text="🔄 Varsayılana Sıfırla", 
                     command=self.reset_shortcuts,
                     width=200, height=40,
                     fg_color=COLORS["warning"]).pack(anchor="w")
    
    def create_shortcut_setting(self, key, label, current_value):
        """Kısayol ayar satırı"""
        frame = ctk.CTkFrame(self.settings_container, 
                            fg_color=("gray90", "gray13"), 
                            corner_radius=8)
        frame.pack(fill="x", pady=5)
        
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)
        
        # Label
        ctk.CTkLabel(content, text=label, 
                    font=ctk.CTkFont(size=13),
                    anchor="w",
                    width=200).pack(side="left")
        
        # Mevcut kısayol gösterimi
        shortcut_var = ctk.StringVar(value=self._format_shortcut_display(current_value))
        
        shortcut_display = ctk.CTkLabel(content, 
                                       textvariable=shortcut_var,
                                       font=ctk.CTkFont(size=12, family="Consolas", weight="bold"),
                                       text_color=COLORS["cyan"],
                                       width=150)
        shortcut_display.pack(side="left", padx=20)
        
        # Değiştir butonu
        def change_shortcut():
            self.edit_shortcut_dialog(key, label, shortcut_var)
        
        ctk.CTkButton(content, text="✏️ Değiştir", 
                     command=change_shortcut,
                     width=100, height=32).pack(side="right")
        
        # Widget'ı kaydet
        self.settings_widgets["shortcuts"][key] = SettingWidget(
            shortcut_var, "entry"
        )
    
    def _format_shortcut_display(self, shortcut):
        """Kısayolu güzel formatta göster"""
        if not shortcut:
            return "Atanmamış"
        
        # Control-n -> Ctrl+N
        shortcut = shortcut.replace("Control-", "Ctrl+")
        shortcut = shortcut.replace("Shift-", "Shift+")
        shortcut = shortcut.replace("Alt-", "Alt+")
        
        # Son karakteri büyük yap
        parts = shortcut.split('+')
        if len(parts) > 1:
            parts[-1] = parts[-1].upper()
            return '+'.join(parts)
        
        return shortcut.upper()
    
    def edit_shortcut_dialog(self, key, label, shortcut_var):
        """Kısayol düzenleme dialogu"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"Kısayol Değiştir: {label}")
        dialog.geometry("450x300")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Ortala
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (225)
        y = (dialog.winfo_screenheight() // 2) - (150)
        dialog.geometry(f"+{x}+{y}")
        
        main = ctk.CTkFrame(dialog, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=30, pady=30)
        
        ctk.CTkLabel(main, text=f"🎹 {label} için yeni kısayol",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 20))
        
        # Bilgi
        info = ctk.CTkFrame(main, fg_color=("gray85", "gray17"), corner_radius=8)
        info.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(info, 
                    text="Aşağıdaki alana tıklayın ve yeni tuş kombinasyonuna basın.\n"
                         "Örnek: Ctrl+Shift+A, F2, Alt+X",
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack(padx=15, pady=12)
        
        # Kısayol yakalama alanı
        capture_frame = ctk.CTkFrame(main, fg_color=("gray90", "gray20"), 
                                    corner_radius=10, height=80)
        capture_frame.pack(fill="x", pady=(0, 20))
        capture_frame.pack_propagate(False)
        
        captured_key = ctk.StringVar(value="Bir tuşa basın...")
        key_label = ctk.CTkLabel(capture_frame, 
                                textvariable=captured_key,
                                font=ctk.CTkFont(size=16, family="Consolas", weight="bold"),
                                text_color=COLORS["primary"])
        key_label.pack(expand=True)
        
        new_shortcut = [None]  # List to store captured key
        
        def on_key_press(event):
            """Tuş basımını yakala"""
            modifiers = []
            
            if event.state & 0x4:  # Control
                modifiers.append("Control")
            if event.state & 0x1:  # Shift
                modifiers.append("Shift")
            if event.state & 0x20000:  # Alt
                modifiers.append("Alt")
            
            # Tuş adını al
            key = event.keysym
            
            # Özel tuşlar
            if key in ["Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R"]:
                return
            
            # Kısayolu oluştur
            if modifiers:
                shortcut = "-".join(modifiers) + "-" + key
            else:
                shortcut = key
            
            new_shortcut[0] = shortcut
            captured_key.set(self._format_shortcut_display(shortcut))
        
        # Bind
        dialog.bind("<KeyPress>", on_key_press)
        capture_frame.bind("<Button-1>", lambda e: dialog.focus_set())
        
        # Butonlar
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        def save_shortcut():
            if new_shortcut[0]:
                # Çakışma kontrolü
                conflict = self._check_shortcut_conflict(key, new_shortcut[0])
                if conflict:
                    if not askyesno("Uyarı", 
                                   f"Bu kısayol '{conflict}' için zaten kullanılıyor.\n\n"
                                   f"Değiştirmek ister misiniz?"):
                        return
                
                shortcut_var.set(self._format_shortcut_display(new_shortcut[0]))
                
                # Gerçek değeri kaydet (display değil)
                if "shortcuts" not in self.settings_widgets:
                    self.settings_widgets["shortcuts"] = {}
                
                # StringVar'ı güncelle ama gerçek değeri sakla
                internal_var = ctk.StringVar(value=new_shortcut[0])
                self.settings_widgets["shortcuts"][key] = SettingWidget(internal_var, "entry")
                
                showinfo("Başarılı", f"✅ Kısayol kaydedildi!\n\n{self._format_shortcut_display(new_shortcut[0])}")
                dialog.destroy()
            else:
                showerror("Hata", "Lütfen bir tuşa basın!")
        
        ctk.CTkButton(btn_frame, text="💾 Kaydet", command=save_shortcut,
                     height=40).pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        ctk.CTkButton(btn_frame, text="❌ İptal", command=dialog.destroy,
                     height=40, fg_color=("gray60", "gray40")).pack(side="left", expand=True, fill="x", padx=(5, 0))
    
    def _check_shortcut_conflict(self, current_key, new_shortcut):
        """Kısayol çakışması kontrolü"""
        if "shortcuts" not in self.settings_widgets:
            return None
        
        for key, widget in self.settings_widgets["shortcuts"].items():
            if key != current_key:
                if widget.var.get() == new_shortcut:
                    # Açıklama bul
                    for category, shortcuts in [
                        ("Genel İşlemler", [
                            ("new_stock", "Yeni Hisse Ekle"),
                            ("backup", "Yedek Al"),
                            ("search", "Ara"),
                            ("refresh_prices", "Fiyatları Güncelle"),
                            ("refresh_page", "Sayfayı Yenile"),
                            ("help", "Yardım"),
                            ("escape", "İptal/Kapat"),
                            ("quit_app", "Çıkış"),
                        ]),
                        ("Sayfa Geçişleri", [
                            ("page_dashboard", "Dashboard"),
                            ("page_portfolio", "Portföy"),
                            ("page_transactions", "İşlemler"),
                            ("page_settings", "Ayarlar"),
                        ])
                    ]:
                        for k, label in shortcuts:
                            if k == key:
                                return label
        return None
    
    def reset_shortcuts(self):
        """Kısayolları varsayılana sıfırla"""
        if askyesno("Onay", "Tüm klavye kısayollarını varsayılan değerlere sıfırlamak istiyor musunuz?"):
            # Varsayılan değerler
            default_shortcuts = {
                "new_stock": "Control-n",
                "backup": "Control-s",
                "search": "Control-f",
                "refresh_prices": "Control-r",
                "refresh_page": "F5",
                "quit_app": "Control-q",
                "page_dashboard": "Control-1",
                "page_portfolio": "Control-2",
                "page_transactions": "Control-3",
                "page_settings": "Control-4",
                "help": "F1",
                "escape": "Escape"
            }
            
            # Ayarlara kaydet
            self.temp_settings["keyboard_shortcuts"] = default_shortcuts
            self.settings_manager.update({"keyboard_shortcuts": default_shortcuts})
            
            showinfo("Başarılı", "✅ Klavye kısayolları varsayılan değerlere sıfırlandı!")
            
            # Sayfayı yenile
            self.show_category("shortcuts")
    
    
    def create_about_settings(self):
        """Hakkında bilgileri"""
        about_header = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        about_header.pack(fill="x", pady=20)
        
        ctk.CTkLabel(about_header, text="📊", 
                    font=ctk.CTkFont(size=64)).pack()
        
        ctk.CTkLabel(about_header, text="Hisse Takip Programı", 
                    font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(10, 5))
        
        ctk.CTkLabel(about_header, text="Versiyon 2.0.0", 
                    font=ctk.CTkFont(size=14), 
                    text_color=("gray50", "gray70")).pack()
        
        info_frame = ctk.CTkFrame(self.settings_container, 
                                 fg_color=("gray90", "gray13"), 
                                 corner_radius=10)
        info_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(info_frame, text="Sistem Bilgileri", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        info_items = [
            ("Python Versiyonu", f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"),
            ("Platform", sys.platform),
            ("Veri Dosyası", getattr(self.db, 'db_name', 'N/A')),
            ("Yedek Konumu", getattr(self.backup_manager, 'backup_dir', 'N/A') if hasattr(self.backup_manager, 'backup_dir') else "N/A")
        ]
        
        for label, value in info_items:
            row = ctk.CTkFrame(info_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=3)
            
            ctk.CTkLabel(row, text=f"{label}:", 
                        font=ctk.CTkFont(size=12),
                        text_color=("gray50", "gray70")).pack(side="left")
            
            ctk.CTkLabel(row, text=str(value), 
                        font=ctk.CTkFont(size=12, weight="bold")).pack(side="right")
        
        ctk.CTkLabel(info_frame, text="", height=10).pack()
        
        footer_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        footer_frame.pack(fill="x", pady=20)
        
        ctk.CTkLabel(footer_frame, text="© 2024 - Tüm Hakları Saklıdır", 
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack()
    
    # ================== YARDIMCI METODLAR - WIDGET OLUŞTURMA ==================
    
    def create_setting_group(self, title):
        """Ayar grubu başlığı"""
        ctk.CTkLabel(self.settings_container, text=title, 
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=COLORS["primary"]).pack(anchor="w", pady=(20, 10))
    
    def create_switch_setting(self, category, label, key, default, description=""):
        """Switch (toggle) ayarı"""
        frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        left_frame = ctk.CTkFrame(frame, fg_color="transparent")
        left_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(left_frame, text=label, 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        if description:
            ctk.CTkLabel(left_frame, text=description, 
                        font=ctk.CTkFont(size=11),
                        text_color=("gray50", "gray70")).pack(anchor="w")
        
        var = ctk.StringVar(value="on" if default else "off")
        self.settings_widgets[category][key] = SettingWidget(var, "switch")
        
        switch = ctk.CTkSwitch(frame, text="", variable=var, onvalue="on", offvalue="off")
        switch.pack(side="right")
    
    def create_combobox_setting(self, category, label, key, values, default, description="", display_values=None):
        """Combobox ayarı"""
        frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(frame, text=label, 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        if description:
            ctk.CTkLabel(frame, text=description, 
                        font=ctk.CTkFont(size=11),
                        text_color=("gray50", "gray70")).pack(anchor="w", pady=(0, 5))
        
        if display_values is None:
            display_values = [str(v) for v in values]
        
        try:
            default_index = values.index(default)
            default_display = display_values[default_index]
        except (ValueError, IndexError):
            default_display = display_values[0] if display_values else ""
        
        var = ctk.StringVar(value=default_display)
        self.settings_widgets[category][key] = SettingWidget(
            var, "combo", 
            values=values, 
            display_values=display_values
        )
        
        combo = ctk.CTkComboBox(frame, values=display_values, variable=var, width=250)
        combo.pack(anchor="w")
    
    def create_entry_setting(self, category, label, key, default, description="", sensitive=False, widget_type="entry"):
        """Entry (text input) ayarı"""
        frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        frame.pack(fill="x", pady=5)
        
        label_frame = ctk.CTkFrame(frame, fg_color="transparent")
        label_frame.pack(fill="x")
        
        ctk.CTkLabel(label_frame, text=label, 
                    font=ctk.CTkFont(size=14)).pack(side="left")
        
        if description:
            ctk.CTkLabel(frame, text=description, 
                        font=ctk.CTkFont(size=11),
                        text_color=("gray50", "gray70")).pack(anchor="w", pady=(0, 5))
        
        entry_frame = ctk.CTkFrame(frame, fg_color="transparent")
        entry_frame.pack(fill="x")
        
        var = ctk.StringVar(value=str(default))
        self.settings_widgets[category][key] = SettingWidget(var, widget_type)
        
        entry = ctk.CTkEntry(entry_frame, textvariable=var, width=300)
        entry.pack(side="left")
        
        # Sensitive field için show/hide toggle
        if sensitive:
            entry.configure(show="*")
            
            show_var = ctk.BooleanVar(value=False)
            
            def toggle_visibility():
                if show_var.get():
                    entry.configure(show="")
                    toggle_btn.configure(text="🙈")
                else:
                    entry.configure(show="*")
                    toggle_btn.configure(text="👁")
            
            toggle_btn = ctk.CTkButton(entry_frame, text="👁", width=40, height=30,
                                      command=toggle_visibility)
            toggle_btn.pack(side="left", padx=5)
    
    # ================== HELPER METODLAR ==================
    
    def _get_decrypted_api_key(self, key):
        """Şifreli API anahtarını çöz"""
        encrypted_value = self.temp_settings.get(key, "")
        if not encrypted_value:
            return ""
        
        if self.secure_settings:
            try:
                return self.secure_settings.decrypt_api_key(encrypted_value)
            except:
                return ""
        return encrypted_value
    
    def _get_cache_size(self):
        """Toplam cache boyutunu hesapla"""
        total_size = 0
        cache_dirs = [
            os.path.join(os.getcwd(), "cache"),
            os.path.join(os.getcwd(), "__pycache__"),
            os.path.join(os.getcwd(), ".yfinance_cache")
        ]
        
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                for dirpath, dirnames, filenames in os.walk(cache_dir):
                    for filename in filenames:
                        filepath = os.path.join(dirpath, filename)
                        try:
                            if os.path.exists(filepath):
                                total_size += os.path.getsize(filepath)
                        except:
                            pass
        
        return total_size
    
    def _test_and_update_status(self, api_id, status_label):
        """API'yi test et ve status'u güncelle - Thread-safe"""
        # Orange: Testing
        status_label.configure(text="●", text_color="orange")
        self.parent.update_idletasks()
        
        def test():
            try:
                api_key_name = f"{api_id}_api_key"
                api_key = None
                
                # Widget'tan API key'i al
                if api_key_name in self.settings_widgets.get("advanced", {}):
                    widget = self.settings_widgets["advanced"][api_key_name]
                    api_key = widget.get_value()
                
                if self.api_manager:
                    success, message = self.api_manager.validate_provider(api_id, api_key)
                    color = COLORS["success"] if success else COLORS["danger"]
                else:
                    color = "gray"
                
                # UI güncelle (main thread'de)
                self.parent.after(0, lambda: status_label.configure(text="●", text_color=color))
            
            except Exception as e:
                print(f"API test error: {e}")
                self.parent.after(0, lambda: status_label.configure(text="●", text_color=COLORS["danger"]))
        
        # Background thread'de test et
        thread = threading.Thread(target=test, daemon=True)
        thread.start()
    
    # ================== İŞLEV METODLARI ==================
    
    @handle_errors(show_error=True)
    def save_all_settings(self):
        """Tüm ayarları kaydet"""
        new_settings = {}
        
        # Tüm kategorilerdeki widget'ları işle
        for category, widgets in self.settings_widgets.items():
            for key, widget in widgets.items():
                try:
                    # API anahtarları için özel işlem
                    if widget.type == "api_key":
                        value = widget.get_value()
                        if value:
                            # Şifrele
                            if self.secure_settings:
                                new_settings[key] = self.secure_settings.encrypt_api_key(value)
                            else:
                                new_settings[key] = value
                        else:
                            new_settings[key] = ""
                    
                    # Oran değerleri (komisyon, vergi)
                    elif widget.type == "rate":
                        try:
                            value = widget.get_value()  # Float olarak gelir
                            new_settings[key] = value
                        except ValueError as e:
                            showerror("Geçersiz Değer", f"{key}: {str(e)}")
                            return
                    
                    # Diğer widget tipleri
                    else:
                        new_settings[key] = widget.get_value()
                
                except Exception as e:
                    print(f"Widget kaydetme hatası ({key}): {e}")
                    traceback.print_exc()
        
        # Keyboard shortcuts özel işlem
        if "shortcuts" in self.settings_widgets:
            shortcuts_dict = {}
            for key, widget in self.settings_widgets["shortcuts"].items():
                shortcuts_dict[key] = widget.get_value()
            new_settings["keyboard_shortcuts"] = shortcuts_dict        
        
        
        # Ayarları kaydet
        self.settings_manager.update(new_settings)
        self.temp_settings = new_settings.copy()
        self.settings = new_settings.copy()
        
        # Klavye kısayollarını yeniden yükle
        if "keyboard_shortcuts" in new_settings:
            if 'reload_shortcuts' in self.app_callbacks:
                self.app_callbacks['reload_shortcuts']()
                
        showinfo("Başarılı", "✓ Ayarlar başarıyla kaydedildi!")
        
        # Yeniden başlatma gereken ayarlar değişti mi?
        restart_needed_keys = ['font_size', 'compact_mode', 'language']
        if any(key in new_settings and new_settings.get(key) != self.settings.get(key) for key in restart_needed_keys):
            if askyesno("Yeniden Başlat", 
                       "Bazı değişikliklerin tam olarak uygulanması için uygulamanın yeniden başlatılması gerekiyor.\n\nŞimdi yeniden başlatmak ister misiniz?"):
                if 'reload_app' in self.app_callbacks:
                    self.app_callbacks['reload_app']()
    
    @handle_errors(show_error=True)
    def reset_to_defaults(self):
        """Varsayılan ayarlara sıfırla"""
        if askyesno("Onay", "⚠️ Tüm ayarları varsayılan değerlere sıfırlamak istediğinizden emin misiniz?\n\nBu işlem geri alınamaz!"):
            self.settings_manager.reset_to_defaults()
            showinfo("Başarılı", "✓ Ayarlar varsayılan değerlere sıfırlandı!")
            
            if 'reload_app' in self.app_callbacks:
                self.app_callbacks['reload_app']()
    
    @handle_errors(show_error=False)
    def preview_theme(self, theme):
        """Tema önizlemesi"""
        if 'toggle_theme' in self.app_callbacks:
            self.app_callbacks['toggle_theme'](theme)
    
    @handle_errors(show_error=True)
    def clear_cache(self):
        """Önbelleği temizle"""
        if askyesno("Onay", "Önbelleği temizlemek istediğinizden emin misiniz?"):
            cache_dirs = [
                os.path.join(os.getcwd(), "cache"),
                os.path.join(os.getcwd(), "__pycache__"),
                os.path.join(os.getcwd(), ".yfinance_cache")
            ]
            
            cleared_size = 0
            
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    # Boyutu hesapla
                    for dirpath, dirnames, filenames in os.walk(cache_dir):
                        for filename in filenames:
                            filepath = os.path.join(dirpath, filename)
                            try:
                                if os.path.exists(filepath):
                                    cleared_size += os.path.getsize(filepath)
                            except:
                                pass
                    
                    # Temizle
                    try:
                        shutil.rmtree(cache_dir)
                        os.makedirs(cache_dir, exist_ok=True)
                    except Exception as e:
                        print(f"Cache temizleme hatası ({cache_dir}): {e}")
            
            size_mb = cleared_size / (1024 * 1024)
            showinfo("Başarılı", f"✓ Önbellek temizlendi!\n\n{size_mb:.2f} MB alan kazanıldı.")
            
            # Sayfayı yenile (boyutu güncelle)
            if self.active_category == "data":
                self.show_category("data")
    
    def select_backup_location(self, location_var):
        """Yedekleme konumu seç"""
        folder = filedialog.askdirectory(title="Yedekleme Konumu Seçin")
        if folder:
            location_var.set(folder)
    
    @handle_errors(show_error=True)
    def backup_now(self):
        """Manuel yedekleme"""
        backup_path = self.backup_manager.create_backup(auto=False)
        if backup_path:
            showinfo("Başarılı", f"✓ Yedek başarıyla alındı!\n\n{os.path.basename(backup_path)}")
            # Sayfayı yenile (yedek listesini güncelle)
            if self.active_category == "backup":
                self.show_category("backup")
    
    @handle_errors(show_error=True)
    def restore_backup(self):
        """Yedeği geri yükle"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")],
            title="Yedek Dosyası Seçin"
        )
        
        if filename:
            if askyesno("Onay", 
                       "⚠️ Mevcut veriler yedeğin verileri ile değiştirilecek.\n\nBu işlem geri alınamaz!\n\nDevam etmek istiyor musunuz?"):
                if self.backup_manager.restore_backup(filename):
                    showinfo("Başarılı", "✓ Yedek başarıyla geri yüklendi!")
                    if 'reload_app' in self.app_callbacks:
                        self.app_callbacks['reload_app']()
    
    @handle_errors(show_error=True)
    def restore_specific_backup(self, backup_path):
        """Belirli bir yedeği geri yükle"""
        if askyesno("Onay", 
                   f"⚠️ Bu yedeği geri yüklemek istiyor musunuz?\n\n{os.path.basename(backup_path)}\n\nMevcut veriler silinecek!"):
            if self.backup_manager.restore_backup(backup_path):
                showinfo("Başarılı", "✓ Yedek başarıyla geri yüklendi!")
                if 'reload_app' in self.app_callbacks:
                    self.app_callbacks['reload_app']()
    
    @handle_errors(show_error=True)
    def export_data(self):
        """Verileri dışa aktar"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")],
            initialfile=f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if filename:
            if self.db.export_data(filename):
                showinfo("Başarılı", f"✓ Veriler başarıyla dışa aktarıldı!\n\n{filename}")
            else:
                showerror("Hata", "Veriler dışa aktarılamadı!")
    
    @handle_errors(show_error=True)
    def import_data(self):
        """Verileri içe aktar"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")],
            title="İçe Aktarılacak Dosyayı Seçin"
        )
        
        if filename:
            if askyesno("Onay", 
                       "⚠️ Mevcut veriler içe aktarılan verilerle değiştirilecek!\n\nBu işlem geri alınamaz!\n\nDevam etmek istiyor musunuz?"):
                if self.db.import_data(filename):
                    showinfo("Başarılı", "✓ Veriler başarıyla içe aktarıldı!")
                    if 'reload_app' in self.app_callbacks:
                        self.app_callbacks['reload_app']()
                else:
                    showerror("Hata", "Veriler içe aktarılamadı!")
    
    @handle_errors(show_error=True)
    def clear_all_data(self):
        """Tüm verileri sil"""
        if askyesno("Onay", 
                   "⚠️ DİKKAT!\n\nTüm portföy, işlem ve temettü verileriniz silinecek!\n\nBu işlem GERİ ALINAMAZ!\n\nDevam etmek istediğinizden emin misiniz?"):
            if askyesno("Son Onay", 
                       "⚠️⚠️⚠️ SON UYARI ⚠️⚠️⚠️\n\nGerçekten TÜM VERİLERİ silmek istiyor musunuz?\n\nBu işlem geri alınamaz!"):
                if self.db.clear_all_data():
                    showinfo("Başarılı", "✓ Tüm veriler silindi!")
                    if 'reload_app' in self.app_callbacks:
                        self.app_callbacks['reload_app']()
                else:
                    showerror("Hata", "Veriler silinemedi!")
    
    @handle_errors(show_error=True)
    def export_settings(self):
        """Ayarları dışa aktar"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")],
            initialfile=f"settings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if filename:
            if self.settings_manager.export_settings(filename):
                showinfo("Başarılı", f"✓ Ayarlar başarıyla dışa aktarıldı!\n\n{filename}")
            else:
                showerror("Hata", "Ayarlar dışa aktarılamadı!")
    
    @handle_errors(show_error=True)
    def import_settings(self):
        """Ayarları içe aktar"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON", "*.json"), ("All Files", "*.*")],
            title="Ayar Dosyasını Seçin"
        )
        
        if filename:
            if askyesno("Onay", "Mevcut ayarlar içe aktarılan ayarlarla değiştirilecek.\n\nDevam etmek istiyor musunuz?"):
                if self.settings_manager.import_settings(filename):
                    showinfo("Başarılı", "✓ Ayarlar başarıyla içe aktarıldı!")
                    if 'reload_app' in self.app_callbacks:
                        self.app_callbacks['reload_app']()
                else:
                    showerror("Hata", "Ayarlar içe aktarılamadı!")
    
    @handle_errors(show_error=True)
    def clear_saved_credentials(self):
        """Kaydedilmiş giriş bilgilerini sil"""
        if askyesno("Onay", "Kaydedilmiş giriş bilgileri silinecek.\n\nDevam etmek istiyor musunuz?"):
            if self.credentials_manager:
                if self.credentials_manager.clear_credentials():
                    showinfo("Başarılı", "✓ Kaydedilmiş bilgiler silindi!")
                    # Sayfayı yenile
                    self.show_category("security")
                else:
                    showerror("Hata", "Bilgiler silinemedi!")
    
        # ================== API VALIDATION METHODS ==================
    
    def validate_all_apis(self):
        """Tüm API'leri test et - Thread-safe with improved error handling"""
        if not self.api_manager:
            showerror("Hata", "API Manager yüklenemedi!")
            return
        
        # Rate limiting kontrolü
        if RateLimiter:
            try:
                @RateLimiter(max_calls=3, period=60)
                def rate_limited_validation():
                    pass
                rate_limited_validation()
            except RateLimitException as e:
                showerror("Rate Limit", str(e))
                return
        
        loading = LoadingDialog(self.parent, "API'ler test ediliyor...")
        
        def test_apis():
            try:
                # API key'leri topla
                api_keys = {}
                advanced_widgets = self.settings_widgets.get("advanced", {})
                
                for key in ["iex_cloud_api_key", "finnhub_api_key", "alpha_vantage_api_key"]:
                    if key in advanced_widgets:
                        widget = advanced_widgets[key]
                        value = widget.get_value()
                        if value:
                            api_keys[key] = value
                
                # Tüm API'leri test et
                results = self.api_manager.validate_all(api_keys)
                
                # Sonuçları formatla
                result_lines = []
                for provider, data in results.items():
                    icon = "✓" if data["success"] else "✗"
                    status = data["message"]
                    has_key = " (Anahtar kayıtlı)" if data["has_key"] else " (Anahtar yok)"
                    
                    provider_names = {
                        "yfinance": "Yahoo Finance",
                        "iex_cloud": "IEX Cloud",
                        "finnhub": "Finnhub",
                        "alpha_vantage": "Alpha Vantage"
                    }
                    
                    name = provider_names.get(provider, provider)
                    result_lines.append(f"{icon} {name}: {status}{has_key}")
                
                message = "\n".join(result_lines)
                
                # UI güncelle (main thread'de) - Schedule with delay
                def show_results():
                    try:
                        loading.safe_destroy()
                    except:
                        pass
                    showinfo("API Doğrulama Sonuçları", message)
                
                self.parent.after(100, show_results)
            
            except Exception as e:
                # Hata durumu
                def show_error():
                    try:
                        loading.safe_destroy()
                    except:
                        pass
                    showerror("Hata", f"API doğrulaması sırasında hata:\n{str(e)}")
                
                self.parent.after(100, show_error)
        
        # Background thread'de test et
        thread = threading.Thread(target=test_apis, daemon=True)
        thread.start()

    def validate_selected_api(self):
        """Seçili API'yi test et - Thread-safe with improved error handling"""
        if not self.api_manager:
            showerror("Hata", "API Manager yüklenemedi!")
            return
        
        try:
            # Seçili provider'ı al
            advanced_widgets = self.settings_widgets.get("advanced", {})
            provider_widget = advanced_widgets.get("api_provider")
            
            if not provider_widget:
                showerror("Hata", "API sağlayıcı seçilmedi!")
                return
            
            provider_name = provider_widget.get_value()
            
            # API key'i al
            api_key = None
            if provider_name != "yfinance":
                key_name = f"{provider_name}_api_key"
                if key_name in advanced_widgets:
                    api_key = advanced_widgets[key_name].get_value()
            
            # Loading göster
            loading = LoadingDialog(self.parent, f"{provider_name} test ediliyor...")
            
            def test():
                try:
                    success, message = self.api_manager.validate_provider(provider_name, api_key)
                    
                    provider_names = {
                        "yfinance": "Yahoo Finance",
                        "iex_cloud": "IEX Cloud",
                        "finnhub": "Finnhub",
                        "alpha_vantage": "Alpha Vantage"
                    }
                    
                    display_name = provider_names.get(provider_name, provider_name)
                    
                    def show_result():
                        try:
                            loading.safe_destroy()
                        except:
                            pass
                        
                        if success:
                            result_msg = f"✓ {display_name}\n\n{message}"
                            showinfo("Başarılı", result_msg)
                        else:
                            result_msg = f"✗ {display_name}\n\n{message}"
                            showerror("Hata", result_msg)
                    
                    self.parent.after(100, show_result)
                
                except Exception as e:
                    def show_error():
                        try:
                            loading.safe_destroy()
                        except:
                            pass
                        showerror("Hata", f"Test hatası:\n{str(e)}")
                    
                    self.parent.after(100, show_error)
            
            # Background thread'de test et
            thread = threading.Thread(target=test, daemon=True)
            thread.start()
        
        except Exception as e:
            showerror("Hata", f"API test edilemedi:\n{str(e)}")
    
    @handle_errors(show_error=False)
    def logout(self):
        """Çıkış yap"""
        if askyesno("Çıkış Yap", "Oturumu kapatmak istediğinizden emin misiniz?"):
            # Uygulamayı yeniden başlat (giriş sayfasına dön)
            if 'reload_app' in self.app_callbacks:
                self.app_callbacks['reload_app']()