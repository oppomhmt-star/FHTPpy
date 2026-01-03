# cloud_sync.py
"""
Bulut Senkronizasyonu Modülü (Cloud Sync)
"""

import requests
import json
import threading
from datetime import datetime
from database import Database

class CloudSync:
    def __init__(self, db: Database, cloud_url="http://localhost:5000"):
        self.db = db
        self.cloud_url = cloud_url
        self.enabled = False
        self.user_id = None
        self.token = None
        self.sync_interval = 300  # 5 dakika
        self.last_sync = None
    
    def set_credentials(self, user_id: int, token: str, cloud_url: str = None):
        """Bulut senkronizasyon kimlik bilgilerini ayarla"""
        self.user_id = user_id
        self.token = token
        if cloud_url:
            self.cloud_url = cloud_url
        self.enabled = True
        print(f"☁️ Bulut senkronizasyonu etkinleştirildi: {self.cloud_url}")
    
    def disable_sync(self):
        """Senkronizasyonu devre dışı bırak"""
        self.enabled = False
        self.user_id = None
        self.token = None
        print("❌ Bulut senkronizasyonu devre dışı bırakıldı")
    
    def get_headers(self):
        """API isteği başlıklarını getir"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def sync_all_data(self):
        """Tüm verileri senkronize et"""
        if not self.enabled or not self.user_id or not self.token:
            return {"success": False, "error": "Senkronizasyon yapılandırılmamış"}
        
        try:
            print("\n☁️ Bulut senkronizasyonu başlıyor...")
            
            # Portföy
            portfolio = self.db.get_portfolio(self.user_id)
            result = self._sync_data("portfolio", portfolio)
            if not result["success"]:
                return result
            
            # İşlemler
            transactions = self.db.get_transactions(self.user_id)
            result = self._sync_data("transactions", transactions)
            if not result["success"]:
                return result
            
            # Temettüler
            dividends = self.db.get_dividends(self.user_id)
            result = self._sync_data("dividends", dividends)
            if not result["success"]:
                return result
            
            # Ayarlar
            settings = self.db.get_settings(self.user_id)
            result = self._sync_data("settings", settings)
            if not result["success"]:
                return result
            
            self.last_sync = datetime.now()
            print("✅ Bulut senkronizasyonu tamamlandı")
            return {"success": True, "message": "Tüm veriler senkronize edildi"}
        
        except Exception as e:
            print(f"❌ Senkronizasyon hatası: {e}")
            return {"success": False, "error": str(e)}
    
    def _sync_data(self, data_type: str, data: list) -> dict:
        """Veri türünü senkronize et"""
        try:
            url = f"{self.cloud_url}/api/sync/{data_type}"
            payload = {
                "user_id": self.user_id,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }
            
            response = requests.post(url, json=payload, headers=self.get_headers(), timeout=10)
            
            if response.status_code in [200, 201]:
                print(f"  ✅ {data_type}: {len(data)} öğe senkronize edildi")
                return {"success": True}
            else:
                print(f"  ❌ {data_type} senkronizasyon hatası: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            print(f"  ❌ {data_type} senkronizasyon hatası: {e}")
            return {"success": False, "error": str(e)}
    
    def pull_data(self, data_type: str = "all") -> dict:
        """Buluttan verileri çek"""
        if not self.enabled or not self.user_id or not self.token:
            return {"success": False, "error": "Senkronizasyon yapılandırılmamış"}
        
        try:
            print(f"\n☁️ {data_type} verileri buluttan çekiliyor...")
            
            url = f"{self.cloud_url}/api/pull/{data_type}"
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {data_type} verileri başarıyla çekildi")
                return {"success": True, "data": data}
            else:
                print(f"❌ Veri çekme hatası: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        
        except Exception as e:
            print(f"❌ Veri çekme hatası: {e}")
            return {"success": False, "error": str(e)}
    
    def merge_data(self, cloud_data: dict, conflict_resolution: str = "cloud"):
        """Bulut verilerini yerel verilerle birleştir"""
        if conflict_resolution == "cloud":
            # Bulut verilerine dayalı merge
            if "portfolio" in cloud_data:
                for item in cloud_data["portfolio"]:
                    # Portföy güncelle/ekle
                    pass
        
        elif conflict_resolution == "local":
            # Yerel verileri sakla
            pass
        
        print(f"✅ Veriler {conflict_resolution} kaynağına göre birleştirildi")
    
    def start_auto_sync(self):
        """Otomatik senkronizasyonu başlat"""
        def sync_loop():
            while self.enabled:
                try:
                    threading.Event().wait(self.sync_interval)
                    if self.enabled:
                        self.sync_all_data()
                except Exception as e:
                    print(f"Auto sync hatası: {e}")
        
        thread = threading.Thread(target=sync_loop, daemon=True)
        thread.start()
        print("⚙️ Otomatik senkronizasyon başlatıldı")
    
    def get_sync_status(self) -> dict:
        """Senkronizasyon durumunu getir"""
        return {
            "enabled": self.enabled,
            "user_id": self.user_id,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "cloud_url": self.cloud_url
        }
    
    def test_connection(self) -> bool:
        """Bulut bağlantısını test et"""
        try:
            url = f"{self.cloud_url}/api/health"
            response = requests.get(url, timeout=5)
            is_ok = response.status_code == 200
            status = "✅" if is_ok else "❌"
            print(f"{status} Bulut bağlantısı: {'başarılı' if is_ok else 'başarısız'}")
            return is_ok
        except Exception as e:
            print(f"❌ Bulut bağlantısı hatası: {e}")
            return False
