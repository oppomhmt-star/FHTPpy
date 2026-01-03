# advanced_api_service.py
"""
Gelişmiş API servisleri - TEFAS, Kripto, Emtia, Monte Carlo
"""

import requests
import yfinance as yf
import numpy as np
import threading
from datetime import datetime, timedelta
import json

class TEFASService:
    """TEFAS (Türkiye Elektronik Fon Bilgi Sistemi) entegrasyonu"""
    
    def __init__(self):
        self.base_url = "https://www.tefas.com.tr"
        self.cache = {}
        self.cache_timeout = 3600  # 1 saat
    
    def get_funds(self, callback=None):
        """Yatırım fonlarını getir"""
        def fetch():
            try:
                # TEFAS API'sine istek gönder
                url = "https://api.tefas.com.tr/v1/fund/list"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    funds = response.json()
                    if callback:
                        callback(funds)
                    return funds
            except Exception as e:
                print(f"❌ TEFAS veri çekme hatası: {e}")
            
            if callback:
                callback([])
            return []
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def get_fund_price(self, fund_code, callback=None):
        """Fon fiyatını getir"""
        def fetch():
            try:
                url = f"https://api.tefas.com.tr/v1/fund/{fund_code}/price"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if callback:
                        callback(data)
                    return data
            except Exception as e:
                print(f"❌ Fon fiyat çekme hatası ({fund_code}): {e}")
            
            if callback:
                callback(None)
            return None
        
        threading.Thread(target=fetch, daemon=True).start()


class CryptoService:
    """Kripto para servisi - CoinGecko API"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache = {}
        self.cache_timeout = 300  # 5 dakika
    
    def get_top_cryptos(self, limit=100, callback=None):
        """İlk N kripto parayı getir"""
        def fetch():
            try:
                url = f"{self.base_url}/coins/markets"
                params = {
                    'vs_currency': 'try',
                    'order': 'market_cap_desc',
                    'per_page': limit,
                    'page': 1,
                    'sparkline': False
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    cryptos = response.json()
                    formatted = [
                        {
                            'sembol': c['symbol'].upper(),
                            'ad': c['name'],
                            'fiyat': c['current_price'] or 0,
                            'degisim_24h': c['price_change_percentage_24h'] or 0,
                            'pazar_deger': c['market_cap'] or 0,
                            'coin_id': c['id']
                        }
                        for c in cryptos
                    ]
                    
                    if callback:
                        callback(formatted)
                    return formatted
            except Exception as e:
                print(f"❌ Kripto veri çekme hatası: {e}")
            
            if callback:
                callback([])
            return []
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def get_crypto_price(self, crypto_id, callback=None):
        """Kripto fiyatını getir"""
        def fetch():
            try:
                url = f"{self.base_url}/simple/price"
                params = {
                    'ids': crypto_id,
                    'vs_currencies': 'try',
                    'include_market_cap': 'true',
                    'include_24hr_change': 'true'
                }
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if callback:
                        callback(data)
                    return data
            except Exception as e:
                print(f"❌ Kripto fiyat çekme hatası ({crypto_id}): {e}")
            
            if callback:
                callback(None)
            return None
        
        threading.Thread(target=fetch, daemon=True).start()


class CommodityService:
    """Emtia servisi - Gümüş, Petrol, Doğalgaz vb."""
    
    def __init__(self):
        self.base_url = "https://www.rapidapi.com/api/stocks"
        self.commodities = {
            'GOLD': {'symbol': 'GC=F', 'ad': 'Altın'},
            'SILVER': {'symbol': 'SI=F', 'ad': 'Gümüş'},
            'CRUDE_OIL': {'symbol': 'CL=F', 'ad': 'Petrol'},
            'NATURAL_GAS': {'symbol': 'NG=F', 'ad': 'Doğalgaz'},
            'COPPER': {'symbol': 'HG=F', 'ad': 'Bakır'},
        }
    
    def get_commodity_price(self, commodity_code, callback=None):
        """Emtia fiyatını getir"""
        def fetch():
            try:
                if commodity_code not in self.commodities:
                    if callback:
                        callback(None)
                    return
                
                symbol = self.commodities[commodity_code]['symbol']
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1d")
                
                if not data.empty:
                    price = data['Close'].iloc[-1]
                    result = {
                        'kod': commodity_code,
                        'ad': self.commodities[commodity_code]['ad'],
                        'fiyat': price,
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


class AdvancedAnalysisService:
    """Gelişmiş analiz servisi - Monte Carlo, Hedef Analizi, Vergi Optimizasyonu"""
    
    @staticmethod
    def monte_carlo_simulation(current_value, daily_return, std_dev, days=252, simulations=10000):
        """
        Monte Carlo Simülasyonu
        
        Args:
            current_value: Güncel portföy değeri
            daily_return: Günlük ortalama getiri (%)
            std_dev: Günlük standart sapma (%)
            days: Simülasyon günü
            simulations: Simülasyon sayısı
        
        Returns:
            dict: Simülasyon sonuçları
        """
        try:
            daily_return = daily_return / 100
            std_dev = std_dev / 100
            
            # Simülasyon için rastgele yollar oluştur
            results = np.zeros(simulations)
            
            for i in range(simulations):
                value = current_value
                for _ in range(days):
                    # Geometrik Brownian Motion
                    daily_change = np.random.normal(daily_return, std_dev)
                    value = value * (1 + daily_change)
                
                results[i] = value
            
            # İstatistikler
            return {
                'baslanc_degeri': current_value,
                'ortalama_bitis': np.mean(results),
                'medyan_bitis': np.median(results),
                'min_degeri': np.min(results),
                'max_degeri': np.max(results),
                'percentil_5': np.percentile(results, 5),
                'percentil_25': np.percentile(results, 25),
                'percentil_75': np.percentile(results, 75),
                'percentil_95': np.percentile(results, 95),
                'std_sapma': np.std(results),
                'simulasyon_sayisi': simulations,
                'gün': days
            }
        except Exception as e:
            print(f"❌ Monte Carlo hatası: {e}")
            return None
    
    @staticmethod
    def goal_projection(current_value, monthly_investment, annual_return, years):
        """
        Hedef Yönelik Analiz
        
        Args:
            current_value: Güncel portföy değeri
            monthly_investment: Aylık yatırım miktarı
            annual_return: Yıllık getiri (%)
            years: Yıl sayısı
        
        Returns:
            dict: Yıllık projeksiyon
        """
        try:
            annual_return = annual_return / 100
            monthly_return = (1 + annual_return) ** (1/12) - 1
            
            projections = []
            value = current_value
            
            for year in range(1, years + 1):
                for month in range(12):
                    value = value * (1 + monthly_return) + monthly_investment
                
                projections.append({
                    'yil': year,
                    'portfoy_degeri': round(value, 2),
                    'toplam_yatirim': round(current_value + monthly_investment * 12 * year, 2),
                    'kazanc': round(value - current_value - monthly_investment * 12 * year, 2)
                })
            
            return projections
        except Exception as e:
            print(f"❌ Hedef analizi hatası: {e}")
            return None
    
    @staticmethod
    def tax_optimization(realized_gains, unrealized_gains, transaction_costs):
        """
        Vergi Optimizasyonu Önerileri
        
        Args:
            realized_gains: Gerçekleşmiş kazançlar
            unrealized_gains: Gerçekleşmemiş kazançlar
            transaction_costs: İşlem maliyetleri
        
        Returns:
            dict: Vergi optimizasyonu tavsiyeleri
        """
        try:
            # Türkiye vergi oranları (2024)
            short_term_tax = 0.20  # 1 yıldan kısa: %20
            long_term_tax = 0.10   # 1 yıldan uzun: %10
            tax_exempt = 13000      # Vergi muaf tutarı
            
            recommendations = []
            
            # Kazanç hesaplaması
            total_gains = realized_gains + unrealized_gains
            taxable_gain = max(0, total_gains - tax_exempt)
            
            # Senaryo 1: Hiçbir satış yapma
            current_tax = realized_gains * short_term_tax
            recommendations.append({
                'senaryo': 'Mevcut Durum',
                'aciklama': 'Hiçbir pozisyon kapatılmıyor',
                'vergi_yuku': round(current_tax, 2),
                'kazanc': round(realized_gains, 2)
            })
            
            # Senaryo 2: Zararlı pozisyonları satma (Loss harvesting)
            if unrealized_gains < 0:
                offsetted_gain = max(0, realized_gains + unrealized_gains)
                tax_with_offset = offsetted_gain * short_term_tax
                recommendations.append({
                    'senaryo': 'Zarar Offseti',
                    'aciklama': f'{abs(unrealized_gains):.2f}₺ zararlı pozisyon satılıyor',
                    'vergi_yuku': round(tax_with_offset, 2),
                    'vergi_tasarrufu': round(current_tax - tax_with_offset, 2)
                })
            
            # Senaryo 3: 1 yıldan uzun pozisyonları tutma
            long_term_tax_amount = total_gains * long_term_tax
            recommendations.append({
                'senaryo': '1 Yıl Üzeri Tutma',
                'aciklama': 'Tüm pozisyonlar 1 yıldan uzun tutulursa',
                'vergi_yuku': round(long_term_tax_amount, 2),
                'vergi_tasarrufu': round(current_tax - long_term_tax_amount, 2)
            })
            
            return {
                'toplam_kazanc': round(total_gains, 2),
                'vergi_muaf_tutar': tax_exempt,
                'vergilendirilebilir_kazanc': round(taxable_gain, 2),
                'oneriler': recommendations
            }
        except Exception as e:
            print(f"❌ Vergi optimizasyonu hatası: {e}")
            return None


class StockSplitCalculator:
    """Hisse Bölünmesi Hesaplama"""
    
    @staticmethod
    def calculate_stock_split(current_adet, current_cost, split_ratio):
        """
        Hisse bölünmesi sonrası yeni adet ve maliyeti hesapla
        
        Args:
            current_adet: Mevcut adet
            current_cost: Ortalama maliyet
            split_ratio: Bölünme oranı (örn: 2 = 1 hisse 2'ye bölünür)
        
        Returns:
            dict: Yeni adet ve maliyet
        """
        try:
            new_adet = current_adet * split_ratio
            new_cost = current_cost / split_ratio
            
            return {
                'eski_adet': current_adet,
                'eski_maliyet': round(current_cost, 2),
                'yeni_adet': int(new_adet),
                'yeni_maliyet': round(new_cost, 2),
                'bölünme_oranı': split_ratio,
                'toplam_maliyet_degismi': False  # Toplam maliyet aynı kalır
            }
        except Exception as e:
            print(f"❌ Stock split hesaplaması hatası: {e}")
            return None


class RightsIssueCalculator:
    """Rüçhan Hakkı (Rights Issue) Hesaplaması"""
    
    @staticmethod
    def calculate_rights_issue(current_adet, current_price, rights_ratio, new_share_price):
        """
        Rüçhan hakkı uygulanırsa yeni maliyeti hesapla
        
        Args:
            current_adet: Mevcut adet
            current_price: Mevcut fiyat
            rights_ratio: Rüçhan oranı (örn: 0.25 = her 4 hisse başına 1 yeni hisse)
            new_share_price: Yeni hisse fiyatı
        
        Returns:
            dict: Rüçhan hakkı uygulanması sonuçları
        """
        try:
            new_adet = current_adet / rights_ratio
            total_investment = current_adet * current_price + new_adet * new_share_price
            new_avg_cost = total_investment / (current_adet + new_adet)
            
            return {
                'eski_adet': current_adet,
                'eski_ortalama_fiyat': round(current_price, 2),
                'yeni_hisse_adet': int(new_adet),
                'yeni_hisse_fiyati': round(new_share_price, 2),
                'toplam_yeni_adet': int(current_adet + new_adet),
                'toplam_yatirim': round(total_investment, 2),
                'yeni_ortalama_maliyet': round(new_avg_cost, 2),
                'otkome': f"Bedelli sermaye artırımı: {new_adet:.0f} hisse x {new_share_price:.2f}₺"
            }
        except Exception as e:
            print(f"❌ Rüçhan hakkı hesaplaması hatası: {e}")
            return None
