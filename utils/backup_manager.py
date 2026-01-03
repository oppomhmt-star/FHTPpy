# utils/backup_manager.py

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

class BackupManager:
    """Otomatik yedekleme yöneticisi"""
    
    def __init__(self, db, settings_manager):
        self.db = db
        self.settings = settings_manager
        self.backup_dir = self.settings.get("backup_location", "")
        
        if not self.backup_dir:
            # Varsayılan: uygulama klasörü içinde backups
            self.backup_dir = os.path.join(os.getcwd(), "backups")
        
        # Klasörü oluştur
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, auto=False):
        """Yedek oluştur"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{'auto_' if auto else ''}{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Veritabanı verilerini dışa aktar
            self.db.export_data(backup_path, user_id=1)
            
            # Eski yedekleri temizle (son 10'u tut)
            self.cleanup_old_backups()
            
            # Son yedek tarihini güncelle
            if auto:
                self.settings.mark_backup_done()
            
            return backup_path
        
        except Exception as e:
            print(f"Yedekleme hatası: {e}")
            return None
    
    def restore_backup(self, backup_path):
        """Yedeği geri yükle"""
        try:
            # Mevcut veritabanını yedekle (güvenlik)
            current_backup = os.path.join(self.backup_dir, f"before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            if os.path.exists(self.db.db_name):
                shutil.copy(self.db.db_name, current_backup)
            
            # Geri yükle
            self.db.import_data(backup_path, user_id=1)
            
            return True
        
        except Exception as e:
            print(f"Geri yükleme hatası: {e}")
            return False
    
    def get_backup_list(self):
        """Yedek listesini al"""
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.json'):
                    path = os.path.join(self.backup_dir, file)
                    stat = os.stat(path)
                    backups.append({
                        "name": file,
                        "path": path,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_mtime)
                    })
            
            # Tarihe göre sırala (en yeni önce)
            backups.sort(key=lambda x: x["created"], reverse=True)
            return backups
        
        except Exception as e:
            print(f"Yedek listesi alma hatası: {e}")
            return []
    
    def cleanup_old_backups(self, keep=10):
        """Eski yedekleri temizle"""
        try:
            backups = self.get_backup_list()
            
            # Sadece otomatik yedekleri temizle
            auto_backups = [b for b in backups if "auto_" in b["name"]]
            
            # Son X tanesini tut, diğerlerini sil
            if len(auto_backups) > keep:
                for backup in auto_backups[keep:]:
                    os.remove(backup["path"])
        
        except Exception as e:
            print(f"Yedek temizleme hatası: {e}")
    
    def check_and_auto_backup(self):
        """Otomatik yedekleme kontrolü"""
        if self.settings.backup_needed():
            return self.create_backup(auto=True)
        return None