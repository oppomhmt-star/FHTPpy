# utils/price_alert_manager.py

import threading
import time
from datetime import datetime
from typing import List, Dict, Optional
from utils.notification_service import NotificationService

class PriceAlertManager:
    """Fiyat alarm sistemi"""
    
    def __init__(self, db, settings_manager=None):
        self.db = db
        self.settings = settings_manager
        self.notifier = NotificationService(settings_manager)
        
        self.active_alerts = {}  # {alert_id: alert_data}
        self.monitoring_thread = None
        self.monitoring_active = False
        
        # DB'den alarmları yükle
        self._load_alerts_from_db()
    
    def _load_alerts_from_db(self):
        """Veritabanından alarmları yükle"""
        try:
            alerts = self.db.get_price_alerts()
            for alert in alerts:
                if alert['active']:
                    self.active_alerts[alert['id']] = alert
        except Exception as e:
            print(f"Alarm yükleme hatası: {e}")
    
    def create_alert(self, symbol: str, target_price: float, 
                    condition: str, note: str = "") -> Optional[int]:
        """
        Yeni alarm oluştur
        
        Args:
            symbol: Hisse sembolü
            target_price: Hedef fiyat
            condition: 'above' (üstüne çıkınca) veya 'below' (altına inince)
            note: Kullanıcı notu
        
        Returns:
            Alert ID veya None (hata durumunda)
        """
        if condition not in ['above', 'below']:
            raise ValueError("Condition 'above' veya 'below' olmalı")
        
        try:
            alert_data = {
                'symbol': symbol.upper(),
                'target_price': float(target_price),
                'condition': condition,
                'note': note,
                'created_at': datetime.now(),
                'active': True,
                'triggered': False,
                'triggered_at': None
            }
            
            # DB'ye kaydet
            alert_id = self.db.add_price_alert(alert_data)
            
            if alert_id:
                alert_data['id'] = alert_id
                self.active_alerts[alert_id] = alert_data
                
                print(f"✓ Alarm oluşturuldu: {symbol} - {condition} {target_price}")
                
                return alert_id
            
        except Exception as e:
            print(f"Alarm oluşturma hatası: {e}")
            return None
    
    def delete_alert(self, alert_id: int) -> bool:
        """Alarm sil"""
        try:
            # DB'den sil
            if self.db.delete_price_alert(alert_id):
                # Aktif listeden kaldır
                if alert_id in self.active_alerts:
                    del self.active_alerts[alert_id]
                return True
        except Exception as e:
            print(f"Alarm silme hatası: {e}")
        
        return False
    
    def update_alert(self, alert_id: int, **kwargs) -> bool:
        """Alarm güncelle"""
        try:
            # DB'de güncelle
            if self.db.update_price_alert(alert_id, **kwargs):
                # Aktif listede güncelle
                if alert_id in self.active_alerts:
                    self.active_alerts[alert_id].update(kwargs)
                return True
        except Exception as e:
            print(f"Alarm güncelleme hatası: {e}")
        
        return False
    
    def toggle_alert(self, alert_id: int) -> bool:
        """Alarmı aç/kapat"""
        try:
            alert = self.active_alerts.get(alert_id) or self.db.get_price_alert(alert_id)
            if not alert:
                return False
            
            new_state = not alert.get('active', False)
            
            if self.update_alert(alert_id, active=new_state):
                if new_state:
                    # Tekrar aktif et
                    self.active_alerts[alert_id] = alert
                    self.active_alerts[alert_id]['active'] = True
                else:
                    # Pasif yap
                    if alert_id in self.active_alerts:
                        del self.active_alerts[alert_id]
                
                return True
        except Exception as e:
            print(f"Alarm toggle hatası: {e}")
        
        return False
    
    def get_all_alerts(self) -> List[Dict]:
        """Tüm alarmları getir"""
        try:
            return self.db.get_price_alerts()
        except Exception as e:
            print(f"Alarm listesi alma hatası: {e}")
            return []
    
    def get_active_alerts(self) -> List[Dict]:
        """Aktif alarmları getir"""
        return list(self.active_alerts.values())
    
    def check_alerts(self, price_data: Dict[str, float]):
        """
        Alarmları kontrol et
        
        Args:
            price_data: {symbol: current_price} dictionary
        """
        triggered_alerts = []
        
        for alert_id, alert in list(self.active_alerts.items()):
            symbol = alert['symbol']
            current_price = price_data.get(symbol)
            
            if current_price is None:
                continue
            
            target = alert['target_price']
            condition = alert['condition']
            
            # Tetikleme kontrolü
            triggered = False
            
            if condition == 'above' and current_price >= target:
                triggered = True
                message = f"{symbol} hedef fiyata ulaştı!\n\n" \
                         f"Hedef: {target:.2f} ₺\n" \
                         f"Güncel: {current_price:.2f} ₺"
                icon = "success"
            
            elif condition == 'below' and current_price <= target:
                triggered = True
                message = f"{symbol} hedef fiyata düştü!\n\n" \
                         f"Hedef: {target:.2f} ₺\n" \
                         f"Güncel: {current_price:.2f} ₺"
                icon = "warning"
            
            if triggered:
                # Bildirimi gönder
                self.notifier.send(
                    title=f"🎯 Fiyat Alarmı: {symbol}",
                    message=message,
                    icon=icon,
                    sound=True
                )
                
                # Alarmı tetiklenmiş olarak işaretle
                self.update_alert(
                    alert_id,
                    triggered=True,
                    triggered_at=datetime.now(),
                    active=False  # Otomatik devre dışı bırak
                )
                
                # Aktif listeden kaldır
                del self.active_alerts[alert_id]
                
                triggered_alerts.append(alert)
                
                print(f"⚡ Alarm tetiklendi: {symbol} @ {current_price:.2f}")
        
        return triggered_alerts
    
    def start_monitoring(self, price_provider, interval=10):
        """
        Alarm izlemeyi başlat
        
        Args:
            price_provider: Fiyat sağlayıcı (get_current_prices() metodu olmalı)
            interval: Kontrol sıklığı (saniye)
        """
        if self.monitoring_active:
            print("⚠ Alarm izleme zaten aktif")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(price_provider, interval),
            daemon=True
        )
        self.monitoring_thread.start()
        
        print(f"✓ Alarm izleme başlatıldı (interval: {interval}s)")
    
    def stop_monitoring(self):
        """Alarm izlemeyi durdur"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        print("⏹ Alarm izleme durduruldu")
    
    def _monitoring_loop(self, price_provider, interval):
        """İzleme döngüsü (arka planda çalışır)"""
        while self.monitoring_active:
            try:
                if not self.active_alerts:
                    # Aktif alarm yoksa bekle
                    time.sleep(interval)
                    continue
                
                # Fiyatları al
                symbols = [alert['symbol'] for alert in self.active_alerts.values()]
                price_data = price_provider.get_current_prices(symbols)
                
                # Alarmları kontrol et
                self.check_alerts(price_data)
                
            except Exception as e:
                print(f"İzleme döngüsü hatası: {e}")
            
            # Bekle
            time.sleep(interval)