# pages/advanced_analysis_page.py
"""
Gelişmiş Analiz Sayfası - Monte Carlo, Hedef Analizi, Vergi Optimizasyonu
"""

import customtkinter as ctk
from tkinter import ttk, messagebox
from datetime import datetime
import numpy as np
from config import COLORS, FONT_SIZES
from advanced_api_service import AdvancedAnalysisService
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from ui_utils import showinfo, showerror

class AdvancedAnalysisPage:
    def __init__(self, parent, db, theme):
        self.parent = parent
        self.db = db
        self.theme = theme
        self.current_user_id = 1
    
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
            text="🔬 Gelişmiş Portföy Analizi",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS["primary"]
        )
        title_label.pack(pady=(0, 20), anchor="w")
        
        # Sekme çerçevesi
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Monte Carlo sekmesi
        self.create_monte_carlo_tab()
        
        # Hedef Analizi sekmesi
        self.create_goal_analysis_tab()
        
        # Vergi Optimizasyonu sekmesi
        self.create_tax_optimization_tab()
    
    def create_monte_carlo_tab(self):
        """Monte Carlo Simülasyonu sekmesi"""
        frame = ctk.CTkFrame(self.notebook, fg_color="transparent")
        self.notebook.add(frame, text="🎲 Monte Carlo Simülasyonu")
        
        # Sol panel - Kontroller
        left_panel = ctk.CTkFrame(frame, fg_color=self.get_bg_color(), corner_radius=8)
        left_panel.pack(side="left", fill="both", padx=10, pady=10, expand=False, anchor="n")
        
        # Başlık
        header = ctk.CTkLabel(
            left_panel, 
            text="Simülasyon Parametreleri",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["primary"]
        )
        header.pack(anchor="w", padx=15, pady=(15, 10))
        
        label = ctk.CTkLabel(left_panel, text="Portföy Değeri (₺):", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.mc_value_entry = ctk.CTkEntry(left_panel, width=200, placeholder_text="0.00")
        self.mc_value_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Günlük getiri
        label = ctk.CTkLabel(left_panel, text="Günlük Ortalama Getiri (%):", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.mc_return_entry = ctk.CTkEntry(left_panel, width=200, placeholder_text="0.05")
        self.mc_return_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.mc_return_entry.insert(0, "0.05")
        
        # Standart sapma
        label = ctk.CTkLabel(left_panel, text="Günlük Std.Sapma (%):", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.mc_std_entry = ctk.CTkEntry(left_panel, width=200, placeholder_text="2.0")
        self.mc_std_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.mc_std_entry.insert(0, "2.0")
        
        # Gün sayısı
        label = ctk.CTkLabel(left_panel, text="Simülasyon Günü:", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.mc_days_entry = ctk.CTkEntry(left_panel, width=200, placeholder_text="252")
        self.mc_days_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.mc_days_entry.insert(0, "252")
        
        # Simulasyon sayısı
        label = ctk.CTkLabel(left_panel, text="Simülasyon Sayısı:", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.mc_sims_entry = ctk.CTkEntry(left_panel, width=200, placeholder_text="10000")
        self.mc_sims_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.mc_sims_entry.insert(0, "10000")
        
        # Hesapla butonu
        calc_btn = ctk.CTkButton(
            left_panel,
            text="🔢 Hesapla",
            command=self.run_monte_carlo,
            width=180,
            height=40,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary"]
        )
        calc_btn.pack(fill="x", padx=15, pady=15)
        
        # Sağ panel - Sonuçlar
        right_panel = ctk.CTkFrame(frame, fg_color=self.get_bg_color(), corner_radius=8)
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        results_header = ctk.CTkLabel(
            right_panel,
            text="Simülasyon Sonuçları",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["success"]
        )
        results_header.pack(anchor="w", padx=15, pady=(15, 10))
        
        self.mc_results_label = ctk.CTkLabel(
            right_panel,
            text="Monte Carlo simülasyonu çalıştırılmamış.\n\nParametreleri girin ve 'Hesapla' butonuna basın.",
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray40")
        )
        self.mc_results_label.pack(fill="both", expand=True, padx=15, pady=15, anchor="nw")
    
    def create_goal_analysis_tab(self):
        """Hedef Analizi sekmesi"""
        frame = ctk.CTkFrame(self.notebook, fg_color="transparent")
        self.notebook.add(frame, text="🎯 Hedef Yönelik Analiz")
        
        # Sol panel
        left_panel = ctk.CTkFrame(frame, fg_color=self.get_bg_color(), corner_radius=8)
        left_panel.pack(side="left", fill="both", padx=10, pady=10, expand=False, anchor="n")
        
        # Başlık
        header = ctk.CTkLabel(
            left_panel,
            text="Hedef Parametreleri",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["primary"]
        )
        header.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Başlangıç değeri
        label = ctk.CTkLabel(left_panel, text="Başlangıç Portföy Değeri (₺):", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.goal_value_entry = ctk.CTkEntry(left_panel, width=200, placeholder_text="0.00")
        self.goal_value_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Aylık yatırım
        label = ctk.CTkLabel(left_panel, text="Aylık Yatırım (₺):", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.goal_monthly_entry = ctk.CTkEntry(left_panel, width=200, placeholder_text="5000")
        self.goal_monthly_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.goal_monthly_entry.insert(0, "5000")
        
        # Yıllık getiri
        label = ctk.CTkLabel(left_panel, text="Yıllık Beklenen Getiri (%):", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.goal_return_entry = ctk.CTkEntry(left_panel, width=200, placeholder_text="12")
        self.goal_return_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.goal_return_entry.insert(0, "12")
        
        # Yıl sayısı
        label = ctk.CTkLabel(left_panel, text="Projeksiyon Yılı:", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.goal_years_entry = ctk.CTkEntry(left_panel, width=200, placeholder_text="10")
        self.goal_years_entry.pack(fill="x", padx=15, pady=(0, 15))
        self.goal_years_entry.insert(0, "10")
        
        # Hesapla butonu
        calc_btn = ctk.CTkButton(
            left_panel,
            text="📈 Hesapla",
            command=self.run_goal_analysis,
            width=180,
            height=40,
            fg_color=COLORS["primary"],
            hover_color=COLORS["primary"]
        )
        calc_btn.pack(fill="x", padx=15, pady=15)
        
        # Sağ panel - Sonuçlar
        right_panel = ctk.CTkFrame(frame, fg_color=self.get_bg_color(), corner_radius=8)
        right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Başlık
        results_header = ctk.CTkLabel(
            right_panel,
            text="Projeksiyon Sonuçları",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["success"]
        )
        results_header.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Sonuçlar tabelosu
        columns = ("Yıl", "Portföy Değeri", "Toplam Yatırım", "Kazanç")
        
        # Tema rengine göre treeview stilini ayarla
        style = ttk.Style()
        if self.theme == "light":
            style.theme_use('clam')
            style.configure("Treeview", background="white", foreground="black", fieldbackground="white")
            style.configure("Treeview.Heading", background="lightgray", foreground="black")
        else:
            style.configure("Treeview", background="gray20", foreground="white", fieldbackground="gray20")
            style.configure("Treeview.Heading", background="gray30", foreground="white")
        
        self.goal_tree = ttk.Treeview(right_panel, columns=columns, height=20, show="headings")
        
        for col in columns:
            self.goal_tree.heading(col, text=col)
            self.goal_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(right_panel, orient="vertical", command=self.goal_tree.yview)
        self.goal_tree.configure(yscroll=scrollbar.set)
        
        self.goal_tree.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        scrollbar.pack(side="right", fill="y", padx=(0, 15), pady=15)
    
    def create_tax_optimization_tab(self):
        """Vergi Optimizasyonu sekmesi"""
        frame = ctk.CTkFrame(self.notebook, fg_color="transparent")
        self.notebook.add(frame, text="💰 Vergi Optimizasyonu")
        
        # İçerik scroll frame
        scroll_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Form container
        form_frame = ctk.CTkFrame(scroll_frame, fg_color=self.get_bg_color(), corner_radius=8)
        form_frame.pack(fill="x", padx=0, pady=0)
        
        # Başlık
        header = ctk.CTkLabel(
            form_frame,
            text="Vergi Analiz Parametreleri",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["primary"]
        )
        header.pack(anchor="w", padx=15, pady=(15, 10))
        
        # Gerçekleşmiş kazançlar
        label = ctk.CTkLabel(form_frame, text="Gerçekleşmiş Kazançlar (₺):", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.tax_realized_entry = ctk.CTkEntry(form_frame, placeholder_text="0.00")
        self.tax_realized_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Gerçekleşmemiş kazançlar
        label = ctk.CTkLabel(form_frame, text="Gerçekleşmemiş Kazançlar (₺):", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.tax_unrealized_entry = ctk.CTkEntry(form_frame, placeholder_text="0.00")
        self.tax_unrealized_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # İşlem maliyetleri
        label = ctk.CTkLabel(form_frame, text="İşlem Maliyetleri (₺):", font=ctk.CTkFont(size=11))
        label.pack(anchor="w", padx=15, pady=(0, 5))
        
        self.tax_costs_entry = ctk.CTkEntry(form_frame, placeholder_text="0.00")
        self.tax_costs_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Hesapla butonu
        calc_btn = ctk.CTkButton(
            form_frame,
            text="🧮 Optimize Et",
            command=self.run_tax_optimization,
            height=40,
            fg_color=COLORS["warning"],
            hover_color=COLORS["warning"]
        )
        calc_btn.pack(fill="x", padx=15, pady=15)
        
        # Sonuçlar frame
        self.tax_results_frame = ctk.CTkFrame(scroll_frame, fg_color=self.get_bg_color(), corner_radius=8)
        self.tax_results_frame.pack(fill="both", expand=True, padx=0, pady=(10, 0))
        
        # Sonuçlar başlığı
        results_header = ctk.CTkLabel(
            self.tax_results_frame,
            text="Optimizasyon Sonuçları",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["success"]
        )
        results_header.pack(anchor="w", padx=15, pady=(15, 10))
        
        self.tax_results_label = ctk.CTkLabel(
            self.tax_results_frame,
            text="Vergi optimizasyonu sonuçları burada gösterilecek.\n\nParametreleri girin ve 'Optimize Et' butonuna basın.",
            justify="left",
            font=ctk.CTkFont(size=11),
            text_color=("gray60", "gray40")
        )
        self.tax_results_label.pack(fill="both", expand=True, padx=15, pady=15, anchor="nw")
    
    def run_monte_carlo(self):
        """Monte Carlo simülasyonu çalıştır"""
        try:
            current_value = float(self.mc_value_entry.get())
            daily_return = float(self.mc_return_entry.get())
            std_dev = float(self.mc_std_entry.get())
            days = int(self.mc_days_entry.get())
            simulations = int(self.mc_sims_entry.get())
            
            # Simülasyon çalıştır
            result = AdvancedAnalysisService.monte_carlo_simulation(
                current_value,
                daily_return,
                std_dev,
                days,
                simulations
            )
            
            if result:
                text = f"""
Monte Carlo Simülasyonu Sonuçları
═════════════════════════════════════

Başlangıç Değeri: {result['baslanc_degeri']:,.2f}₺
Simülasyon Dönemi: {result['gün']} gün

Ortalama Son Değer: {result['ortalama_bitis']:,.2f}₺
Medyan Son Değer: {result['medyan_bitis']:,.2f}₺
Standart Sapma: {result['std_sapma']:,.2f}₺

En Kötü Senaryo: {result['min_degeri']:,.2f}₺
En İyi Senaryo: {result['max_degeri']:,.2f}₺

Güven Aralıkları:
  5. Persentil: {result['percentil_5']:,.2f}₺
  25. Persentil: {result['percentil_25']:,.2f}₺
  75. Persentil: {result['percentil_75']:,.2f}₺
  95. Persentil: {result['percentil_95']:,.2f}₺

Toplam Simülasyon: {result['simulasyon_sayisi']:,}
                """
                
                self.mc_results_label.configure(text=text)
        
        except ValueError:
            showerror("Hata", "Lütfen geçerli sayı değerleri girin")
        except Exception as e:
            showerror("Hata", str(e))
    
    def run_goal_analysis(self):
        """Hedef analizi çalıştır"""
        try:
            current_value = float(self.goal_value_entry.get())
            monthly_investment = float(self.goal_monthly_entry.get())
            annual_return = float(self.goal_return_entry.get())
            years = int(self.goal_years_entry.get())
            
            # Analiz çalıştır
            projections = AdvancedAnalysisService.goal_projection(
                current_value,
                monthly_investment,
                annual_return,
                years
            )
            
            if projections:
                # Tabloyu temizle
                for item in self.goal_tree.get_children():
                    self.goal_tree.delete(item)
                
                # Verileri ekle
                for proj in projections:
                    values = (
                        proj['yil'],
                        f"{proj['portfoy_degeri']:,.2f}₺",
                        f"{proj['toplam_yatirim']:,.2f}₺",
                        f"{proj['kazanc']:,.2f}₺"
                    )
                    self.goal_tree.insert("", "end", values=values)
        
        except ValueError:
            showerror("Hata", "Lütfen geçerli sayı değerleri girin")
        except Exception as e:
            showerror("Hata", str(e))
    
    def run_tax_optimization(self):
        """Vergi optimizasyonu çalıştır"""
        try:
            realized_gains = float(self.tax_realized_entry.get())
            unrealized_gains = float(self.tax_unrealized_entry.get())
            transaction_costs = float(self.tax_costs_entry.get())
            
            # Optimizasyon çalıştır
            result = AdvancedAnalysisService.tax_optimization(
                realized_gains,
                unrealized_gains,
                transaction_costs
            )
            
            if result:
                text = f"""
Vergi Optimizasyonu Analizi
═════════════════════════════════════

Toplam Kazanç: {result['toplam_kazanc']:,.2f}₺
Vergi Muaf Tutar: {result['vergi_muaf_tutar']:,.2f}₺
Vergilendirilebilir Kazanç: {result['vergilendirilebilir_kazanc']:,.2f}₺

Önerilen Senaryolar:
───────────────────────────────────────
"""
                
                for rec in result['oneriler']:
                    text += f"""
{rec['senaryo']}
  Açıklama: {rec['aciklama']}
  Vergi Yükü: {rec['vergi_yuku']:,.2f}₺"""
                    
                    if 'vergi_tasarrufu' in rec:
                        text += f"\n  Vergi Tasarrufu: {rec['vergi_tasarrufu']:,.2f}₺"
                    
                    text += "\n"
                
                self.tax_results_label.configure(text=text)
        
        except ValueError:
            showerror("Hata", "Lütfen geçerli sayı değerleri girin")
        except Exception as e:
            showerror("Hata", str(e))
