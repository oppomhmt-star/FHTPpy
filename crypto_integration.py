# crypto_integration.py
"""
Kripto Para Entegrasyonu - Top 100 kripto parayı ekleyebilme
"""

import threading
import requests
from typing import Callable, Optional

class CryptoIntegration:
    """CoinGecko API ile kripto para entegrasyonu"""
    
    def __init__(self, db):
        self.db = db
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache = {}
        self.top_100_cache = None
    
    def get_top_100_cryptos(self, callback: Optional[Callable] = None):
        """İlk 100 kripto parayı getir"""
        def fetch():
            try:
                url = f"{self.base_url}/coins/markets"
                params = {
                    'vs_currency': 'try',
                    'order': 'market_cap_desc',
                    'per_page': 100,
                    'page': 1,
                    'sparkline': False,
                    'locale': 'tr'
                }
                
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    cryptos = response.json()
                    
                    formatted = []
                    for crypto in cryptos:
                        formatted.append({
                            'id': crypto['id'],
                            'sembol': crypto['symbol'].upper(),
                            'ad': crypto['name'],
                            'fiyat': crypto['current_price'] or 0,
                            'degisim_24h': crypto['price_change_percentage_24h'] or 0,
                            'pazar_deger': crypto['market_cap'] or 0,
                            'hacim': crypto['total_volume'] or 0,
                            'siralaması': crypto['market_cap_rank']
                        })
                    
                    self.top_100_cache = formatted
                    
                    if callback:
                        callback(formatted)
                    
                    return formatted
            
            except Exception as e:
                print(f"❌ Top 100 kripto çekme hatası: {e}")
            
            if callback:
                callback([])
            return []
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def get_crypto_detailed(self, crypto_id: str, callback: Optional[Callable] = None):
        """Kripto para detaylarını getir"""
        def fetch():
            try:
                url = f"{self.base_url}/coins/{crypto_id}"
                params = {
                    'localization': 'false',
                    'tickers': False,
                    'market_data': True,
                    'community_data': False,
                    'developer_data': False
                }
                
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    market_data = data.get('market_data', {})
                    
                    result = {
                        'ad': data.get('name'),
                        'sembol': data.get('symbol', '').upper(),
                        'kategoriler': data.get('categories', []),
                        'fiyat': market_data.get('current_price', {}).get('try', 0),
                        'pazar_deger': market_data.get('market_cap', {}).get('try', 0),
                        'yil_yuksek': market_data.get('high_24h', {}).get('try', 0),
                        'yil_dusuk': market_data.get('low_24h', {}).get('try', 0),
                        'degisim_24h': market_data.get('price_change_percentage_24h', 0),
                        'degisim_7d': market_data.get('price_change_percentage_7d', 0),
                        'degisim_30d': market_data.get('price_change_percentage_30d', 0),
                        'hacim_24h': market_data.get('total_volume', {}).get('try', 0),
                    }
                    
                    if callback:
                        callback(result)
                    
                    return result
            
            except Exception as e:
                print(f"❌ Kripto detay çekme hatası ({crypto_id}): {e}")
            
            if callback:
                callback(None)
            return None
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def add_crypto_to_portfolio(self, user_id: int, crypto_data: dict) -> bool:
        """Kripto parayı portföye ekle"""
        try:
            asset_data = {
                'sembol': crypto_data['sembol'],
                'tur': 'kripto',
                'ad': crypto_data['ad'],
                'adet': crypto_data['adet'],
                'ort_maliyet': crypto_data['ort_maliyet'],
                'guncel_fiyat': crypto_data['guncel_fiyat'],
                'para_birimi': 'USD'
            }
            
            return self.db.add_asset(asset_data, user_id) is not None
        
        except Exception as e:
            print(f"❌ Kripto ekleme hatası: {e}")
            return False
