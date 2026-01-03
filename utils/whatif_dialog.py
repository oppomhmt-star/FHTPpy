# utils/whatif_dialog.py

import customtkinter as ctk
from config import COLORS
import copy
from datetime import datetime
import threading

class WhatIfDialog:
    def __init__(self, parent, db, api, current_portfolio, on_complete=None):
        self.parent = parent
        self.db = db
        self.api = api
        self.current_portfolio = copy.deepcopy(current_portfolio) 
        self.on_complete = on_complete
        
        # Simülasyon sonuçları
        self.original_value = sum(s["adet"] * s.get("guncel_fiyat", s["ort_maliyet"]) for s in current_portfolio)
        self.simulated_portfolio = None
        self.simulated_value = 0
        self.difference = 0
        self.percentage = 0
        
    def show(self):
        """Simülasyon penceresini göster"""
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("💭 What-If Analizi")
        self.dialog.geometry("700x600")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Ana içerik bölümü
        self.main_frame = ctk.CTkScrollableFrame(self.dialog)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        self._create_header()
        self._create_scenario_builder()
        self._create_result_section()
        
        # Alt butonlar
        self.button_frame = ctk.CTkFrame(self.dialog, fg_color="transparent")
        self.button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkButton(self.button_frame, text="🧮 Simülasyon Yap", command=self._run_simulation,
                      height=40, font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color=COLORS["primary"]).pack(side="left", expand=True, fill="x", padx=5)
                      
        ctk.CTkButton(self.button_frame, text="❌ Kapat", command=self.dialog.destroy,
                      height=40, font=ctk.CTkFont(size=14),
                      fg_color=("gray60", "gray40")).pack(side="left", expand=True, fill="x", padx=5)
        
    def _create_header(self):
        """Başlık ve açıklama bölümü"""
        header = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="💭 Ya Şöyle Yapsaydım?", 
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        
        ctk.CTkLabel(header, text="Bu araç ile farklı portföy senaryolarını test edebilirsiniz.",
                    font=ctk.CTkFont(size=14), text_color=("gray40", "gray70")).pack(anchor="w", pady=(5, 0))
        
        # Mevcut portföy değeri
        value_frame = ctk.CTkFrame(self.main_frame, fg_color=("gray85", "gray17"), corner_radius=10)
        value_frame.pack(fill="x", pady=(0, 20))
        
        content = ctk.CTkFrame(value_frame, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(content, text="Mevcut Portföy Değeri:", 
                    font=ctk.CTkFont(size=14)).pack(side="left")
                    
        ctk.CTkLabel(content, text=f"{self.original_value:,.2f} ₺", 
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=COLORS["success"]).pack(side="right")
    
    def _create_scenario_builder(self):
        """Senaryo oluşturma bölümü"""
        scenario_frame = ctk.CTkFrame(self.main_frame, corner_radius=10)
        scenario_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(scenario_frame, text="Senaryo Oluştur", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Senaryo tipleri
        options_frame = ctk.CTkFrame(scenario_frame, fg_color="transparent")
        options_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Hisse ekleme seçeneği
        add_frame = ctk.CTkFrame(options_frame, fg_color=("gray80", "gray20"), corner_radius=6)
        add_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(add_frame, text="Yeni Hisse Ekle:", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Sembol, adet, fiyat
        form_frame = ctk.CTkFrame(add_frame, fg_color="transparent")
        form_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # Grid yapısı
        form_frame.grid_columnconfigure(0, weight=2)  # Sembol
        form_frame.grid_columnconfigure(1, weight=1)  # Adet
        form_frame.grid_columnconfigure(2, weight=1)  # Fiyat
        
        # Etiketler
        ctk.CTkLabel(form_frame, text="Sembol", font=ctk.CTkFont(size=12), 
                    anchor="w").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(form_frame, text="Adet", font=ctk.CTkFont(size=12), 
                    anchor="w").grid(row=0, column=1, sticky="w", padx=5, pady=2)
        ctk.CTkLabel(form_frame, text="Fiyat (₺)", font=ctk.CTkFont(size=12), 
                    anchor="w").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        
        # Giriş alanları
        self.new_symbol_entry = ctk.CTkEntry(form_frame, placeholder_text="ör: THYAO")
        self.new_symbol_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=2)
        
        self.new_amount_entry = ctk.CTkEntry(form_frame, placeholder_text="ör: 100")
        self.new_amount_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
        
        self.new_price_entry = ctk.CTkEntry(form_frame, placeholder_text="ör: 25.50")
        self.new_price_entry.grid(row=1, column=2, sticky="ew", padx=5, pady=2)
        
        ctk.CTkButton(form_frame, text="Ekle", command=self._add_to_simulation,
                     width=80, height=24, fg_color=COLORS["success"]).grid(row=1, column=3, padx=5, pady=2)
        
        # Mevcut hisseleri değiştirme
        modify_frame = ctk.CTkFrame(options_frame, fg_color=("gray80", "gray20"), corner_radius=6)
        modify_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(modify_frame, text="Mevcut Hisseyi Değiştir:", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w", padx=15, pady=(10, 5))
        
        # Hisse listesi
        list_frame = ctk.CTkFrame(modify_frame, fg_color="transparent")
        list_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        if not self.current_portfolio:
            ctk.CTkLabel(list_frame, text="Portföyde hisse yok", text_color="gray").pack(pady=10)
        else:
            for i, stock in enumerate(self.current_portfolio):
                stock_frame = ctk.CTkFrame(list_frame, fg_color=("gray70", "gray25"), corner_radius=4)
                stock_frame.pack(fill="x", pady=3)
                
                # İçerik
                content = ctk.CTkFrame(stock_frame, fg_color="transparent")
                content.pack(fill="x", padx=10, pady=8)
                
                # Sembol ve bilgi
                ctk.CTkLabel(content, text=stock['sembol'], 
                            font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
                
                ctk.CTkLabel(content, text=f"{stock['adet']} adet", 
                            font=ctk.CTkFont(size=12), 
                            text_color=("gray40", "gray60")).pack(side="left", padx=10)
                
                value = stock['adet'] * stock.get('guncel_fiyat', stock['ort_maliyet'])
                ctk.CTkLabel(content, text=f"{value:,.0f} ₺", 
                            font=ctk.CTkFont(size=12, weight="bold")).pack(side="right")
                
                # İşlem butonları
                btn_frame = ctk.CTkFrame(content, fg_color="transparent")
                btn_frame.pack(side="right", padx=(0, 10))
                
                ctk.CTkButton(btn_frame, text="-", width=30, height=24,
                              fg_color=COLORS["warning"], command=lambda s=stock: self._decrease_stock(s)).pack(side="left", padx=2)
                              
                ctk.CTkButton(btn_frame, text="+", width=30, height=24,
                              fg_color=COLORS["success"], command=lambda s=stock: self._increase_stock(s)).pack(side="left", padx=2)
                              
                ctk.CTkButton(btn_frame, text="×", width=30, height=24,
                              fg_color=COLORS["danger"], command=lambda s=stock: self._remove_stock(s)).pack(side="left", padx=2)
    
    def _create_result_section(self):
        """Sonuç bölümü"""
        result_frame = ctk.CTkFrame(self.main_frame, corner_radius=10,
                                   fg_color=("gray85", "gray17"))
        result_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(result_frame, text="Simülasyon Sonucu", 
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Sonuç içeriği
        self.result_content = ctk.CTkFrame(result_frame, fg_color="transparent")
        self.result_content.pack(fill="x", padx=15, pady=(0, 15))
        
        # Başlangıçta sonuç yok
        ctk.CTkLabel(self.result_content, text="Henüz simülasyon yapılmadı", 
                    text_color="gray").pack(pady=20)
    
    def _add_to_simulation(self):
        """Yeni hisse ekle"""
        try:
            symbol = self.new_symbol_entry.get().strip().upper()
            amount = int(self.new_amount_entry.get().strip())
            price = float(self.new_price_entry.get().strip().replace(',', '.'))
            
            if not symbol or amount <= 0 or price <= 0:
                self._show_error("Lütfen geçerli değerler girin.")
                return
            
            # Mevcut portföyde var mı kontrol et
            for stock in self.current_portfolio:
                if stock['sembol'] == symbol:
                    stock['adet'] += amount
                    self._show_info(f"{symbol}: {amount} adet eklendi.")
                    self._create_scenario_builder()  # Listeyi yenile
                    return
            
            # Yeni hisse ekle
            self.current_portfolio.append({
                'sembol': symbol,
                'adet': amount,
                'ort_maliyet': price,
                'guncel_fiyat': price
            })
            
            self._show_info(f"{symbol}: {amount} adet eklendi.")
            self._create_scenario_builder()  # Listeyi yenile
            
            # Giriş alanlarını temizle
            self.new_symbol_entry.delete(0, 'end')
            self.new_amount_entry.delete(0, 'end')
            self.new_price_entry.delete(0, 'end')
            
        except (ValueError, TypeError):
            self._show_error("Lütfen geçerli değerler girin.")
    
    def _increase_stock(self, stock):
        """Hisse adedini arttır"""
        # Burada değeri %10 arttıralım (veya 10 adet, hangisi büyükse)
        increase = max(int(stock['adet'] * 0.1), 10)
        stock['adet'] += increase
        self._show_info(f"{stock['sembol']}: {increase} adet eklendi.")
        self._create_scenario_builder()  # Listeyi yenile
    
    def _decrease_stock(self, stock):
        """Hisse adedini azalt"""
        # Değeri %10 azaltalım (veya 10 adet, hangisi küçükse)
        decrease = min(max(int(stock['adet'] * 0.1), 1), stock['adet'])
        stock['adet'] -= decrease
        
        # Eğer 0'a düştüyse sil
        if stock['adet'] <= 0:
            self.current_portfolio.remove(stock)
        
        self._show_info(f"{stock['sembol']}: {decrease} adet çıkarıldı.")
        self._create_scenario_builder()  # Listeyi yenile
    
    def _remove_stock(self, stock):
        """Hisseyi tamamen çıkar"""
        self.current_portfolio.remove(stock)
        self._show_info(f"{stock['sembol']}: Portföyden çıkarıldı.")
        self._create_scenario_builder()  # Listeyi yenile
    
    def _run_simulation(self):
        """Simülasyonu başlat"""
        # Sonuç bölümünü temizle
        for widget in self.result_content.winfo_children():
            widget.destroy()
        
        # Yükleniyor mesajı
        loading = ctk.CTkLabel(self.result_content, text="⏳ Simülasyon çalışıyor...",
                              font=ctk.CTkFont(size=14))
        loading.pack(pady=20)
        
        # Simülasyon thread ile çalıştır
        threading.Thread(target=self._calculate_simulation, daemon=True).start()
    
    def _calculate_simulation(self):
        """Simülasyon hesaplamalarını yap (ayrı thread'de çalışır)"""
        try:
            # Güncel fiyatları kontrol et/güncelle
            for stock in self.current_portfolio:
                if not stock.get('guncel_fiyat'):
                    # API'den fiyat çek
                    try:
                        price = self.api.get_stock_price(f"{stock['sembol']}.IS")
                        if price:
                            stock['guncel_fiyat'] = price
                        else:
                            stock['guncel_fiyat'] = stock['ort_maliyet']
                    except:
                        stock['guncel_fiyat'] = stock['ort_maliyet']
            
            # Simüle edilmiş portföy değerini hesapla
            self.simulated_value = sum(s['adet'] * s.get('guncel_fiyat', s['ort_maliyet']) for s in self.current_portfolio)
            self.difference = self.simulated_value - self.original_value
            
            if self.original_value > 0:
                self.percentage = (self.difference / self.original_value) * 100
            else:
                self.percentage = 0
            
            # UI güncellemesi için ana thread'e dön
            self.dialog.after(0, self._show_simulation_results)
            
        except Exception as e:
            print(f"Simülasyon hatası: {e}")
            self.dialog.after(0, lambda: self._show_error(f"Simülasyon hesaplanırken hata: {e}"))
    
    def _show_simulation_results(self):
        """Simülasyon sonuçlarını göster"""
        # Sonuç bölümünü temizle
        for widget in self.result_content.winfo_children():
            widget.destroy()
        
        # Sonuç başlığı
        result_label = ctk.CTkLabel(self.result_content, text="📊 Simülasyon Sonuçları",
                                  font=ctk.CTkFont(size=16, weight="bold"))
        result_label.pack(anchor="w", pady=(10, 20))
        
        # Değer karşılaştırma tablosu
        table = ctk.CTkFrame(self.result_content, fg_color="transparent")
        table.pack(fill="x")
        
        # Başlık satırı
        header = ctk.CTkFrame(table, fg_color=("gray75", "gray25"), corner_radius=4)
        header.pack(fill="x", pady=(0, 2))
        
        ctk.CTkLabel(header, text="Portföy", width=100, font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(header, text="Değer (₺)", width=100, font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(header, text="Fark (₺)", width=100, font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(header, text="Değişim (%)", width=100, font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", padx=10, pady=5)
        
        # Mevcut portföy satırı
        current_row = ctk.CTkFrame(table, fg_color=("gray85", "gray20"), corner_radius=4)
        current_row.pack(fill="x", pady=1)
        
        ctk.CTkLabel(current_row, text="Mevcut", width=100).pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(current_row, text=f"{self.original_value:,.0f} ₺", width=100, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(current_row, text="-", width=100).pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(current_row, text="-", width=100).pack(side="left", padx=10, pady=5)
        
        # Simüle edilmiş portföy satırı
        simulated_row = ctk.CTkFrame(table, fg_color=("gray85", "gray20"), corner_radius=4)
        simulated_row.pack(fill="x", pady=1)
        
        # Fark için renk
        color = COLORS["success"] if self.difference >= 0 else COLORS["danger"]
        icon = "📈" if self.difference >= 0 else "📉"
        
        ctk.CTkLabel(simulated_row, text="Simüle Edilmiş", width=100).pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(simulated_row, text=f"{self.simulated_value:,.0f} ₺", width=100, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(simulated_row, text=f"{self.difference:+,.0f} ₺", width=100, 
                    text_color=color, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
        ctk.CTkLabel(simulated_row, text=f"{self.percentage:+.2f}%", width=100,
                    text_color=color, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
        
        # Sonuç özeti
        summary = ctk.CTkFrame(self.result_content, fg_color=("gray85", "gray20"), corner_radius=10)
        summary.pack(fill="x", pady=(20, 10))
        
        summary_content = ctk.CTkFrame(summary, fg_color="transparent")
        summary_content.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(summary_content, text=f"{icon} Sonuç: ", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left")
        
        if self.difference > 0:
            msg = f"Bu senaryo portföyünüzün {self.difference:,.0f} ₺ ({self.percentage:+.2f}%) daha değerli olmasını sağlıyor!"
        elif self.difference < 0:
            msg = f"Bu senaryo portföyünüzün {abs(self.difference):,.0f} ₺ ({self.percentage:.2f}%) daha az değerli olmasına neden oluyor."
        else:
            msg = "Bu senaryo portföyünüzde değer değişikliğine neden olmuyor."
        
        ctk.CTkLabel(summary_content, text=msg, font=ctk.CTkFont(size=14), 
                    wraplength=400).pack(side="left", padx=5)
    
    def _show_info(self, message):
        """Bilgi mesajı göster"""
        info_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS["primary"], corner_radius=10)
        info_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(info_frame, text=message, text_color="white", 
                    font=ctk.CTkFont(size=12)).pack(pady=8)
        
        # 3 saniye sonra kaybol
        self.main_frame.after(3000, info_frame.destroy)
    
    def _show_error(self, message):
        """Hata mesajı göster"""
        error_frame = ctk.CTkFrame(self.main_frame, fg_color=COLORS["danger"], corner_radius=10)
        error_frame.pack(fill="x", pady=5)
        
        ctk.CTkLabel(error_frame, text=message, text_color="white",
                    font=ctk.CTkFont(size=12)).pack(pady=8)
        
        # 3 saniye sonra kaybol
        self.main_frame.after(3000, error_frame.destroy)