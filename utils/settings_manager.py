# utils/settings_manager.py

import os
import json
from datetime import datetime
from config import DEFAULT_SETTINGS, FONT_SIZES, THEME_COLORS

class SettingsManager:
    """Ayarları yönet ve uygula"""
    
    def __init__(self, db):
        self.db = db
        self.settings = db.get_settings()
    
    def get(self, key, default=None):
        """Ayar değeri al"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Ayar değeri kaydet"""
        self.settings[key] = value
        self.db.update_settings(self.settings)
    
    def update(self, settings_dict):
        """Toplu güncelleme"""
        self.settings.update(settings_dict)
        self.db.update_settings(self.settings)
    
    def reset_to_defaults(self):
        """Varsayılanlara sıfırla"""
        self.settings = DEFAULT_SETTINGS.copy()
        self.db.update_settings(self.settings)
    
    def get_font_size(self, type="normal"):
        """Font boyutunu al"""
        size_key = self.settings.get("font_size", "normal")
        sizes = FONT_SIZES.get(size_key, FONT_SIZES["normal"])
        return sizes.get(type, 13)
    
    def get_theme_color(self):
        """Tema rengini al"""
        color_key = self.settings.get("color_scheme", "#3b82f6")
        return color_key
    
    def should_auto_update(self):
        """Otomatik güncelleme aktif mi?"""
        value = self.settings.get("otomatik_guncelleme", True)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        return bool(value)
    
    def get_update_interval(self):
        """Güncelleme aralığı (saniye)"""
        minutes = self.settings.get("guncelleme_suresi", 5)
        
        try:
            minutes = int(minutes)
        except (ValueError, TypeError):
            minutes = 5
        
        if minutes < 1:
            minutes = 1
        elif minutes > 60:
            minutes = 60
        
        return minutes * 60
    
    def is_notifications_enabled(self):
        """Bildirimler aktif mi?"""
        value = self.settings.get("notifications_enabled", True)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes', 'on']
        return bool(value)
    
    def should_show_sensitive_data(self):
        """Hassas veriler gösterilsin mi?"""
        value = self.settings.get("hide_sensitive_data", False)
        hide = bool(value)
        return not hide
    
    def get_commission_rate(self):
        """Komisyon oranı (ondalık)"""
        rate = self.settings.get("commission_rate", 0.04)
        
        try:
            if isinstance(rate, str):
                rate = rate.replace(',', '.')
            rate = float(rate)
        except (ValueError, TypeError):
            rate = 0.04
        
        return rate / 100
    
    def get_tax_rate(self):
        """Vergi oranı (ondalık)"""
        rate = self.settings.get("tax_rate", 0)
        try:
            if isinstance(rate, str):
                rate = rate.replace(',', '.')
            rate = float(rate)
        except (ValueError, TypeError):
            rate = 0
        return rate / 100
    
    def backup_needed(self):
        """Yedekleme gerekli mi?"""
        auto_backup = self.settings.get("auto_backup", True)
        
        if isinstance(auto_backup, str):
            auto_backup = auto_backup.lower() in ['true', '1', 'yes', 'on']
        
        if not auto_backup:
            return False
        
        last_backup = self.settings.get("last_backup", "")
        if not last_backup:
            return True
        
        try:
            last = datetime.fromisoformat(last_backup)
            now = datetime.now()
            
            frequency = self.settings.get("backup_frequency", "weekly")
            
            if frequency == "daily":
                return (now - last).days >= 1
            elif frequency == "weekly":
                return (now - last).days >= 7
            elif frequency == "monthly":
                return (now - last).days >= 30
        except Exception as e:
            print(f"Yedekleme kontrolü hatası: {e}")
            return True
        
        return False
    
    def mark_backup_done(self):
        """Yedekleme yapıldığını işaretle"""
        self.set("last_backup", datetime.now().isoformat())
    
    def export_settings(self, filename):
        """Ayarları dışa aktar"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"Ayar dışa aktarma hatası: {e}")
            return False
    
    def import_settings(self, filename):
        """Ayarları içe aktar"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported = json.load(f)
                self.settings.update(imported)
                self.db.update_settings(self.settings)
            return True
        except Exception as e:
            print(f"Ayar içe aktarma hatası: {e}")
            return False