# pages/dashboard_page.py - TAM VE GÜNCELLENMİŞ VERSİYON

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datetime import datetime
import random
import threading
from config import COLORS
from ui_utils import showinfo, showerror, askyesno

def normalize_symbol(text):
    """Türkçe karakterleri İngilizce'ye çevir ve büyük harf yap"""
    tr_map = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    normalized = text.translate(tr_map).upper()
    return ''.join(c for c in normalized if c.isalpha())


class DashboardPage:
    def __init__(self, parent, db, api, theme, currency_data=None, index_data=None):
        self.parent = parent
        self.db = db
        self.api = api
        self.theme = theme
        self.currency_cache = currency_data or []
        self.index_cache = index_data or []
        self.clock_timer = None
        self.market_timer = None
        self.currency_container = None
        self.index_container = None
    
    def create(self):
        self.main_container = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        self.main_container.grid_rowconfigure(0, weight=0, minsize=60)
        self.main_container.grid_rowconfigure(1, weight=0, minsize=80)
        self.main_container.grid_rowconfigure(2, weight=0, minsize=85)
        self.main_container.grid_rowconfigure(3, weight=1, minsize=140)
        self.main_container.grid_rowconfigure(4, weight=0, minsize=140)
        self.main_container.grid_rowconfigure(5, weight=1, minsize=100)
        self.main_container.grid_rowconfigure(6, weight=2, minsize=250)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        self.create_header()
        self.create_quick_actions()
        self.create_currency_row()
        self.create_kpi_row()
        self.create_indices_row()
        self.create_stats_row()
        self.create_charts_row()
    
    # ========== HEADER & CLOCK ==========
    
    def create_header(self):
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent", height=60)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=(0, 3))
        header_frame.grid_propagate(False)
        
        left_header = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_header.pack(side="left", fill="both", expand=True)
        
        ctk.CTkLabel(left_header, text="📊 Dashboard", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left", padx=(5, 10))
        
        self.clock_label = ctk.CTkLabel(left_header, text="", font=ctk.CTkFont(size=12), text_color=("gray50", "gray60"))
        self.clock_label.pack(side="left", padx=5)
        self.update_clock()
        
        self.market_status_label = ctk.CTkLabel(left_header, text="", font=ctk.CTkFont(size=11, weight="bold"))
        self.market_status_label.pack(side="left", padx=10)
        self.update_market_status()

    def update_clock(self):
        now = datetime.now()
        months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        time_str = f"{now.day} {months[now.month-1]} {now.year}, {now.strftime('%H:%M:%S')}"
        if hasattr(self, 'clock_label') and self.clock_label.winfo_exists():
            try:
                self.clock_label.configure(text=f"🕐 {time_str}")
                self.clock_timer = self.parent.after(1000, self.update_clock)
            except: pass

    def update_market_status(self):
        now = datetime.now()
        is_open = now.weekday() < 5 and 10 <= now.hour < 18
        status = "🟢 Piyasa Açık" if is_open else "🔴 Piyasa Kapalı"
        color = COLORS["success"] if is_open else COLORS["danger"]
        if hasattr(self, 'market_status_label') and self.market_status_label.winfo_exists():
            try:
                self.market_status_label.configure(text=status, text_color=color)
                self.market_timer = self.parent.after(60000, self.update_market_status)
            except: pass

    # ========== HIZLI İŞLEMLER ==========
        
    def create_quick_actions(self):
        quick_frame = ctk.CTkFrame(self.main_container, fg_color=("gray90", "gray13"), corner_radius=8)
        quick_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        content = ctk.CTkFrame(quick_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=10)
        ctk.CTkLabel(content, text="⚡ Hızlı İşlemler", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 8))
        button_container = ctk.CTkFrame(content, fg_color="transparent")
        button_container.pack(fill="x", expand=True)
        actions = [
            ("➕ Al", self.quick_add_stock, COLORS["success"]),
            ("📤 Sat", self.quick_sell_stock, COLORS["danger"]),
            ("💵 Temettü", self.quick_add_dividend, COLORS["purple"]),
            ("🔄 Güncelle", self.update_all_prices, COLORS["primary"]),
            ("📊 Excel", self.export_to_excel, COLORS["orange"]),
            ("💾 Yedek", self.quick_backup, COLORS["warning"]),
        ]
        button_count = len(actions)
        for i in range(button_count):
            button_container.grid_columnconfigure(i, weight=1, uniform="button")
        for i, (text, command, color) in enumerate(actions):
            btn = ctk.CTkButton(
                button_container, text=text, command=command, fg_color=color, 
                hover_color=self.darken_color(color), height=36, corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"), border_width=0)
            btn.grid(row=0, column=i, padx=4, sticky="ew")
      
    
    
    def quick_add_stock(self):
        """Hızlı hisse alımı - Dinamik ve responsive dialog"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("➕ Hisse Al")
        dialog.geometry("500x680")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 250
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 340
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(main_frame, text="➕ Yeni Hisse Ekle", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 20))
        
        form = ctk.CTkFrame(main_frame, fg_color="transparent")
        form.pack(fill="x")
        
        entries = {}
        fields = [
            ("sembol", "Sembol:", "THYAO"),
            ("miktar", "Adet:", "100"),
            ("fiyat", "Alım Fiyatı (₺):", "50.00"),
            ("tarih", "Tarih (GG.AA.YYYY):", datetime.now().strftime("%d.%m.%Y")),  # ✅ Otomatik tarih
            ("notlar", "Notlar:", "Açıklama (opsiyonel)")
        ]
        
        for key, label, placeholder in fields:
            ctk.CTkLabel(form, text=label, font=ctk.CTkFont(size=13), anchor="w").pack(fill="x", pady=(12 if key != "sembol" else 0, 4))
            entry = ctk.CTkEntry(form, placeholder_text=placeholder, height=40)
            
            # ✅ Tarih için otomatik değer
            if key == "tarih":
                entry.insert(0, datetime.now().strftime("%d.%m.%Y"))
            
            entry.pack(fill="x")
            entries[key] = entry
        
        # ✅ SEMBOL NORMALİZASYONU
        def on_symbol_change(event):
            current = entries["sembol"].get()
            normalized = normalize_symbol(current)
            if current != normalized:
                cursor_pos = entries["sembol"].index(ctk.INSERT)
                entries["sembol"].delete(0, ctk.END)
                entries["sembol"].insert(0, normalized)
                entries["sembol"].icursor(min(cursor_pos, len(normalized)))
        
        entries["sembol"].bind("<KeyRelease>", on_symbol_change)
        
        summary_frame = ctk.CTkFrame(main_frame, fg_color=("gray85", "gray20"), corner_radius=10)
        summary_frame.pack(fill="x", pady=(20, 15))
        
        summary_content = ctk.CTkFrame(summary_frame, fg_color="transparent")
        summary_content.pack(fill="both", expand=True, padx=15, pady=12)
        
        islem_label = ctk.CTkLabel(summary_content, text="İşlem Tutarı: -", font=ctk.CTkFont(size=12), anchor="w")
        islem_label.pack(fill="x")
        
        komisyon_label = ctk.CTkLabel(summary_content, text="Komisyon: -", font=ctk.CTkFont(size=12), anchor="w")
        komisyon_label.pack(fill="x", pady=3)
        
        toplam_label = ctk.CTkLabel(summary_content, text="Toplam Maliyet: -", font=ctk.CTkFont(size=14, weight="bold"), anchor="w", text_color=COLORS["primary"])
        toplam_label.pack(fill="x")
        
        settings_mgr = self.get_settings_manager()
        komisyon_oran = 0.0004
        if settings_mgr:
            try:
                komisyon_oran = float(settings_mgr.get("komisyon_orani", 0.0004))
            except: pass
            
        def update_summary(*args):
            try:
                adet = float(entries["miktar"].get() or 0)
                fiyat = float(entries["fiyat"].get().replace(',', '.') or 0)
                islem_tutari = adet * fiyat
                komisyon = islem_tutari * komisyon_oran
                toplam = islem_tutari + komisyon
                islem_label.configure(text=f"İşlem Tutarı: {islem_tutari:,.2f} ₺")
                komisyon_label.configure(text=f"Komisyon (%{(komisyon_oran*100):.3f}): {komisyon:,.2f} ₺")
                toplam_label.configure(text=f"Toplam Maliyet: {toplam:,.2f} ₺")
            except:
                islem_label.configure(text="İşlem Tutarı: -")
                komisyon_label.configure(text="Komisyon: -")
                toplam_label.configure(text="Toplam Maliyet: -")
        
        entries["miktar"].bind("<KeyRelease>", update_summary)
        entries["fiyat"].bind("<KeyRelease>", update_summary)
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        def save_purchase():
            try:
                # ✅ BOŞ DEĞER KONTROLÜ
                sembol = entries["sembol"].get().strip().upper()
                sembol = normalize_symbol(sembol)  # ✅ Ekstra normalizasyon
                
                miktar_str = entries["miktar"].get().strip()
                fiyat_str = entries["fiyat"].get().strip().replace(',', '.')
                
                if not sembol:
                    showerror("Hata", "Lütfen sembol girin!")
                    return
                
                if not miktar_str or not fiyat_str:
                    showerror("Hata", "Lütfen adet ve fiyat bilgilerini girin!")
                    return
                
                try:
                    miktar = int(miktar_str)
                    fiyat = float(fiyat_str)
                except ValueError:
                    showerror("Hata", "Lütfen geçerli sayılar girin!")
                    return
                
                notlar = entries["notlar"].get().strip()
                
                try:
                    tarih = datetime.strptime(entries["tarih"].get(), "%d.%m.%Y")
                except:
                    tarih = datetime.now()
                
                if miktar <= 0 or fiyat <= 0:
                    showerror("Hata", "Adet ve fiyat 0'dan büyük olmalı!")
                    return
                
                brut_tutar = miktar * fiyat
                komisyon = brut_tutar * komisyon_oran
                toplam = brut_tutar + komisyon
                
                user_id = self.get_user_id()
                
                transaction_data = {
                    'sembol': sembol, 'tip': 'Alım',
                    'adet': miktar, 'fiyat': fiyat,
                    'toplam': brut_tutar, 'komisyon': komisyon, 
                    'tarih': tarih.strftime('%Y-%m-%d %H:%M:%S')}
                
                transaction_id = self.db.add_transaction(transaction_data, user_id=user_id)
                
                if not transaction_id:
                    showerror("Hata", "İşlem kaydedilemedi!")
                    return
                
                self.db.recalculate_portfolio_from_transactions(user_id)
                
                showinfo("Başarılı", f"✅ Alım işlemi kaydedildi: {sembol}")
                dialog.destroy()
                self.refresh_dashboard()
            except Exception as e:
                showerror("Hata", f"İşlem kaydedilemedi: {e}")
                import traceback
                traceback.print_exc()

        ctk.CTkButton(btn_frame, text="💾 Satın Al", command=save_purchase, height=45, font=ctk.CTkFont(size=14, weight="bold"), fg_color=COLORS["success"]).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_frame, text="❌ İptal", command=dialog.destroy, height=45, font=ctk.CTkFont(size=14, weight="bold"), fg_color=("gray70", "gray30")).pack(side="left", expand=True, padx=(5, 0))

    def quick_sell_stock(self):
        """Hızlı hisse satışı - GELİŞMİŞ HESAPLAMA"""
        user_id = self.get_user_id()
        portfolio = self.db.get_portfolio(user_id)
        
        if not portfolio:
            showerror("Hata", "Portföyde satılacak hisse yok!")
            return
        
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("📤 Hisse Sat")
        dialog.geometry("540x850")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 270
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 425
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(main_frame, text="📤 Hisse Sat", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 15))
        
        form = ctk.CTkFrame(main_frame, fg_color="transparent")
        form.pack(fill="x")
        
        ctk.CTkLabel(form, text="Hisse Sembolü:", font=ctk.CTkFont(size=13), anchor="w").pack(fill="x", pady=(0, 4))
        stock_options = [f"{s['sembol']} ({s['adet']} adet)" for s in portfolio]
        stock_var = ctk.StringVar(value=stock_options[0])
        stock_combo = ctk.CTkComboBox(form, values=stock_options, variable=stock_var, height=40)
        stock_combo.pack(fill="x", pady=(0, 15))
        
        info_frame = ctk.CTkFrame(form, fg_color=("gray85", "gray20"), corner_radius=10)
        info_frame.pack(fill="x", pady=(0, 15))
        info_label = ctk.CTkLabel(info_frame, text="", font=ctk.CTkFont(size=12), anchor="w", justify="left")
        info_label.pack(fill="x", padx=15, pady=12)
        
        ctk.CTkLabel(form, text="Satılacak Adet:", font=ctk.CTkFont(size=13), anchor="w").pack(fill="x", pady=(0, 4))
        amount_entry = ctk.CTkEntry(form, placeholder_text="100", height=40)
        amount_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form, text="Satış Fiyatı (₺):", font=ctk.CTkFont(size=13), anchor="w").pack(fill="x", pady=(0, 4))
        price_entry = ctk.CTkEntry(form, placeholder_text="50.00", height=40)
        price_entry.pack(fill="x")
        
        ctk.CTkButton(form, text="📊 Güncel Fiyatı Getir", 
                      command=lambda: self.fetch_and_set_price(stock_var, price_entry), 
                      height=30, font=ctk.CTkFont(size=11, weight="bold")).pack(fill="x", pady=(8, 15))
        
        ctk.CTkLabel(form, text="Tarih (GG.AA.YYYY):", font=ctk.CTkFont(size=13), anchor="w").pack(fill="x", pady=(0, 4))
        date_entry = ctk.CTkEntry(form, height=40)
        date_entry.insert(0, datetime.now().strftime("%d.%m.%Y"))
        date_entry.pack(fill="x", pady=(0, 20))
        
        # ✅ ÖZET PANEL
        summary_frame = ctk.CTkFrame(main_frame, fg_color=("gray85", "gray20"), corner_radius=10)
        summary_frame.pack(fill="x", pady=(0, 15))
        
        summary_content = ctk.CTkFrame(summary_frame, fg_color="transparent")
        summary_content.pack(fill="x", padx=15, pady=12)
        
        satis_tutari_label = ctk.CTkLabel(summary_content, text="💵 Satış Tutarı: -", 
                                          font=ctk.CTkFont(size=12), anchor="w")
        satis_tutari_label.pack(fill="x", pady=2)
        
        komisyon_label = ctk.CTkLabel(summary_content, text="📊 Komisyon: -", 
                                      font=ctk.CTkFont(size=12), anchor="w")
        komisyon_label.pack(fill="x", pady=2)
        
        vergi_label = ctk.CTkLabel(summary_content, text="🏛️ Vergi: -", 
                                   font=ctk.CTkFont(size=12), anchor="w")
        vergi_label.pack(fill="x", pady=2)
        
        ctk.CTkLabel(summary_content, text="─" * 40, 
                    font=ctk.CTkFont(size=10), text_color=("gray60", "gray50")).pack(fill="x", pady=3)
        
        net_tutar_label = ctk.CTkLabel(summary_content, text="💰 Net Tutar: -", 
                                       font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        net_tutar_label.pack(fill="x", pady=2)
        
        kar_zarar_label = ctk.CTkLabel(summary_content, text="📊 Kar/Zarar: -", 
                                       font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        kar_zarar_label.pack(fill="x", pady=2)
        
        # ✅ AYARLARDAN ORANLARI AL - DÜZELTİLDİ
        settings_mgr = self.get_settings_manager()
        
        # ✅ DOĞRU KEY'LER: commission_rate ve tax_rate (İngilizce)
        komisyon_oran = 0.0004  # Varsayılan
        vergi_oran = 0.0  # Varsayılan
        
        if settings_mgr:
            try:
                komisyon_oran = float(settings_mgr.get("commission_rate", 0.0004))
            except:
                komisyon_oran = 0.0004
            
            try:
                vergi_oran = float(settings_mgr.get("tax_rate", 0.0))
            except:
                vergi_oran = 0.0
        
        print(f"[DEBUG] Komisyon oranı: {komisyon_oran}, Vergi oranı: {vergi_oran}")  # ✅ Debug
        
        # ✅ FONKSİYONLARI ÖNCE TANIMLA
        def reset_labels():
            """Label'ları sıfırla"""
            satis_tutari_label.configure(text="💵 Satış Tutarı: -", text_color=("gray50", "gray60"))
            komisyon_label.configure(text="📊 Komisyon: -", text_color=("gray50", "gray60"))
            vergi_label.configure(text="🏛️ Vergi: -", text_color=("gray50", "gray60"))
            net_tutar_label.configure(text="💰 Net Tutar: -", text_color=("gray50", "gray60"))
            kar_zarar_label.configure(text="📊 Kar/Zarar: -", text_color=("gray50", "gray60"))
        
        def calculate_and_update(*args):
            """Satış özetini hesapla ve güncelle - DÜZELTİLDİ"""
            try:
                selected = stock_var.get()
                sembol = selected.split(" (")[0].strip()
                stock = next((s for s in portfolio if s['sembol'] == sembol), None)
                
                if not stock:
                    reset_labels()
                    return
                
                miktar_str = amount_entry.get().strip()
                fiyat_str = price_entry.get().strip().replace(',', '.')
                
                if not miktar_str or not fiyat_str:
                    reset_labels()
                    return
                
                try:
                    miktar = int(miktar_str)
                    fiyat = float(fiyat_str)
                except:
                    reset_labels()
                    return
                
                if miktar <= 0 or fiyat <= 0:
                    reset_labels()
                    return
                
                # ✅ HESAPLAMALAR - SATIŞ FİYATINDAN
                brut_tutar = miktar * fiyat  # ✅ Satış fiyatından
                komisyon = brut_tutar * komisyon_oran  # ✅ Satış tutarından komisyon
                
                # ✅ Kar hesabı
                maliyet = miktar * stock['ort_maliyet']
                kar = (brut_tutar - komisyon) - maliyet  # ✅ Net satış - maliyet
                
                # ✅ Vergi (sadece kar varsa)
                if kar > 0:
                    vergi = kar * vergi_oran
                else:
                    vergi = 0
                
                # ✅ Net tutar
                net_tutar = brut_tutar - komisyon - vergi
                toplam_kar_zarar = net_tutar - maliyet
                
                # Oran gösterimi
                komisyon_yuzde = komisyon_oran * 100
                vergi_yuzde = vergi_oran * 100
                
                # ✅ Debug
                print(f"[DEBUG] Brüt: {brut_tutar:.2f}, Komisyon: {komisyon:.2f} ({komisyon_yuzde:.4f}%), "
                      f"Kar: {kar:.2f}, Vergi: {vergi:.2f} ({vergi_yuzde:.4f}%), Net: {net_tutar:.2f}")
                
                # Label'ları güncelle
                satis_tutari_label.configure(
                    text=f"💵 Satış Tutarı: {brut_tutar:,.2f} ₺",
                    text_color=COLORS["primary"]
                )
                
                komisyon_label.configure(
                    text=f"📊 Komisyon (%{komisyon_yuzde:.4f}): -{komisyon:,.2f} ₺",
                    text_color=COLORS["warning"]
                )
                
                if vergi > 0:
                    vergi_label.configure(
                        text=f"🏛️ Vergi (%{vergi_yuzde:.2f} kar üzerinden): -{vergi:,.2f} ₺",
                        text_color=COLORS["orange"]
                    )
                else:
                    vergi_label.configure(
                        text=f"🏛️ Vergi: Yok (kar yok)",
                        text_color=("gray50", "gray60")
                    )
                
                net_color = COLORS["success"] if net_tutar > maliyet else COLORS["warning"]
                net_tutar_label.configure(
                    text=f"💰 Net Tutar: {net_tutar:,.2f} ₺",
                    text_color=net_color
                )
                
                kar_zarar_color = COLORS["success"] if toplam_kar_zarar >= 0 else COLORS["danger"]
                kar_zarar_icon = "📈" if toplam_kar_zarar >= 0 else "📉"
                kar_zarar_label.configure(
                    text=f"{kar_zarar_icon} Kar/Zarar: {toplam_kar_zarar:+,.2f} ₺ ({(toplam_kar_zarar/maliyet*100):+.2f}%)",
                    text_color=kar_zarar_color
                )
            
            except Exception as e:
                print(f"[ERROR] Hesaplama hatası: {e}")
                import traceback
                traceback.print_exc()
                reset_labels()
        
        def update_info(*args):
            try:
                selected = stock_var.get()
                sembol = selected.split(" (")[0]
                stock = next((s for s in portfolio if s['sembol'] == sembol), None)
                if stock:
                    guncel = stock.get('guncel_fiyat', stock['ort_maliyet'])
                    perf = ((guncel - stock['ort_maliyet']) / stock['ort_maliyet'] * 100) if stock['ort_maliyet'] > 0 else 0
                    info_text = (f"📦 Portföyde: {stock['adet']} adet\n"
                               f"💰 Maliyet: {stock['ort_maliyet']:.2f}₺\n"
                               f"📊 Güncel: {guncel:.2f}₺\n"
                               f"{'📈' if perf >= 0 else '📉'} Performans: {perf:+.2f}%")
                    info_label.configure(text=info_text)
                    # ✅ Güncel fiyatı otomatik doldur
                    if not price_entry.get():
                        price_entry.delete(0, 'end')
                        price_entry.insert(0, f"{guncel:.2f}")
                        calculate_and_update()  # ✅ Hemen hesapla
            except: 
                pass
        
        # ✅ BIND'LERİ AYARLA
        amount_entry.bind("<KeyRelease>", calculate_and_update)
        price_entry.bind("<KeyRelease>", calculate_and_update)
        stock_combo.configure(command=lambda choice: [update_info(), calculate_and_update()])
        
        # ✅ İLK YÜKLEMEDE ÇALIŞTIR
        update_info()
        calculate_and_update()
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        def save_sale():
            """Satışı kaydet - DÜZELTİLDİ"""
            try:
                selected = stock_var.get()
                sembol = selected.split(" (")[0]
                stock = next((s for s in portfolio if s['sembol'] == sembol), None)
                if not stock: 
                    showerror("Hata", "Hisse bulunamadı!")
                    return
                
                miktar_str = amount_entry.get().strip()
                fiyat_str = price_entry.get().strip().replace(',', '.')
                
                if not miktar_str or not fiyat_str:
                    showerror("Hata", "Lütfen adet ve fiyat bilgilerini girin!")
                    return
                
                try:
                    miktar = int(miktar_str)
                    fiyat = float(fiyat_str)
                except ValueError:
                    showerror("Hata", "Lütfen geçerli sayılar girin!")
                    return
                
                try: 
                    tarih = datetime.strptime(date_entry.get(), "%d.%m.%Y")
                except: 
                    tarih = datetime.now()
                
                if miktar <= 0:
                    showerror("Hata", "Satılacak adet 0'dan büyük olmalı!")
                    return
                
                if fiyat <= 0:
                    showerror("Hata", "Satış fiyatı 0'dan büyük olmalı!")
                    return
                
                if miktar > stock['adet']: 
                    showerror("Hata", f"Yetersiz adet!\n\nPortföyde: {stock['adet']} adet\nSatmak istediğiniz: {miktar} adet")
                    return
                
                # ✅ SATIŞ HESAPLAMALARI
                brut_tutar = miktar * fiyat  # ✅ Satış fiyatından
                komisyon = brut_tutar * komisyon_oran  # ✅ Satış tutarından komisyon
                
                # ✅ Kar ve vergi
                maliyet = miktar * stock['ort_maliyet']
                kar = (brut_tutar - komisyon) - maliyet
                vergi = max(0, kar * vergi_oran) if kar > 0 else 0
                
                net_tutar = brut_tutar - komisyon - vergi
                
                print(f"[DEBUG SAVE] Brüt: {brut_tutar:.2f}, Komisyon: {komisyon:.2f}, "
                      f"Kar: {kar:.2f}, Vergi: {vergi:.2f}, Net: {net_tutar:.2f}")
                
                transaction_data = {
                    'sembol': sembol, 
                    'tip': 'Satış', 
                    'adet': miktar, 
                    'fiyat': fiyat,  # ✅ Satış fiyatı
                    'toplam': brut_tutar, 
                    'komisyon': komisyon, 
                    'tarih': tarih.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                transaction_id = self.db.add_transaction(transaction_data, user_id=user_id)
                
                if not transaction_id: 
                    showerror("Hata", "İşlem kaydedilemedi!")
                    return
                
                self.db.recalculate_portfolio_from_transactions(user_id)
                
                showinfo("Başarılı", 
                        f"✅ Satış işlemi tamamlandı: {sembol}\n\n"
                        f"📊 {miktar} adet x {fiyat:.2f}₺\n"
                        f"💵 Brüt Tutar: {brut_tutar:,.2f}₺\n"
                        f"📉 Komisyon: -{komisyon:.2f}₺\n"
                        f"🏛️ Vergi: -{vergi:.2f}₺\n"
                        f"{'─' * 30}\n"
                        f"💰 Net Tutar: {net_tutar:,.2f}₺\n"
                        f"{'📈 Kar' if kar >= 0 else '📉 Zarar'}: {kar:+,.2f}₺")
                
                dialog.destroy()
                self.refresh_dashboard()
                
            except Exception as e:
                showerror("Hata", f"Satış kaydedilemedi:\n{str(e)}")
                import traceback
                traceback.print_exc()

        ctk.CTkButton(btn_frame, text="💾 Satışı Tamamla", command=save_sale, height=45, 
                      fg_color=COLORS["danger"], font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_frame, text="❌ İptal", command=dialog.destroy, height=45, 
                      fg_color=("gray70", "gray30"), font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", expand=True, padx=(5, 0))

    def quick_add_dividend(self):
        """Hızlı temettü ekleme"""
        user_id = self.get_user_id()
        portfolio = self.db.get_portfolio(user_id)
        if not portfolio: showerror("Hata", "Temettü eklenecek hisse yok!"); return
        
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("💵 Temettü Ekle")
        dialog.geometry("480x550")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 240
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 275
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(main_frame, text="💵 Temettü Ekle", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 20))
        
        form = ctk.CTkFrame(main_frame, fg_color="transparent")
        form.pack(fill="x")
        
        ctk.CTkLabel(form, text="Hisse Sembolü:", font=ctk.CTkFont(size=13), anchor="w").pack(fill="x", pady=(0, 4))
        symbols = [s['sembol'] for s in portfolio]
        symbol_var = ctk.StringVar(value=symbols[0])
        ctk.CTkComboBox(form, values=symbols, variable=symbol_var, height=40).pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form, text="Toplam Temettü Tutarı (₺):", font=ctk.CTkFont(size=13), anchor="w").pack(fill="x", pady=(0, 4))
        amount_entry = ctk.CTkEntry(form, placeholder_text="100.00", height=40)
        amount_entry.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(form, text="Tarih (GG.AA.YYYY):", font=ctk.CTkFont(size=13), anchor="w").pack(fill="x", pady=(0, 4))
        date_entry = ctk.CTkEntry(form, height=40)
        date_entry.insert(0, datetime.now().strftime("%d.%m.%Y"))  # ✅ Otomatik bugünün tarihi
        date_entry.pack(fill="x", pady=(0, 15))
    
    
        
        ctk.CTkLabel(form, text="Notlar:", font=ctk.CTkFont(size=13), anchor="w").pack(fill="x", pady=(0, 4))
        ctk.CTkEntry(form, placeholder_text="Açıklama (opsiyonel)", height=40).pack(fill="x", pady=(0, 20))
        
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        def save_dividend():
            try:
                sembol = symbol_var.get().strip().upper()
                tutar = float(amount_entry.get().replace(',', '.'))
                try: tarih = datetime.strptime(date_entry.get(), "%d.%m.%Y")
                except: tarih = datetime.now()
                
                if not sembol or tutar <= 0: showerror("Hata", "Geçersiz değerler!"); return
                
                stock = next((s for s in portfolio if s['sembol'] == sembol), None)
                adet = stock['adet'] if stock else 0
                hisse_basi = tutar / adet if adet > 0 else 0
                
                dividend_data = {'sembol': sembol, 'tutar': tutar, 'adet': adet, 'hisse_basi_tutar': hisse_basi, 'tarih': tarih.strftime('%Y-%m-%d %H:%M:%S')}
                
                dividend_id = self.db.add_dividend(dividend_data, user_id=user_id)
                
                if not dividend_id: showerror("Hata", "Temettü kaydedilemedi!"); return
                
                showinfo("Başarılı", f"✅ {sembol} temettüsü kaydedildi: {tutar:.2f}₺")
                dialog.destroy()
                self.refresh_dashboard()
            except Exception as e:
                showerror("Hata", f"Temettü kaydedilemedi: {e}")
                import traceback
                traceback.print_exc()
        
        ctk.CTkButton(btn_frame, text="💾 Temettüyü Kaydet", command=save_dividend, height=45, fg_color=COLORS["purple"], font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", expand=True, padx=(0, 5))
        ctk.CTkButton(btn_frame, text="❌ İptal", command=dialog.destroy, height=45, fg_color=("gray70", "gray30"), font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", expand=True, padx=(5, 0))

   
    def update_all_prices(self):
        """Tüm fiyatları güncelle"""
        if not askyesno("Güncelle", "Tüm fiyatlar güncellenecek. Devam?"):
            return
        
        progress = ctk.CTkToplevel(self.parent)
        progress.title("🔄 Güncelleniyor")
        progress.geometry("400x180")
        progress.transient(self.parent)
        progress.grab_set()
        
        progress.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 200
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 90
        progress.geometry(f"+{x}+{y}")
        
        ctk.CTkLabel(progress, text="🔄 Fiyatlar Güncelleniyor", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)
        status = ctk.CTkLabel(progress, text="Başlatılıyor...", font=ctk.CTkFont(size=12))
        status.pack(pady=8)
        pbar = ctk.CTkProgressBar(progress, width=320)
        pbar.pack(pady=15)
        pbar.set(0)
        
        def update_thread():
            try:
                user_id = self.get_user_id()
                portfolio = self.db.get_portfolio(user_id)
                
                if not portfolio:
                    self.parent.after(0, lambda: [status.configure(text="Portföy boş!"), progress.after(1500, progress.destroy)])
                    return
                
                total = len(portfolio)
                updated = 0
                
                import yfinance as yf
                
                for i, stock in enumerate(portfolio):
                    self.parent.after(0, lambda p=(i+1)/total, s=stock['sembol'], idx=i+1: [pbar.set(p), status.configure(text=f"{s} ({idx}/{total})")])
                    
                    try:
                        ticker = yf.Ticker(f"{stock['sembol']}.IS")
                        hist = ticker.history(period="1d")
                        
                        if not hist.empty:
                            price = float(hist['Close'].iloc[-1])
                            
                            with self.db.get_connection() as conn:
                                conn.cursor().execute('UPDATE portfolios SET guncel_fiyat=?, updated_at=CURRENT_TIMESTAMP WHERE sembol=? AND user_id=?', (price, stock['sembol'], user_id))
                            
                            updated += 1
                    
                    except Exception as e:
                        print(f"Hata ({stock['sembol']}): {e}")
                
                self.parent.after(0, lambda: [status.configure(text=f"✅ {updated}/{total} güncellendi"), pbar.set(1)])
                self.parent.after(1800, progress.destroy)
                self.parent.after(2000, self.refresh_dashboard)
            
            except Exception as e:
                self.parent.after(0, lambda: [status.configure(text=f"❌ {e}"), progress.after(2000, progress.destroy)])
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def quick_backup(self):
        """Hızlı yedekleme"""
        try:
            backup_mgr = self.get_backup_manager()
            if not backup_mgr:
                showerror("Hata", "Backup Manager bulunamadı!")
                return
            
            progress = ctk.CTkToplevel(self.parent)
            progress.title("💾 Yedekleme")
            progress.geometry("380x130")
            progress.transient(self.parent)
            progress.grab_set()
            
            progress.update_idletasks()
            x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - 190
            y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - 65
            progress.geometry(f"+{x}+{y}")
            
            ctk.CTkLabel(progress, text="💾 Yedekleniyor...", font=ctk.CTkFont(size=15, weight="bold")).pack(pady=12)
            pbar = ctk.CTkProgressBar(progress, width=300, mode="indeterminate")
            pbar.pack(pady=15)
            pbar.start()
            
            def backup_thread():
                try:
                    path = backup_mgr.create_backup(auto=False)
                    
                    if path:
                        import os
                        name = os.path.basename(path)
                        self.parent.after(0, lambda: [progress.destroy(), showinfo("Başarılı", f"✅ Yedek alındı!\n\n📁 {name}")])
                    else:
                        self.parent.after(0, lambda: [progress.destroy(), showerror("Hata", "Yedek oluşturulamadı!")])
                
                except Exception as e:
                    self.parent.after(0, lambda: [progress.destroy(), showerror("Hata", f"Yedekleme hatası:\n{e}")])
            
            threading.Thread(target=backup_thread, daemon=True).start()
        
        except Exception as e:
            showerror("Hata", f"Başlatılamadı:\n{e}")
            
    def export_to_excel(self):
        """Excel'e aktar - CSV formatında"""
        from tkinter import filedialog
        import csv
        import os
        import platform
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dosyası (Excel)", "*.csv"), ("Tüm Dosyalar", "*.*")],
            initialfile=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        
        if not filename:
            return
        
        try:
            user_id = self.get_user_id()
            portfolio = self.db.get_portfolio(user_id)
            
            if not portfolio:
                showinfo("Bilgi", "Portföyde hisse yok!")
                return
            
            # CSV'ye yaz (UTF-8 BOM ile Türkçe karakter desteği)
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                
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
                
                total_cost = 0
                total_value = 0
                total_profit = 0
                
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
                        f"{stock['ort_maliyet']:.2f}".replace('.', ','),
                        f"{g:.2f}".replace('.', ','),
                        f"{tm:.2f}".replace('.', ','),
                        f"{tv:.2f}".replace('.', ','),
                        f"{kz:.2f}".replace('.', ','),
                        f"{kz_p:.2f}".replace('.', ',')
                    ])
                
                writer.writerow([])
                
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
                
                writer.writerow([])
                writer.writerow(['ÖZET BİLGİLER'])
                writer.writerow(['Toplam Hisse Sayısı', len(portfolio)])
                writer.writerow(['Toplam Adet', sum(s['adet'] for s in portfolio)])
                writer.writerow(['Dışa Aktarma Tarihi', datetime.now().strftime('%d.%m.%Y %H:%M')])
            
            showinfo("Başarılı", 
                    f"✅ Portföy Excel'e aktarıldı!\n\n"
                    f"📁 {os.path.basename(filename)}\n\n"
                    f"💡 Excel'de açmak için:\n"
                    f"1. Dosyaya çift tıklayın\n"
                    f"2. veya Excel'de Dosya > Aç")
            
            if askyesno("Dosyayı Aç", "Excel dosyasını şimdi açmak ister misiniz?"):
                if platform.system() == 'Windows':
                    os.startfile(filename)
                elif platform.system() == 'Darwin':
                    os.system(f'open "{filename}"')
                else:
                    os.system(f'xdg-open "{filename}"')
        
        except Exception as e:
            showerror("Hata", f"Excel export hatası:\n{str(e)}")
            import traceback
            traceback.print_exc()
    
    # ========== CURRENCY ROW ==========
    
    def create_currency_row(self):
        row_frame = ctk.CTkFrame(self.main_container, fg_color="transparent", height=85)
        row_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=2)
        row_frame.grid_propagate(False)
        row_frame.grid_columnconfigure(0, weight=3)
        row_frame.grid_columnconfigure(1, weight=1)
        row_frame.grid_rowconfigure(0, weight=1)
        
        self.currency_container = ctk.CTkFrame(row_frame, fg_color="transparent")
        self.currency_container.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        for i in range(4):
            self.currency_container.grid_columnconfigure(i, weight=1)
        self.currency_container.grid_rowconfigure(0, weight=1)
        self.display_currencies()
        
        alerts_frame = ctk.CTkFrame(row_frame, corner_radius=8, fg_color=("gray85", "gray17"))
        alerts_frame.grid(row=0, column=1, sticky="nsew")
        self.create_alerts(alerts_frame)
    
    def display_currencies(self):
        if not self.currency_cache:
            card = ctk.CTkFrame(self.currency_container, corner_radius=8, fg_color=("gray85", "gray17"))
            card.grid(row=0, column=0, columnspan=4, padx=2, sticky="nsew")
            ctk.CTkLabel(card, text="Döviz verileri bulunamadı", font=ctk.CTkFont(size=12)).pack(expand=True, pady=20)
            return
        
        icons = {"DOLAR": "💵", "EURO": "💶", "ALTIN": "🪙", "BTC": "₿"}
        
        for i, curr in enumerate(self.currency_cache):
            card = ctk.CTkFrame(self.currency_container, corner_radius=8, fg_color=("gray85", "gray17"))
            card.grid(row=0, column=i, padx=3, sticky="nsew")
            card.grid_rowconfigure(0, weight=0)
            card.grid_rowconfigure(1, weight=1)
            card.grid_rowconfigure(2, weight=0)
            card.grid_columnconfigure(0, weight=1)
            
            top_frame = ctk.CTkFrame(card, fg_color="transparent")
            top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(5, 0))
            
            ctk.CTkLabel(top_frame, text=icons.get(curr["name"], "💱"), font=ctk.CTkFont(size=20)).pack(side="left", padx=(0, 5))
            ctk.CTkLabel(top_frame, text=curr["name"], font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
            
            color = COLORS["success"] if curr["change"] >= 0 else COLORS["danger"]
            
            ctk.CTkLabel(card, text=curr["value_text"], font=ctk.CTkFont(size=16, weight="bold"), text_color=color).grid(row=1, column=0, sticky="s")
            ctk.CTkLabel(card, text=curr["subtitle"], font=ctk.CTkFont(size=11), text_color=("gray60", "gray50")).grid(row=2, column=0, sticky="s", pady=(2, 5))
    
    def create_alerts(self, parent):
        content = ctk.CTkFrame(parent, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=8, pady=6)
        
        ctk.CTkLabel(content, text="🔔 Uyarılar", font=ctk.CTkFont(size=10, weight="bold")).pack(fill="x")
        
        user_id = self.get_user_id()
        portfolio = self.db.get_portfolio(user_id)
        alert_count = 0
        
        for hisse in portfolio[:2]:
            guncel = hisse.get("guncel_fiyat", hisse["ort_maliyet"])
            perf = ((guncel - hisse["ort_maliyet"]) / hisse["ort_maliyet"] * 100)
            
            if abs(perf) > 5:
                alert_count += 1
                icon = "📈" if perf > 0 else "📉"
                color = COLORS["success"] if perf > 0 else COLORS["danger"]
                
                af = ctk.CTkFrame(content, fg_color="transparent")
                af.pack(fill="x", pady=2)
                
                ctk.CTkLabel(af, text=f"{icon} {hisse['sembol']}", font=ctk.CTkFont(size=9, weight="bold"), width=50).pack(side="left")
                ctk.CTkLabel(af, text=f"{perf:+.1f}%", font=ctk.CTkFont(size=9, weight="bold"), text_color=color).pack(side="right")
        
        if alert_count == 0:
            ctk.CTkLabel(content, text="✅ Yeni uyarı yok", font=ctk.CTkFont(size=9), text_color="gray").pack(pady=10)
    
    # ========== INDICES ROW ==========
    
    def create_indices_row(self):
        self.index_container = ctk.CTkFrame(self.main_container, fg_color="transparent", height=140)
        self.index_container.grid(row=4, column=0, sticky="ew", padx=5, pady=2)
        self.index_container.grid_propagate(False)
        
        for i in range(3):
            self.index_container.grid_columnconfigure(i, weight=1)
        self.index_container.grid_rowconfigure(0, weight=1)
        
        self.display_indices()
    
    def display_indices(self):
        if not self.index_cache:
            card = ctk.CTkFrame(self.index_container, corner_radius=10, fg_color=("gray85", "gray17"))
            card.grid(row=0, column=0, columnspan=3, padx=2, sticky="nsew")
            ctk.CTkLabel(card, text="Endeks verileri bulunamadı", font=ctk.CTkFont(size=12)).pack(expand=True, pady=30)
            return
        
        for i, idx in enumerate(self.index_cache):
            card = ctk.CTkFrame(self.index_container, corner_radius=10, fg_color=("gray85", "gray17"))
            card.grid(row=0, column=i, padx=2, sticky="nsew")
            
            content = ctk.CTkFrame(card, fg_color="transparent")
            content.pack(fill="both", expand=True, padx=12, pady=10)
            
            color = COLORS["success"] if idx["change"] >= 0 else COLORS["danger"]
            icon = "📊" if idx["change"] >= 0 else "📉"
            
            top = ctk.CTkFrame(content, fg_color="transparent")
            top.pack(fill="x")
            
            ctk.CTkLabel(top, text=icon, font=ctk.CTkFont(size=18)).pack(side="left")
            ctk.CTkLabel(top, text=idx["name"], font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=(6, 0))
            
            ctk.CTkLabel(content, text=f"{idx['value']:,.2f}", font=ctk.CTkFont(size=18, weight="bold"), text_color=color).pack(anchor="w", pady=(4, 0))
            ctk.CTkLabel(content, text=f"{idx['change']:+.2f}%", font=ctk.CTkFont(size=11), text_color=color).pack(anchor="w", pady=(1, 6))
            
            if idx.get("history") and len(idx["history"]) > 10:
                graph_frame = ctk.CTkFrame(content, fg_color="transparent", height=45)
                graph_frame.pack(fill="x")
                graph_frame.pack_propagate(False)
                
                fig = Figure(figsize=(4, 0.6), dpi=80)
                fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
                ax = fig.add_subplot(111)
                ax.plot(idx["history"], color=color, linewidth=2, alpha=0.8)
                ax.axis('off')
                ax.margins(x=0, y=0.15)
                fig.patch.set_alpha(0.0)
                ax.patch.set_alpha(0.0)
                
                canvas = FigureCanvasTkAgg(fig, graph_frame)
                canvas.draw()
                cw = canvas.get_tk_widget()
                bg = '#2b2b2b' if self.theme == "dark" else '#d9d9d9'
                cw.configure(bg=bg, highlightthickness=0)
                cw.pack(fill="both", expand=True)
    
    # ========== KPI ROW ==========
    
    def create_kpi_row(self):
        kpi_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        kpi_container.grid(row=3, column=0, sticky="nsew", padx=5, pady=2)
        
        user_id = self.get_user_id()
        portfolio = self.db.get_portfolio(user_id)
        dividends = self.db.get_dividends(user_id)
        transactions = self.db.get_transactions(user_id)
        
        toplam_yatirim = sum(h["adet"] * h["ort_maliyet"] for h in portfolio)
        portfoy_deger = sum(h["adet"] * h.get("guncel_fiyat", h["ort_maliyet"]) for h in portfolio)
        gunluk_degisim, gunluk_yuzde = self.calculate_daily_change()
        toplam_kar_zarar = portfoy_deger - toplam_yatirim
        kar_zarar_yuzde = (toplam_kar_zarar / toplam_yatirim * 100) if toplam_yatirim > 0 else 0
        toplam_temettü = sum(t["tutar"] for t in dividends)
        
        kpis = [
            {"icon": "💰", "title": "Toplam Yatırım", "value": f"{toplam_yatirim:,.0f} ₺", "subtitle": f"{len(portfolio)} hisse", "color": COLORS["primary"]},
            {"icon": "📊", "title": "Portföy Değeri", "value": f"{portfoy_deger:,.0f} ₺", "subtitle": "Güncel", "color": COLORS["success"]},
            {"icon": "📈" if gunluk_degisim >= 0 else "📉", "title": "Bugün", "value": f"{abs(gunluk_degisim):,.0f} ₺", "subtitle": f"{gunluk_yuzde:+.2f}%", "color": COLORS["success"] if gunluk_degisim >= 0 else COLORS["danger"]},
            {"icon": "💎" if toplam_kar_zarar >= 0 else "⚠️", "title": "Toplam K/Z", "value": f"{abs(toplam_kar_zarar):,.0f} ₺", "subtitle": f"{kar_zarar_yuzde:+.2f}%", "color": COLORS["success"] if toplam_kar_zarar >= 0 else COLORS["danger"]},
            {"icon": "💵", "title": "Temettü", "value": f"{toplam_temettü:,.0f} ₺", "subtitle": f"{len(dividends)} ödeme", "color": COLORS["purple"]},
            {"icon": "📝", "title": "İşlemler", "value": f"{len(transactions)}", "subtitle": "Toplam", "color": COLORS["orange"]}
        ]
        
        for i in range(len(kpis)):
            kpi_container.grid_columnconfigure(i, weight=1, uniform="kpi")
        kpi_container.grid_rowconfigure(0, weight=1)
        
        for i, kpi in enumerate(kpis):
            self.create_kpi_card(kpi_container, kpi, 0, i)
    
    def create_kpi_card(self, parent, kpi, row, col):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color=("gray85", "gray17"))
        card.grid(row=row, column=col, padx=3, sticky="nsew")
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=12, pady=10)
        content.grid_rowconfigure(0, weight=0)
        content.grid_rowconfigure(1, weight=1, minsize=40)
        content.grid_rowconfigure(2, weight=0)
        content.grid_columnconfigure(0, weight=1)
        
        top_frame = ctk.CTkFrame(content, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew")
        
        ctk.CTkLabel(top_frame, text=kpi["icon"], font=ctk.CTkFont(size=22)).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(top_frame, text=kpi["title"], font=ctk.CTkFont(size=11), text_color=("gray50", "gray60")).pack(side="left")
        
        value_frame = ctk.CTkFrame(content, fg_color="transparent")
        value_frame.grid(row=1, column=0, sticky="nsew")
        
        value_label = ctk.CTkLabel(value_frame, text=kpi["value"], font=ctk.CTkFont(size=22, weight="bold"), text_color=kpi["color"], wraplength=150)
        value_label.pack(expand=True, anchor="center")
        
        if kpi["title"] in ["Bugün", "Toplam K/Z"]:
            ctk.CTkLabel(content, text=kpi["subtitle"], font=ctk.CTkFont(size=13, weight="bold"), text_color=kpi["color"]).grid(row=2, column=0, sticky="s", pady=(0, 5))
        else:
            ctk.CTkLabel(content, text=kpi["subtitle"], font=ctk.CTkFont(size=11), text_color=("gray60", "gray50")).grid(row=2, column=0, sticky="s", pady=(0, 5))
    
    # ========== STATS ROW ==========
    
    def create_stats_row(self):
        stats_container = ctk.CTkFrame(self.main_container, fg_color="transparent", height=90)
        stats_container.grid(row=5, column=0, sticky="ew", padx=5, pady=2)
        stats_container.grid_propagate(False)
        stats_container.grid_columnconfigure(0, weight=2)
        stats_container.grid_columnconfigure(1, weight=3)
        stats_container.grid_rowconfigure(0, weight=1)
        
        quick_stats = ctk.CTkFrame(stats_container, corner_radius=8, fg_color=("gray85", "gray17"))
        quick_stats.grid(row=0, column=0, sticky="nsew", padx=(0, 3))
        self.create_quick_stats(quick_stats)
        
        recent = ctk.CTkFrame(stats_container, corner_radius=8, fg_color=("gray85", "gray17"))
        recent.grid(row=0, column=1, sticky="nsew")
        self.create_recent_transactions(recent)
    
    def create_quick_stats(self, parent):
        content = ctk.CTkFrame(parent, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=8)
        
        ctk.CTkLabel(content, text="⚡ Hızlı İstatistikler", font=ctk.CTkFont(size=11, weight="bold")).pack(fill="x", pady=(0, 5))
        
        user_id = self.get_user_id()
        portfolio = self.db.get_portfolio(user_id)
        
        if portfolio:
            best = max(portfolio, key=lambda h: ((h.get("guncel_fiyat", h["ort_maliyet"]) - h["ort_maliyet"]) / h["ort_maliyet"]))
            best_perf = ((best.get("guncel_fiyat", best["ort_maliyet"]) - best["ort_maliyet"]) / best["ort_maliyet"] * 100)
            
            worst = min(portfolio, key=lambda h: ((h.get("guncel_fiyat", h["ort_maliyet"]) - h["ort_maliyet"]) / h["ort_maliyet"]))
            worst_perf = ((worst.get("guncel_fiyat", worst["ort_maliyet"]) - worst["ort_maliyet"]) / worst["ort_maliyet"] * 100)
            
            biggest = max(portfolio, key=lambda h: h["adet"] * h.get("guncel_fiyat", h["ort_maliyet"]))
            biggest_val = biggest["adet"] * biggest.get("guncel_fiyat", biggest["ort_maliyet"])
            
            stats = [
                ("🏆 En İyi", best['sembol'], f"+{best_perf:.1f}%", COLORS["success"]),
                ("📉 En Kötü", worst['sembol'], f"{worst_perf:.1f}%", COLORS["danger"]),
                ("💼 En Büyük", biggest['sembol'], f"{biggest_val:,.0f}₺", COLORS["primary"])
            ]
            
            for title, symbol, value, color in stats:
                sf = ctk.CTkFrame(content, fg_color="transparent")
                sf.pack(fill="x", pady=1)
                
                ctk.CTkLabel(sf, text=title, font=ctk.CTkFont(size=9), text_color=("gray60", "gray50"), width=60).pack(side="left")
                ctk.CTkLabel(sf, text=symbol, font=ctk.CTkFont(size=9, weight="bold"), width=50).pack(side="left", padx=5)
                ctk.CTkLabel(sf, text=value, font=ctk.CTkFont(size=9, weight="bold"), text_color=color).pack(side="right")
        else:
            ctk.CTkLabel(content, text="Portföyde hisse yok", font=ctk.CTkFont(size=9), text_color="gray").pack(pady=10)
    
    def create_recent_transactions(self, parent):
        content = ctk.CTkFrame(parent, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=10, pady=8)
        
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 8))
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)
        
        ctk.CTkLabel(header, text="📝 Son İşlemler", font=ctk.CTkFont(size=11, weight="bold"), anchor="w").grid(row=0, column=0, sticky="w")
        
        user_id = self.get_user_id()
        transactions = self.db.get_transactions(user_id)
        transactions.sort(key=lambda x: x.get("tarih", "1970-01-01"), reverse=True)
        
        list_frame = ctk.CTkFrame(content, fg_color="transparent")
        list_frame.pack(fill="both", expand=True)
        
        if transactions:
            for trans in transactions[:3]:
                tf = ctk.CTkFrame(list_frame, fg_color=("gray80", "gray20"), corner_radius=6)
                tf.pack(fill="x", pady=2, expand=False)
                
                tc = ctk.CTkFrame(tf, fg_color="transparent")
                tc.pack(fill="x", padx=8, pady=3)
                
                tip = trans.get("tip", "Bilinmiyor")
                icon = "🟢" if tip == "Alım" else "🔴" if tip == "Satış" else "💰"  # ✅ "Alım" kontrolü
                color = COLORS["success"] if tip == "Alım" else COLORS["danger"] if tip == "Satış" else COLORS["purple"]  # ✅ Alımda yeşil
                
                ctk.CTkLabel(tc, text=f"{icon} {tip}", font=ctk.CTkFont(size=8, weight="bold"), text_color=color, width=45, anchor="w").pack(side="left")
                ctk.CTkLabel(tc, text=trans.get("sembol", "???"), font=ctk.CTkFont(size=8, weight="bold"), width=45, anchor="w").pack(side="left", padx=3)
                ctk.CTkLabel(tc, text=f"{trans.get('adet', 0)} ad", font=ctk.CTkFont(size=8), text_color=("gray60", "gray50"), width=35, anchor="w").pack(side="left", padx=2)
                
                tutar = trans.get("toplam", trans.get("tutar", 0))
                ctk.CTkLabel(tc, text=f"{tutar:,.0f}₺", font=ctk.CTkFont(size=8, weight="bold")).pack(side="right")
        else:
            ctk.CTkLabel(list_frame, text="Henüz işlem yok", font=ctk.CTkFont(size=9), text_color="gray", justify="center").pack(expand=True)
    
    # ========== CHARTS ROW ==========
    
    def create_charts_row(self):
        charts_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        charts_container.grid(row=6, column=0, sticky="nsew", padx=5, pady=2)
        
        for i in range(3):
            charts_container.grid_columnconfigure(i, weight=1)
        charts_container.grid_rowconfigure(0, weight=1)
        
        pie_frame = ctk.CTkFrame(charts_container, corner_radius=10, fg_color=("gray90", "gray13"))
        pie_frame.grid(row=0, column=0, sticky="nsew", padx=2)
        self.create_pie_chart(pie_frame)
        
        perf_frame = ctk.CTkFrame(charts_container, corner_radius=10, fg_color=("gray90", "gray13"))
        perf_frame.grid(row=0, column=1, sticky="nsew", padx=2)
        self.create_performance_chart(perf_frame)
        
        rank_frame = ctk.CTkFrame(charts_container, corner_radius=10, fg_color=("gray90", "gray13"))
        rank_frame.grid(row=0, column=2, sticky="nsew", padx=2)
        self.create_ranking(rank_frame)
    
    def create_pie_chart(self, parent):
        ctk.CTkLabel(parent, text="📊 Portföy Dağılımı", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=10, padx=12, anchor="w")
        
        chart_frame = ctk.CTkFrame(parent, fg_color="transparent")
        chart_frame.pack(fill="both", expand=True)
        
        fig = Figure(figsize=(5, 4), dpi=90)
        ax = fig.add_subplot(111)
        
        user_id = self.get_user_id()
        portfolio = self.db.get_portfolio(user_id)
        
        if portfolio:
            labels = [h["sembol"] for h in portfolio]
            sizes = [h["adet"] * h.get("guncel_fiyat", h["ort_maliyet"]) for h in portfolio]
            colors = [COLORS["primary"], COLORS["success"], COLORS["warning"], COLORS["purple"], COLORS["pink"], COLORS["teal"], COLORS["orange"], COLORS["cyan"], COLORS["lime"]][:len(labels)]
            
            text_color = 'white' if self.theme == "dark" else 'black'
            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90, pctdistance=0.85, textprops={'color': text_color, 'fontsize': 9, 'weight': 'bold'})
            
            for at in autotexts:
                at.set_color('white')
            
            ax.axis('equal')
        else:
            ax.text(0.5, 0.5, 'Portföyde hisse yok', ha='center', va='center', transform=ax.transAxes, fontsize=11, color='gray')
            ax.axis('off')
        
        fig.patch.set_alpha(0.0)
        ax.patch.set_alpha(0.0)
        
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.draw()
        cw = canvas.get_tk_widget()
        bg = '#2b2b2b' if self.theme == "dark" else '#ebebeb'
        cw.configure(bg=bg, highlightthickness=0)
        cw.pack(fill="both", expand=True, padx=5, pady=(0, 5))
    
    def create_performance_chart(self, parent):
        ctk.CTkLabel(parent, text="📈 Performans (%)", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=10, padx=12, anchor="w")
        
        chart_frame = ctk.CTkFrame(parent, fg_color="transparent")
        chart_frame.pack(fill="both", expand=True)
        
        fig = Figure(figsize=(5, 4), dpi=90)
        ax = fig.add_subplot(111)
        
        user_id = self.get_user_id()
        portfolio = self.db.get_portfolio(user_id)
        
        if portfolio:
            symbols = [h["sembol"] for h in portfolio]
            performances = []
            
            for h in portfolio:
                guncel = h.get("guncel_fiyat", h["ort_maliyet"])
                perf = ((guncel - h["ort_maliyet"]) / h["ort_maliyet"] * 100)
                performances.append(perf)
            
            colors = [COLORS["success"] if p >= 0 else COLORS["danger"] for p in performances]
            bars = ax.barh(symbols, performances, color=colors, height=0.6)
            
            for bar, perf in zip(bars, performances):
                width = bar.get_width()
                ax.text(width + (0.5 if width > 0 else -0.5), bar.get_y() + bar.get_height()/2, f'{perf:.1f}%', ha='left' if width > 0 else 'right', va='center', fontsize=8, weight='bold', color=COLORS["success"] if perf >= 0 else COLORS["danger"])
            
            ax.axvline(x=0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
            ax.set_xlabel('Performans (%)', fontsize=9, weight='bold')
            ax.grid(axis='x', alpha=0.2, linestyle='--')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            tc = 'white' if self.theme == "dark" else 'black'
            ax.tick_params(colors=tc, labelsize=8)
            ax.xaxis.label.set_color(tc)
            ax.spines['bottom'].set_color(tc)
            ax.spines['left'].set_color(tc)
        else:
            ax.text(0.5, 0.5, 'Portföyde hisse yok', ha='center', va='center', transform=ax.transAxes, fontsize=11, color='gray')
            ax.axis('off')
        
        fig.patch.set_alpha(0.0)
        ax.patch.set_alpha(0.0)
        
        canvas = FigureCanvasTkAgg(fig, chart_frame)
        canvas.draw()
        cw = canvas.get_tk_widget()
        bg = '#2b2b2b' if self.theme == "dark" else '#ebebeb'
        cw.configure(bg=bg, highlightthickness=0)
        cw.pack(fill="both", expand=True, padx=5, pady=(0, 5))
    
    def create_ranking(self, parent):
        ctk.CTkLabel(parent, text="🏆 Sıralama", font=ctk.CTkFont(size=13, weight="bold")).pack(pady=10, padx=12, anchor="w")
        
        user_id = self.get_user_id()
        portfolio = self.db.get_portfolio(user_id)
        
        if not portfolio:
            no_data = ctk.CTkFrame(parent, fg_color="transparent")
            no_data.pack(expand=True)
            ctk.CTkLabel(no_data, text="📊", font=ctk.CTkFont(size=40)).pack(pady=(15, 8))
            ctk.CTkLabel(no_data, text="Portföyde hisse yok", font=ctk.CTkFont(size=11), text_color="gray").pack()
            return
        
        stocks_perf = []
        for h in portfolio:
            guncel = h.get("guncel_fiyat", h["ort_maliyet"])
            perf = ((guncel - h["ort_maliyet"]) / h["ort_maliyet"] * 100)
            stocks_perf.append((h["sembol"], perf))
        
        stocks_perf.sort(key=lambda x: x[1], reverse=True)
        
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        
        ctk.CTkLabel(scroll, text="🏆 En İyi", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["success"]).pack(fill="x", pady=(2, 5), padx=3)
        
        for i, (symbol, perf) in enumerate(stocks_perf[:min(3, len(stocks_perf))], 1):
            f = ctk.CTkFrame(scroll, fg_color=("gray80", "gray20"), corner_radius=6)
            f.pack(fill="x", pady=2, padx=3)
            
            c = ctk.CTkFrame(f, fg_color="transparent")
            c.pack(fill="x", padx=8, pady=5)
            
            color = COLORS["success"] if perf >= 0 else COLORS["danger"]
            
            ctk.CTkLabel(c, text=f"{i}", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["success"], width=20).pack(side="left")
            ctk.CTkLabel(c, text=symbol, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=5, fill="x", expand=True)
            ctk.CTkLabel(c, text=f"{perf:+.2f}%", font=ctk.CTkFont(size=10, weight="bold"), text_color=color).pack(side="right")
        
        ctk.CTkLabel(scroll, text="📉 En Kötü", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLORS["danger"]).pack(fill="x", pady=(15, 5), padx=3)
        
        worst = stocks_perf[-min(3, len(stocks_perf)):][::-1]
        
        for i, (symbol, perf) in enumerate(worst, 1):
            f = ctk.CTkFrame(scroll, fg_color=("gray80", "gray20"), corner_radius=6)
            f.pack(fill="x", pady=2, padx=3)
            
            c = ctk.CTkFrame(f, fg_color="transparent")
            c.pack(fill="x", padx=8, pady=5)
            
            color = COLORS["success"] if perf >= 0 else COLORS["danger"]
            
            ctk.CTkLabel(c, text=f"{i}", font=ctk.CTkFont(size=13, weight="bold"), text_color=COLORS["danger"], width=20).pack(side="left")
            ctk.CTkLabel(c, text=symbol, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left", padx=5, fill="x", expand=True)
            ctk.CTkLabel(c, text=f"{perf:+.2f}%", font=ctk.CTkFont(size=10, weight="bold"), text_color=color).pack(side="right")
    
    # ========== HELPER METHODS ==========
    
    def calculate_daily_change(self):
        user_id = self.get_user_id()
        portfolio = self.db.get_portfolio(user_id)
        change_tl = 0
        
        for h in portfolio:
            guncel = h.get("guncel_fiyat", h["ort_maliyet"])
            daily = random.uniform(-0.03, 0.03)
            change_tl += h["adet"] * guncel * daily
        
        total = sum(h["adet"] * h.get("guncel_fiyat", h["ort_maliyet"]) for h in portfolio)
        change_pct = (change_tl / total * 100) if total > 0 else 0
        
        return change_tl, change_pct
    
    def get_current_price(self, symbol):
        """Güncel fiyat al"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(f"{symbol}.IS")
            hist = ticker.history(period="1d")
            return float(hist['Close'].iloc[-1]) if not hist.empty else 0.0
        except:
            return 0.0
    
    def get_user_id(self):
        """User ID al"""
        root = self.parent
        while root.master:
            root = root.master
        return getattr(root, 'current_user_id', 1)
    
    def get_backup_manager(self):
        """Backup Manager al"""
        root = self.parent
        while root.master:
            root = root.master
        return getattr(root, 'backup_manager', None)
    
    def get_settings_manager(self):
        """Settings Manager al"""
        root = self.parent
        while root.master:
            root = root.master
        return getattr(root, 'settings_manager', None)
    
    def refresh_dashboard(self):
        """Dashboard yenile - DÜZELTILMIŞ"""
        try:
            # Timer'ları durdur
            if hasattr(self, 'clock_timer') and self.clock_timer:
                try:
                    self.parent.after_cancel(self.clock_timer)
                    self.clock_timer = None
                except:
                    pass
            
            if hasattr(self, 'market_timer') and self.market_timer:
                try:
                    self.parent.after_cancel(self.market_timer)
                    self.market_timer = None
                except:
                    pass
            
            
            # Root window'u bul
            root = self.parent
            depth = 0
            max_depth = 10
            
            while root.master and depth < max_depth:
                root = root.master
                depth += 1

            # ✅ Tüm sayfaları refresh et (varsa)
            if hasattr(root, 'refresh_all_pages'):
                print("[INFO] Tüm sayfalar yenileniyor...")
                root.after(100, root.refresh_all_pages)
            
            # Ana uygulamadan yenile
            if hasattr(root, 'show_page'):
                print("[INFO] Dashboard ana uygulamadan yenileniyor...")
                root.after(100, lambda: root.show_page('dashboard'))
            else:
                print("[WARN] show_page bulunamadı, yerel yenileme...")
                if hasattr(self, 'main_container') and self.main_container.winfo_exists():
                    for widget in self.main_container.winfo_children():
                        widget.destroy()
                    self.create()
        
        except Exception as e:
            print(f"[ERROR] Dashboard yenileme hatası: {e}")
            import traceback
            traceback.print_exc()
    
    def darken_color(self, color):
        """Rengi koyulaştır"""
        try:
            color = color.lstrip('#')
            r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
            r, g, b = max(0, int(r*0.8)), max(0, int(g*0.8)), max(0, int(b*0.8))
            return f'#{r:02x}{g:02x}{b:02x}'
        except:
            return color
    
    # ========== YARDIMCI DİALOG METODLARI ==========
    
    def fetch_and_set_price(self, stock_var, price_entry):
        """Güncel fiyatı çek ve entry'ye yaz"""
        try:
            selected = stock_var.get()
            sembol = selected.split(" (")[0].strip()
            
            price_entry.configure(state="disabled")
            price_entry.delete(0, 'end')
            price_entry.insert(0, "Yükleniyor...")
            
            def fetch():
                try:
                    price = self.get_current_price(sembol)
                    self.parent.after(0, lambda: [
                        price_entry.configure(state="normal"),
                        price_entry.delete(0, 'end'),
                        price_entry.insert(0, f"{price:.2f}" if price > 0 else "")
                    ])
                except Exception as e:
                    self.parent.after(0, lambda: [
                        price_entry.configure(state="normal"),
                        price_entry.delete(0, 'end'),
                        showerror("Hata", f"Fiyat alınamadı:\n{e}")
                    ])
            
            threading.Thread(target=fetch, daemon=True).start()
        
        except Exception as e:
            price_entry.configure(state="normal")
            showerror("Hata", f"Hata:\n{e}")
    
    def calculate_sell_summary_new(self, stock_var, amount_entry, price_entry, summary_label, portfolio):
        """Satış özetini hesapla - Güncellenmiş"""
        try:
            # Değerleri al
            selected = stock_var.get()
            sembol = selected.split(" (")[0].strip()
            stock = next((s for s in portfolio if s['sembol'] == sembol), None)
            
            if not stock:
                summary_label.configure(text="⚠️ Hisse bulunamadı")
                return
            
            miktar = int(amount_entry.get())
            fiyat = float(price_entry.get().replace(',', '.'))
            
            # Ayarlardan oranları al
            settings_mgr = self.get_settings_manager()
            komisyon_oran = float(settings_mgr.get("komisyon_orani", 0.0004)) if settings_mgr else 0.0004
            vergi_oran = float(settings_mgr.get("vergi_orani", 0)) if settings_mgr else 0
            
            # Hesaplamalar
            brut_tutar = miktar * fiyat
            komisyon = brut_tutar * komisyon_oran
            
            # Kar ve vergi
            maliyet = miktar * stock['ort_maliyet']
            kar = brut_tutar - maliyet - komisyon
            vergi = max(0, kar * vergi_oran) if kar > 0 else 0
            
            net_tutar = brut_tutar - komisyon - vergi
            toplam_kar_zarar = net_tutar - maliyet
            
            # Oran gösterimi
            komisyon_yuzde = komisyon_oran * 100
            vergi_yuzde = vergi_oran * 100
            
            # Özet
            summary_text = (
                f"💵 Brüt Tutar: {brut_tutar:,.2f}₺\n"
                f"📊 Komisyon (%{komisyon_yuzde:.3f}): -{komisyon:.2f}₺\n"
            )
            
            if vergi > 0:
                summary_text += f"🏛️ Vergi (%{vergi_yuzde:.2f}): -{vergi:.2f}₺\n"
            
            summary_text += (
                f"{'─' * 35}\n"
                f"💰 Net Tutar: {net_tutar:,.2f}₺\n"
                f"\n{'📈 Kar' if toplam_kar_zarar >= 0 else '📉 Zarar'}: "
                f"{abs(toplam_kar_zarar):,.2f}₺"
            )
            
            summary_label.configure(text=summary_text)
        
        except (ValueError, TypeError):
            summary_label.configure(text="⚠️ Geçerli değerler girin")
        except Exception as e:
            summary_label.configure(text=f"❌ Hata: {str(e)}")

    def get_current_price(self, symbol):
        """Güncel fiyat al"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(f"{symbol}.IS")
            hist = ticker.history(period="1d")
            return float(hist['Close'].iloc[-1]) if not hist.empty else 0.0
        except:
            return 0.0
    
    def __del__(self):
        """Temizlik"""
        if self.clock_timer:
            try:
                self.parent.after_cancel(self.clock_timer)
            except:
                pass
        
        if self.market_timer:
            try:
                self.parent.after_cancel(self.market_timer)
            except:
                pass