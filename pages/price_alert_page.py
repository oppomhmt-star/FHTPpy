# pages/price_alert_page.py

import customtkinter as ctk
from config import COLORS
from ui_utils import showinfo, showerror, askyesno
from utils.price_alert_manager import PriceAlertManager
from datetime import datetime

class PriceAlertPage:
    """Fiyat Alarmları Sayfası"""
    
    def __init__(self, parent, db, app_callbacks):
        self.parent = parent
        self.db = db
        self.app_callbacks = app_callbacks
        
        # Alert manager
        settings_manager = None
        if 'get_settings_manager' in app_callbacks:
            settings_manager = app_callbacks['get_settings_manager']()
        
        self.alert_manager = PriceAlertManager(db, settings_manager)
        
        # Alert kartları
        self.alert_widgets = {}
        
        # Container referansları
        self.active_alerts_container = None
        self.triggered_alerts_container = None
        
        # Main frame referansı
        self.main_frame = None
    
    def create(self):
        """Sayfa oluştur"""
        # ÖNCELİKLE MEVCUT FRAME'İ TEMİZLE
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Yeni main frame oluştur
        self.main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık ve yeni alarm butonu
        self.create_header()
        
        # İki kolon: Aktif & Tetiklenmiş
        content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, pady=10)
        
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        content_frame.grid_rowconfigure(0, weight=1)
        
        # Sol: Aktif alarmlar
        self.create_active_alerts_section(content_frame)
        
        # Sağ: Tetiklenmiş alarmlar
        self.create_triggered_alerts_section(content_frame)
    
    def create_header(self):
        """Başlık kısmı"""
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        # Sol: Başlık
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(side="left")
        
        ctk.CTkLabel(title_frame, text="🔔 Fiyat Alarmları", 
                    font=ctk.CTkFont(size=32, weight="bold")).pack(side="left")
        
        # Aktif alarm sayısı
        active_count = len(self.alert_manager.get_active_alerts())
        ctk.CTkLabel(title_frame, 
                    text=f"({active_count} aktif)", 
                    font=ctk.CTkFont(size=14),
                    text_color=("gray50", "gray70")).pack(side="left", padx=10)
        
        # Sağ: Butonlar
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="➕ Yeni Alarm", 
                     command=self.show_create_alarm_dialog,
                     width=150, height=40,
                     fg_color=COLORS["success"],
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="🔄 Yenile", 
                     command=self.refresh_alerts,
                     width=100, height=40).pack(side="left", padx=5)
        
        ctk.CTkButton(btn_frame, text="🧪 Test Bildirimi", 
                     command=self.test_notification,
                     width=140, height=40,
                     fg_color=COLORS["warning"]).pack(side="left", padx=5)
    
    def create_active_alerts_section(self, parent):
        """Aktif alarmlar bölümü"""
        section = ctk.CTkFrame(parent, fg_color=("gray90", "gray13"), corner_radius=10)
        section.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Başlık
        header = ctk.CTkFrame(section, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(header, text="✅ Aktif Alarmlar", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        
        # Scrollable content
        self.active_alerts_container = ctk.CTkScrollableFrame(
            section, 
            fg_color="transparent"
        )
        self.active_alerts_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Alarmları yükle
        self.load_active_alerts()
    
    def create_triggered_alerts_section(self, parent):
        """Tetiklenmiş alarmlar bölümü"""
        section = ctk.CTkFrame(parent, fg_color=("gray90", "gray13"), corner_radius=10)
        section.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Başlık
        header = ctk.CTkFrame(section, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(header, text="⚡ Tetiklenmiş Alarmlar", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        
        # Temizle butonu
        ctk.CTkButton(header, text="🗑️ Tümünü Temizle", 
                     command=self.clear_triggered_alerts,
                     width=140, height=30,
                     fg_color=COLORS["danger"]).pack(side="right")
        
        # Scrollable content
        self.triggered_alerts_container = ctk.CTkScrollableFrame(
            section, 
            fg_color="transparent"
        )
        self.triggered_alerts_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Alarmları yükle
        self.load_triggered_alerts()
    
    def load_active_alerts(self):
        """Aktif alarmları yükle"""
        # Container'ı temizle
        if self.active_alerts_container:
            for widget in self.active_alerts_container.winfo_children():
                widget.destroy()
        
        alerts = [a for a in self.alert_manager.get_all_alerts() 
                 if a['active'] and not a['triggered']]
        
        if not alerts:
            ctk.CTkLabel(self.active_alerts_container, 
                        text="Henüz aktif alarm yok\n\n➕ Yeni Alarm butonuna tıklayarak\nilk alarmınızı oluşturun",
                        font=ctk.CTkFont(size=13),
                        text_color=("gray50", "gray70"),
                        justify="center").pack(pady=50)
            return
        
        for alert in alerts:
            self.create_alert_card(self.active_alerts_container, alert, active=True)
    
    def load_triggered_alerts(self):
        """Tetiklenmiş alarmları yükle"""
        # Container'ı temizle
        if self.triggered_alerts_container:
            for widget in self.triggered_alerts_container.winfo_children():
                widget.destroy()
        
        alerts = [a for a in self.alert_manager.get_all_alerts() if a['triggered']]
        
        if not alerts:
            ctk.CTkLabel(self.triggered_alerts_container, 
                        text="Henüz tetiklenmiş alarm yok",
                        font=ctk.CTkFont(size=13),
                        text_color=("gray50", "gray70")).pack(pady=50)
            return
        
        for alert in alerts:
            self.create_alert_card(self.triggered_alerts_container, alert, active=False)
    
    def create_alert_card(self, parent, alert, active=True):
        """Alarm kartı oluştur"""
        card = ctk.CTkFrame(parent, 
                           fg_color=("gray85", "gray17"), 
                           corner_radius=8)
        card.pack(fill="x", pady=5, padx=5)
        
        # Ana içerik
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=12)
        
        # Sol: Bilgiler
        info_frame = ctk.CTkFrame(content, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        # Sembol ve hedef
        symbol_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        symbol_frame.pack(fill="x")
        
        ctk.CTkLabel(symbol_frame, 
                    text=alert['symbol'], 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        
        # Ok işareti
        arrow = "▲" if alert['condition'] == 'above' else "▼"
        arrow_color = COLORS["success"] if alert['condition'] == 'above' else COLORS["danger"]
        
        ctk.CTkLabel(symbol_frame, 
                    text=f"  {arrow}  ", 
                    font=ctk.CTkFont(size=16),
                    text_color=arrow_color).pack(side="left")
        
        ctk.CTkLabel(symbol_frame, 
                    text=f"{alert['target_price']:.2f} ₺", 
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=arrow_color).pack(side="left")
        
        # Koşul açıklaması
        condition_text = "üstüne çıkınca" if alert['condition'] == 'above' else "altına inince"
        ctk.CTkLabel(info_frame, 
                    text=f"{condition_text} bildir", 
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack(anchor="w")
        
        # Not varsa göster
        if alert.get('note'):
            ctk.CTkLabel(info_frame, 
                        text=f"📝 {alert['note']}", 
                        font=ctk.CTkFont(size=11),
                        text_color=("gray60", "gray60")).pack(anchor="w", pady=(3, 0))
        
        # Tarih bilgisi
        if active:
            if isinstance(alert['created_at'], datetime):
                date_text = alert['created_at'].strftime("%d/%m/%Y %H:%M")
            else:
                date_text = str(alert['created_at'])
            date_label = f"🕒 {date_text}"
        else:
            if alert.get('triggered_at'):
                if isinstance(alert['triggered_at'], datetime):
                    date_text = alert['triggered_at'].strftime("%d/%m/%Y %H:%M")
                else:
                    date_text = str(alert['triggered_at'])
            else:
                date_text = "N/A"
            date_label = f"⚡ {date_text}"
        
        ctk.CTkLabel(info_frame, 
                    text=date_label, 
                    font=ctk.CTkFont(size=10),
                    text_color=("gray50", "gray70")).pack(anchor="w", pady=(5, 0))
        
        # Sağ: Aksiyonlar
        actions_frame = ctk.CTkFrame(content, fg_color="transparent")
        actions_frame.pack(side="right")
        
        if active:
            # Aktif alarmlar için: Düzenle, Sil
            ctk.CTkButton(actions_frame, 
                         text="✏️", 
                         width=35, height=35,
                         command=lambda a=alert: self.edit_alert(a),
                         fg_color=COLORS["primary"]).pack(side="top", pady=2)
            
            ctk.CTkButton(actions_frame, 
                         text="🗑️", 
                         width=35, height=35,
                         command=lambda a=alert: self.delete_alert(a),
                         fg_color=COLORS["danger"]).pack(side="top", pady=2)
        else:
            # Tetiklenmiş alarmlar için: Yeniden aktifleştir, Sil
            ctk.CTkButton(actions_frame, 
                         text="🔄", 
                         width=35, height=35,
                         command=lambda a=alert: self.reactivate_alert(a),
                         fg_color=COLORS["success"]).pack(side="top", pady=2)
            
            ctk.CTkButton(actions_frame, 
                         text="🗑️", 
                         width=35, height=35,
                         command=lambda a=alert: self.delete_alert(a),
                         fg_color=COLORS["danger"]).pack(side="top", pady=2)
    
    def show_create_alarm_dialog(self):
        """Yeni alarm oluşturma dialog'u"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Yeni Fiyat Alarmı")
        dialog.geometry("500x450")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center window
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # İçerik
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        ctk.CTkLabel(content, text="🔔 Yeni Alarm Oluştur", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 20))
        
        # Hisse Sembolü
        ctk.CTkLabel(content, text="Hisse Sembolü:", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        symbol_var = ctk.StringVar()
        symbol_entry = ctk.CTkEntry(content, textvariable=symbol_var, 
                                    width=400, height=40,
                                    placeholder_text="Örn: THYAO")
        symbol_entry.pack(pady=(5, 15))
        symbol_entry.focus()
        
        # Hedef Fiyat
        ctk.CTkLabel(content, text="Hedef Fiyat (₺):", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        price_var = ctk.StringVar()
        price_entry = ctk.CTkEntry(content, textvariable=price_var, 
                                   width=400, height=40,
                                   placeholder_text="Örn: 125.50")
        price_entry.pack(pady=(5, 15))
        
        # Koşul
        ctk.CTkLabel(content, text="Koşul:", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        condition_var = ctk.StringVar(value="above")
        
        condition_frame = ctk.CTkFrame(content, fg_color="transparent")
        condition_frame.pack(fill="x", pady=(5, 15))
        
        ctk.CTkRadioButton(condition_frame, text="Fiyat üstüne çıkınca bildir", 
                          variable=condition_var, value="above",
                          font=ctk.CTkFont(size=13)).pack(anchor="w", pady=3)
        
        ctk.CTkRadioButton(condition_frame, text="Fiyat altına inince bildir", 
                          variable=condition_var, value="below",
                          font=ctk.CTkFont(size=13)).pack(anchor="w", pady=3)
        
        # Not (opsiyonel)
        ctk.CTkLabel(content, text="Not (opsiyonel):", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        note_var = ctk.StringVar()
        note_entry = ctk.CTkEntry(content, textvariable=note_var, 
                                  width=400, height=40,
                                  placeholder_text="Örn: Kar al seviyesi")
        note_entry.pack(pady=(5, 20))
        
        # Butonlar
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        def create_alert():
            symbol = symbol_var.get().strip().upper()
            price_str = price_var.get().strip().replace(',', '.')
            condition = condition_var.get()
            note = note_var.get().strip()
            
            # Validasyon
            if not symbol:
                showerror("Hata", "Lütfen hisse sembolü girin!")
                return
            
            try:
                target_price = float(price_str)
                if target_price <= 0:
                    raise ValueError()
            except:
                showerror("Hata", "Lütfen geçerli bir fiyat girin!")
                return
            
            # Alarm oluştur
            alert_id = self.alert_manager.create_alert(
                symbol=symbol,
                target_price=target_price,
                condition=condition,
                note=note
            )
            
            if alert_id:
                showinfo("Başarılı", f"✓ Alarm oluşturuldu!\n\n{symbol} - {condition} {target_price:.2f} ₺")
                dialog.destroy()
                self.refresh_alerts()  # Sayfayı yenile
            else:
                showerror("Hata", "Alarm oluşturulamadı!")
        
        ctk.CTkButton(btn_frame, text="✓ Oluştur", 
                     command=create_alert,
                     width=190, height=40,
                     fg_color=COLORS["success"],
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(btn_frame, text="✗ İptal", 
                     command=dialog.destroy,
                     width=190, height=40,
                     fg_color=COLORS["danger"],
                     font=ctk.CTkFont(size=14)).pack(side="left")
        
        # Enter tuşu ile oluştur
        dialog.bind('<Return>', lambda e: create_alert())
    
    def edit_alert(self, alert):
        """Alarm düzenle"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Alarm Düzenle")
        dialog.geometry("500x400")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Center
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        content = ctk.CTkFrame(dialog, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Başlık
        ctk.CTkLabel(content, text=f"✏️ {alert['symbol']} Alarmını Düzenle", 
                    font=ctk.CTkFont(size=20, weight="bold")).pack(pady=(0, 20))
        
        # Hedef Fiyat
        ctk.CTkLabel(content, text="Hedef Fiyat (₺):", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        price_var = ctk.StringVar(value=str(alert['target_price']))
        price_entry = ctk.CTkEntry(content, textvariable=price_var, 
                                   width=400, height=40)
        price_entry.pack(pady=(5, 15))
        
        # Koşul
        ctk.CTkLabel(content, text="Koşul:", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        condition_var = ctk.StringVar(value=alert['condition'])
        
        condition_frame = ctk.CTkFrame(content, fg_color="transparent")
        condition_frame.pack(fill="x", pady=(5, 15))
        
        ctk.CTkRadioButton(condition_frame, text="Fiyat üstüne çıkınca bildir", 
                          variable=condition_var, value="above",
                          font=ctk.CTkFont(size=13)).pack(anchor="w", pady=3)
        
        ctk.CTkRadioButton(condition_frame, text="Fiyat altına inince bildir", 
                          variable=condition_var, value="below",
                          font=ctk.CTkFont(size=13)).pack(anchor="w", pady=3)
        
        # Not
        ctk.CTkLabel(content, text="Not:", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        note_var = ctk.StringVar(value=alert.get('note', ''))
        note_entry = ctk.CTkEntry(content, textvariable=note_var, 
                                  width=400, height=40)
        note_entry.pack(pady=(5, 20))
        
        # Butonlar
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        def update_alert():
            try:
                target_price = float(price_var.get().replace(',', '.'))
                if target_price <= 0:
                    raise ValueError()
            except:
                showerror("Hata", "Lütfen geçerli bir fiyat girin!")
                return
            
            if self.alert_manager.update_alert(
                alert['id'],
                target_price=target_price,
                condition=condition_var.get(),
                note=note_var.get().strip()
            ):
                showinfo("Başarılı", "✓ Alarm güncellendi!")
                dialog.destroy()
                self.refresh_alerts()
            else:
                showerror("Hata", "Alarm güncellenemedi!")
        
        ctk.CTkButton(btn_frame, text="✓ Güncelle", 
                     command=update_alert,
                     width=190, height=40,
                     fg_color=COLORS["success"],
                     font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(btn_frame, text="✗ İptal", 
                     command=dialog.destroy,
                     width=190, height=40,
                     fg_color=COLORS["danger"],
                     font=ctk.CTkFont(size=14)).pack(side="left")
    
    def delete_alert(self, alert):
        """Alarm sil"""
        if askyesno("Alarm Sil", f"{alert['symbol']} alarmını silmek istediğinizden emin misiniz?"):
            if self.alert_manager.delete_alert(alert['id']):
                showinfo("Başarılı", "✓ Alarm silindi!")
                self.refresh_alerts()
            else:
                showerror("Hata", "Alarm silinemedi!")
    
    def reactivate_alert(self, alert):
        """Alarmı yeniden aktifleştir"""
        if self.alert_manager.update_alert(
            alert['id'],
            active=True,
            triggered=False,
            triggered_at=None
        ):
            showinfo("Başarılı", f"✓ {alert['symbol']} alarmı yeniden aktifleştirildi!")
            self.refresh_alerts()
        else:
            showerror("Hata", "Alarm aktifleştirilemedi!")
    
    def clear_triggered_alerts(self):
        """Tüm tetiklenmiş alarmları sil"""
        triggered = [a for a in self.alert_manager.get_all_alerts() if a['triggered']]
        
        if not triggered:
            showinfo("Bilgi", "Silinecek alarm yok.")
            return
        
        if askyesno("Tümünü Sil", f"{len(triggered)} adet tetiklenmiş alarmı silmek istediğinizden emin misiniz?"):
            for alert in triggered:
                self.alert_manager.delete_alert(alert['id'])
            
            showinfo("Başarılı", f"✓ {len(triggered)} alarm silindi!")
            self.refresh_alerts()
    
    def refresh_alerts(self):
        """Alarm listesini yenile - DÜZELTME"""
        try:
            # Sadece container'ları yenile, tüm sayfayı değil
            if self.active_alerts_container and self.active_alerts_container.winfo_exists():
                self.load_active_alerts()
            
            if self.triggered_alerts_container and self.triggered_alerts_container.winfo_exists():
                self.load_triggered_alerts()
            
            # Header'daki alarm sayısını güncelle
            # Tüm sayfayı yeniden oluşturmak daha güvenli (container kontrolü için)
            # self.create()
            
        except Exception as e:
            print(f"[ERROR] Alarm yenileme hatası: {e}")
            # Hata durumunda tüm sayfayı yeniden oluştur
            self.create()
    
    def test_notification(self):
        """Test bildirimi gönder"""
        self.alert_manager.notifier.send(
            title="🧪 Test Bildirimi",
            message="Bildirim sistemi çalışıyor!\n\nFiyat alarmlarınız bu şekilde bildirilecek.",
            icon="info",
            sound=True
        )
        showinfo("Test", "Test bildirimi gönderildi!")