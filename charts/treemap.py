# charts/treemap.py

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import squarify  # pip install squarify gerekli
from config import COLORS

class TreemapChart:
    def __init__(self, parent, theme='dark'):
        self.parent = parent
        self.theme = theme
    
    def create_portfolio_treemap(self, portfolio):
        """
        Portföy ağırlık dağılımı treemap
        
        portfolio: Portföy listesi
        """
        fig = Figure(figsize=(10, 6), dpi=90)
        ax = fig.add_subplot(111)
        
        # Tema
        bg_color = '#2b2b2b' if self.theme == "dark" else '#ebebeb'
        text_color = 'white' if self.theme == "dark" else 'black'
        
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        if not portfolio:
            ax.text(0.5, 0.5, 'Portföyde veri yok', 
                   ha='center', va='center', transform=ax.transAxes, 
                   fontsize=12, color='gray')
            ax.axis('off')
            fig.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, self.parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
            return canvas
        
        # Verileri hazırla
        labels = []
        sizes = []
        colors_list = []
        
        for stock in portfolio:
            value = stock['adet'] * stock.get('guncel_fiyat', stock['ort_maliyet'])
            sizes.append(value)
            
            # Performans hesapla
            current = stock.get('guncel_fiyat', stock['ort_maliyet'])
            cost = stock['ort_maliyet']
            perf = ((current - cost) / cost) * 100
            
            # Etiket oluştur
            label = f"{stock['sembol']}\n{value:,.0f}₺\n{perf:+.1f}%"
            labels.append(label)
            
            # Renk seç (performansa göre)
            if perf > 10:
                colors_list.append('#10b981')  # Koyu yeşil
            elif perf > 0:
                colors_list.append('#34d399')  # Açık yeşil
            elif perf > -10:
                colors_list.append('#fbbf24')  # Sarı
            else:
                colors_list.append('#ef4444')  # Kırmızı
        
        # Treemap çiz
        squarify.plot(sizes=sizes, label=labels, color=colors_list, 
                     alpha=0.8, text_kwargs={'fontsize': 10, 'weight': 'bold', 'color': 'white'},
                     edgecolor='white', linewidth=2, ax=ax)
        
        # Eksenleri kaldır
        ax.axis('off')
        
        # Başlık
        ax.set_title('Portföy Dağılımı (Değere Göre)', 
                    color=text_color, fontsize=14, weight='bold', pad=15)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        return canvas