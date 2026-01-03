# charts/line_chart.py

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

class LineChart:
    def __init__(self, parent, theme='dark'):
        self.parent = parent
        self.theme = theme
    
    def create_portfolio_value_chart(self, dates, values, cost_line=None, title="Portföy Değeri"):
        """
        Portföy değerinin zaman içindeki grafiği
        
        dates: Liste of datetime objects
        values: Liste of portfolio values
        cost_line: (Optional) Maliyet çizgisi değeri
        """
        fig = Figure(figsize=(10, 5), dpi=90)
        ax = fig.add_subplot(111)
        
        # Tema ayarları
        bg_color = '#2b2b2b' if self.theme == "dark" else '#ebebeb'
        text_color = 'white' if self.theme == "dark" else 'black'
        grid_color = 'gray' if self.theme == "dark" else 'lightgray'
        
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        # Ana çizgi
        ax.plot(dates, values, color='#14b8a6', linewidth=2.5, label='Güncel Değer', marker='o', markersize=4)
        
        # Maliyet çizgisi (varsa)
        if cost_line:
            ax.axhline(y=cost_line, color='#f59e0b', linestyle='--', linewidth=2, label='Toplam Maliyet', alpha=0.7)
        
        # Alan doldurma (kar/zarar bölgesi)
        if cost_line:
            ax.fill_between(dates, values, cost_line, 
                           where=(np.array(values) >= cost_line), 
                           color='#10b981', alpha=0.2, interpolate=True)
            ax.fill_between(dates, values, cost_line, 
                           where=(np.array(values) < cost_line), 
                           color='#ef4444', alpha=0.2, interpolate=True)
        
        # Eksenleri formatla
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, len(dates)//10)))
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='--', color=grid_color)
        
        # Başlık ve etiketler
        ax.set_title(title, color=text_color, fontsize=14, weight='bold', pad=15)
        ax.set_xlabel('Tarih', color=text_color, fontsize=11)
        ax.set_ylabel('Değer (₺)', color=text_color, fontsize=11)
        
        # Tick renkleri
        ax.tick_params(colors=text_color, labelsize=9)
        
        # Çerçeve renkleri
        for spine in ax.spines.values():
            spine.set_color(text_color)
            spine.set_linewidth(0.5)
        
        # Legend
        ax.legend(loc='upper left', facecolor=bg_color, edgecolor=text_color, 
                 labelcolor=text_color, fontsize=10, framealpha=0.9)
        
        # Tarihleri eğik göster
        fig.autofmt_xdate()
        
        fig.tight_layout()
        
        # Canvas oluştur
        canvas = FigureCanvasTkAgg(fig, self.parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        return canvas
    
    def create_comparison_chart(self, dates, portfolio_values, benchmark_values, 
                               portfolio_label="Portföy", benchmark_label="BIST100"):
        """
        Portföy vs Benchmark karşılaştırma grafiği
        Her iki seriyi normalize eder (başlangıç = 100)
        """
        fig = Figure(figsize=(10, 5), dpi=90)
        ax = fig.add_subplot(111)
        
        # Tema ayarları
        bg_color = '#2b2b2b' if self.theme == "dark" else '#ebebeb'
        text_color = 'white' if self.theme == "dark" else 'black'
        
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        # Normalize et (ilk değer = 100)
        if len(portfolio_values) > 0 and portfolio_values[0] != 0:
            norm_portfolio = [(v / portfolio_values[0]) * 100 for v in portfolio_values]
        else:
            norm_portfolio = [100] * len(portfolio_values)
        
        if len(benchmark_values) > 0 and benchmark_values[0] != 0:
            norm_benchmark = [(v / benchmark_values[0]) * 100 for v in benchmark_values]
        else:
            norm_benchmark = [100] * len(benchmark_values)
        
        # Çizgileri çiz
        ax.plot(dates, norm_portfolio, color='#14b8a6', linewidth=2.5, label=portfolio_label, marker='o', markersize=3)
        ax.plot(dates, norm_benchmark, color='#f59e0b', linewidth=2.5, label=benchmark_label, marker='s', markersize=3, alpha=0.8)
        
        # %100 çizgisi
        ax.axhline(y=100, color='gray', linestyle=':', linewidth=1.5, alpha=0.5)
        
        # Grid
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # Formatla
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
        ax.set_title('Portföy vs Benchmark Karşılaştırması', color=text_color, fontsize=14, weight='bold')
        ax.set_ylabel('İndeks (Başlangıç = 100)', color=text_color, fontsize=11)
        
        ax.tick_params(colors=text_color)
        for spine in ax.spines.values():
            spine.set_color(text_color)
        
        ax.legend(loc='best', facecolor=bg_color, edgecolor=text_color, labelcolor=text_color)
        
        fig.autofmt_xdate()
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        return canvas