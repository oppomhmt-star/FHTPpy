# integration_manager.py
"""
Entegrasyon Yöneticisi - Tüm API ve varlık entegrasyonlarını yönet
"""

from advanced_api_service import TEFASService, CryptoService, CommodityService, AdvancedAnalysisService
from crypto_integration import CryptoIntegration
from tefas_integration import TEFASIntegration
from commodity_integration import CommodityIntegration

class IntegrationManager:
    """Tüm entegrasyonları merkezi yerde yönet"""
    
    def __init__(self, db):
        self.db = db
        
        # API Servisleri
        self.tefas_service = TEFASService()
        self.crypto_service = CryptoService()
        self.commodity_service = CommodityService()
        self.analysis_service = AdvancedAnalysisService
        
        # Entegrasyonlar
        self.crypto_integration = CryptoIntegration(db)
        self.tefas_integration = TEFASIntegration(db)
        self.commodity_integration = CommodityIntegration(db)
    
    def get_all_services(self) -> dict:
        """Tüm servisleri döndür"""
        return {
            'tefas_service': self.tefas_service,
            'crypto_service': self.crypto_service,
            'commodity_service': self.commodity_service,
            'analysis_service': self.analysis_service,
            'crypto_integration': self.crypto_integration,
            'tefas_integration': self.tefas_integration,
            'commodity_integration': self.commodity_integration
        }
    
    def sync_crypto_prices(self, user_id: int, callback=None):
        """Kripto fiyatlarını senkronize et"""
        def update_prices():
            assets = self.db.get_assets_by_type('kripto', user_id)
            
            for asset in assets:
                self.crypto_service.get_crypto_price(asset['sembol'].lower(), 
                    callback=lambda price_data: self._update_asset_price(user_id, asset['sembol'], 'kripto', price_data))
            
            if callback:
                callback()
        
        import threading
        threading.Thread(target=update_prices, daemon=True).start()
    
    def sync_commodity_prices(self, user_id: int, callback=None):
        """Emtia fiyatlarını senkronize et"""
        def update_prices():
            assets = self.db.get_assets_by_type('emtia', user_id)
            
            for asset in assets:
                self.commodity_service.get_commodity_price(asset['sembol'],
                    callback=lambda price_data: self._update_asset_price(user_id, asset['sembol'], 'emtia', price_data))
            
            if callback:
                callback()
        
        import threading
        threading.Thread(target=update_prices, daemon=True).start()
    
    def sync_fund_prices(self, user_id: int, callback=None):
        """Fon fiyatlarını senkronize et"""
        def update_prices():
            assets = self.db.get_assets_by_type('fon', user_id)
            
            for asset in assets:
                self.tefas_service.get_fund_price(asset['sembol'],
                    callback=lambda price_data: self._update_asset_price(user_id, asset['sembol'], 'fon', price_data))
            
            if callback:
                callback()
        
        import threading
        threading.Thread(target=update_prices, daemon=True).start()
    
    def _update_asset_price(self, user_id: int, symbol: str, asset_type: str, price_data: dict):
        """Varlık fiyatını güncelle"""
        if price_data:
            try:
                # price_data yapısı API'ye göre farklılık gösterebilir
                # Burada standart bir yapı kullanıyoruz
                guncel_fiyat = price_data.get('fiyat', 0) or price_data.get('price', 0)
                
                # Veritabanında güncelle
                assets = self.db.get_assets_by_type(asset_type, user_id)
                asset = next((a for a in assets if a['sembol'] == symbol.upper()), None)
                
                if asset:
                    asset['guncel_fiyat'] = guncel_fiyat
                    self.db.add_asset(asset, user_id)
            
            except Exception as e:
                print(f"Fiyat güncellemesi hatası: {e}")
