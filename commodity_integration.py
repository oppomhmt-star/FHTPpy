# commodity_integration.py
"""
Emtia Yönetimi - Gümüş, Petrol, Doğalgaz vb.
"""

import yfinance as yf
import threading
from typing import Callable, Optional

class CommodityIntegration:
    """Emtia fiyatları entegrasyonu"""
    
    def __init__(self, db):
        self.db = db
        self.cache = {}
        
        # Desteklenen emtialar
        self.commodities = {
            'GOLD': {
                'symbol': 'GC=F',
                'ad': 'Altın',
                'birim': 'USD/oz'
            },
            'SILVER': {
                'symbol': 'SI=F',
                'ad': 'Gümüş',
                'birim': 'USD/oz'
            },
            'CRUDE_OIL': {
                'symbol': 'CL=F',
                'ad': 'WTI Petrol',
                'birim': 'USD/bbl'
            },
            'BRENT_OIL': {
                'symbol': 'BZ=F',
                'ad': 'Brent Petrol',
                'birim': 'USD/bbl'
            },
            'NATURAL_GAS': {
                'symbol': 'NG=F',
                'ad': 'Doğalgaz',
                'birim': 'USD/MMBtu'
            },
            'COPPER': {
                'symbol': 'HG=F',
                'ad': 'Bakır',
                'birim': 'USD/lb'
            },
            'ALUMINUM': {
                'symbol': 'ALI=F',
                'ad': 'Alüminyum',
                'birim': 'USD/mt'
            },
            'NICKEL': {
                'symbol': 'NI=F',
                'ad': 'Nikel',
                'birim': 'USD/mt'
            },
            'ZINC': {
                'symbol': 'ZN=F',
                'ad': 'Çinko',
                'birim': 'USD/mt'
            },
            'LEAD': {
                'symbol': 'PL=F',
                'ad': 'Kurşun',
                'birim': 'USD/mt'
            }
        }
    
    def get_commodity_price(self, commodity_code: str, callback: Optional[Callable] = None):
        """Emtia fiyatını getir"""
        def fetch():
            try:
                if commodity_code not in self.commodities:
                    if callback:
                        callback(None)
                    return
                
                commodity = self.commodities[commodity_code]
                ticker = yf.Ticker(commodity['symbol'])
                data = ticker.history(period="1d")
                
                if not data.empty:
                    price = data['Close'].iloc[-1]
                    volume = data['Volume'].iloc[-1]
                    
                    result = {
                        'kod': commodity_code,
                        'ad': commodity['ad'],
                        'fiyat': price,
                        'birim': commodity['birim'],
                        'hacim': volume,
                        'para_birimi': 'USD'
                    }
                    
                    if callback:
                        callback(result)
                    
                    return result
            
            except Exception as e:
                print(f"❌ Emtia fiyat çekme hatası ({commodity_code}): {e}")
            
            if callback:
                callback(None)
            return None
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def get_all_commodities(self, callback: Optional[Callable] = None):
        """Tüm desteklenen emtiaları getir"""
        def fetch():
            try:
                results = []
                
                for code, commodity in self.commodities.items():
                    try:
                        ticker = yf.Ticker(commodity['symbol'])
                        data = ticker.history(period="1d")
                        
                        if not data.empty:
                            price = data['Close'].iloc[-1]
                            results.append({
                                'kod': code,
                                'ad': commodity['ad'],
                                'fiyat': price,
                                'birim': commodity['birim'],
                                'para_birimi': 'USD'
                            })
                    except:
                        pass
                
                if callback:
                    callback(results)
                
                return results
            
            except Exception as e:
                print(f"❌ Emtia listesi çekme hatası: {e}")
            
            if callback:
                callback([])
            return []
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def add_commodity_to_portfolio(self, user_id: int, commodity_data: dict) -> bool:
        """Emtiayı portföye ekle"""
        try:
            asset_data = {
                'sembol': commodity_data['kod'],
                'tur': 'emtia',
                'ad': commodity_data['ad'],
                'adet': commodity_data['adet'],
                'ort_maliyet': commodity_data['ort_maliyet'],
                'guncel_fiyat': commodity_data['guncel_fiyat'],
                'para_birimi': 'USD'
            }
            
            return self.db.add_asset(asset_data, user_id) is not None
        
        except Exception as e:
            print(f"❌ Emtia ekleme hatası: {e}")
            return False
    
    def get_supported_commodities(self) -> dict:
        """Desteklenen emtiaları döndür"""
        return self.commodities
