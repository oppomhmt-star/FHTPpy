# config.py

"""
Uygulama yapılandırma ayarları
"""

# Endeks sembolleri
INDICES = {
    "XU100": "XU100.IS",
    "NASDAQ": "^IXIC",
    "S&P 500": "^GSPC"
}

# Döviz ve Altın sembolleri
CURRENCIES = {
    "DOLAR": "TRY=X",
    "EURO": "EURTRY=X",
    "ALTIN": "GC=F",
    "BTC": "BTC-USD"
}

# Varsayılan ayarlar (GENİŞLETİLMİŞ)
DEFAULT_SETTINGS = {
    # Genel
    "start_page": "dashboard",
    "language": "tr",
    "date_format": "DD/MM/YYYY",
    "currency_format": "₺",
    "number_format": "1.234,56",
    
    # Görünüm
    "tema": "dark",
    "color_scheme": "#3b82f6",
    "font_size": "normal",
    "chart_animations": True,
    "compact_mode": False,
    "sidebar_width": 200,
    
    # Veri ve Güncelleme
    "otomatik_guncelleme": True,
    "guncelleme_suresi": 5,
    "update_after_hours": False,
    "cache_duration": 15,
    "api_timeout": 10,
    
    # Bildirimler
    "bildirimler": True,
    "notifications_enabled": True,
    "desktop_notifications": True,
    "sound_alerts": True,
    "price_target_alert": True,
    "price_change_threshold": 5,
    "daily_change_threshold": 3,
    
    # Portföy
    "commission_rate": 0.04,  # %0.04 (on binde 4)
    "tax_rate": 0,
    "portfolio_target": 100000,
    "risk_tolerance": "orta",
    "investment_period": "orta",
    
    # Grafikler
    "default_chart_type": "line",
    "default_time_range": "1y",
    "show_sma": True,
    "show_bollinger": False,
    "show_volume": True,
    "increase_color": "green",
    "decrease_color": "red",
    
    # Güvenlik
    "pin_lock": False,
    "pin_code": "",
    "auto_lock_time": 15,
    "hide_sensitive_data": False,
    "block_screenshot": False,
    
    # Yedekleme
    "auto_backup": True,
    "backup_frequency": "weekly",
    "backup_location": "",
    "last_backup": "",
    
    # Gelişmiş
    "debug_mode": False,
    "performance_mode": False,
    "log_level": "error",
    
    # API Sağlayıcıları
    "api_provider": "yfinance",  # yfinance, finnhub, alpha_vantage, iex
    "finnhub_api_key": "",
    "alpha_vantage_api_key": "",
    "iex_api_key": "",
    
    # Cloud Sync
    "cloud_sync_enabled": False,
    "cloud_url": "http://localhost:5000",
    "cloud_auto_sync": True,
    "cloud_sync_interval": 300,  # 5 dakika
    
    # Eski ayarlar (geriye uyumluluk)
    "doviz_kuru": 34.50,
    "dil": "tr",
    "currency_symbols": ["DOLAR", "EURO", "ALTIN", "BTC"],
    "gosterilecek_hisseler": 10,
    
     # Klavye kısayolları
    "keyboard_shortcuts": {
        "new_stock": "Control-n",
        "backup": "Control-s",
        "search": "Control-f",
        "refresh_prices": "Control-r",
        "refresh_page": "F5",
        "quit_app": "Control-q",
        "page_dashboard": "Control-Key-1",
        "page_portfolio": "Control-Key-2",
        "page_transactions": "Control-Key-3",
        "page_settings": "Control-Key-4",
        "help": "F1",
        "escape": "Escape"
    },
        
}

# Renkler
COLORS = {
    "primary": "#3b82f6",
    "success": "#10b981",
    "danger": "#ef4444",
    "warning": "#f59e0b",
    "purple": "#8b5cf6",
    "pink": "#ec4899",
    "teal": "#14b8a6",
    "orange": "#f97316",
    "cyan": "#06b6d4",
    "lime": "#84cc16"
}

# Font boyutları
FONT_SIZES = {
    "small": {"normal": 11, "title": 16, "header": 24},
    "normal": {"normal": 13, "title": 20, "header": 32},
    "large": {"normal": 15, "title": 24, "header": 36},
    "xlarge": {"normal": 17, "title": 28, "header": 40}
}

# Tema renkleri
THEME_COLORS = {
    "blue": "#3b82f6",
    "purple": "#8b5cf6",
    "green": "#10b981",
    "orange": "#f97316",
    "pink": "#ec4899",
    "teal": "#14b8a6"
}

# Grafik renkleri (tema bazlı)
CHART_COLORS = {
    "dark": {
        "bg": "#1a1a1a",
        "text": "white",
        "grid": "gray"
    },
    "light": {
        "bg": "#f0f0f0",
        "text": "black",
        "grid": "lightgray"
    }
}