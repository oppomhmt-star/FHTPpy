# utils/api_manager.py

import requests
import time
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Dict
import threading

class APIProvider(ABC):
    """Base API Provider sınıfı"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.last_test_time = None
        self.last_test_result = None
        self.cache_duration = 300  # 5 dakika
    
    @abstractmethod
    def validate(self) -> Tuple[bool, str]:
        """API bağlantısını doğrula"""
        pass
    
    @abstractmethod
    def get_stock_price(self, symbol: str) -> Optional[float]:
        """Hisse fiyatı al"""
        pass
    
    def get_cached_result(self) -> Optional[Tuple[bool, str]]:
        """Cache'lenmiş test sonucunu döndür"""
        if self.last_test_time and self.last_test_result:
            if time.time() - self.last_test_time < self.cache_duration:
                return self.last_test_result
        return None
    
    def _cache_result(self, result: Tuple[bool, str]):
        """Test sonucunu cache'le"""
        self.last_test_time = time.time()
        self.last_test_result = result


class YFinanceProvider(APIProvider):
    """Yahoo Finance API Provider"""
    
    def validate(self) -> Tuple[bool, str]:
        # Önce cache kontrol et
        cached = self.get_cached_result()
        if cached:
            return cached
        
        try:
            import yfinance as yf
            stock = yf.Ticker("AAPL")
            data = stock.history(period="1d")
            
            if not data.empty:
                result = (True, "Yahoo Finance bağlantısı çalışıyor")
            else:
                result = (False, "Veri alınamadı")
            
            self._cache_result(result)
            return result
            
        except ImportError:
            result = (False, "yfinance modülü yüklü değil")
            self._cache_result(result)
            return result
        except Exception as e:
            result = (False, f"Bağlantı hatası: {str(e)[:50]}")
            self._cache_result(result)
            return result
    
    def get_stock_price(self, symbol: str) -> Optional[float]:
        try:
            import yfinance as yf
            stock = yf.Ticker(symbol)
            data = stock.history(period="1d")
            if not data.empty:
                return float(data['Close'].iloc[-1])
        except:
            pass
        return None


class IEXCloudProvider(APIProvider):
    """IEX Cloud API Provider"""
    
    def validate(self) -> Tuple[bool, str]:
        if not self.api_key:
            return (False, "API anahtarı eksik")
        
        cached = self.get_cached_result()
        if cached:
            return cached
        
        try:
            response = requests.get(
                f"https://cloud.iexapis.com/stable/status?token={self.api_key}",
                timeout=5
            )
            
            if response.status_code == 200:
                result = (True, "IEX Cloud bağlantısı başarılı")
            elif response.status_code == 401:
                result = (False, "Geçersiz API anahtarı")
            elif response.status_code == 403:
                result = (False, "API limitine ulaşıldı")
            else:
                result = (False, f"HTTP {response.status_code}")
            
            self._cache_result(result)
            return result
            
        except requests.Timeout:
            result = (False, "Zaman aşımı (5 saniye)")
            self._cache_result(result)
            return result
        except Exception as e:
            result = (False, f"Bağlantı hatası: {str(e)[:50]}")
            self._cache_result(result)
            return result
    
    def get_stock_price(self, symbol: str) -> Optional[float]:
        if not self.api_key:
            return None
        
        try:
            response = requests.get(
                f"https://cloud.iexapis.com/stable/stock/{symbol}/quote?token={self.api_key}",
                timeout=5
            )
            if response.status_code == 200:
                return float(response.json().get('latestPrice', 0))
        except:
            pass
        return None


class FinnhubProvider(APIProvider):
    """Finnhub API Provider"""
    
    def validate(self) -> Tuple[bool, str]:
        if not self.api_key:
            return (False, "API anahtarı eksik")
        
        cached = self.get_cached_result()
        if cached:
            return cached
        
        try:
            response = requests.get(
                f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={self.api_key}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'c' in data and data['c'] > 0:
                    result = (True, "Finnhub bağlantısı başarılı")
                else:
                    result = (False, "Geçersiz yanıt")
            elif response.status_code == 401:
                result = (False, "Geçersiz API anahtarı")
            elif response.status_code == 429:
                result = (False, "API limitine ulaşıldı")
            else:
                result = (False, f"HTTP {response.status_code}")
            
            self._cache_result(result)
            return result
            
        except requests.Timeout:
            result = (False, "Zaman aşımı (5 saniye)")
            self._cache_result(result)
            return result
        except Exception as e:
            result = (False, f"Bağlantı hatası: {str(e)[:50]}")
            self._cache_result(result)
            return result
    
    def get_stock_price(self, symbol: str) -> Optional[float]:
        if not self.api_key:
            return None
        
        try:
            response = requests.get(
                f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={self.api_key}",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                return float(data.get('c', 0))
        except:
            pass
        return None


class AlphaVantageProvider(APIProvider):
    """Alpha Vantage API Provider"""
    
    def validate(self) -> Tuple[bool, str]:
        if not self.api_key:
            return (False, "API anahtarı eksik")
        
        cached = self.get_cached_result()
        if cached:
            return cached
        
        try:
            response = requests.get(
                f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey={self.api_key}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if "Global Quote" in data and data["Global Quote"]:
                    result = (True, "Alpha Vantage bağlantısı başarılı")
                elif "Error Message" in data:
                    result = (False, "Geçersiz sembol veya API hatası")
                elif "Note" in data:
                    result = (False, "API limitine ulaşıldı")
                else:
                    result = (False, "Geçersiz API anahtarı")
            else:
                result = (False, f"HTTP {response.status_code}")
            
            self._cache_result(result)
            return result
            
        except requests.Timeout:
            result = (False, "Zaman aşımı (10 saniye)")
            self._cache_result(result)
            return result
        except Exception as e:
            result = (False, f"Bağlantı hatası: {str(e)[:50]}")
            self._cache_result(result)
            return result
    
    def get_stock_price(self, symbol: str) -> Optional[float]:
        if not self.api_key:
            return None
        
        try:
            response = requests.get(
                f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.api_key}",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if "Global Quote" in data:
                    return float(data["Global Quote"].get("05. price", 0))
        except:
            pass
        return None


class APIManager:
    """Tüm API provider'ları yönetir"""
    
    PROVIDERS = {
        "yfinance": YFinanceProvider,
        "iex_cloud": IEXCloudProvider,
        "finnhub": FinnhubProvider,
        "alpha_vantage": AlphaVantageProvider
    }
    
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self.providers = {}
        self._init_providers()
    
    def _init_providers(self):
        """Tüm provider'ları başlat"""
        for name, provider_class in self.PROVIDERS.items():
            api_key = None
            if self.settings_manager:
                api_key = self.settings_manager.settings.get(f"{name}_api_key")
            self.providers[name] = provider_class(api_key)
    
    def validate_provider(self, provider_name: str, api_key: Optional[str] = None) -> Tuple[bool, str]:
        """Belirli bir provider'ı doğrula"""
        provider_class = self.PROVIDERS.get(provider_name)
        if not provider_class:
            return (False, "Bilinmeyen API sağlayıcı")
        
        if api_key is None and provider_name in self.providers:
            provider = self.providers[provider_name]
        else:
            provider = provider_class(api_key)
        
        return provider.validate()
    
    def validate_all(self, api_keys: Dict[str, str] = None) -> Dict[str, Dict]:
        """Tüm provider'ları doğrula"""
        results = {}
        
        for name, provider_class in self.PROVIDERS.items():
            api_key = None
            if api_keys and name in api_keys:
                api_key = api_keys.get(f"{name}_api_key")
            elif name in self.providers:
                api_key = self.providers[name].api_key
            
            provider = provider_class(api_key)
            success, message = provider.validate()
            
            results[name] = {
                "success": success,
                "message": message,
                "has_key": bool(api_key)
            }
        
        return results
    
    def get_active_provider(self) -> Optional[APIProvider]:
        """Aktif provider'ı döndür"""
        if self.settings_manager:
            provider_name = self.settings_manager.settings.get("api_provider", "yfinance")
            return self.providers.get(provider_name)
        return self.providers.get("yfinance")
    
    def get_stock_price(self, symbol: str) -> Optional[float]:
        """Aktif provider ile hisse fiyatı al"""
        provider = self.get_active_provider()
        if provider:
            return provider.get_stock_price(symbol)
        return None