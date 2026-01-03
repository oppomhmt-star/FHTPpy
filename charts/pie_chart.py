# charts/pie_chart.py

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from config import COLORS

class PieChart:
    def __init__(self, parent, data, labels, title, theme='dark'):
        self.parent = parent
        self.data = data
        self.labels = labels
        self.title = title
        self.theme = theme

    def create_chart(self):
        fig = Figure(figsize=(5, 4), dpi=90)
        ax = fig.add_subplot(111)
        
        # Grafik arkaplanını ve metin rengini ayarla
        bg_color = '#2b2b2b' if self.theme == "dark" else '#ebebeb'
        text_color = 'white' if self.theme == "dark" else 'black'
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        if self.data and sum(self.data) > 0:
            # Renkleri config dosyasından al
            chart_colors = list(COLORS.values())
            
            wedges, texts, autotexts = ax.pie(
                self.data, 
                labels=self.labels, 
                autopct='%1.1f%%',
                colors=chart_colors,
                startangle=90, 
                pctdistance=0.85,
                textprops={'color': text_color, 'fontsize': 9, 'weight': 'bold'}
            )
            # Yüzde dilimlerinin içindeki yazıyı her zaman beyaz yap
            for autotext in autotexts:
                autotext.set_color('white')
            ax.axis('equal')
        else:
            ax.text(0.5, 0.5, 'Grafik için veri yok', ha='center', va='center',
                   transform=ax.transAxes, fontsize=11, color='gray')
            ax.axis('off')

        ax.set_title(self.title, color=text_color, fontsize=14, weight='bold')
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=5, pady=5)
        return canvas