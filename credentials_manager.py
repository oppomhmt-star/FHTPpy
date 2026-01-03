# credentials_manager.py
"""
Giriş bilgilerini güvenli bir şekilde saklayan servis
"""

import os
import sys
import json
import base64
from cryptography.fernet import Fernet
import hashlib

class CredentialsManager:
    def __init__(self, app_dir=None):
        """Credentials yöneticisini başlat"""
        if app_dir is None:
            # PyInstaller exe modunda: sys.executable'ın dizini
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                app_dir = os.path.dirname(sys.executable)
            else:
                # Normal Python modunda: script'in dizini
                app_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.app_dir = app_dir
        self.creds_file = os.path.join(app_dir, '.credentials')
        
        # Encryption key oluştur (bilgisayar spesifik)
        self.key = self._generate_key()
        self.cipher = Fernet(self.key)
    
    def _generate_key(self):
        """Bilgisayar spesifik bir encryption key oluştur"""
        try:
            import socket
            import getpass
            
            # Bilgisayar + kullanıcı adı kombinasyonundan hash oluştur
            machine_id = f"{socket.gethostname()}:{getpass.getuser()}"
            hash_obj = hashlib.sha256(machine_id.encode())
            hash_hex = hash_obj.hexdigest()
            
            # Fernet için geçerli bir key oluştur
            key_bytes = hash_hex[:32].encode()
            key = base64.urlsafe_b64encode(key_bytes)
            
            # Fernet key uzunluğunu kontrol et (44 karakter olmalı)
            if len(key) < 44:
                key = key + b'=' * (44 - len(key))
            elif len(key) > 44:
                key = key[:44]
            
            return key
        except:
            # Fallback: sabit key
            return b'FjZCMGWINZkD8HfQHjZCMGWINZkD8HfQHjZCMGWINZkD8='
    
    def save_credentials(self, username, password):
        """Giriş bilgilerini kaydet"""
        try:
            data = {
                'username': username,
                'password': password
            }
            
            json_str = json.dumps(data)
            encrypted = self.cipher.encrypt(json_str.encode())
            encrypted_b64 = base64.b64encode(encrypted).decode()
            
            with open(self.creds_file, 'w') as f:
                f.write(encrypted_b64)
            
            return True
        except Exception as e:
            print(f"Credentials kayıt hatası: {e}")
            return False
    
    def load_credentials(self):
        """Kaydedilmiş giriş bilgilerini yükle"""
        try:
            if not os.path.exists(self.creds_file):
                return None
            
            with open(self.creds_file, 'r') as f:
                encrypted_b64 = f.read()
            
            encrypted = base64.b64decode(encrypted_b64)
            decrypted = self.cipher.decrypt(encrypted)
            data = json.loads(decrypted.decode())
            
            return {
                'username': data.get('username', ''),
                'password': data.get('password', '')
            }
        except Exception as e:
            print(f"Credentials yükleme hatası: {e}")
            return None
    
    def clear_credentials(self):
        """Kaydedilmiş bilgileri sil"""
        try:
            if os.path.exists(self.creds_file):
                os.remove(self.creds_file)
            return True
        except Exception as e:
            print(f"Credentials silme hatası: {e}")
            return False
    
    def has_saved_credentials(self):
        """Kaydedilmiş bilgiler var mı"""
        return os.path.exists(self.creds_file)
