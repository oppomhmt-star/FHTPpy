# pages/transactions_page.py - TAMAMEN GÜNCELLENMİŞ

import customtkinter as ctk
from datetime import datetime
from config import COLORS
from ui_utils import askyesno, showinfo, showerror

def format_rate_display(rate):
    """Komisyon oranını kullanıcıya uygun formatta gösterme"""
    onbinde = rate * 10000
    binde = rate * 1000
    yuzde = rate * 100
    
    if rate >= 0.01:  # %1 veya üstü
        return f"Yüzde {yuzde:.2f}"
    elif rate >= 0.001:  # Binde 1 veya üstü 
        return f"Binde {binde:.2f}"
    else:  # Onbinde göster
        return f"Onbinde {onbinde:.2f}"

class TransactionsPage:
    def __init__(self, parent, db, api, theme):
        self.parent = parent
        self.db = db
        self.api = api
        self.theme = theme
        self.list_container = None
        self.filter_combo = None
        self.sort_combo = None
    
    # ✅ YENİ: User ID alma metodu
    def get_user_id(self):
        """Aktif kullanıcı ID'sini al"""
        root = self.parent
        while root.master:
            root = root.master
        return getattr(root, 'current_user_id', 1)
        
    def create(self):
        """İşlemler sayfasını oluşturur"""
        self.main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)

        self.create_header()
        self.create_filter_bar()
        self.create_list_container()
        
        self.display_transactions()

    def create_header(self):
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20), padx=5)
        ctk.CTkLabel(header_frame, text="💰 İşlem Geçmişi", 
                     font=ctk.CTkFont(size=32, weight="bold")).pack(side="left")

    def create_filter_bar(self):
        filter_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        filter_frame.pack(fill="x", pady=(0, 15), padx=5)
        
        ctk.CTkLabel(filter_frame, text="Filtrele:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 10))
        self.filter_combo = ctk.CTkComboBox(filter_frame, values=["Tümü", "Alım", "Satış", "Temettü"], width=150, command=lambda _: self.display_transactions())
        self.filter_combo.set("Tümü")
        self.filter_combo.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(filter_frame, text="Sırala:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 10))
        self.sort_combo = ctk.CTkComboBox(filter_frame, values=["Yeni → Eski", "Eski → Yeni", "Tutar (Yüksek → Düşük)"], width=200, command=lambda _: self.display_transactions())
        self.sort_combo.set("Yeni → Eski")
        self.sort_combo.pack(side="left")

    def create_list_container(self):
        self.list_container = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.list_container.pack(fill="both", expand=True, padx=5)

    def display_transactions(self):
        for widget in self.list_container.winfo_children():
            widget.destroy()
        
        # ✅ USER ID AL
        user_id = self.get_user_id()
        
        # ✅ DÜZELTİLMİŞ - user_id ile
        all_transactions = self.db.get_transactions(user_id).copy()
        
        # Temettüleri ekle
        for div in self.db.get_dividends(user_id):
            all_transactions.append({
                "tip": "Temettü", 
                "sembol": div.get("sembol", "N/A"),
                "toplam": div.get("tutar", 0), 
                "tarih": div.get("tarih", "N/A"),
                "adet": div.get("adet", 0), 
                "fiyat": div.get("hisse_basi_tutar", 0),
                "tutar": div.get("tutar", 0), 
                "komisyon": 0
            })
        
        filter_type = self.filter_combo.get()
        if filter_type != "Tümü":
            all_transactions = [t for t in all_transactions if t.get("tip") == filter_type]
        
        # ✅ SIRALAMADA TARİH DÜZELTMESİ
        sort_option = self.sort_combo.get()
        reverse_sort = sort_option in ["Yeni → Eski", "Tutar (Yüksek → Düşük)"]
        
        if "Tutar" in sort_option:
            # Tutara göre sırala
            all_transactions.sort(key=lambda x: x.get("toplam", 0), reverse=reverse_sort)
        else:
            # Tarihe göre sırala - datetime'a çevirerek
            def get_datetime(transaction):
                try:
                    tarih_str = transaction.get("tarih", "1970-01-01 00:00:00")
                    return datetime.fromisoformat(tarih_str.replace(" ", "T"))
                except:
                    return datetime(1970, 1, 1)
            
            all_transactions.sort(key=get_datetime, reverse=reverse_sort)
        
        grid_frame = ctk.CTkFrame(self.list_container, fg_color="transparent")
        grid_frame.pack(fill="x", expand=True)

        headers = ["Tarih", "Tip", "Sembol", "Adet", "Fiyat", "Toplam", "İşlemler"]
        weights = [10, 10, 10, 8, 10, 18, 15] 
        
        for i, w in enumerate(weights): 
            grid_frame.grid_columnconfigure(i, weight=w)

        header_bg = ctk.CTkFrame(grid_frame, fg_color=("gray75", "gray25"), corner_radius=8, height=40)
        header_bg.grid(row=0, column=0, columnspan=len(headers), sticky="nsew", pady=(0, 5))
        
        for i, h_text in enumerate(headers):
            ctk.CTkLabel(grid_frame, text=h_text, font=ctk.CTkFont(size=12, weight="bold"), bg_color=header_bg.cget("fg_color")).grid(row=0, column=i, sticky="nsew", padx=5)

        if not all_transactions:
            ctk.CTkLabel(grid_frame, text="Filtreye uygun işlem bulunamadı.", text_color="gray").grid(row=1, column=0, columnspan=len(headers), pady=50)
            return

        for row_idx, transaction in enumerate(all_transactions, start=1):
            self.create_transaction_row(grid_frame, transaction, row_idx)


    def create_transaction_row(self, parent, transaction, row_idx):
        tip = transaction.get("tip", "Bilinmiyor")
        
        # ✅ Renk düzenlemesi - Alım için yeşil, Satış için sarı
        type_color = {
            "Alım": COLORS["success"],     # ✅ Yeşil
            "Satış": COLORS["warning"],    # ✅ Sarı
            "Temettü": COLORS["purple"]    # Mor
        }.get(tip, "gray")
        
        try:
            dt_object = datetime.fromisoformat(transaction.get("tarih", "1970-01-01").replace(" ", "T"))
            tarih_text = dt_object.strftime('%d/%m/%Y')
        except:
            tarih_text = transaction.get("tarih", "N/A")[:10]

        adet_text = f'{transaction.get("adet", 0):,}' if transaction.get("adet", 0) > 0 else "-"
        fiyat_text = f'{transaction.get("fiyat", 0):.2f} ₺' if transaction.get("fiyat", 0) > 0 else "-"
        
        # ✅ GÖSTERİM DÜZELTMESİ
        brut_tutar = transaction.get("toplam", 0)
        komisyon = transaction.get("komisyon", 0)
        
        # Her işlem tipi için düzenli gösterim
        if tip == "Alım":
            net_tutar = brut_tutar + komisyon
            
            if komisyon > 0:
                total_text = f"{net_tutar:,.2f} ₺"
                detail_text = f"İşlem: {brut_tutar:,.2f} ₺ | Komisyon: {komisyon:.2f} ₺"
            else:
                total_text = f"{brut_tutar:,.2f} ₺"
                detail_text = None
                
        elif tip == "Satış":
            net_tutar = brut_tutar - komisyon
            
            if komisyon > 0:
                total_text = f"{net_tutar:,.2f} ₺"
                detail_text = f"İşlem: {brut_tutar:,.2f} ₺ | Komisyon: {komisyon:.2f} ₺"
            else:
                total_text = f"{brut_tutar:,.2f} ₺"
                detail_text = None
                
        else:  # Temettü
            total_text = f"{brut_tutar:,.2f} ₺"
            detail_text = None
               
        # Label'lar
        ctk.CTkLabel(parent, text=tarih_text, font=ctk.CTkFont(size=12)).grid(row=row_idx, column=0, sticky="nsew", pady=10)
        ctk.CTkLabel(parent, text=tip, font=ctk.CTkFont(size=13, weight="bold"), text_color=type_color).grid(row=row_idx, column=1, sticky="nsew")
        ctk.CTkLabel(parent, text=transaction.get("sembol", "-"), font=ctk.CTkFont(size=13, weight="bold")).grid(row=row_idx, column=2, sticky="nsew")
        ctk.CTkLabel(parent, text=adet_text).grid(row=row_idx, column=3, sticky="nsew")
        ctk.CTkLabel(parent, text=fiyat_text).grid(row=row_idx, column=4, sticky="nsew")
        
        # ✅ RENK DÜZELTMESİ - Tüm satırlar aynı renkte
        total_container = ctk.CTkFrame(parent, fg_color="transparent")
        total_container.grid(row=row_idx, column=5, sticky="nsew", pady=5)
        
        # Ana tutar - type_color ile
        ctk.CTkLabel(total_container, text=total_text, 
                    font=ctk.CTkFont(size=12, weight="bold"), 
                    text_color=type_color).pack()  # ✅ type_color
        
        # Detay varsa göster - AYNI RENKTE
        if detail_text:
            ctk.CTkLabel(total_container, text=detail_text, 
                        font=ctk.CTkFont(size=9), 
                        text_color=type_color).pack()  # ✅ type_color (gri yerine)

        # İşlem butonları
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.grid(row=row_idx, column=6, sticky="ew")
        
        ctk.CTkButton(btn_frame, text="Düzenle", width=60, height=28, 
                     command=lambda t=transaction: self.edit_transaction(t), 
                     fg_color=COLORS["primary"]).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Sil", width=40, height=28, 
                     command=lambda t=transaction: self.delete_transaction(t), 
                     fg_color=COLORS["danger"]).pack(side="left", padx=5)
    
    def delete_transaction(self, transaction):
        tip = transaction.get("tip")
        if not askyesno("Onay", f"Bu {tip} işlemini silmek istediğinizden emin misiniz?\nBu işlem portföyünüzü kalıcı olarak etkileyecektir."):
            return
        
        # ✅ USER ID AL
        user_id = self.get_user_id()
        
        tarih = transaction.get("tarih")
        
        try:
            if tip == "Temettü":
                # Temettü sil
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        DELETE FROM dividends 
                        WHERE tarih = ? AND tutar = ? AND user_id = ?
                    ''', (tarih, transaction.get("tutar"), user_id))  # ✅ user_id eklendi
            else:
                # İşlem sil
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        DELETE FROM transactions 
                        WHERE tarih = ? AND toplam = ? AND user_id = ?
                    ''', (tarih, transaction.get("toplam"), user_id))  # ✅ user_id eklendi
            
            # ✅ DÜZELTİLMİŞ - user_id ile
            self.db.recalculate_portfolio_from_transactions(user_id)
            
            showinfo("Başarılı", "İşlem silindi ve portföy yeniden hesaplandı.")
            self.display_transactions()
        except Exception as e:
            showerror("Hata", f"İşlem silinemedi: {str(e)}")
            import traceback
            traceback.print_exc()

    def edit_transaction(self, transaction):
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title(f"İşlem Düzenle: {transaction.get('sembol')}")
        dialog.geometry("450x1")
        dialog.transient(self.parent)
        dialog.grab_set()

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="x", expand=True, padx=30, pady=20)

        tip = transaction.get("tip")
        ctk.CTkLabel(form, text=f"✏️ {tip} İşlemini Düzenle", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 20))

        ctk.CTkLabel(form, text="Hisse Sembolü:", anchor="w").pack(fill="x")
        symbol_entry = ctk.CTkEntry(form, placeholder_text="Sembol")
        symbol_entry.insert(0, transaction.get('sembol', ''))
        symbol_entry.pack(fill="x", pady=(0, 15))

        if tip == "Temettü":
            ctk.CTkLabel(form, text="Toplam Temettü Tutarı (₺):", anchor="w").pack(fill="x")
            amount_entry = ctk.CTkEntry(form)
            amount_entry.insert(0, str(transaction.get('toplam', 0)))
            amount_entry.pack(fill="x", pady=(0, 15))
        else:
            ctk.CTkLabel(form, text="Adet:", anchor="w").pack(fill="x")
            adet_entry = ctk.CTkEntry(form)
            adet_entry.insert(0, str(transaction.get('adet', 0)))
            adet_entry.pack(fill="x", pady=(0, 15))
            
            ctk.CTkLabel(form, text="Fiyat (₺):", anchor="w").pack(fill="x")
            fiyat_entry = ctk.CTkEntry(form)
            fiyat_entry.insert(0, str(transaction.get('fiyat', 0)))
            fiyat_entry.pack(fill="x", pady=(0, 15))
            
            # Komisyon bilgisini ekle
            ctk.CTkLabel(form, text="Komisyon (₺):", anchor="w").pack(fill="x")
            komisyon_entry = ctk.CTkEntry(form)
            komisyon_entry.insert(0, str(transaction.get('komisyon', 0)))
            komisyon_entry.pack(fill="x", pady=(0, 15))
            
            # ✅ USER ID AL
            user_id = self.get_user_id()
            
            # ✅ DÜZELTİLMİŞ - komisyon_orani
            settings = self.db.get_settings(user_id)
            commission_rate = settings.get("komisyon_orani", 0.0004)  # ✅ komisyon_orani
            
            try:
                if isinstance(commission_rate, str):
                    commission_rate = float(commission_rate.replace(',', '.'))
                else:
                    commission_rate = float(commission_rate)
            except:
                commission_rate = 0.0004
                
            # Komisyon oranı gösterimi
            commission_display = format_rate_display(commission_rate)
            
            # Komisyon yeniden hesaplama
            info_frame = ctk.CTkFrame(form, fg_color=("gray85", "gray17"), corner_radius=10)
            info_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(info_frame, text=f"Komisyon oranı: {commission_display}", 
                        font=ctk.CTkFont(size=11),
                        text_color=("gray50", "gray70")).pack(padx=15, pady=(10, 5))
            
            def recalculate_commission():
                try:
                    new_adet = int(adet_entry.get())
                    new_fiyat = float(fiyat_entry.get().replace(',', '.'))
                    islem_tutari = new_adet * new_fiyat
                    new_komisyon = islem_tutari * commission_rate
                    komisyon_entry.delete(0, 'end')
                    komisyon_entry.insert(0, f"{new_komisyon:.2f}")
                except:
                    pass
            
            ctk.CTkButton(info_frame, text="Komisyonu Yeniden Hesapla", 
                          command=recalculate_commission, 
                          height=25, width=200).pack(pady=(0, 10))
        
        def save_changes():
            # ✅ USER ID AL
            user_id = self.get_user_id()
            
            original_tarih = transaction.get('tarih')
            
            try:
                new_symbol = symbol_entry.get().strip().upper()
                if not new_symbol:
                    raise ValueError("Sembol boş olamaz.")

                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    
                    if tip == "Temettü":
                        new_tutar = float(amount_entry.get())
                        cursor.execute('''
                            UPDATE dividends 
                            SET sembol = ?, tutar = ? 
                            WHERE tarih = ? AND tutar = ? AND user_id = ?
                        ''', (new_symbol, new_tutar, original_tarih, transaction.get('tutar'), user_id))  # ✅ user_id eklendi
                    else:
                        new_adet = int(adet_entry.get())
                        new_fiyat = float(fiyat_entry.get().replace(',', '.'))
                        new_komisyon = float(komisyon_entry.get().replace(',', '.'))
                        new_toplam = new_adet * new_fiyat
                        cursor.execute('''
                            UPDATE transactions 
                            SET sembol = ?, adet = ?, fiyat = ?, toplam = ?, komisyon = ? 
                            WHERE tarih = ? AND toplam = ? AND user_id = ?
                        ''', (new_symbol, new_adet, new_fiyat, new_toplam, new_komisyon, original_tarih, transaction.get('toplam'), user_id))  # ✅ user_id eklendi
                
                # ✅ DÜZELTİLMİŞ - user_id ile
                self.db.recalculate_portfolio_from_transactions(user_id)
                
                # Sembol değişmişse güncel fiyatı çek
                if tip != "Temettü" and new_symbol != transaction.get('sembol'):
                    try:
                        import yfinance as yf
                        t = yf.Ticker(f"{new_symbol}.IS")
                        h = t.history(period="1d")
                        if not h.empty:
                            new_price = h['Close'].iloc[-1]
                            with self.db.get_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE portfolios 
                                    SET guncel_fiyat = ? 
                                    WHERE sembol = ? AND user_id = ?
                                ''', (new_price, new_symbol, user_id))  # ✅ user_id eklendi
                    except:
                        pass
                
                showinfo("Başarılı", "İşlem güncellendi.")
                dialog.destroy()
                self.display_transactions()

            except (ValueError, TypeError) as e:
                showerror("Hata", f"Lütfen geçerli sayılar girin. {str(e)}")

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkButton(btn_frame, text="💾 Kaydet", command=save_changes, height=40).pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkButton(btn_frame, text="❌ İptal", command=dialog.destroy, height=40, fg_color=("gray60", "gray40")).pack(side="left", expand=True, fill="x", padx=(5, 0))
        
        # Dinamik boyut
        dialog.update_idletasks()
        required_height = dialog.winfo_reqheight()
        min_height = 350
        max_height = 700
        final_height = max(min_height, min(required_height, max_height))
        dialog.geometry(f"450x{final_height}")
        
        # Ortala
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (final_height // 2)
        dialog.geometry(f"450x{final_height}+{x}+{y}")