"""
API servisleri modülü - Birden fazla veri sağlayıcısı desteği
"""

import yfinance as yf
from datetime import datetime, timedelta
import threading
import requests
from config import INDICES, CURRENCIES

class APIService:
    def __init__(self, provider="yfinance"):
        self.cache = {}
        self.cache_timeout = 300  # 5 dakika
        self.usd_try_rate = 34.50
        self.provider = provider  # yfinance, finnhub, alpha_vantage, iex
        self.providers_config = {
            "finnhub": {"api_key": "", "base_url": "https://finnhub.io/api/v1"},
            "alpha_vantage": {"api_key": "", "base_url": "https://www.alphavantage.co/query"},
            "iex": {"api_key": "", "base_url": "https://cloud.iexapis.com/stable"},
        }
    
    def set_api_key(self, provider, api_key):
        """API anahtarını ayarla"""
        if provider in self.providers_config:
            self.providers_config[provider]["api_key"] = api_key
            print(f"✅ {provider} API anahtarı kaydedildi")
            return True
        return False
    
    def switch_provider(self, provider):
        """Veri sağlayıcısını değiştir"""
        if provider in ["yfinance", "finnhub", "alpha_vantage", "iex"]:
            self.provider = provider
            print(f"📊 Veri sağlayıcısı: {provider}")
            return True
        return False
    
    # ============ YFINANCE (Varsayılan) ============
    
    def _get_index_data_yfinance(self, callback=None):
        """yfinance ile endeks verisi"""
        def fetch():
            indices_data = []
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            for name, symbol in INDICES.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(start=start_date, end=end_date)
                    
                    if not hist.empty:
                        last_price = hist['Close'].iloc[-1]
                        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else last_price
                        daily_change = ((last_price - prev_price) / prev_price) * 100 if prev_price else 0
                        
                        indices_data.append({
                            "name": name,
                            "value": last_price,
                            "change": daily_change,
                            "history": hist['Close'].values.tolist()
                        })
                except Exception as e:
                    print(f"Endeks hatası ({name}): {e}")
            
            if callback:
                callback(indices_data)
            return indices_data
        
        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()
    
    def _get_currency_data_yfinance(self, callback=None):
        """yfinance ile döviz/altın verisi"""
        def fetch():
            currency_data = []
            
            try:
                usd_try_ticker = yf.Ticker("TRY=X")
                usd_try_hist = usd_try_ticker.history(period="2d")
                if not usd_try_hist.empty:
                    self.usd_try_rate = usd_try_hist['Close'].iloc[-1]
            except:
                self.usd_try_rate = 34.50
            
            for name, symbol in CURRENCIES.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")
                    
                    if not hist.empty:
                        last_price = hist['Close'].iloc[-1]
                        prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else last_price
                        daily_change = ((last_price - prev_price) / prev_price) * 100 if prev_price else 0
                        
                        # Formatla
                        if name == "BTC":
                            value_text = f"${last_price:,.0f}"
                            subtitle_text = f"₺{last_price * self.usd_try_rate:,.0f}"
                        elif name == "ALTIN":
                            value_text = f"${last_price:,.2f}"
                            subtitle_text = f"₺{last_price * self.usd_try_rate:,.2f}"
                        elif name in ["DOLAR", "EURO"]:
                            value_text = f"₺{last_price:.4f}"
                            subtitle_text = f"{daily_change:+.2f}%"
                        else:
                            value_text = f"{last_price:.2f}"
                            subtitle_text = f"{daily_change:+.2f}%"
                        
                        currency_data.append({
                            "name": name,
                            "value": last_price,
                            "value_text": value_text,
                            "change": daily_change,
                            "symbol": symbol,
                            "subtitle": subtitle_text
                        })
                except Exception as e:
                    print(f"Döviz hatası ({name}): {e}")
            
            if callback:
                callback(currency_data)
            return currency_data
        
        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()
    
    def _get_stock_price_yfinance(self, symbol):
        """yfinance ile hisse fiyatı"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                return data['Close'].iloc[-1]
        except:
            pass
        return None
    
    def _get_stock_history_yfinance(self, symbol, period="1y"):
        """yfinance ile hisse geçmişi"""
        try:
            ticker = yf.Ticker(symbol)
            return ticker.history(period=period)
        except:
            return None
    
    # ============ FINNHUB ============
    
    def _get_stock_price_finnhub(self, symbol):
        """Finnhub ile hisse fiyatı"""
        api_key = self.providers_config["finnhub"]["api_key"]
        if not api_key:
            print("⚠️ Finnhub API anahtarı ayarlanmamış")
            return self._get_stock_price_yfinance(symbol)
        
        try:
            url = f"{self.providers_config['finnhub']['base_url']}/quote"
            params = {"symbol": symbol, "token": api_key}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('c')  # current price
        except Exception as e:
            print(f"Finnhub hatası: {e}")
        
        return self._get_stock_price_yfinance(symbol)
    
    def _get_stock_candles_finnhub(self, symbol, resolution="D", count=365):
        """Finnhub ile mum grafikleri"""
        api_key = self.providers_config["finnhub"]["api_key"]
        if not api_key:
            return self._get_stock_history_yfinance(symbol)
        
        try:
            url = f"{self.providers_config['finnhub']['base_url']}/stock/candle"
            from_time = int((datetime.now() - timedelta(days=count)).timestamp())
            to_time = int(datetime.now().timestamp())
            
            params = {
                "symbol": symbol,
                "resolution": resolution,
                "from": from_time,
                "to": to_time,
                "token": api_key
            }
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Finnhub mum grafikleri hatası: {e}")
        
        return None
    
    # ============ ALPHA VANTAGE ============
    
    def _get_stock_price_alpha_vantage(self, symbol):
        """Alpha Vantage ile hisse fiyatı"""
        api_key = self.providers_config["alpha_vantage"]["api_key"]
        if not api_key:
            print("⚠️ Alpha Vantage API anahtarı ayarlanmamış")
            return self._get_stock_price_yfinance(symbol)
        
        try:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": api_key
            }
            response = requests.get(self.providers_config["alpha_vantage"]["base_url"], 
                                   params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                quote = data.get('Global Quote', {})
                return float(quote.get('05. price', 0))
        except Exception as e:
            print(f"Alpha Vantage hatası: {e}")
        
        return self._get_stock_price_yfinance(symbol)
    
    def _get_stock_daily_alpha_vantage(self, symbol, size="full"):
        """Alpha Vantage ile günlük veriler"""
        api_key = self.providers_config["alpha_vantage"]["api_key"]
        if not api_key:
            return self._get_stock_history_yfinance(symbol)
        
        try:
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "outputsize": size,
                "apikey": api_key
            }
            response = requests.get(self.providers_config["alpha_vantage"]["base_url"], 
                                   params=params, timeout=5)
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Alpha Vantage günlük veri hatası: {e}")
        
        return None
    
    # ============ IEX CLOUD ============
    
    def _get_stock_price_iex(self, symbol):
        """IEX Cloud ile hisse fiyatı"""
        api_key = self.providers_config["iex"]["api_key"]
        if not api_key:
            print("⚠️ IEX Cloud API anahtarı ayarlanmamış")
            return self._get_stock_price_yfinance(symbol)
        
        try:
            url = f"{self.providers_config['iex']['base_url']}/stock/{symbol}/quote"
            params = {"token": api_key}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('latestPrice')
        except Exception as e:
            print(f"IEX hatası: {e}")
        
        return self._get_stock_price_yfinance(symbol)
    
    def _get_stock_chart_iex(self, symbol, range="1y"):
        """IEX ile grafik verisi"""
        api_key = self.providers_config["iex"]["api_key"]
        if not api_key:
            return self._get_stock_history_yfinance(symbol, range)
        
        try:
            url = f"{self.providers_config['iex']['base_url']}/stock/{symbol}/chart/{range}"
            params = {"token": api_key}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"IEX grafik hatası: {e}")
        
        return None
    
    # ============ PUBLIC INTERFACE (Sağlayıcıdan bağımsız) ============
    
    def get_index_data(self, callback=None):
        """Endeks verisi getir (otomatik sağlayıcı seçimi)"""
        if self.provider == "yfinance":
            return self._get_index_data_yfinance(callback)
        # Diğer sağlayıcılar şimdilik yfinance'a fallback
        return self._get_index_data_yfinance(callback)
    
    def get_currency_data(self, callback=None):
        """Döviz verisi getir (otomatik sağlayıcı seçimi)"""
        if self.provider == "yfinance":
            return self._get_currency_data_yfinance(callback)
        return self._get_currency_data_yfinance(callback)
    
    def get_stock_price(self, symbol):
        """Hisse fiyatı getir"""
        if self.provider == "finnhub":
            return self._get_stock_price_finnhub(symbol)
        elif self.provider == "alpha_vantage":
            return self._get_stock_price_alpha_vantage(symbol)
        elif self.provider == "iex":
            return self._get_stock_price_iex(symbol)
        else:
            return self._get_stock_price_yfinance(symbol)
    
    def get_stock_history(self, symbol, period="1y"):
        """Hisse geçmişi getir"""
        if self.provider == "finnhub":
            return self._get_stock_candles_finnhub(symbol)
        elif self.provider == "alpha_vantage":
            return self._get_stock_daily_alpha_vantage(symbol)
        elif self.provider == "iex":
            return self._get_stock_chart_iex(symbol)
        else:
            return self._get_stock_history_yfinance(symbol, period)
    
    def test_provider(self, provider):
        """Sağlayıcıyı test et"""
        test_symbol = "AAPL"
        try:
            if provider == "yfinance":
                price = self._get_stock_price_yfinance(test_symbol)
            elif provider == "finnhub":
                price = self._get_stock_price_finnhub(test_symbol)
            elif provider == "alpha_vantage":
                price = self._get_stock_price_alpha_vantage(test_symbol)
            elif provider == "iex":
                price = self._get_stock_price_iex(test_symbol)
            else:
                return False
            
            return price is not None
        except:
            return False
