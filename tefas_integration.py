# tefas_integration.py
"""
TEFAS (Türkiye Elektronik Fon Bilgi Sistemi) Entegrasyonu
"""

import requests
import threading
from typing import Callable, Optional

class TEFASIntegration:
    """TEFAS API ile yatırım fonu entegrasyonu"""
    
    def __init__(self, db):
        self.db = db
        # TEFAS API genellikle REST API sağlamamaktadır
        # Burada ek bilgiler ve fon listesi için ayrı kaynak kullanıyoruz
        self.cache = {}
        self.funds_cache = None
    
    def get_popular_funds(self, callback: Optional[Callable] = None):
        """Popüler yatırım fonlarını getir"""
        def fetch():
            try:
                # Açık kaynaklı fon listesi
                popular_funds = [
                    {
                        'kod': 'FXUSZ',
                        'ad': 'Garanti Emeklilik ve Yatırımlar A.Ş. Dolar Fonu',
                        'tür': 'Dolar Fonu',
                        'kategori': 'Döviz'
                    },
                    {
                        'kod': 'GBNK',
                        'ad': 'Garanti Bankacılık ve Finansman Fonu',
                        'tür': 'Hisse Fonu',
                        'kategori': 'Yerli'
                    },
                    {
                        'kod': 'GLTL',
                        'ad': 'Garanta Lira Fonu',
                        'tür': 'Borçlanma Aracı Fonu',
                        'kategori': 'Sabit Getiri'
                    },
                    {
                        'kod': 'AKBNK',
                        'ad': 'Akbank Fon',
                        'tür': 'Hisse Fonu',
                        'kategori': 'Yerli'
                    },
                    {
                        'kod': 'VAKDF',
                        'ad': 'Vakıf Yatırım Fonu',
                        'tür': 'Hisse Fonu',
                        'kategori': 'Yerli'
                    }
                ]
                
                self.funds_cache = popular_funds
                
                if callback:
                    callback(popular_funds)
                
                return popular_funds
            
            except Exception as e:
                print(f"❌ Fon listesi çekme hatası: {e}")
            
            if callback:
                callback([])
            return []
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def get_fund_details(self, fund_code: str, callback: Optional[Callable] = None):
        """Fon detaylarını getir"""
        def fetch():
            try:
                # Gerçek uygulamada TEFAS API'sine istek gönderilir
                # Şimdilik örnek veri döndürüyoruz
                fund_details = {
                    'kod': fund_code,
                    'ad': 'Örnek Fon',
                    'fiyat': 1.5,
                    'para_birimi': 'TRY',
                    'portföy_değeri': 1000000000,
                    'birim_sayısı': 500000000,
                    'başlama_tarihi': '2015-01-01',
                    'kategori': 'Hisse Fonu',
                    'getiri_1ay': 1.5,
                    'getiri_3ay': 4.2,
                    'getiri_1yil': 12.5,
                }
                
                if callback:
                    callback(fund_details)
                
                return fund_details
            
            except Exception as e:
                print(f"❌ Fon detay çekme hatası ({fund_code}): {e}")
            
            if callback:
                callback(None)
            return None
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def add_fund_to_portfolio(self, user_id: int, fund_data: dict) -> bool:
        """Fonu portföye ekle"""
        try:
            asset_data = {
                'sembol': fund_data['kod'],
                'tur': 'fon',
                'ad': fund_data['ad'],
                'adet': fund_data['adet'],
                'ort_maliyet': fund_data['ort_maliyet'],
                'guncel_fiyat': fund_data['guncel_fiyat'],
                'para_birimi': 'TRY'
            }
            
            return self.db.add_asset(asset_data, user_id) is not None
        
        except Exception as e:
            print(f"❌ Fon ekleme hatası: {e}")
            return False
    
    def get_fund_categories(self) -> list:
        """Fon kategorilerini getir"""
        return [
            'Borçlanma Aracı Fonları',
            'Hisse Fonları',
            'Karma Fonlar',
            'Döviz Fonları',
            'Emtia Fonları',
            'Gayrimenkul Fonları',
            'Altın Fonları',
            'Endeks Fonları'
        ]
