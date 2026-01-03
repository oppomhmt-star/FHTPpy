# charts/bar_chart.py

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS

class BarChart:
    def __init__(self, parent, theme='dark'):
        self.parent = parent
        self.theme = theme
    
    def create_horizontal_bar(self, labels, values, title="", value_label="", sort_descending=True):
        """
        Yatay bar grafik (Kar/Zarar için ideal)
        
        labels: Liste of stock symbols
        values: Liste of kar/zarar values
        """
        fig = Figure(figsize=(6, max(4, len(labels) * 0.4)), dpi=90)
        ax = fig.add_subplot(111)
        
        # Tema
        bg_color = '#2b2b2b' if self.theme == "dark" else '#ebebeb'
        text_color = 'white' if self.theme == "dark" else 'black'
        
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        # Sırala
        if sort_descending:
            sorted_data = sorted(zip(labels, values), key=lambda x: x[1], reverse=True)
            labels, values = zip(*sorted_data) if sorted_data else ([], [])
        
        # Renkler (pozitif=yeşil, negatif=kırmızı)
        colors = [COLORS["success"] if v >= 0 else COLORS["danger"] for v in values]
        
        # Bar'ları çiz
        bars = ax.barh(labels, values, color=colors, height=0.6, edgecolor='none')
        
        # Değerleri bar üzerine yaz
        for i, (bar, value) in enumerate(zip(bars, values)):
            width = bar.get_width()
            label_x_pos = width + (max(values) * 0.02 if width > 0 else min(values) * 0.02)
            
            ax.text(label_x_pos, bar.get_y() + bar.get_height()/2, 
                   f'{value:,.0f}₺',
                   ha='left' if value > 0 else 'right', 
                   va='center',
                   fontsize=9, 
                   weight='bold',
                   color=COLORS["success"] if value >= 0 else COLORS["danger"])
        
        # Sıfır çizgisi
        ax.axvline(x=0, color='gray', linestyle='-', linewidth=1.5, alpha=0.7)
        
        # Grid
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        # Başlık
        ax.set_title(title, color=text_color, fontsize=14, weight='bold', pad=15)
        ax.set_xlabel(value_label, color=text_color, fontsize=11)
        
        # Tick renkleri
        ax.tick_params(colors=text_color, labelsize=10)
        
        # Çerçeve
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['bottom', 'left']:
            ax.spines[spine].set_color(text_color)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        return canvas
    
    def create_grouped_bar(self, categories, series_data, series_labels, title=""):
        """
        Gruplu bar grafik
        
        categories: Liste of category names (örn: sektörler)
        series_data: Dict of {series_name: values_list}
        """
        import numpy as np
        
        fig = Figure(figsize=(10, 5), dpi=90)
        ax = fig.add_subplot(111)
        
        bg_color = '#2b2b2b' if self.theme == "dark" else '#ebebeb'
        text_color = 'white' if self.theme == "dark" else 'black'
        
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        x = np.arange(len(categories))
        width = 0.8 / len(series_data)
        
        color_list = [COLORS["primary"], COLORS["success"], COLORS["warning"], COLORS["purple"]]
        
        for i, (label, values) in enumerate(series_data.items()):
            offset = (i - len(series_data)/2) * width + width/2
            ax.bar(x + offset, values, width, label=label, color=color_list[i % len(color_list)])
        
        ax.set_xticks(x)
        ax.set_xticklabels(categories, rotation=45, ha='right')
        ax.set_title(title, color=text_color, fontsize=14, weight='bold')
        ax.legend(facecolor=bg_color, edgecolor=text_color, labelcolor=text_color)
        ax.grid(axis='y', alpha=0.3)
        
        ax.tick_params(colors=text_color)
        for spine in ax.spines.values():
            spine.set_color(text_color)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        
        return canvas