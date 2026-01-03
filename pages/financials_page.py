# pages/financials_page.py (Sıralama Olmadan, Sadece Temizleme)

import customtkinter as ctk
from datetime import datetime
import threading
import pandas as pd
from isyatirimhisse import fetch_financials
from config import COLORS
from ui_utils import showerror
import re

class FinancialsPage:
    def __init__(self, parent, db, api, theme):
        self.parent = parent
        self.db = db
        self.api = api
        self.theme = theme
        self.stock_combo = None
        self.start_year_entry = None
        self.end_year_entry = None
        self.table_frame = None

    def create(self):
        self.main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)
        self.create_header()
        self.create_controls()
        self.table_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color=("gray90", "gray20"))
        self.table_frame.pack(fill="both", expand=True, padx=5, pady=10)
        ctk.CTkLabel(self.table_frame, text="Lütfen yukarıdan bir hisse seçip 'Verileri Getir' butonuna basın.", text_color="gray").pack(expand=True, pady=50)

    def create_header(self):
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20), padx=5)
        ctk.CTkLabel(header_frame, text="📑 Finansal Tablolar", 
                     font=ctk.CTkFont(size=32, weight="bold")).pack(side="left")

    def create_controls(self):
        controls_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        controls_frame.pack(fill="x", pady=(0, 10), padx=5)
        
        ctk.CTkLabel(controls_frame, text="Hisse:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 10))
        portfolio_stocks = sorted([stock['sembol'] for stock in self.db.get_portfolio()])
        self.stock_combo = ctk.CTkComboBox(controls_frame, values=portfolio_stocks if portfolio_stocks else ["Portföy Boş"], width=150)
        if portfolio_stocks: self.stock_combo.set(portfolio_stocks[0])
        self.stock_combo.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(controls_frame, text="Başlangıç Yılı:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 10))
        current_year = datetime.now().year
        self.start_year_entry = ctk.CTkEntry(controls_frame, width=70)
        self.start_year_entry.insert(0, str(current_year - 2))
        self.start_year_entry.pack(side="left", padx=(0, 20))
        
        ctk.CTkLabel(controls_frame, text="Bitiş Yılı:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 10))
        self.end_year_entry = ctk.CTkEntry(controls_frame, width=70)
        self.end_year_entry.insert(0, str(current_year))
        self.end_year_entry.pack(side="left", padx=(0, 20))
        
        ctk.CTkButton(controls_frame, text="📊 Verileri Getir", command=self.fetch_data, height=35).pack(side="left")

    def fetch_data(self):
        symbol = self.stock_combo.get()
        if symbol == "Portföy Boş": return showerror("Hata", "Lütfen önce portföyünüze bir hisse ekleyin.")
        try:
            start_year = int(self.start_year_entry.get()); end_year = int(self.end_year_entry.get())
            if start_year > end_year: return showerror("Hata", "Başlangıç yılı, bitiş yılından büyük olamaz.")
        except (ValueError, TypeError): return showerror("Hata", "Lütfen geçerli bir yıl formatı girin (örn: 2023).")
        
        for widget in self.table_frame.winfo_children(): widget.destroy()
        ctk.CTkLabel(self.table_frame, text=f"⏳ {symbol} için veriler çekiliyor...", text_color="gray").pack(expand=True, pady=50)
        
        threading.Thread(target=self._fetch_thread, args=(symbol, start_year, end_year), daemon=True).start()

    def _fetch_thread(self, symbol, start_year, end_year):
        try:
            df = fetch_financials(symbols=symbol, start_year=start_year, end_year=end_year, save_to_excel=False)
            self.parent.after(0, self.display_data, df)
        except Exception as e:
            print(f"Finansal veri hatası: {e}")
            self.parent.after(0, self.display_data, None)

    # <<< YENİLENMİŞ VE EN SADE display_data FONKSİYONU >>>
    def display_data(self, df):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        if df is None or df.empty:
            ctk.CTkLabel(self.table_frame, text="Veri bulunamadı veya API'den çekilemedi.", text_color="gray").pack(expand=True, pady=50)
            return

        # 1. İstenmeyen sütunları kaldır
        columns_to_drop = ['SYMBOL', 'FINANCIAL_ITEM_NAME_EN', 'FINANCIAL_ITEM_CODE']
        df_final = df.drop(columns=[col for col in columns_to_drop if col in df.columns], errors='ignore')
        
        # 2. Tabloyu oluştur
        grid_frame = ctk.CTkFrame(self.table_frame, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)

        # Başlıkları doğrudan temizlenmiş DataFrame'den al
        headers = df_final.columns.tolist()
        
        # Dinamik genişlik hesaplaması
        font = ctk.CTkFont(size=12)
        min_widths = {i: font.measure(str(header)) for i, header in enumerate(headers)}
        
        for _, row in df_final.iterrows():
            for i, value in enumerate(row):
                try: formatted_value = f"{int(value):,}"
                except: formatted_value = str(value)
                min_widths[i] = max(min_widths.get(i, 0), font.measure(formatted_value))
        
        for i, width in min_widths.items():
            grid_frame.grid_columnconfigure(i, minsize=width + 25)

        # Başlıkları yerleştir
        header_bg = ctk.CTkFrame(grid_frame, fg_color=("gray75", "gray25"), corner_radius=8, height=40)
        header_bg.grid(row=0, column=0, columnspan=len(headers), sticky="nsew", pady=(0, 5))
        for col_idx, header_text in enumerate(headers):
            header_label = ctk.CTkLabel(grid_frame, text=header_text, font=ctk.CTkFont(size=12, weight="bold"), bg_color=header_bg.cget("fg_color"))
            header_label.grid(row=0, column=col_idx, sticky="nsew", padx=5)

        # Veri satırlarını yerleştir
        for row_idx, row_data in enumerate(df_final.itertuples(index=False), start=1):
            for col_idx, cell_data in enumerate(row_data):
                anchor = "w" if headers[col_idx] == 'FINANCIAL_ITEM_NAME_TR' else "e"
                try: formatted_text = f"{int(cell_data):,}".replace(",", ".")
                except (ValueError, TypeError): formatted_text = str(cell_data)
                ctk.CTkLabel(grid_frame, text=formatted_text, anchor=anchor, font=ctk.CTkFont(size=12)).grid(row=row_idx, column=col_idx, sticky="ew", padx=5, pady=2)
