#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

# Read the file
with open('pages/settings_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

# First, find and fix the validate_all_apis method - remove Advanced API section
content = re.sub(
    r"(\s+# Advanced API\s+adv_key.*?results\.append\(\"⊘ Advanced API:.*?\"\)\s+)",
    "",
    content,
    flags=re.DOTALL
)

# Fix the validate_selected_api method - need to add proper indentation and replace advanced_api
new_validate_selected_api = '''    def validate_selected_api(self):
        """Seçili API'yi test et"""
        try:
            provider = self.settings_widgets.get("api_provider")
            if not provider:
                showerror("Hata", "API sağlayıcı seçilmedi")
                return
            
            if isinstance(provider, dict):
                selected = provider["var"].get()
                # Display value'dan actual value'ya dönüştür
                try:
                    idx = provider["display_values"].index(selected)
                    provider_name = provider["values"][idx]
                except:
                    provider_name = selected
            else:
                provider_name = provider.get()
            
            # Seçilen provider'ı test et
            if provider_name == "yfinance":
                try:
                    import yfinance as yf
                    stock = yf.Ticker("AAPL")
                    data = stock.history(period="1d")
                    if not data.empty:
                        showinfo("Başarılı", "✓ Yahoo Finance bağlantısı çalışıyor!")
                    else:
                        showerror("Hata", "✗ Yahoo Finance veri döndüremiyor")
                except Exception as e:
                    showerror("Hata", f"✗ Yahoo Finance hatası: {str(e)}")
            
            elif provider_name == "iex_cloud":
                iex_key = self.settings_widgets.get("iex_cloud_api_key")
                if iex_key and iex_key.get():
                    try:
                        import requests
                        response = requests.get(
                            f"https://cloud.iexapis.com/stable/status?token={iex_key.get()}",
                            timeout=5
                        )
                        if response.status_code == 200:
                            showinfo("Başarılı", "✓ IEX Cloud bağlantısı çalışıyor!")
                        else:
                            showerror("Hata", "✗ IEX Cloud başarısız")
                    except Exception as e:
                        showerror("Hata", f"✗ IEX Cloud hatası: {str(e)}")
                else:
                    showerror("Hata", "IEX Cloud API anahtarı girilmedi!")
            
            elif provider_name == "finnhub":
                finnhub_key = self.settings_widgets.get("finnhub_api_key")
                if finnhub_key and finnhub_key.get():
                    try:
                        import requests
                        response = requests.get(
                            f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={finnhub_key.get()}",
                            timeout=5
                        )
                        if response.status_code == 200:
                            showinfo("Başarılı", "✓ Finnhub bağlantısı çalışıyor!")
                        else:
                            showerror("Hata", "✗ Finnhub başarısız")
                    except Exception as e:
                        showerror("Hata", f"✗ Finnhub hatası: {str(e)}")
                else:
                    showerror("Hata", "Finnhub API anahtarı girilmedi!")
            
            elif provider_name == "alpha_vantage":
                av_key = self.settings_widgets.get("alpha_vantage_api_key")
                if av_key and av_key.get():
                    showinfo("Başarılı", "✓ Alpha Vantage API anahtarı kayıtlı")
                else:
                    showerror("Hata", "Alpha Vantage API anahtarı girilmedi!")
        
        except Exception as e:
            showerror("Hata", f"API doğrulaması sırasında hata: {str(e)}")'''

# Replace the broken validate_selected_api method
# Find and replace the entire method
pattern = r'def validate_selected_api\(self\):.*?(?=\n    def )'
content = re.sub(pattern, new_validate_selected_api + '\n\n    ', content, flags=re.DOTALL)

# Write back
with open('pages/settings_page.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed settings_page.py")
