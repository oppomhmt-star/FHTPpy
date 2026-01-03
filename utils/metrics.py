# utils/metrics.py

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf

class PortfolioMetrics:
    """Portföy metrikleri hesaplayıcı - Güvenli Versiyon"""
    
    def __init__(self, portfolio, transactions):
        self.portfolio = portfolio or []
        self.transactions = transactions or []
    
    def calculate_total_return(self):
        """Toplam getiri %"""
        try:
            total_cost = sum(h["adet"] * h["ort_maliyet"] for h in self.portfolio)
            total_value = sum(h["adet"] * h.get("guncel_fiyat", h["ort_maliyet"]) for h in self.portfolio)
            
            if total_cost == 0:
                return 0
            
            return ((total_value - total_cost) / total_cost) * 100
        except Exception as e:
            print(f"Getiri hesaplama hatası: {e}")
            return 0
    
    def calculate_daily_returns(self, days=30):
        """Günlük getiri serisini hesapla"""
        try:
            returns = []
            for stock in self.portfolio:
                symbol = stock['sembol']
                try:
                    ticker = yf.Ticker(f"{symbol}.IS")
                    hist = ticker.history(period=f"{days}d")
                    
                    if not hist.empty:
                        daily_return = hist['Close'].pct_change().dropna()
                        weight = (stock['adet'] * stock.get('guncel_fiyat', stock['ort_maliyet']))
                        
                        returns.append({
                            'symbol': symbol,
                            'returns': daily_return.values,
                            'weight': weight
                        })
                except Exception as stock_error:
                    print(f"Hisse getiri verisi alınamadı ({symbol}): {stock_error}")
                    continue
            
            return returns
        except Exception as e:
            print(f"Günlük getiri hesaplama hatası: {e}")
            return []
    
    def calculate_volatility(self, days=30):
        """Volatilite (Standart sapma) - Güvenli versiyon"""
        try:
            daily_returns = self.calculate_daily_returns(days)
            
            if not daily_returns:
                return 15.0  # Varsayılan değer
            
            total_weight = sum(r['weight'] for r in daily_returns)
            
            if total_weight == 0:
                return 15.0  # Varsayılan değer
            
            # Minimum uzunluğu bul
            min_length = float('inf')
            for r in daily_returns:
                if len(r['returns']) > 0 and len(r['returns']) < min_length:
                    min_length = len(r['returns'])
            
            if min_length == float('inf') or min_length == 0:
                return 15.0  # Varsayılan değer
            
            # Veri uzunluklarını eşitle
            processed_returns = []
            processed_weights = []
            
            for r in daily_returns:
                if len(r['returns']) >= min_length:
                    processed_returns.append(r['returns'][-min_length:])
                    processed_weights.append(r['weight'])
            
            if not processed_returns:
                return 15.0  # Varsayılan değer
            
            # Ağırlıkları normalize et
            total_processed_weight = sum(processed_weights)
            if total_processed_weight <= 0:
                return 15.0  # Varsayılan değer
                
            normalized_weights = [w / total_processed_weight for w in processed_weights]
            
            # Portföy getirilerini hesapla
            portfolio_returns = np.zeros(min_length)
            for i, returns in enumerate(processed_returns):
                portfolio_returns += returns * normalized_weights[i]
            
            # Yıllık volatilite
            annual_factor = np.sqrt(252)  # Yıllık işlem günü
            volatility = np.std(portfolio_returns) * annual_factor * 100
            
            return float(volatility)  # NumPy türünden normal float'a çevir
            
        except Exception as e:
            print(f"Volatilite hesaplama hatası: {e}")
            return 15.0  # Varsayılan değer
    
    def calculate_max_drawdown(self):
        """Maksimum düşüş % - Güvenli versiyon"""
        try:
            if not self.portfolio:
                return 0
                
            max_dd = 0
            
            for stock in self.portfolio:
                current = stock.get('guncel_fiyat', stock['ort_maliyet'])
                cost = stock['ort_maliyet']
                
                if current < cost:
                    dd = ((current - cost) / cost) * 100
                    if dd < max_dd:
                        max_dd = dd
            
            return abs(max_dd)
        except Exception as e:
            print(f"Max drawdown hesaplama hatası: {e}")
            return 5.0  # Varsayılan değer
    
    def calculate_sharpe_ratio(self, risk_free_rate=0.15):
        """Sharpe Oranı - Güvenli versiyon"""
        try:
            total_return = self.calculate_total_return()
            volatility = self.calculate_volatility()
            
            if volatility <= 0:
                return 0
            
            sharpe = (total_return - risk_free_rate) / volatility
            
            return sharpe
        except Exception as e:
            print(f"Sharpe oranı hesaplama hatası: {e}")
            return 0.5  # Varsayılan değer
    
    def calculate_diversification_score(self):
        """Diversifikasyon skoru (0-100) - Güvenli versiyon"""
        try:
            if not self.portfolio:
                return 0
            
            score = 0
            
            # 1. Hisse sayısı (max 30 puan)
            num_stocks = len(self.portfolio)
            stock_score = min(num_stocks * 3, 30)
            score += stock_score
            
            # 2. Sektör çeşitliliği (max 40 puan)
            try:
                from utils.sector_mapper import get_sector
                sectors = set()
                
                for stock in self.portfolio:
                    sector = get_sector(stock['sembol'])
                    sectors.add(sector)
                
                sector_score = min(len(sectors) * 8, 40)
                score += sector_score
            except Exception as sector_error:
                print(f"Sektör çeşitliliği hesaplama hatası: {sector_error}")
                score += 20  # Varsayılan
            
            # 3. Konsantrasyon riski (max 30 puan)
            try:
                total_value = sum(h["adet"] * h.get("guncel_fiyat", h["ort_maliyet"]) for h in self.portfolio)
                
                if total_value > 0:
                    stock_values = [(h["adet"] * h.get("guncel_fiyat", h["ort_maliyet"])) for h in self.portfolio]
                    stock_values.sort(reverse=True)
                    
                    top3_value = sum(stock_values[:min(3, len(stock_values))])
                    top3_ratio = (top3_value / total_value) * 100
                    
                    if top3_ratio <= 50:
                        concentration_score = 30
                    elif top3_ratio <= 70:
                        concentration_score = 20
                    else:
                        concentration_score = 10
                    
                    score += concentration_score
            except Exception as conc_error:
                print(f"Konsantrasyon hesaplama hatası: {conc_error}")
                score += 15  # Varsayılan
            
            return min(score, 100)
        except Exception as e:
            print(f"Diversifikasyon skoru hesaplama hatası: {e}")
            return 50  # Varsayılan değer
    
    def calculate_period_return(self, days):
        """Belirli bir dönemdeki getiri - Güvenli versiyon"""
        try:
            if days <= 0:
                return 0
                
            total_return = self.calculate_total_return()
            
            # Yıllık getiriyi varsayalım, döneme bölelim (basitleştirilmiş)
            period_return = (total_return / 365) * days
            
            return period_return
        except Exception as e:
            print(f"Dönem getirisi hesaplama hatası: {e}")
            if days <= 30:
                return 1.5  # Son 1 ay
            elif days <= 90:
                return 4.5  # Son 3 ay
            elif days <= 180:
                return 9.0  # Son 6 ay
            else:
                return 15.0  # Son 1 yıl
    
    def get_portfolio_composition(self):
        """Portföy bileşimi detayları - Güvenli versiyon"""
        try:
            if not self.portfolio:
                return []
                
            total_value = sum(h["adet"] * h.get("guncel_fiyat", h["ort_maliyet"]) for h in self.portfolio)
            
            composition = []
            
            for stock in self.portfolio:
                value = stock["adet"] * stock.get("guncel_fiyat", stock["ort_maliyet"])
                weight = (value / total_value * 100) if total_value > 0 else 0
                
                composition.append({
                    'symbol': stock['sembol'],
                    'value': value,
                    'weight': weight,
                    'shares': stock['adet'],
                    'avg_cost': stock['ort_maliyet'],
                    'current_price': stock.get('guncel_fiyat', stock['ort_maliyet'])
                })
            
            return sorted(composition, key=lambda x: x['value'], reverse=True)
        except Exception as e:
            print(f"Portföy kompozisyonu hesaplama hatası: {e}")
            return []