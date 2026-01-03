# utils/secure_settings.py

import os
import base64
from cryptography.fernet import Fernet

class SecureSettings:
    """API anahtarları ve hassas verileri şifreleyerek saklar"""
    
    def __init__(self, key_file=".settings_key"):
        self.key_file = os.path.join(os.getcwd(), key_file)
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self):
        """Machine-specific encryption key oluştur veya yükle"""
        if os.path.exists(self.key_file):
            try:
                with open(self.key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"Key okuma hatası: {e}")
        
        # Yeni key oluştur
        key = Fernet.generate_key()
        try:
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Dosyayı gizle (Windows)
            if os.name == 'nt':
                try:
                    import ctypes
                    ctypes.windll.kernel32.SetFileAttributesW(self.key_file, 2)
                except:
                    pass
        except Exception as e:
            print(f"Key kaydetme hatası: {e}")
        
        return key
    
    def encrypt(self, value):
        """Değeri şifrele"""
        if not value or value == "":
            return ""
        
        try:
            encrypted = self.cipher.encrypt(str(value).encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            print(f"Şifreleme hatası: {e}")
            return value
    
    def decrypt(self, encrypted_value):
        """Şifreli değeri çöz"""
        if not encrypted_value or encrypted_value == "":
            return ""
        
        try:
            decoded = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            # Zaten şifrelenmemiş olabilir
            return encrypted_value
    
    def encrypt_api_key(self, api_key):
        """API anahtarını şifrele"""
        return self.encrypt(api_key)
    
    def decrypt_api_key(self, encrypted_key):
        """API anahtarını çöz"""
        return self.decrypt(encrypted_key)
    
    def is_encrypted(self, value):
        """Değerin şifreli olup olmadığını kontrol et"""
        if not value:
            return False
        try:
            decoded = base64.urlsafe_b64decode(value.encode())
            self.cipher.decrypt(decoded)
            return True
        except:
            return False