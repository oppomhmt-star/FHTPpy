# utils/export_utils.py

import json
from datetime import datetime
import os
from tkinter import filedialog
from ui_utils import showinfo, showerror

def export_to_txt(data, title="Rapor", show_dialog=True):
    """Basit metin dosyasına dışa aktar"""
    if show_dialog:
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text", "*.txt")],
            title="Raporu Kaydet"
        )
        if not filename:
            return False
    else:
        # Otomatik dosya adı oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title.lower().replace(' ', '_')}_{timestamp}.txt"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 50 + "\n")
            f.write(f"{title.upper()}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Oluşturulma Tarihi: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
            
            if isinstance(data, str):
                f.write(data)
            elif isinstance(data, dict):
                for key, value in data.items():
                    f.write(f"{key}: {value}\n")
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        f.write("\n".join([f"{k}: {v}" for k, v in item.items()]))
                        f.write("\n" + "-" * 30 + "\n")
                    else:
                        f.write(f"{item}\n")
        
        if show_dialog:
            showinfo("Başarılı", f"Rapor kaydedildi:\n{filename}")
        return True
    
    except Exception as e:
        if show_dialog:
            showerror("Hata", f"Rapor kaydedilemedi:\n{str(e)}")
        return False

def export_to_json(data, title="Rapor", show_dialog=True):
    """JSON formatında dışa aktar"""
    if show_dialog:
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            title="JSON Olarak Kaydet"
        )
        if not filename:
            return False
    else:
        # Otomatik dosya adı oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title.lower().replace(' ', '_')}_{timestamp}.json"
    
    try:
        # Metadata ekle
        export_data = {
            "metadata": {
                "title": title,
                "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "version": "1.0"
            },
            "data": data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=4)
        
        if show_dialog:
            showinfo("Başarılı", f"JSON dosyası kaydedildi:\n{filename}")
        return True
    
    except Exception as e:
        if show_dialog:
            showerror("Hata", f"JSON dosyası kaydedilemedi:\n{str(e)}")
        return False

def export_to_html(data, title="Rapor", show_dialog=True):
    """HTML formatında dışa aktar"""
    try:
        import plotly
        import pandas as pd
    except ImportError:
        if show_dialog:
            showerror("Hata", "HTML raporu için gerekli kütüphaneler bulunamadı. Lütfen 'pip install plotly pandas' komutunu çalıştırın.")
        return False
    
    if show_dialog:
        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML", "*.html")],
            title="HTML Raporu Kaydet"
        )
        if not filename:
            return False
    else:
        # Otomatik dosya adı oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{title.lower().replace(' ', '_')}_{timestamp}.html"
    
    try:
        # Basit HTML template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; text-align: center; }}
                .section {{ margin-bottom: 30px; border: 1px solid #ddd; padding: 20px; border-radius: 5px; }}
                .section-title {{ color: #3b82f6; margin-top: 0; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f8f9fa; }}
                .positive {{ color: green; }}
                .negative {{ color: red; }}
                .footer {{ text-align: center; margin-top: 40px; color: #777; font-size: 12px; }}
            </style>
        </head>
        <body>
            <h1>{title}</h1>
            <div class="section">
                <h2 class="section-title">Rapor Bilgileri</h2>
                <p>Oluşturulma Tarihi: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        """
        
        # Veri tipine göre HTML içeriği oluştur
        if isinstance(data, dict):
            html_content += """
                <h2 class="section-title">Özet Bilgiler</h2>
                <table>
                    <tr><th>Metrik</th><th>Değer</th></tr>
            """
            
            for key, value in data.items():
                # Sayısal değerlere pozitif/negatif sınıfı ekle
                value_class = ""
                if isinstance(value, (int, float)) and key != 'date':
                    try:
                        if value > 0:
                            value_class = "positive"
                            value = f"+{value}"
                        elif value < 0:
                            value_class = "negative"
                    except:
                        pass
                
                html_content += f"<tr><td>{key}</td><td class='{value_class}'>{value}</td></tr>"
            
            html_content += "</table>"
            
        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                # Liste öğeleri sözlük ise, tablo olarak göster
                html_content += """
                    <h2 class="section-title">Detay Bilgiler</h2>
                    <table>
                        <tr>
                """
                
                # Tablo başlıklarını al
                headers = data[0].keys()
                for header in headers:
                    html_content += f"<th>{header}</th>"
                
                html_content += "</tr>"
                
                # Satırları ekle
                for item in data:
                    html_content += "<tr>"
                    for key, value in item.items():
                        value_class = ""
                        if isinstance(value, (int, float)) and key not in ['date', 'id', 'adet']:
                            try:
                                if value > 0:
                                    value_class = "positive"
                                elif value < 0:
                                    value_class = "negative"
                            except:
                                pass
                        
                        html_content += f"<td class='{value_class}'>{value}</td>"
                    html_content += "</tr>"
                
                html_content += "</table>"
            else:
                # Basit liste
                html_content += """
                    <h2 class="section-title">Veriler</h2>
                    <ul>
                """
                for item in data:
                    html_content += f"<li>{item}</li>"
                
                html_content += "</ul>"
        
        html_content += """
            </div>
            <div class="footer">
                <p>Bu rapor Hisse Takip Programı tarafından otomatik olarak oluşturulmuştur.</p>
            </div>
        </body>
        </html>
        """
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        if show_dialog:
            showinfo("Başarılı", f"HTML raporu kaydedildi:\n{filename}")
        return True
    
    except Exception as e:
        if show_dialog:
            showerror("Hata", f"HTML raporu kaydedilemedi:\n{str(e)}")
        return False