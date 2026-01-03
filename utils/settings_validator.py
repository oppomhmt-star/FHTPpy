# utils/settings_validator.py

import re
from typing import Tuple, Any

class SettingsValidator:
    """Ayar değerlerini doğrular"""
    
    @staticmethod
    def validate_commission_rate(value: str) -> Tuple[bool, Any]:
        """
        Komisyon oranı validasyonu
        Kullanıcı yüzde olarak girer (örn: 0.04 = %0.04)
        Sistem decimal olarak saklar (0.0004 = 0.04%)
        """
        try:
            # Virgülü noktaya çevir
            clean_value = value.replace(',', '.').strip()
            rate_percent = float(clean_value)
            
            # 0-100 arasında olmalı
            if not 0 <= rate_percent <= 100:
                return False, "Komisyon oranı 0-100 arasında olmalı"
            
            # Yüzde olarak girildiği için 100'e böl
            actual_rate = rate_percent / 100
            
            return True, actual_rate
            
        except ValueError:
            return False, "Geçersiz sayı formatı"
        except Exception as e:
            return False, f"Doğrulama hatası: {str(e)}"
    
    @staticmethod
    def validate_tax_rate(value: str) -> Tuple[bool, Any]:
        """Vergi oranı validasyonu"""
        try:
            clean_value = value.replace(',', '.').strip()
            rate_percent = float(clean_value)
            
            if not 0 <= rate_percent <= 100:
                return False, "Vergi oranı 0-100 arasında olmalı"
            
            actual_rate = rate_percent / 100
            return True, actual_rate
            
        except ValueError:
            return False, "Geçersiz sayı formatı"
        except Exception as e:
            return False, f"Doğrulama hatası: {str(e)}"
    
    @staticmethod
    def validate_api_key(value: str, provider: str) -> Tuple[bool, Any]:
        """API anahtarı validasyonu"""
        if not value or value.strip() == "":
            return False, "API anahtarı boş olamaz"
        
        value = value.strip()
        
        # Minimum uzunluklar
        min_lengths = {
            "iex_cloud": 32,
            "finnhub": 20,
            "alpha_vantage": 16
        }
        
        min_len = min_lengths.get(provider, 10)
        
        if len(value) < min_len:
            return False, f"API anahtarı en az {min_len} karakter olmalı"
        
        # Sadece alfanumerik ve bazı özel karakterler
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', value):
            return False, "API anahtarı geçersiz karakterler içeriyor"
        
        return True, value
    
    @staticmethod
    def validate_timeout(value: str) -> Tuple[bool, Any]:
        """Timeout değeri validasyonu"""
        try:
            timeout = int(value)
            
            if not 1 <= timeout <= 60:
                return False, "Timeout 1-60 saniye arasında olmalı"
            
            return True, timeout
            
        except ValueError:
            return False, "Geçersiz sayı formatı"
        except Exception as e:
            return False, f"Doğrulama hatası: {str(e)}"
    
    @staticmethod
    def validate_portfolio_target(value: str) -> Tuple[bool, Any]:
        """Portföy hedefi validasyonu"""
        try:
            clean_value = value.replace(',', '').replace('.', '').strip()
            target = float(clean_value)
            
            if target < 0:
                return False, "Portföy hedefi negatif olamaz"
            
            if target > 1_000_000_000:  # 1 milyar
                return False, "Portföy hedefi çok yüksek"
            
            return True, target
            
        except ValueError:
            return False, "Geçersiz sayı formatı"
        except Exception as e:
            return False, f"Doğrulama hatası: {str(e)}"
    
    @staticmethod
    def validate_percentage(value: str, field_name: str = "Değer") -> Tuple[bool, Any]:
        """Genel yüzde validasyonu"""
        try:
            clean_value = value.replace(',', '.').strip()
            percent = float(clean_value)
            
            if not 0 <= percent <= 100:
                return False, f"{field_name} 0-100 arasında olmalı"
            
            return True, percent
            
        except ValueError:
            return False, "Geçersiz sayı formatı"
        except Exception as e:
            return False, f"Doğrulama hatası: {str(e)}"
    
    @staticmethod
    def validate_update_interval(value: int) -> Tuple[bool, Any]:
        """Güncelleme sıklığı validasyonu"""
        valid_intervals = [1, 5, 15, 30, 60]
        
        if value not in valid_intervals:
            return False, f"Geçersiz aralık. Geçerli değerler: {', '.join(map(str, valid_intervals))}"
        
        return True, value