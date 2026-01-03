import customtkinter as ctk
from tkinter import filedialog
from datetime import datetime
import yfinance as yf
from config import COLORS
import re
from ui_utils import showinfo, showerror, askyesno
import csv

def format_rate_display(rate):
    """Komisyon oranını kullanıcıya uygun formatta gösterme"""
    # Onbinde ve binde hesapla
    onbinde = rate * 10000
    binde = rate * 1000
    yuzde = rate * 100
    
    if rate >= 0.01:  # %1 veya üstü
        return f"Yüzde {yuzde:.2f}"
    elif rate >= 0.001:  # Binde 1 veya üstü 
        return f"Binde {binde:.2f}"
    else:  # Onbinde göster
        return f"Onbinde {onbinde:.2f}"

class PortfolioPage:
    def __init__(self, parent, db, api, theme, data_changed_callback=None):
        self.parent = parent
        self.db = db
        self.api = api
        self.theme = theme
        self.data_changed_callback = data_changed_callback
        
        self.main_container = None
        self.summary_container = None
        self.list_container = None
        
        self.search_var = None
        self.sort_combo = None
        
    # YENİ: User ID alma metodu
    def get_user_id(self):
        """Aktif kullanıcı ID'sini al"""
        root = self.parent
        while root.master:
            root = root.master
        return getattr(root, 'current_user_id', 1)
        
        
    def create(self):
        self.main_container = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        self.create_header()
        
        self.summary_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.summary_container.pack(fill="x", pady=(0, 20))
        
        self.create_filter_bar()
        
        self.list_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.list_container.pack(fill="both", expand=True)
        
        self.refresh_ui()

    def create_header(self):
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="💼 Portföy Yönetimi", 
                    font=ctk.CTkFont(size=32, weight="bold")).pack(side="left")
        
    def refresh_ui(self):
        self.refresh_summary()
        self.refresh_list()

    def refresh_summary(self):
        if not self.summary_container or not self.summary_container.winfo_exists():
            return
        
        for widget in self.summary_container.winfo_children():
            widget.destroy()
        
        # USER ID AL
        user_id = self.get_user_id()
        
        # DÜZELTİLMİŞ - user_id ile
        portfolio = self.db.get_portfolio(user_id)
        
        total_stocks = len(portfolio)
        total_amount = sum(h["adet"] for h in portfolio)
        total_inv = sum(h["adet"] * h["ort_maliyet"] for h in portfolio)
        curr_val = sum(h["adet"] * h.get("guncel_fiyat", h["ort_maliyet"]) for h in portfolio)
        pl = curr_val - total_inv
        pl_p = (pl / total_inv * 100) if total_inv > 0 else 0
        
        # Toplam komisyon hesapla
        settings = self.db.get_settings(user_id)
        commission_rate = settings.get("komisyon_orani", 0.0004)  # ✅ DÜZELTİLDİ
        
        try:
            if isinstance(commission_rate, str):
                commission_rate = float(commission_rate.replace(',', '.'))
            else:
                commission_rate = float(commission_rate)
        except:
            commission_rate = 0.0004
        
        # Komisyon oranı gösterimi
        commission_display = format_rate_display(commission_rate)
        
        transactions = self.db.get_transactions(user_id)  # ✅ user_id eklendi
        total_commission = sum(t.get("komisyon", t.get("toplam", 0) * commission_rate) for t in transactions if t.get("tip") == "Alım")
           
        for i in range(5):
            self.summary_container.grid_columnconfigure(i, weight=1)
        
        cards = [
            ("Toplam Hisse", str(total_stocks), f"({total_amount:,} adet)", COLORS["primary"]),
            ("Toplam Yatırım", f"{total_inv:,.2f} ₺", "Komisyon Dahil", COLORS["primary"]),
            ("Güncel Değer", f"{curr_val:,.2f} ₺", "Portföy", COLORS["success"]),
            ("Kar/Zarar", f"{pl:,.2f} ₺", f"{pl_p:+.2f}%", COLORS["success"] if pl >= 0 else COLORS["danger"]),
            ("Toplam Komisyon", f"{total_commission:,.2f} ₺", f"{commission_display}", COLORS["warning"])
        ]
        
        for i, (t, v, s, c) in enumerate(cards):
            card = ctk.CTkFrame(self.summary_container, corner_radius=12, fg_color=("gray85", "gray17"))
            card.grid(row=0, column=i, padx=6, pady=8, sticky="nsew")
            
            ctk.CTkLabel(card, text=t, font=ctk.CTkFont(size=12), 
                        text_color="gray").pack(pady=(12, 5))
            
            ctk.CTkLabel(card, text=v, font=ctk.CTkFont(size=20, weight="bold"), 
                        text_color=c).pack(pady=3)
            
            ctk.CTkLabel(card, text=s, font=ctk.CTkFont(size=10), 
                        text_color="gray").pack(pady=(0, 12))

    def create_filter_bar(self):
        filter_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(filter_frame, text="🔍", font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 5))
        
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Ara...", 
                                         width=200, textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=(0, 15))
        self.search_var.trace("w", lambda *args: self.refresh_list())
        
        ctk.CTkLabel(filter_frame, text="Sırala:", font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 5))
        
        self.sort_combo = ctk.CTkComboBox(filter_frame, 
                                          values=["Varsayılan", "Sembol A-Z", "Sembol Z-A", "Kar↓", "Zarar↓"], 
                                          width=140, command=lambda x: self.refresh_list())
        self.sort_combo.set("Varsayılan")
        self.sort_combo.pack(side="left")

    def _normalize_symbol_text(self, text):
        tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
        return text.translate(tr_map).upper()

    def refresh_list(self):
        if not self.list_container or not self.list_container.winfo_exists():
            return
        
        for w in self.list_container.winfo_children():
            w.destroy()
        
        # USER ID AL
        user_id = self.get_user_id()    
        
        portfolio = self.db.get_portfolio(user_id)
        
        if self.search_var and self.search_var.get():
            s = self.search_var.get().upper()
            portfolio = [h for h in portfolio if s in h["sembol"].upper()]
        
        if self.sort_combo:
            sort_map = {
                "Sembol A-Z": ("sembol", False),
                "Sembol Z-A": ("sembol", True),
                "Kar↓": (lambda x: (x.get("guncel_fiyat", x["ort_maliyet"]) - x["ort_maliyet"]) * x["adet"], True),
                "Zarar↓": (lambda x: (x.get("guncel_fiyat", x["ort_maliyet"]) - x["ort_maliyet"]) * x["adet"], False)
            }
            sort_option = self.sort_combo.get()
            if sort_option in sort_map:
                key, reverse = sort_map[sort_option]
                portfolio.sort(key=key if isinstance(key, str) else lambda x: key(x), reverse=reverse)
        
        grid_frame = ctk.CTkFrame(self.list_container, fg_color="transparent")
        grid_frame.pack(fill="x", expand=True)

        headers = ["Sembol", "Adet", "Ort.Maliyet", "Güncel Fiyat", "Top.Maliyet", "Güncel Değer", "Kar/Zarar", "İşlemler"]
        weights = [8, 6, 8, 8, 10, 10, 13, 17]
        
        for i, w in enumerate(weights):
            grid_frame.grid_columnconfigure(i, weight=w)

        header_bg = ctk.CTkFrame(grid_frame, fg_color=("gray75", "gray25"), corner_radius=8, height=40)
        header_bg.grid(row=0, column=0, columnspan=len(headers), sticky="nsew", pady=(0, 5))
        
        for i, h_text in enumerate(headers):
            ctk.CTkLabel(grid_frame, text=h_text, font=ctk.CTkFont(size=12, weight="bold"), 
                        bg_color=header_bg.cget("fg_color")).grid(row=0, column=i, sticky="nsew", padx=5)
        
        if not portfolio:
            ctk.CTkLabel(grid_frame, text="Portföyde hisse yok", 
                        text_color="gray").grid(row=1, column=0, columnspan=len(headers), pady=50)
            return

        for row_idx, stock in enumerate(portfolio, start=1):
            self.create_row(grid_frame, stock, row_idx)

    def create_row(self, parent, stock, row_idx):
        g = stock.get("guncel_fiyat", stock["ort_maliyet"])
        tm = stock["adet"] * stock["ort_maliyet"]
        tv = stock["adet"] * g
        kz = tv - tm
        kz_p = (kz / tm * 100) if tm > 0 else 0
        
        ctk.CTkLabel(parent, text=stock["sembol"], 
                    font=ctk.CTkFont(size=14, weight="bold")).grid(row=row_idx, column=0, sticky="nsew", pady=10)
        
        ctk.CTkLabel(parent, text=f"{stock['adet']:,}").grid(row=row_idx, column=1, sticky="nsew")
        
        ctk.CTkLabel(parent, text=f"{stock['ort_maliyet']:.2f} ₺").grid(row=row_idx, column=2, sticky="nsew")
        
        ctk.CTkLabel(parent, text=f"{g:.2f} ₺").grid(row=row_idx, column=3, sticky="nsew")
        
        ctk.CTkLabel(parent, text=f"{tm:,.0f} ₺").grid(row=row_idx, column=4, sticky="nsew")
        
        ctk.CTkLabel(parent, text=f"{tv:,.0f} ₺").grid(row=row_idx, column=5, sticky="nsew")
        
        color = COLORS["success"] if kz >= 0 else COLORS["danger"]
        kz_label = ctk.CTkLabel(parent, text=f"{kz:,.0f}₺ ({kz_p:+.1f}%)", 
                                font=ctk.CTkFont(size=12, weight="bold"), text_color=color)
        kz_label.grid(row=row_idx, column=6, sticky="nsew")
        
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=row_idx, column=7, sticky="ew", padx=3)
        
        ctk.CTkButton(btn_frame, text="Sat", width=40, height=26, 
                     command=lambda s=stock: self.sell_stock(s), 
                     fg_color=COLORS["warning"]).pack(side="left", padx=2, pady=5)
        
        ctk.CTkButton(btn_frame, text="↻", width=28, height=26, 
                     command=lambda s=stock: self.update_price(s)).pack(side="left", padx=2, pady=5)
        
        ctk.CTkButton(btn_frame, text="✕", width=28, height=26, 
                     command=lambda s=stock: self.delete_stock(s), 
                     fg_color=COLORS["danger"]).pack(side="left", padx=2, pady=5)

    def _create_validated_entry(self, parent, **kwargs):
        entry = ctk.CTkEntry(parent, **kwargs)
        
        def on_key_release(event):
            current_text = entry.get()
            normalized_text = self._normalize_symbol_text(current_text)
            if current_text != normalized_text:
                cursor_pos = entry.index(ctk.INSERT)
                entry.delete(0, ctk.END)
                entry.insert(0, normalized_text)
                entry.icursor(cursor_pos)
        
        entry.bind("<KeyRelease>", on_key_release)
        return entry

    def _trigger_update(self):
        self.refresh_ui()
        if self.data_changed_callback:
            self.data_changed_callback()

    def add_stock_dialog(self):
        """Alım İşlemi / Hisse Ekle (KOMİSYON HESAPLAMALI)"""
        d = ctk.CTkToplevel(self.parent)
        d.title("Alım İşlemi / Hisse Ekle")
        d.geometry("450x1")  # Geçici boyut
        d.transient(self.parent)
        d.grab_set()

        m = ctk.CTkFrame(d)
        m.pack(fill="both", expand=True, padx=25, pady=25)
        
        ctk.CTkLabel(m, text="➕ Yeni Hisse Ekle", 
                    font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 20))
        
        f = ctk.CTkFrame(m, fg_color="transparent")
        f.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(f, text="Sembol:", anchor="w").pack(fill="x")
        s_e = self._create_validated_entry(f, height=38, placeholder_text="THYAO")
        s_e.pack(fill="x", pady=(0, 8))
        s_e.focus()
        
        ctk.CTkLabel(f, text="Adet:", anchor="w").pack(fill="x")
        a_e = ctk.CTkEntry(f, height=38, placeholder_text="100")
        a_e.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(f, text="Alış Fiyatı (₺):", anchor="w").pack(fill="x")
        p_e = ctk.CTkEntry(f, height=38, placeholder_text="150.50")
        p_e.pack(fill="x", pady=(0, 8))
        
        # USER ID AL
        user_id = self.get_user_id() 
        
        # Komisyon oranını al
        settings = self.db.get_settings()
        commission_rate = settings.get("komisyon_orani", 0.0004)
        
        try:
            if isinstance(commission_rate, str):
                commission_rate = float(commission_rate.replace(',', '.'))
            else:
                commission_rate = float(commission_rate)
        except:
            commission_rate = 0.0004
        
        # Komisyon oranı gösterimi
        commission_display = format_rate_display(commission_rate)
        
        commission_label = ctk.CTkLabel(f, text=f"Komisyon Oranı: {commission_display}",
                                       font=ctk.CTkFont(size=11),
                                       text_color=("gray50", "gray70"))
        commission_label.pack(fill="x", pady=(5, 0))
        
        # Hesaplama özeti için frame
        summary_frame = ctk.CTkFrame(m, fg_color=("gray85", "gray17"), corner_radius=10)
        summary_frame.pack(fill="x", pady=15)
        
        summary_content = ctk.CTkFrame(summary_frame, fg_color="transparent")
        summary_content.pack(fill="x", padx=15, pady=12)
        
        islem_label = ctk.CTkLabel(summary_content, text="İşlem Tutarı: -", 
                                  font=ctk.CTkFont(size=12), anchor="w")
        islem_label.pack(fill="x")
        
        komisyon_label = ctk.CTkLabel(summary_content, text="Komisyon: -", 
                                     font=ctk.CTkFont(size=12), anchor="w")
        komisyon_label.pack(fill="x", pady=3)
        
        toplam_label = ctk.CTkLabel(summary_content, text="Toplam Maliyet: -", 
                                   font=ctk.CTkFont(size=14, weight="bold"), 
                                   anchor="w", text_color=COLORS["primary"])
        toplam_label.pack(fill="x")
        
        def update_summary(*args):
            """Özet bilgileri güncelle"""
            try:
                adet = float(a_e.get() or 0)
                fiyat = float(p_e.get().replace(',', '.') or 0)
                
                islem_tutari = adet * fiyat
                komisyon = islem_tutari * commission_rate
                toplam = islem_tutari + komisyon
                
                islem_label.configure(text=f"İşlem Tutarı: {islem_tutari:,.2f} ₺")
                komisyon_label.configure(text=f"Komisyon ({commission_display}): {komisyon:,.2f} ₺")
                toplam_label.configure(text=f"Toplam Maliyet: {toplam:,.2f} ₺")
            except:
                islem_label.configure(text="İşlem Tutarı: -")
                komisyon_label.configure(text="Komisyon: -")
                toplam_label.configure(text="Toplam Maliyet: -")
        
        # Entry'lerde değişiklik olunca özeti güncelle
        a_e.bind("<KeyRelease>", update_summary)
        p_e.bind("<KeyRelease>", update_summary)
        
        def save():
            try:
                sym = s_e.get().strip().upper()
                adet = int(a_e.get())
                fiyat = float(p_e.get().replace(',', '.'))
                
                if not sym or adet <= 0 or fiyat <= 0:
                    raise ValueError()
                
                # Komisyon ve toplam tutarı hesapla
                islem_tutari = adet * fiyat
                komisyon = islem_tutari * commission_rate
                
                # İşlemi kaydet - KOMİSYON DAHİL
                self.db.add_transaction({
                    "tip": "Alım",
                    "sembol": sym,
                    "adet": adet,
                    "fiyat": fiyat,
                    "toplam": islem_tutari,  # İşlem tutarı
                    "komisyon": komisyon,    # Komisyon ayrıca kaydediliyor
                    "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                # Portföyü yeniden hesapla
                self.db.recalculate_portfolio_from_transactions()
                
                # Bilgilendirme mesajında komisyon göster
                showinfo("Başarılı", 
                        f"✅ Alım işlemi kaydedildi\n\n"
                        f"{sym}: {adet} adet x {fiyat:.2f}₺\n"
                        f"Komisyon: {komisyon:.2f}₺\n"
                        f"Toplam Maliyet: {islem_tutari + komisyon:.2f}₺")
                
                d.destroy()
                self._trigger_update()
            except ValueError:
                return showerror("Hata", "Lütfen geçerli değerler girin.")
        
        btn_frame = ctk.CTkFrame(m, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        ctk.CTkButton(btn_frame, text="💾 Kaydet", command=save, height=40).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(btn_frame, text="❌ İptal", command=d.destroy, height=40, fg_color=("gray60", "gray40")).pack(side="left", expand=True, fill="x", padx=(5, 0))
        
        # Dinamik boyut ayarlaması
        d.update_idletasks()
        required_height = d.winfo_reqheight()
        min_height = 450
        max_height = 800
        final_height = max(min_height, min(required_height, max_height))
        d.geometry(f"450x{final_height}")
        
        # Pencerenin ekranın ortasında konumlandırılması
        d.update_idletasks()
        x = (d.winfo_screenwidth() // 2) - (450 // 2)
        y = (d.winfo_screenheight() // 2) - (final_height // 2)
        d.geometry(f"450x{final_height}+{x}+{y}")

    def sell_stock(self, stock):
        """Satış İşlemi (KOMİSYON HESAPLAMALI)"""
        d = ctk.CTkToplevel(self.parent)
        d.title(f"Satış İşlemi: {stock['sembol']}")
        d.geometry("450x1")  # Geçici boyut
        d.transient(self.parent)
        d.grab_set()
        
        # USER ID AL
        user_id = self.get_user_id()
    
        # Komisyon oranını al - DÜZELTİLDİ
        settings = self.db.get_settings(user_id)
        commission_rate = settings.get("komisyon_orani", 0.0004)  # ✅ komisyon_orani
        
        try:
            if isinstance(commission_rate, str):
                commission_rate = float(commission_rate.replace(',', '.'))
            else:
                commission_rate = float(commission_rate)
        except:
            commission_rate = 0.0004
        
        # ... komisyon hesaplama ...
        
        def exe():
            try:
                adet = int(a_e.get())
                fiyat = float(p_e.get().replace(',', '.'))
                
                if adet <= 0 or adet > stock["adet"] or fiyat <= 0:
                    raise ValueError()
                
                # Toplam hesapla
                islem_tutari = adet * fiyat
                komisyon = islem_tutari * commission_rate
                
                # İşlemi kaydet - USER ID İLE
                self.db.add_transaction({
                    "tip": "Satış",
                    "sembol": stock["sembol"],
                    "adet": adet,
                    "fiyat": fiyat,
                    "toplam": islem_tutari,
                    "komisyon": komisyon,
                    "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }, user_id=user_id)  # ✅ user_id eklendi
                
                # Portföyü yeniden hesapla - USER ID İLE
                self.db.recalculate_portfolio_from_transactions(user_id)  # ✅ user_id eklendi
                
                # Kar/Zarar hesapla - komisyon etkisini dahil et
                kar_zarar = (fiyat - stock['ort_maliyet']) * adet
                net_kazanc = kar_zarar - komisyon
                
                showinfo("Başarılı", 
                        f"✅ Satış tamamlandı!\n\n"
                        f"{stock['sembol']}: {adet} adet x {fiyat:.2f}₺\n"
                        f"Kar/Zarar: {kar_zarar:,.2f}₺\n"
                        f"Komisyon: -{komisyon:,.2f}₺\n"
                        f"Net Kazanç: {net_kazanc:,.2f}₺")
                
                d.destroy()
                self._trigger_update()
            except ValueError:
                return showerror("Hata", "Geçersiz adet veya fiyat.")

        m = ctk.CTkFrame(d)
        m.pack(fill="both", expand=True, padx=25, pady=25)
        
        ctk.CTkLabel(m, text=f"💰 {stock['sembol']} Sat", 
                    font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 15))
        
        # Mevcut bilgiler
        info_frame = ctk.CTkFrame(m, fg_color=("gray85", "gray17"), corner_radius=10)
        info_frame.pack(fill="x", pady=(0, 15))
        
        info_content = ctk.CTkFrame(info_frame, fg_color="transparent")
        info_content.pack(fill="x", padx=15, pady=12)
        
        ctk.CTkLabel(info_content, text=f"Portföyde: {stock['adet']} adet", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w")
        ctk.CTkLabel(info_content, text=f"Ortalama Maliyet: {stock['ort_maliyet']:.2f} ₺", 
                    font=ctk.CTkFont(size=12)).pack(anchor="w")
        
        # Form
        form_frame = ctk.CTkFrame(m, fg_color="transparent")
        form_frame.pack(fill="x")
        
        ctk.CTkLabel(form_frame, text=f"Satılacak Adet (Maks: {stock['adet']}):", 
                    anchor="w").pack(fill="x")
        a_e = ctk.CTkEntry(form_frame, height=38)
        a_e.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(form_frame, text="Satış Fiyatı (₺):", anchor="w").pack(fill="x")
        p_e = ctk.CTkEntry(form_frame, height=38)
        p_e.insert(0, str(stock.get('guncel_fiyat', stock['ort_maliyet'])))
        p_e.pack(fill="x", pady=(0, 8))
        
        ctk.CTkLabel(form_frame, text=f"Komisyon Oranı: {commission_display}", 
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack(fill="x", pady=(5, 0))
        
        # Hesaplama özeti
        summary_frame = ctk.CTkFrame(m, fg_color=("gray85", "gray17"), corner_radius=10)
        summary_frame.pack(fill="x", pady=15)
        
        summary_content = ctk.CTkFrame(summary_frame, fg_color="transparent")
        summary_content.pack(fill="x", padx=15, pady=12)
        
        islem_label = ctk.CTkLabel(summary_content, text="İşlem Tutarı: -", 
                                  font=ctk.CTkFont(size=12), anchor="w")
        islem_label.pack(fill="x")
        
        kar_zarar_label = ctk.CTkLabel(summary_content, text="Kar/Zarar: -", 
                                       font=ctk.CTkFont(size=12), anchor="w")
        kar_zarar_label.pack(fill="x", pady=3)
        
        komisyon_label = ctk.CTkLabel(summary_content, text="Komisyon: -", 
                                     font=ctk.CTkFont(size=12), anchor="w")
        komisyon_label.pack(fill="x", pady=3)
        
        net_label = ctk.CTkLabel(summary_content, text="Net Kazanç: -", 
                                font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
        net_label.pack(fill="x")
        
        def update_summary(*args):
            """Özet bilgileri güncelle"""
            try:
                adet = float(a_e.get() or 0)
                fiyat = float(p_e.get().replace(',', '.') or 0)
                
                islem_tutari = adet * fiyat
                kar_zarar = (fiyat - stock['ort_maliyet']) * adet
                komisyon = islem_tutari * commission_rate
                net_kazanc = kar_zarar - komisyon
                
                color = COLORS["success"] if kar_zarar >= 0 else COLORS["danger"]
                net_color = COLORS["success"] if net_kazanc >= 0 else COLORS["danger"]
                
                islem_label.configure(text=f"İşlem Tutarı: {islem_tutari:,.2f} ₺")
                kar_zarar_label.configure(text=f"Kar/Zarar: {kar_zarar:+,.2f} ₺", text_color=color)
                komisyon_label.configure(text=f"Komisyon ({commission_display}): -{komisyon:,.2f} ₺")
                net_label.configure(text=f"Net Kazanç: {net_kazanc:+,.2f} ₺", text_color=net_color)
            except:
                islem_label.configure(text="İşlem Tutarı: -")
                kar_zarar_label.configure(text="Kar/Zarar: -")
                komisyon_label.configure(text="Komisyon: -")
                net_label.configure(text="Net Kazanç: -")
        
        # Entry'lerde değişiklik olunca özeti güncelle
        a_e.bind("<KeyRelease>", update_summary)
        p_e.bind("<KeyRelease>", update_summary)
        
        btn_frame = ctk.CTkFrame(m, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        btn_font = ctk.CTkFont(size=13, weight="bold")
        ctk.CTkButton(btn_frame, text="💰 Sat", command=exe, height=40, font=btn_font).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(btn_frame, text="❌ İptal", command=d.destroy, height=40, font=btn_font, fg_color=("gray60", "gray40")).pack(side="left", expand=True, fill="x", padx=(5, 0))
        
        # Dinamik boyut ayarlaması
        d.update_idletasks()
        required_height = d.winfo_reqheight()
        min_height = 500
        max_height = 800
        final_height = max(min_height, min(required_height, max_height))
        d.geometry(f"450x{final_height}")
        
        # Pencerenin ekranın ortasında konumlandırılması
        d.update_idletasks()
        x = (d.winfo_screenwidth() // 2) - (450 // 2)
        y = (d.winfo_screenheight() // 2) - (final_height // 2)
        d.geometry(f"450x{final_height}+{x}+{y}")

    def add_dividend_dialog(self):
        """Temettü Ekle"""
        d = ctk.CTkToplevel(self.parent)
        d.title("Temettü Ekle")
        d.geometry("450x1")  # Geçici boyut
        d.transient(self.parent)
        d.grab_set()
        
        ctk.CTkLabel(d, text="💵 Temettü Ekle", 
                    font=ctk.CTkFont(size=24, weight="bold")).pack(pady=20)
        
        form_frame = ctk.CTkFrame(d, fg_color="transparent")
        form_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkLabel(form_frame, text="Hisse Sembolü:", anchor="w").pack(fill="x")
        symbol_entry = self._create_validated_entry(form_frame, placeholder_text="THYAO")
        symbol_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form_frame, text="Hisse Başı Net Tutar (₺):", anchor="w").pack(fill="x")
        amount_entry = ctk.CTkEntry(form_frame, placeholder_text="1.25")
        amount_entry.pack(fill="x", pady=(0, 15))
        
        def save_dividend():
            try:
                symbol = symbol_entry.get().strip().upper()
                per_share_amount = float(amount_entry.get().strip().replace(',', '.'))
                
                if not symbol or per_share_amount <= 0:
                    raise ValueError
            except ValueError:
                return showerror("Hata", "Lütfen geçerli değerler girin.")
            
            # USER ID AL
            user_id = self.get_user_id()
            
            # Portföyden kontrol - USER ID İLE
            stock_in_portfolio = next(
                (s for s in self.db.get_portfolio(user_id) if s['sembol'] == symbol), 
                None
            )
            
            if not stock_in_portfolio:
                return showerror("Hata", f"{symbol} hissesi portföyünüzde bulunamadı.")
            
            stock_quantity = stock_in_portfolio['adet']
            total_dividend_amount = stock_quantity * per_share_amount
            
            # Temettü ekle - USER ID İLE
            self.db.add_dividend({
                "sembol": symbol,
                "tutar": total_dividend_amount,
                "adet": stock_quantity,
                "hisse_basi_tutar": per_share_amount,
                "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, user_id=user_id)  # ✅ user_id eklendi
            
            showinfo("Başarılı", f"{symbol} için {total_dividend_amount:,.2f} ₺ temettü eklendi!")
            d.destroy()
            self._trigger_update()
        
        btn_frame = ctk.CTkFrame(d, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=10)
        
        ctk.CTkButton(btn_frame, text="💾 Kaydet", command=save_dividend, height=40).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(btn_frame, text="❌ İptal", command=d.destroy, height=40, fg_color=("gray60", "gray40")).pack(side="left", expand=True, fill="x", padx=(5, 0))
        
        # Dinamik boyut ayarlaması
        d.update_idletasks()
        required_height = d.winfo_reqheight()
        min_height = 350
        max_height = 600
        final_height = max(min_height, min(required_height, max_height))
        d.geometry(f"450x{final_height}")
        
        # Pencerenin ekranın ortasında konumlandırılması
        d.update_idletasks()
        x = (d.winfo_screenwidth() // 2) - (450 // 2)
        y = (d.winfo_screenheight() // 2) - (final_height // 2)
        d.geometry(f"450x{final_height}+{x}+{y}")

    def update_price(self, stock):
        """Güncel fiyatı güncelle"""
        try:
            t = yf.Ticker(f"{stock['sembol']}.IS")
            h = t.history(period="1d")
            
            if not h.empty:
                new_price = h['Close'].iloc[-1]
                # DB'ye güncel fiyatı kaydet
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE portfolios 
                        SET guncel_fiyat = ? 
                        WHERE sembol = ?
                    ''', (new_price, stock['sembol']))
                showinfo("✓", f"{stock['sembol']}\n{new_price:.2f} ₺")
                self.refresh_ui()
            else:
                showerror("Hata", "Fiyat alınamadı!")
        except Exception as e:
            showerror("Hata", f"Bağlantı hatası!\n{str(e)}")
    
    def export_to_excel(self):
        """Excel'e aktar - CSV formatında"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dosyası (Excel)", "*.csv"), ("Tüm Dosyalar", "*.*")],
            initialfile=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not filename:
            return
        
        try:
            # Portföy verilerini al
            portfolio = self.db.get_portfolio()
            
            if not portfolio:
                showinfo("Bilgi", "Portföyde hisse yok!")
                return
            
            # CSV'ye yaz (UTF-8 BOM ile Türkçe karakter desteği)
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')  # Excel için noktalı virgül
                
                # Başlıklar
                writer.writerow([
                    'Sembol', 
                    'Adet', 
                    'Ortalama Maliyet (₺)', 
                    'Güncel Fiyat (₺)', 
                    'Toplam Maliyet (₺)', 
                    'Güncel Değer (₺)', 
                    'Kar/Zarar (₺)', 
                    'Kar/Zarar (%)'
                ])
                
                # Toplamlar için
                total_cost = 0
                total_value = 0
                total_profit = 0
                
                # Her hisse için satır
                for stock in portfolio:
                    g = stock.get("guncel_fiyat", stock["ort_maliyet"])
                    tm = stock["adet"] * stock["ort_maliyet"]
                    tv = stock["adet"] * g
                    kz = tv - tm
                    kz_p = (kz / tm * 100) if tm > 0 else 0
                    
                    total_cost += tm
                    total_value += tv
                    total_profit += kz
                    
                    writer.writerow([
                        stock["sembol"],
                        stock["adet"],
                        f"{stock['ort_maliyet']:.2f}".replace('.', ','),  # Excel için virgül
                        f"{g:.2f}".replace('.', ','),
                        f"{tm:.2f}".replace('.', ','),
                        f"{tv:.2f}".replace('.', ','),
                        f"{kz:.2f}".replace('.', ','),
                        f"{kz_p:.2f}".replace('.', ',')
                    ])
                
                # Boş satır
                writer.writerow([])
                
                # Toplamlar satırı
                total_profit_percent = (total_profit / total_cost * 100) if total_cost > 0 else 0
                writer.writerow([
                    'TOPLAM',
                    '',
                    '',
                    '',
                    f"{total_cost:.2f}".replace('.', ','),
                    f"{total_value:.2f}".replace('.', ','),
                    f"{total_profit:.2f}".replace('.', ','),
                    f"{total_profit_percent:.2f}".replace('.', ',')
                ])
                
                # Özet bilgiler
                writer.writerow([])
                writer.writerow(['ÖZET BİLGİLER'])
                writer.writerow(['Toplam Hisse Sayısı', len(portfolio)])
                writer.writerow(['Toplam Adet', sum(s['adet'] for s in portfolio)])
                writer.writerow(['Dışa Aktarma Tarihi', datetime.now().strftime('%d.%m.%Y %H:%M')])
            
            showinfo("Başarılı", 
                    f"✅ Portföy Excel'e aktarıldı!\n\n"
                    f"📁 {filename}\n\n"
                    f"💡 Excel'de açmak için:\n"
                    f"1. Dosyaya çift tıklayın\n"
                    f"2. veya Excel'de Dosya > Aç menüsünden seçin")
            
            # Dosyayı açmak ister misiniz?
            if askyesno("Dosyayı Aç", "Excel dosyasını şimdi açmak ister misiniz?"):
                import os
                os.startfile(filename)  # Windows'ta dosyayı aç
        
        except Exception as e:
            showerror("Hata", f"Excel export hatası:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def delete_stock(self, stock):
        """Hisseyi sil"""
        if askyesno("Silme Onayı", f"{stock['sembol']} hissesini ve ilgili tüm alım/satım işlemlerini silmek istediğinize emin misiniz?"):
            self.db.delete_portfolio(stock["sembol"])
            showinfo("✓", f"{stock['sembol']} silindi!")
            self._trigger_update()

    def update_all_prices(self):
        """Tüm fiyatları güncelle"""
        # USER ID AL
        user_id = self.get_user_id()
        
        portfolio = self.db.get_portfolio(user_id)  # ✅ user_id eklendi
        
        if not portfolio:
            return showinfo("Bilgi", "Portföy boş!")
        
        updated = 0
        for s in portfolio:
            try:
                t = yf.Ticker(f"{s['sembol']}.IS")
                h = t.history(period="1d")
                if not h.empty:
                    new_price = h['Close'].iloc[-1]
                    # DB'ye güncel fiyatı kaydet
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE portfolios 
                            SET guncel_fiyat = ? 
                            WHERE sembol = ? AND user_id = ?
                        ''', (new_price, s['sembol'], user_id))  # ✅ user_id eklendi
                    updated += 1
            except:
                pass
        
        showinfo("✓", f"{updated}/{len(portfolio)} güncellendi!")
        self.refresh_ui()