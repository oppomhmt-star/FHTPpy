# utils/sector_mapper.py

import yfinance as yf
from functools import lru_cache

# Statik yedek harita (API çalışmazsa)
FALLBACK_SECTOR_MAP = {
    'THYAO': 'Ulaştırma', 'PGSUS': 'Ulaştırma',
    'AKBNK': 'Finans', 'GARAN': 'Finans', 'ISCTR': 'Finans',
    'EREGL': 'Metal Eşya', 'TUPRS': 'Petrol & Kimya', 'FROTO': 'Metal Eşya',
    'BIMAS': 'Perakende', 'MGROS': 'Perakende',
    'TCELL': 'Telekomünikasyon', 'TTKOM': 'Telekomünikasyon',
    'SAHOL': 'Holding', 'KCHOL': 'Holding',
    'SISE': 'Cam', 'ASELS': 'Teknoloji',
    'KRDMD': 'Perakende', 'KOZAL': 'Madencilik',
    'SODA': 'Kimya', 'PETKM': 'Petrol & Kimya'
}

@lru_cache(maxsize=200)
def get_sector(symbol):
    """
    Hisse senedinin sektörünü döndürür.
    Önce yfinance'den çeker, başarısız olursa statik haritaya bakar.
    """
    try:
        # Yahoo Finance'den çekmeyi dene
        ticker = yf.Ticker(f"{symbol}.IS")
        info = ticker.info
        
        # Farklı olası alan adlarını kontrol et
        sector = info.get('sector') or info.get('sectorDisp') or info.get('industry')
        
        if sector and sector != 'N/A':
            # İngilizce sektör adlarını Türkçeleştir
            sector_translation = {
                'Financial Services': 'Finans',
                'Industrials': 'Sanayi',
                'Basic Materials': 'Temel Malzemeler',
                'Consumer Cyclical': 'Tüketim',
                'Technology': 'Teknoloji',
                'Communication Services': 'Telekomünikasyon',
                'Energy': 'Enerji',
                'Utilities': 'Elektrik & Gaz',
                'Real Estate': 'Gayrimenkul',
                'Healthcare': 'Sağlık',
                'Consumer Defensive': 'Gıda & İçecek'
            }
            
            return sector_translation.get(sector, sector)
    
    except Exception as e:
        print(f"Sektör bilgisi alınamadı ({symbol}): {e}")
    
    # Fallback: Statik haritadan çek
    return FALLBACK_SECTOR_MAP.get(symbol, 'Diğer')

def get_all_sectors(portfolio):
    """Portföydeki tüm hisselerin sektörlerini döndürür"""
    sectors = {}
    
    for stock in portfolio:
        symbol = stock['sembol']
        sector = get_sector(symbol)
        
        if sector not in sectors:
            sectors[sector] = []
        
        sectors[sector].append(stock)
    
    return sectors