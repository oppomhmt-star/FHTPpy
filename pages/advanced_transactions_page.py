# pages/advanced_transactions_page.py
"""
Gelişmiş İşlemler Sayfası - Stock Split, Rights Issue
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
from config import COLORS, FONT_SIZES
from advanced_api_service import StockSplitCalculator, RightsIssueCalculator
from ui_utils import showinfo, showerror

class AdvancedTransactionsPage:
    def __init__(self, parent, db, theme):
        self.parent = parent
        self.db = db
        self.theme = theme
        self.current_user_id = 1
        self.portfolio = []
    
    def get_bg_color(self):
        """Tema rengine göre arka plan rengi döndür"""
        if self.theme == "light":
            return ("white", "gray20")  # Light theme: white, Dark theme: gray20
        return ("gray95", "gray15")  # Default
    
    def create(self):
        """Sayfayı oluştur"""
        # Ana frame
        main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        title_label = ctk.CTkLabel(
            main_frame,
            text="⚙️ Gelişmiş İşlemler",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS["primary"]
        )
        title_label.pack(pady=(0, 20), anchor="w")
        
        # Sekme çerçevesi
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Stock Split sekmesi
        self.create_stock_split_tab()
        
        # Rights Issue sekmesi
        self.create_rights_issue_tab()
        
        # İşlem geçmişi sekmesi
        self.create_history_tab()
    
    def create_stock_split_tab(self):
        """Hisse bölünmesi sekmesi"""
        frame = ctk.CTkFrame(self.notebook, fg_color="transparent")
        self.notebook.add(frame, text="📊 Hisse Bölünmesi")
        
        # Ana frame
        scroll_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Form
        form_frame = ctk.CTkFrame(scroll_frame, fg_color=self.get_bg_color(), corner_radius=8)
        form_frame.pack(fill="x", padx=0, pady=0)
        
        # Başlık
        header = ctk.CTkLabel(
            form_frame,
            text="Hisse Bölünmesi Hesapla",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["primary"]
        )
        header.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Hisse seçimi
        label = ctk.CTkLabel(form_frame, text="Hisse Seçin:", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.stock_split_combo = ctk.CTkComboBox(
            form_frame,
            values=self.get_portfolio_symbols(),
            state="readonly"
        )
        self.stock_split_combo.pack(fill="x", padx=15, pady=(0, 15))
        
        # Bölünme oranı
        label = ctk.CTkLabel(form_frame, text="Bölünme Oranı (örn: 2 = 1 hisse 2'ye bölünür):", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.split_ratio_entry = ctk.CTkEntry(form_frame, placeholder_text="2")
        self.split_ratio_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.split_ratio_entry.insert(0, "2")
        
        # Hesaplama butonu
        calc_btn = ctk.CTkButton(
            form_frame,
            text="🔢 Hesapla",
            command=self.calculate_stock_split,
            height=40,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary"]
        )
        calc_btn.pack(fill="x", padx=15, pady=15)
        
        # Sonuçlar
        self.split_results_frame = ctk.CTkFrame(scroll_frame, fg_color=self.get_bg_color(), corner_radius=8)
        self.split_results_frame.pack(fill="x", padx=0, pady=(10, 0))
        
        results_header = ctk.CTkLabel(
            self.split_results_frame,
            text="Hesaplama Sonuçları",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["success"]
        )
        results_header.pack(anchor="w", padx=15, pady=(15, 10))
        
        self.split_results_label = ctk.CTkLabel(
            self.split_results_frame,
            text="Hesaplama sonuçları burada gösterilecek",
            justify="left",
            font=ctk.CTkFont(size=11)
        )
        self.split_results_label.pack(padx=15, pady=15, anchor="nw", fill="both", expand=True)
        
        # Uygula butonu
        apply_btn = ctk.CTkButton(
            self.split_results_frame,
            text="✅ Uygula",
            command=self.apply_stock_split,
            height=40,
            fg_color=COLORS["success"],
            hover_color=COLORS["success"]
        )
        apply_btn.pack(fill="x", padx=15, pady=15)
    
    def create_rights_issue_tab(self):
        """Rüçhan hakkı sekmesi"""
        frame = ctk.CTkFrame(self.notebook, fg_color="transparent")
        self.notebook.add(frame, text="💼 Bedelli Sermaye Artırımı")
        
        # Ana frame
        scroll_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Form
        form_frame = ctk.CTkFrame(scroll_frame, fg_color=self.get_bg_color(), corner_radius=8)
        form_frame.pack(fill="x", padx=0, pady=0)
        
        # Başlık
        header = ctk.CTkLabel(
            form_frame,
            text="Bedelli Sermaye Artırımı Hesapla",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["primary"]
        )
        header.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Hisse seçimi
        label = ctk.CTkLabel(form_frame, text="Hisse Seçin:", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.rights_combo = ctk.CTkComboBox(
            form_frame,
            values=self.get_portfolio_symbols(),
            state="readonly"
        )
        self.rights_combo.pack(fill="x", padx=15, pady=(0, 15))
        
        # Rüçhan oranı
        label = ctk.CTkLabel(form_frame, text="Rüçhan Oranı (örn: 0.25 = her 4 hisse'ye 1 yeni):", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.rights_ratio_entry = ctk.CTkEntry(form_frame, placeholder_text="0.25")
        self.rights_ratio_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.rights_ratio_entry.insert(0, "0.25")
        
        # Yeni hisse fiyatı
        label = ctk.CTkLabel(form_frame, text="Yeni Hisse Fiyatı (₺):", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.new_price_entry = ctk.CTkEntry(form_frame, placeholder_text="0.00")
        self.new_price_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Hesaplama butonu
        calc_btn = ctk.CTkButton(
            form_frame,
            text="🔢 Hesapla",
            command=self.calculate_rights_issue,
            height=40,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary"]
        )
        calc_btn.pack(fill="x", padx=15, pady=15)
        
        # Sonuçlar
        self.rights_results_frame = ctk.CTkFrame(scroll_frame, fg_color=self.get_bg_color(), corner_radius=8)
        self.rights_results_frame.pack(fill="x", padx=0, pady=(10, 0))
        
        results_header = ctk.CTkLabel(
            self.rights_results_frame,
            text="Hesaplama Sonuçları",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["success"]
        )
        results_header.pack(anchor="w", padx=15, pady=(15, 10))
        
        self.rights_results_label = ctk.CTkLabel(
            self.rights_results_frame,
            text="Hesaplama sonuçları burada gösterilecek",
            justify="left",
            font=ctk.CTkFont(size=11)
        )
        self.rights_results_label.pack(padx=15, pady=15, anchor="nw", fill="both", expand=True)
        
        # Uygula butonu
        apply_btn = ctk.CTkButton(
            self.rights_results_frame,
            text="✅ Uygula",
            command=self.apply_rights_issue,
            height=40,
            fg_color=COLORS["success"],
            hover_color=COLORS["success"]
        )
        apply_btn.pack(fill="x", padx=15, pady=15)
    
    def create_history_tab(self):
        """İşlem geçmişi sekmesi"""
        frame = ctk.CTkFrame(self.notebook, fg_color=self.get_bg_color())
        self.notebook.add(frame, text="📜 Geçmiş")
        
        # Başlık
        header = ctk.CTkLabel(
            frame,
            text="Gelişmiş İşlem Geçmişi",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["primary"]
        )
        header.pack(anchor="w", padx=10, pady=(10, 15))
        
        # Treeview
        columns = ("Tarih", "Hisse", "İşlem Türü", "Adet", "Fiyat", "Toplam", "Not")
        
        # Tema rengine göre treeview stilini ayarla
        style = ttk.Style()
        if self.theme == "light":
            style.theme_use('clam')
            style.configure("Treeview", background="white", foreground="black", fieldbackground="white")
            style.configure("Treeview.Heading", background="lightgray", foreground="black")
        else:
            style.configure("Treeview", background="gray20", foreground="white", fieldbackground="gray20")
            style.configure("Treeview.Heading", background="gray30", foreground="white")
        
        tree = ttk.Treeview(frame, columns=columns, height=20, show="headings")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=80)
        
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        
        # Verileri yükle
        self.refresh_history(tree)
    
    def refresh_history(self, tree):
        """Geçmiş işlemleri yükle"""
        for item in tree.get_children():
            tree.delete(item)
        
        # TODO: advanced_transactions tablosundan verileri çek
    
    def get_portfolio_symbols(self):
        """Portföyden hisse sembollerini getir"""
        portfolio = self.db.get_portfolio(self.current_user_id)
        return [stock['sembol'] for stock in portfolio]
    
    def calculate_stock_split(self):
        """Stock split hesapla"""
        try:
            symbol = self.stock_split_combo.get()
            if not symbol:
                showerror("Hata", "Lütfen bir hisse seçin")
                return
            
            split_ratio = float(self.split_ratio_entry.get())
            
            # Portföyden hisseyi bul
            portfolio = self.db.get_portfolio(self.current_user_id)
            stock = next((s for s in portfolio if s['sembol'] == symbol), None)
            
            if not stock:
                showerror("Hata", f"{symbol} portföyde bulunamadı")
                return
            
            # Hesapla
            result = StockSplitCalculator.calculate_stock_split(
                stock['adet'],
                stock['ort_maliyet'],
                split_ratio
            )
            
            # Sonuçları göster
            text = f"""Eski Adet: {result['eski_adet']} x {result['eski_maliyet']:.2f}₺
Yeni Adet: {result['yeni_adet']} x {result['yeni_maliyet']:.2f}₺
Bölünme Oranı: 1:{split_ratio}

✅ Toplam maliyet değişmedi"""
            
            self.split_results_label.configure(text=text)
            
        except ValueError:
            showerror("Hata", "Lütfen geçerli bir sayı girin")
        except Exception as e:
            showerror("Hata", str(e))
    
    def apply_stock_split(self):
        """Stock split uygula"""
        try:
            symbol = self.stock_split_combo.get()
            split_ratio = float(self.split_ratio_entry.get())
            
            if not symbol:
                showerror("Hata", "Lütfen bir hisse seçin")
                return
            
            if self.db.apply_stock_split(symbol, split_ratio, self.current_user_id):
                showinfo("Başarılı", f"{symbol} hisse bölünmesi uygulandı")
                # Combo'yu yenile
                self.stock_split_combo.configure(values=self.get_portfolio_symbols())
            else:
                showerror("Hata", "İşlem uygulanırken hata oluştu")
        
        except Exception as e:
            showerror("Hata", str(e))
    
    def calculate_rights_issue(self):
        """Rüçhan hakkı hesapla"""
        try:
            symbol = self.rights_combo.get()
            if not symbol:
                showerror("Hata", "Lütfen bir hisse seçin")
                return
            
            rights_ratio = float(self.rights_ratio_entry.get())
            new_price = float(self.new_price_entry.get())
            
            # Portföyden hisseyi bul
            portfolio = self.db.get_portfolio(self.current_user_id)
            stock = next((s for s in portfolio if s['sembol'] == symbol), None)
            
            if not stock:
                showerror("Hata", f"{symbol} portföyde bulunamadı")
                return
            
            # Hesapla
            result = RightsIssueCalculator.calculate_rights_issue(
                stock['adet'],
                stock['guncel_fiyat'],
                rights_ratio,
                new_price
            )
            
            # Sonuçları göster
            text = f"""Eski Adet: {result['eski_adet']}
Yeni Hisse Sayısı: {result['yeni_hisse_adet']}
Yeni Hisse Fiyatı: {result['yeni_hisse_fiyati']:.2f}₺

Toplam Adet (sonra): {result['toplam_yeni_adet']}
Yeni Ort. Maliyet: {result['yeni_ortalama_maliyet']:.2f}₺
Toplam Yatırım: {result['toplam_yatirim']:.2f}₺"""
            
            self.rights_results_label.configure(text=text)
            
        except ValueError:
            showerror("Hata", "Lütfen geçerli sayı değerleri girin")
        except Exception as e:
            showerror("Hata", str(e))
    
    def apply_rights_issue(self):
        """Rüçhan hakkı uygula"""
        try:
            symbol = self.rights_combo.get()
            rights_ratio = float(self.rights_ratio_entry.get())
            new_price = float(self.new_price_entry.get())
            
            if not symbol:
                showerror("Hata", "Lütfen bir hisse seçin")
                return
            
            if self.db.apply_rights_issue(symbol, rights_ratio, new_price, self.current_user_id):
                showinfo("Başarılı", f"{symbol} bedelli sermaye artırımı uygulandı")
                self.rights_combo.configure(values=self.get_portfolio_symbols())
            else:
                showerror("Hata", "İşlem uygulanırken hata oluştu")
        
        except Exception as e:
            showerror("Hata", str(e))
