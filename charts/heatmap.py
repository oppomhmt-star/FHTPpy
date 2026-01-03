# charts/heatmap.py

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

class HeatmapChart:
    def __init__(self, parent, theme='dark'):
        self.parent = parent
        self.theme = theme
    
    def create_correlation_matrix(self, portfolio, period_days=90):
        """
        Hisseler arası korelasyon matrisi
        
        portfolio: Portföy listesi
        period_days: Kaç günlük veri kullanılacak
        """
        fig = Figure(figsize=(8, 7), dpi=90)
        ax = fig.add_subplot(111)
        
        # Tema
        bg_color = '#2b2b2b' if self.theme == "dark" else '#ebebeb'
        text_color = 'white' if self.theme == "dark" else 'black'
        
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        # Portföydeki hisselerin sembollerini al
        symbols = [stock['sembol'] for stock in portfolio]
        
        if len(symbols) < 2:
            ax.text(0.5, 0.5, 'Korelasyon için en az 2 hisse gerekli', 
                   ha='center', va='center', transform=ax.transAxes, 
                   fontsize=12, color='gray')
            ax.axis('off')
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, self.parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            return canvas
        
        # Fiyat verilerini çek
        price_data = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(f"{symbol}.IS")
                hist = ticker.history(start=start_date, end=end_date)
                
                if not hist.empty:
                    price_data[symbol] = hist['Close']
            except Exception as e:
                print(f"Korelasyon verisi alınamadı ({symbol}): {e}")
        
        if len(price_data) < 2:
            ax.text(0.5, 0.5, 'Yeterli veri alınamadı', 
                   ha='center', va='center', transform=ax.transAxes, 
                   fontsize=12, color='gray')
            ax.axis('off')
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, self.parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            return canvas
        
        # DataFrame oluştur
        df = pd.DataFrame(price_data)
        
        # Günlük getiri hesapla
        returns = df.pct_change(fill_method=None).dropna()
        
        # Korelasyon matrisini hesapla
        correlation_matrix = returns.corr()
        
        # Heatmap çiz
        im = ax.imshow(correlation_matrix, cmap='RdYlGn', aspect='auto', 
                      vmin=-1, vmax=1, interpolation='nearest')
        
        # Colorbar ekle
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Korelasyon', color=text_color, fontsize=10)
        cbar.ax.tick_params(colors=text_color, labelsize=9)
        
        # Eksen etiketleri
        ax.set_xticks(np.arange(len(symbols)))
        ax.set_yticks(np.arange(len(symbols)))
        ax.set_xticklabels(symbols, fontsize=10)
        ax.set_yticklabels(symbols, fontsize=10)
        
        # X etiketlerini üstte göster
        ax.xaxis.tick_top()
        ax.xaxis.set_label_position('top')
        
        # Etiketleri döndür
        plt.setp(ax.get_xticklabels(), rotation=45, ha="left", rotation_mode="anchor")
        
        # Değerleri hücrelere yaz
        for i in range(len(symbols)):
            for j in range(len(symbols)):
                value = correlation_matrix.iloc[i, j]
                
                # Renk kontrastı için metin rengini ayarla
                text_col = 'white' if abs(value) > 0.5 else 'black'
                
                ax.text(j, i, f'{value:.2f}',
                       ha="center", va="center", 
                       color=text_col, fontsize=9, weight='bold')
        
        # Başlık
        ax.set_title('Hisseler Arası Korelasyon Matrisi\n(Son 90 Gün)', 
                    color=text_color, fontsize=13, weight='bold', pad=20)
        
        # Tick renkleri
        ax.tick_params(colors=text_color, labelsize=10)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        return canvas