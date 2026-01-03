# utils/rate_limiter.py

import time
from functools import wraps
from typing import Callable

class RateLimiter:
    """Fonksiyon çağrı hızını sınırlar"""
    
    def __init__(self, max_calls: int, period: int):
        """
        Args:
            max_calls: Dönem içinde maksimum çağrı sayısı
            period: Süre (saniye)
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            
            # Eski çağrıları temizle
            self.calls = [call_time for call_time in self.calls if now - call_time < self.period]
            
            # Limit kontrolü
            if len(self.calls) >= self.max_calls:
                wait_time = self.period - (now - self.calls[0])
                raise RateLimitException(
                    f"Çok fazla istek! {wait_time:.1f} saniye sonra tekrar deneyin."
                )
            
            # Çağrıyı kaydet ve fonksiyonu çalıştır
            self.calls.append(now)
            return func(*args, **kwargs)
        
        return wrapper


class RateLimitException(Exception):
    """Rate limit aşıldığında fırlatılır"""
    pass