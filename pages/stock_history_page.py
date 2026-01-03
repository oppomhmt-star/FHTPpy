# pages/stock_history_page.py

import customtkinter as ctk
from datetime import datetime, timedelta
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import pandas as pd
from config import COLORS
import threading

# Mplfinance (opsiyonel - mum grafiği için)
try:
    import mplfinance as mpf
    HAS_MPLFINANCE = True
except ImportError:
    print("⚠️ mplfinance yüklü değil. Basit grafik kullanılacak.")
    print("Mum grafiği için: pip install mplfinance")
    HAS_MPLFINANCE = False

class StockHistoryPage:
    def __init__(self, parent, db, api, theme):
        self.parent = parent
        self.db = db
        self.api = api
        self.theme = theme
        
        self.stock_symbol = None
        self.stock_data = None
        self.chart_period = "1y"  # Varsayılan: 1 yıl
        
        # Grafikler ve widget'lar
        self.stock_selector = None
        self.period_selector = None
        self.tabview = None
        self.scale_var = None
        
    def create(self):
        """Ana sayfayı oluştur"""
        self.main_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True)
        
        # Üst kontrol bölümü
        self.create_controls()
        
        # Sekme yapısı
        self.tabview = ctk.CTkTabview(self.main_frame, corner_radius=10)
        self.tabview.pack(fill="both", expand=True, padx=5, pady=(10, 5))
        
        # Sekmeleri oluştur
        self.tabview.add("📊 Genel Bakış")
        self.tabview.add("📈 Fiyat Grafiği")
        self.tabview.add("⚡ Teknik Analiz")
        self.tabview.add("📑 İstatistikler")
        
        # Veri yoksa bilgi mesajı
        self.show_welcome_message()
        
    def show_welcome_message(self):
        """Hoş geldin mesajı"""
        tab = self.tabview.tab("📊 Genel Bakış")
        
        message_frame = ctk.CTkFrame(tab, fg_color="transparent")
        message_frame.pack(expand=True)
        
        ctk.CTkLabel(message_frame, text="📈", 
                    font=ctk.CTkFont(size=64)).pack(pady=(50, 20))
        
        ctk.CTkLabel(message_frame, text="Hisse Geçmişi Analizi", 
                    font=ctk.CTkFont(size=24, weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(message_frame, text="👆 Lütfen yukarıdan incelemek istediğiniz hisseyi seçin", 
                    font=ctk.CTkFont(size=14), text_color="gray").pack(pady=5)
        
    def create_controls(self):
        """Kontrol bölümünü oluştur"""
        controls_frame = ctk.CTkFrame(self.main_frame, fg_color=("gray85", "gray17"), corner_radius=10)
        controls_frame.pack(fill="x", padx=5, pady=5)
        
        content = ctk.CTkFrame(controls_frame, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=10)
        
        # Başlık
        ctk.CTkLabel(content, text="📈 Hisse Geçmişi", 
                   font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        
        # Hisse seçimi
        stock_frame = ctk.CTkFrame(content, fg_color="transparent")
        stock_frame.pack(side="left", padx=(20, 0))
        
        ctk.CTkLabel(stock_frame, text="Hisse:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 5))
        
        # Portföydeki hisseler + "Diğer Hisse..." seçeneği
        portfolio = self.db.get_portfolio()
        stock_options = ["Seçiniz..."] + [s['sembol'] for s in portfolio] + ["➕ Diğer Hisse..."]
        
        self.stock_selector = ctk.CTkComboBox(
            stock_frame, 
            values=stock_options,
            width=150,
            command=self.on_stock_selected
        )
        self.stock_selector.set("Seçiniz...")
        self.stock_selector.pack(side="left")
        
        # Dönem seçimi
        period_frame = ctk.CTkFrame(content, fg_color="transparent")
        period_frame.pack(side="right")
        
        ctk.CTkLabel(period_frame, text="Dönem:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 5))
        
        self.period_selector = ctk.CTkComboBox(
            period_frame, 
            values=["1 Ay", "3 Ay", "6 Ay", "1 Yıl", "5 Yıl", "Tümü"],
            width=100,
            command=self.on_period_selected
        )
        self.period_selector.set("1 Yıl")
        self.period_selector.pack(side="left")
    
    def on_stock_selected(self, symbol):
        """Hisse seçildiğinde"""
        if symbol == "Seçiniz...":
            return
        
        if symbol == "➕ Diğer Hisse...":
            self.show_custom_stock_dialog()
            return
        
        self.stock_symbol = symbol
        self.load_stock_data()
    
    def on_period_selected(self, period):
        """Dönem seçildiğinde"""
        # Dönemi yfinance formatına dönüştür
        period_map = {
            "1 Ay": "1mo",
            "3 Ay": "3mo",
            "6 Ay": "6mo",
            "1 Yıl": "1y",
            "5 Yıl": "5y",
            "Tümü": "max"
        }
        
        self.chart_period = period_map.get(period, "1y")
        
        if self.stock_symbol:
            self.load_stock_data()
    
    def show_custom_stock_dialog(self):
        """Özel hisse kodu giriş penceresi"""
        dialog = ctk.CTkToplevel(self.parent)
        dialog.title("Özel Hisse Girişi")
        dialog.geometry("350x180")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Merkeze konumlandır
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (dialog.winfo_screenheight() // 2) - (180 // 2)
        dialog.geometry(f"350x180+{x}+{y}")
        
        ctk.CTkLabel(dialog, text="Hisse Kodu Girin:", 
                   font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(20, 10))
        
        ctk.CTkLabel(dialog, text="(Örn: THYAO, AKBNK, GARAN)", 
                   font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(0, 10))
        
        entry = ctk.CTkEntry(dialog, width=250, height=35, font=ctk.CTkFont(size=14))
        entry.pack(pady=10)
        entry.focus()
        
        def on_submit():
            symbol = entry.get().strip().upper()
            if symbol:
                dialog.destroy()
                self.stock_symbol = symbol
                self.load_stock_data()
        
        # Enter tuşu ile submit
        entry.bind("<Return>", lambda e: on_submit())
        
        button_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(fill="x", padx=30, pady=15)
        
        ctk.CTkButton(button_frame, text="✓ Tamam", command=on_submit, 
                    width=120, height=35).pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        ctk.CTkButton(button_frame, text="✕ İptal", command=dialog.destroy,
                    fg_color=("gray60", "gray40"), width=120, height=35).pack(side="left", expand=True, fill="x", padx=(5, 0))
    
    def load_stock_data(self):
        """Hisse verilerini yükle"""
        if not self.tabview:
            return
        
        # Yükleniyor göstergesi
        for tab_name in ["📊 Genel Bakış", "📈 Fiyat Grafiği", "⚡ Teknik Analiz", "📑 İstatistikler"]:
            try:
                tab = self.tabview.tab(tab_name)
                for widget in tab.winfo_children():
                    widget.destroy()
                
                loading_label = ctk.CTkLabel(tab, text=f"⏳ {self.stock_symbol} verisi yükleniyor...",
                                          font=ctk.CTkFont(size=14))
                loading_label.pack(expand=True)
            except:
                pass
        
        # Verileri arka planda yükle
        threading.Thread(target=self._load_data_thread, daemon=True).start()
    
    def _load_data_thread(self):
        """Veri yükleme işlemi (arka planda)"""
        try:
            # YFinance'den veri çek
            ticker = yf.Ticker(f"{self.stock_symbol}.IS")  # Türk hisseleri için .IS ekle
            
            # Hisse bilgilerini al
            info = ticker.info
            
            # Fiyat geçmişini al
            hist = ticker.history(period=self.chart_period)
            
            if hist.empty:
                raise Exception("Hisse verisi bulunamadı. Hisse kodu doğru mu kontrol edin.")
            
            # Teknik indikatörleri hesapla
            self.calculate_indicators(hist)
            
            # Ana thread'de UI güncelle
            self.parent.after(0, lambda: self.update_ui(ticker, info, hist))
            
        except Exception as e:
            error_msg = str(e)
            print(f"Veri yükleme hatası: {error_msg}")
            
            # Ana thread'de hata mesajı göster
            self.parent.after(0, lambda: self.show_error(error_msg))
    
    def calculate_indicators(self, data):
        """Teknik göstergeleri hesapla"""
        # Kopyasını oluştur, orjinali değiştirme
        df = data.copy()
        
        try:
            # SMA (Simple Moving Average) - 20, 50, 200 gün
            if len(df) >= 20:
                df['SMA20'] = df['Close'].rolling(window=20).mean()
            if len(df) >= 50:
                df['SMA50'] = df['Close'].rolling(window=50).mean()
            if len(df) >= 200:
                df['SMA200'] = df['Close'].rolling(window=200).mean()
            
            # Bollinger Bands (20 günlük)
            if len(df) >= 20:
                df['BB_middle'] = df['Close'].rolling(window=20).mean()
                df['BB_std'] = df['Close'].rolling(window=20).std()
                df['BB_upper'] = df['BB_middle'] + 2 * df['BB_std']
                df['BB_lower'] = df['BB_middle'] - 2 * df['BB_std']
            
            # RSI (Relative Strength Index) - 14 günlük
            if len(df) >= 15:
                delta = df['Close'].diff()
                up = delta.clip(lower=0)
                down = -1 * delta.clip(upper=0)
                ema_up = up.ewm(com=13, adjust=False).mean()
                ema_down = down.ewm(com=13, adjust=False).mean()
                rs = ema_up / ema_down
                df['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD (Moving Average Convergence Divergence)
            if len(df) >= 26:
                exp12 = df['Close'].ewm(span=12, adjust=False).mean()
                exp26 = df['Close'].ewm(span=26, adjust=False).mean()
                df['MACD'] = exp12 - exp26
                df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
                df['MACD_Hist'] = df['MACD'] - df['Signal']
            
            self.stock_data = df
        except Exception as e:
            print(f"Gösterge hesaplama hatası: {e}")
            self.stock_data = df
    
    def update_ui(self, ticker, info, hist):
        """UI'ı güncellenmiş verilerle güncelle"""
        if not self.tabview:
            return
        
        # Sekmeleri temizle
        for tab_name in ["📊 Genel Bakış", "📈 Fiyat Grafiği", "⚡ Teknik Analiz", "📑 İstatistikler"]:
            try:
                tab = self.tabview.tab(tab_name)
                for widget in tab.winfo_children():
                    widget.destroy()
            except:
                pass
        
        # Her sekmeyi doldur
        try:
            self.create_overview_tab(ticker, info, hist)
            self.create_price_chart_tab(hist)
            self.create_technical_tab()
            self.create_stats_tab(hist)
        except Exception as e:
            print(f"UI güncelleme hatası: {e}")
            self.show_error(f"UI oluşturma hatası: {str(e)}")
    
    def create_overview_tab(self, ticker, info, hist):
        """Genel Bakış sekmesini oluştur"""
        tab = self.tabview.tab("📊 Genel Bakış")
        
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        # Hisse başlığı
        header_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        header_frame.pack(fill="x", pady=10)
        
        symbol_text = self.stock_symbol
        name_text = info.get('longName', info.get('shortName', 'Bilinmiyor'))
        
        ctk.CTkLabel(header_frame, text=f"{symbol_text}", 
                    font=ctk.CTkFont(size=32, weight="bold")).pack(side="left")
        
        ctk.CTkLabel(header_frame, text=f"{name_text}", 
                    font=ctk.CTkFont(size=14), 
                    text_color=("gray50", "gray70")).pack(side="left", padx=10, pady=8)
        
        # Fiyat özet kartı
        price_card = ctk.CTkFrame(scroll, corner_radius=10, 
                                fg_color=("gray90", "gray13"))
        price_card.pack(fill="x", pady=10)
        
        try:
            # Son fiyat ve değişim
            current = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current
            change = current - prev_close
            change_pct = (change / prev_close * 100) if prev_close > 0 else 0
            
            color = COLORS["success"] if change >= 0 else COLORS["danger"]
            
            price_content = ctk.CTkFrame(price_card, fg_color="transparent")
            price_content.pack(fill="x", padx=15, pady=15)
            
            ctk.CTkLabel(price_content, text="Son Fiyat", 
                        font=ctk.CTkFont(size=12), 
                        text_color=("gray50", "gray70")).pack(anchor="w")
            
            price_row = ctk.CTkFrame(price_content, fg_color="transparent")
            price_row.pack(fill="x", pady=5)
            
            ctk.CTkLabel(price_row, text=f"{current:.2f} ₺", 
                        font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
            
            ctk.CTkLabel(price_row, text=f"{change:+.2f} ₺ ({change_pct:+.2f}%)", 
                        font=ctk.CTkFont(size=16, weight="bold"), 
                        text_color=color).pack(side="left", padx=15)
            
            # Gün değerleri
            day_frame = ctk.CTkFrame(price_content, fg_color="transparent")
            day_frame.pack(fill="x", pady=(10, 0))
            
            day_values = [
                ("Açılış", hist['Open'].iloc[-1]),
                ("En Yüksek", hist['High'].iloc[-1]),
                ("En Düşük", hist['Low'].iloc[-1]),
                ("Hacim", hist['Volume'].iloc[-1])
            ]
            
            for i, (label, value) in enumerate(day_values):
                frame = ctk.CTkFrame(day_frame, fg_color="transparent")
                frame.pack(side="left", expand=True, fill="x", padx=5)
                
                ctk.CTkLabel(frame, text=label, 
                            font=ctk.CTkFont(size=11), 
                            text_color=("gray50", "gray70")).pack(anchor="w")
                
                if label == "Hacim":
                    formatted = f"{value:,.0f}" if not pd.isna(value) else "N/A"
                else:
                    formatted = f"{value:.2f} ₺" if not pd.isna(value) else "N/A"
                
                ctk.CTkLabel(frame, text=formatted, 
                            font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        
        except Exception as e:
            print(f"Fiyat kartı oluşturma hatası: {e}")
            ctk.CTkLabel(price_card, text=f"Fiyat bilgisi alınamadı", 
                        text_color="gray").pack(pady=20)
        
        # Şirket bilgileri
        info_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray90", "gray13"))
        info_card.pack(fill="x", pady=10)
        
        ctk.CTkLabel(info_card, text="Şirket Bilgileri", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        info_grid = ctk.CTkFrame(info_card, fg_color="transparent")
        info_grid.pack(fill="x", padx=15, pady=(0, 15))
        
        # Grid yapısı
        for i in range(3):
            info_grid.grid_columnconfigure(i, weight=1)
        
        info_items = [
            ("Sektör", info.get('sector', 'N/A')),
            ("Piyasa Değeri", f"{info.get('marketCap', 0):,.0f} ₺" if info.get('marketCap') else 'N/A'),
            ("F/K Oranı", f"{info.get('trailingPE', 0):.2f}" if info.get('trailingPE') else 'N/A'),
            ("Beta", f"{info.get('beta', 0):.2f}" if info.get('beta') else 'N/A'),
            ("52H Düşük", f"{info.get('fiftyTwoWeekLow', 0):.2f} ₺" if info.get('fiftyTwoWeekLow') else 'N/A'),
            ("52H Yüksek", f"{info.get('fiftyTwoWeekHigh', 0):.2f} ₺" if info.get('fiftyTwoWeekHigh') else 'N/A'),
        ]
        
        for i, (label, value) in enumerate(info_items):
            row = i // 3
            col = i % 3
            
            frame = ctk.CTkFrame(info_grid, fg_color="transparent")
            frame.grid(row=row, column=col, padx=5, pady=5, sticky="w")
            
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11), 
                        text_color=("gray50", "gray70")).pack(anchor="w")
            
            ctk.CTkLabel(frame, text=value, 
                        font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
        
        # Mini fiyat grafiği
        mini_chart_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray90", "gray13"))
        mini_chart_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(mini_chart_frame, text="Fiyat Trendi", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        chart_container = ctk.CTkFrame(mini_chart_frame, fg_color="transparent", height=200)
        chart_container.pack(fill="x", padx=15, pady=(0, 15))
        chart_container.pack_propagate(False)
        
        try:
            # Son 30 gün
            last_30 = hist.tail(min(30, len(hist)))
            
            fig = plt.Figure(figsize=(8, 3.5), dpi=100)
            ax = fig.add_subplot(111)
            
            bg_color = '#2b2b2b' if self.theme == "dark" else '#f8f9fa'
            text_color = 'white' if self.theme == "dark" else 'black'
            
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
            
            dates = mdates.date2num(last_30.index.to_pydatetime())
            
            # Çizgi grafiği
            ax.plot(dates, last_30['Close'], color='#14b8a6', linewidth=2.5)
            
            # Alan doldurma
            if len(last_30) > 1:
                first_val = last_30['Close'].iloc[0]
                ax.fill_between(dates, last_30['Close'], first_val, 
                               where=(last_30['Close'] >= first_val), 
                               color='#10b981', alpha=0.2)
                ax.fill_between(dates, last_30['Close'], first_val, 
                               where=(last_30['Close'] < first_val), 
                               color='#ef4444', alpha=0.2)
            
            # Eksenleri formatla
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            
            # Stil
            ax.grid(True, alpha=0.3, linestyle='--')
            for spine in ax.spines.values():
                spine.set_color(text_color)
            
            ax.tick_params(colors=text_color, labelsize=9)
            
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            print(f"Mini grafik hatası: {e}")
            ctk.CTkLabel(chart_container, text="Grafik oluşturulamadı", 
                        text_color="gray").pack(expand=True)
    
    def create_price_chart_tab(self, hist):
        """Fiyat Grafiği sekmesi"""
        tab = self.tabview.tab("📈 Fiyat Grafiği")
        
        # Fiyat grafiği oluştur
        chart_frame = ctk.CTkFrame(tab, fg_color=("gray90", "gray13"), corner_radius=10)
        chart_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Basit fiyat grafiği
        self.create_simple_price_chart(chart_frame, self.stock_data if self.stock_data is not None else hist)
    
    def create_simple_price_chart(self, parent, data):
        """Basitleştirilmiş fiyat grafiği (hareketli ortalamalar ile)"""
        try:
            # Grafik container
            chart_content = ctk.CTkFrame(parent, fg_color="transparent")
            chart_content.pack(fill="both", expand=True, padx=15, pady=15)
            
            # Matplotlib ile grafik
            fig = plt.Figure(figsize=(11, 7), dpi=100)
            ax = fig.add_subplot(111)
            
            # Renkleri ayarla
            bg_color = '#2b2b2b' if self.theme == "dark" else '#f8f9fa'
            text_color = 'white' if self.theme == "dark" else 'black'
            
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
            
            # Tarihleri formatla
            dates = mdates.date2num(data.index.to_pydatetime())
            
            # Fiyat çizgisi
            ax.plot(dates, data['Close'], color='#14b8a6', linewidth=2.5, label='Kapanış', zorder=5)
            
            # Hareketli ortalamalar (varsa)
            if 'SMA20' in data.columns and not data['SMA20'].isna().all():
                ax.plot(dates, data['SMA20'], color='#3b82f6', linewidth=1.8, 
                       linestyle='--', label='SMA 20', alpha=0.8, zorder=4)
            
            if 'SMA50' in data.columns and not data['SMA50'].isna().all():
                ax.plot(dates, data['SMA50'], color='#8b5cf6', linewidth=1.8, 
                       linestyle='--', label='SMA 50', alpha=0.8, zorder=3)
            
            if 'SMA200' in data.columns and not data['SMA200'].isna().all():
                ax.plot(dates, data['SMA200'], color='#ec4899', linewidth=2, 
                       linestyle='--', label='SMA 200', alpha=0.8, zorder=2)
            
            # Bollinger Bantları (varsa)
            if 'BB_upper' in data.columns and not data['BB_upper'].isna().all():
                ax.plot(dates, data['BB_upper'], color='#f59e0b', linewidth=1, 
                       linestyle=':', alpha=0.5, zorder=1)
                ax.plot(dates, data['BB_lower'], color='#f59e0b', linewidth=1, 
                       linestyle=':', alpha=0.5, zorder=1)
                ax.fill_between(dates, data['BB_upper'], data['BB_lower'], 
                               color='#f59e0b', alpha=0.1, zorder=0)
            
            # Eksenleri formatla
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%y'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())
            
            # Grid ve stilizasyon
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
            ax.legend(loc='upper left', facecolor=bg_color, 
                     edgecolor=text_color, labelcolor=text_color, 
                     fontsize=10, framealpha=0.9)
            
            # Eksen renkleri
            ax.tick_params(colors=text_color, labelsize=10)
            for spine in ax.spines.values():
                spine.set_color(text_color)
                spine.set_linewidth(1)
            
            ax.set_xlabel('Tarih', color=text_color, fontsize=11, weight='bold')
            ax.set_ylabel('Fiyat (₺)', color=text_color, fontsize=11, weight='bold')
            ax.set_title(f'{self.stock_symbol} Fiyat Grafiği', 
                        color=text_color, fontsize=14, weight='bold', pad=15)
            
            # Tarihleri eğik göster
            fig.autofmt_xdate()
            
            fig.tight_layout()
            
            # Tkinter'e yerleştir
            canvas = FigureCanvasTkAgg(fig, chart_content)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            print(f"Fiyat grafiği oluşturma hatası: {e}")
            ctk.CTkLabel(parent, text=f"Grafik oluşturulamadı: {str(e)}", 
                        text_color="gray").pack(expand=True, pady=50)
    
    def create_technical_tab(self):
        """Teknik Analiz sekmesi"""
        tab = self.tabview.tab("⚡ Teknik Analiz")
        
        if self.stock_data is None:
            ctk.CTkLabel(tab, text="Veri yüklenemedi", 
                        text_color="gray").pack(expand=True, pady=50)
            return
        
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        # RSI Grafiği
        self.create_rsi_chart(scroll)
        
        # MACD Grafiği
        self.create_macd_chart(scroll)
    
    def create_rsi_chart(self, parent):
        """RSI göstergesi grafiği"""
        try:
            if 'RSI' not in self.stock_data.columns or self.stock_data['RSI'].isna().all():
                return
            
            frame = ctk.CTkFrame(parent, corner_radius=10, fg_color=("gray90", "gray13"))
            frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(frame, text="RSI (Relative Strength Index)", 
                        font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
            
            chart_container = ctk.CTkFrame(frame, fg_color="transparent", height=250)
            chart_container.pack(fill="x", padx=15, pady=(0, 15))
            chart_container.pack_propagate(False)
            
            fig = plt.Figure(figsize=(10, 3), dpi=100)
            ax = fig.add_subplot(111)
            
            bg_color = '#2b2b2b' if self.theme == "dark" else '#f8f9fa'
            text_color = 'white' if self.theme == "dark" else 'black'
            
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
            
            dates = mdates.date2num(self.stock_data.index.to_pydatetime())
            
            # RSI çizgisi
            ax.plot(dates, self.stock_data['RSI'], color='#8b5cf6', linewidth=2)
            
            # Aşırı alım/satım seviyeleri
            ax.axhline(y=70, color='#ef4444', linestyle='--', linewidth=1, alpha=0.7, label='Aşırı Alım (70)')
            ax.axhline(y=30, color='#10b981', linestyle='--', linewidth=1, alpha=0.7, label='Aşırı Satım (30)')
            ax.axhline(y=50, color='gray', linestyle=':', linewidth=1, alpha=0.5)
            
            # Aşırı alım/satım bölgelerini vurgula
            ax.fill_between(dates, 70, 100, color='#ef4444', alpha=0.1)
            ax.fill_between(dates, 0, 30, color='#10b981', alpha=0.1)
            
            ax.set_ylim(0, 100)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper left', facecolor=bg_color, edgecolor=text_color, labelcolor=text_color, fontsize=9)
            
            ax.tick_params(colors=text_color, labelsize=9)
            for spine in ax.spines.values():
                spine.set_color(text_color)
            
            ax.set_ylabel('RSI', color=text_color, fontsize=10)
            
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            print(f"RSI grafiği hatası: {e}")
    
    def create_macd_chart(self, parent):
        """MACD göstergesi grafiği"""
        try:
            if 'MACD' not in self.stock_data.columns or self.stock_data['MACD'].isna().all():
                return
            
            frame = ctk.CTkFrame(parent, corner_radius=10, fg_color=("gray90", "gray13"))
            frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(frame, text="MACD (Moving Average Convergence Divergence)", 
                        font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
            
            chart_container = ctk.CTkFrame(frame, fg_color="transparent", height=250)
            chart_container.pack(fill="x", padx=15, pady=(0, 15))
            chart_container.pack_propagate(False)
            
            fig = plt.Figure(figsize=(10, 3), dpi=100)
            ax = fig.add_subplot(111)
            
            bg_color = '#2b2b2b' if self.theme == "dark" else '#f8f9fa'
            text_color = 'white' if self.theme == "dark" else 'black'
            
            fig.patch.set_facecolor(bg_color)
            ax.set_facecolor(bg_color)
            
            dates = mdates.date2num(self.stock_data.index.to_pydatetime())
            
            # MACD ve Signal çizgileri
            ax.plot(dates, self.stock_data['MACD'], color='#3b82f6', linewidth=2, label='MACD')
            ax.plot(dates, self.stock_data['Signal'], color='#f59e0b', linewidth=2, label='Signal')
            
            # Histogram
            colors = ['#10b981' if val >= 0 else '#ef4444' for val in self.stock_data['MACD_Hist']]
            ax.bar(dates, self.stock_data['MACD_Hist'], color=colors, alpha=0.3, width=0.7)
            
            # Sıfır çizgisi
            ax.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
            
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper left', facecolor=bg_color, edgecolor=text_color, labelcolor=text_color, fontsize=9)
            
            ax.tick_params(colors=text_color, labelsize=9)
            for spine in ax.spines.values():
                spine.set_color(text_color)
            
            ax.set_ylabel('MACD', color=text_color, fontsize=10)
            
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except Exception as e:
            print(f"MACD grafiği hatası: {e}")
    
    def create_stats_tab(self, hist):
        """İstatistikler sekmesi"""
        tab = self.tabview.tab("📑 İstatistikler")
        
        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        
        # Fiyat istatistikleri
        stats_frame = ctk.CTkFrame(scroll, corner_radius=10, fg_color=("gray90", "gray13"))
        stats_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(stats_frame, text="Fiyat İstatistikleri", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", padx=15, pady=(0, 15))
        
        for i in range(3):
            stats_grid.grid_columnconfigure(i, weight=1)
        
        # İstatistikleri hesapla
        try:
            stats = [
                ("Ortalama", f"{hist['Close'].mean():.2f} ₺"),
                ("Medyan", f"{hist['Close'].median():.2f} ₺"),
                ("Std. Sapma", f"{hist['Close'].std():.2f} ₺"),
                ("En Düşük", f"{hist['Close'].min():.2f} ₺"),
                ("En Yüksek", f"{hist['Close'].max():.2f} ₺"),
                ("Varyans", f"{hist['Close'].var():.2f}"),
            ]
            
            for i, (label, value) in enumerate(stats):
                row = i // 3
                col = i % 3
                
                frame = ctk.CTkFrame(stats_grid, fg_color="transparent")
                frame.grid(row=row, column=col, padx=5, pady=8, sticky="w")
                
                ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11), 
                            text_color=("gray50", "gray70")).pack(anchor="w")
                
                ctk.CTkLabel(frame, text=value, 
                            font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w")
        
        except Exception as e:
            print(f"İstatistik hesaplama hatası: {e}")
            ctk.CTkLabel(stats_frame, text="İstatistikler hesaplanamadı", 
                        text_color="gray").pack(pady=20)
    
    def show_error(self, message):
        """Hata mesajını göster"""
        if not self.tabview:
            return
        
        for tab_name in ["📊 Genel Bakış", "📈 Fiyat Grafiği", "⚡ Teknik Analiz", "📑 İstatistikler"]:
            try:
                tab = self.tabview.tab(tab_name)
                for widget in tab.winfo_children():
                    widget.destroy()
                
                error_frame = ctk.CTkFrame(tab, fg_color="transparent")
                error_frame.pack(expand=True)
                
                ctk.CTkLabel(error_frame, text="⚠️", font=ctk.CTkFont(size=48)).pack(pady=(50, 10))
                
                ctk.CTkLabel(error_frame, text="Hata Oluştu", 
                            font=ctk.CTkFont(size=20, weight="bold"), 
                            text_color=COLORS["danger"]).pack(pady=10)
                
                ctk.CTkLabel(error_frame, text=message, 
                            font=ctk.CTkFont(size=14), 
                            text_color="gray",
                            wraplength=500).pack()
            except:
                pass