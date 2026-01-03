# auth_service.py
"""
Kimlik doğrulama ve JWT Token servisleri
"""

import hashlib
import jwt
import secrets
from datetime import datetime, timedelta
from database import Database

class AuthService:
    def __init__(self, db: Database, secret_key=None):
        self.db = db
        self.secret_key = secret_key or secrets.token_hex(32)
        self.algorithm = "HS256"
        self.token_expiry = 7  # 7 gün
    
    def hash_password(self, password: str) -> str:
        """Şifreyi hash'le (PBKDF2)"""
        salt = secrets.token_hex(32)
        pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}${pwd_hash.hex()}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Şifreyi doğrula"""
        try:
            salt, stored_hash = password_hash.split('$')
            pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return pwd_hash.hex() == stored_hash
        except:
            return False
    
    def register_user(self, username: str, email: str, password: str) -> dict:
        """Yeni kullanıcı kaydı"""
        # Validasyon
        if len(username) < 3:
            return {"success": False, "error": "Kullanıcı adı en az 3 karakter olmalı"}
        if len(password) < 6:
            return {"success": False, "error": "Şifre en az 6 karakter olmalı"}
        if '@' not in email:
            return {"success": False, "error": "Geçersiz email"}
        
        password_hash = self.hash_password(password)
        user_id = self.db.create_user(username, email, password_hash)
        
        if user_id:
            # Varsayılan ayarları yükle
            from config import DEFAULT_SETTINGS
            self.db.update_settings(DEFAULT_SETTINGS.copy(), user_id)
            return {"success": True, "user_id": user_id, "message": "Kayıt başarılı"}
        else:
            return {"success": False, "error": "Bu kullanıcı adı veya email zaten kullanılıyor"}
    
    def login_user(self, username: str, password: str) -> dict:
        """Kullanıcı girişi"""
        user = self.db.get_user(username)
        
        if not user:
            return {"success": False, "error": "Kullanıcı adı veya şifre yanlış"}
        
        if not self.verify_password(password, user['password_hash']):
            return {"success": False, "error": "Kullanıcı adı veya şifre yanlış"}
        
        if not user['is_active']:
            return {"success": False, "error": "Hesap deaktif edilmiş"}
        
        token = self.create_token(user['id'])
        return {
            "success": True,
            "user_id": user['id'],
            "username": user['username'],
            "token": token,
            "message": "Giriş başarılı"
        }
    
    def create_token(self, user_id: int) -> str:
        """JWT token oluştur"""
        payload = {
            'user_id': user_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=self.token_expiry)
        }
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> dict:
        """Token doğrula"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return {"success": True, "user_id": payload['user_id']}
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Token süresi dolmuş"}
        except jwt.InvalidTokenError:
            return {"success": False, "error": "Geçersiz token"}
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> dict:
        """Şifre değiştir"""
        user = self.db.get_user(user_id)
        if not user:
            return {"success": False, "error": "Kullanıcı bulunamadı"}
        
        if not self.verify_password(old_password, user['password_hash']):
            return {"success": False, "error": "Eski şifre yanlış"}
        
        if len(new_password) < 6:
            return {"success": False, "error": "Yeni şifre en az 6 karakter olmalı"}
        
        new_hash = self.hash_password(new_password)
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (new_hash, user_id))
            conn.commit()
        
        return {"success": True, "message": "Şifre başarıyla değiştirildi"}
    
    def get_user_info(self, user_id: int) -> dict:
        """Kullanıcı bilgisi getir"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, email, created_at FROM users WHERE id = ?
            ''', (user_id,))
            user = cursor.fetchone()
            
            if user:
                return dict(user)
        return None
