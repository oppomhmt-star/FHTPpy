# pages/auth_page.py
"""
Giriş ve Kayıt Sayfası
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
from auth_service import AuthService
from database import Database
from credentials_manager import CredentialsManager
from config import COLORS, FONT_SIZES

class AuthPage:
    def __init__(self, parent, auth_service: AuthService):
        self.parent = parent
        self.auth = auth_service
        self.frame = None
        self.current_mode = "login"  # login or register
        self.credentials_manager = CredentialsManager()
    
    def create(self):
        """Auth sayfası oluştur"""
        self.frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.frame.pack(fill="both", expand=True)
        
        # Ana container (ortalanmış)
        container = ctk.CTkFrame(self.frame, fg_color="transparent")
        container.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Başlık
        title = ctk.CTkLabel(
            container,
            text="📊 Hisse Senedi Takip",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        title.pack(pady=(0, 5))
        
        subtitle = ctk.CTkLabel(
            container,
            text="Portföy Yönetimi Platformu",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 40))
        
        # İçerik frame
        content_frame = ctk.CTkFrame(container, fg_color="transparent")
        content_frame.pack(fill="x", padx=50)
        
        if self.current_mode == "login":
            self._create_login_form(content_frame)
        else:
            self._create_register_form(content_frame)
    
    def _create_login_form(self, parent):
        """Giriş formu"""
        # Logo
        logo = ctk.CTkLabel(parent, text="🔐 GİRİŞ YAP", font=ctk.CTkFont(size=24, weight="bold"))
        logo.pack(pady=(0, 30))
        
        # Kullanıcı adı
        ctk.CTkLabel(parent, text="Kullanıcı Adı", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 0))
        username_entry = ctk.CTkEntry(parent, placeholder_text="kullanıcı adınız", height=40)
        username_entry.pack(fill="x", pady=(5, 15))
        
        # Şifre
        ctk.CTkLabel(parent, text="Şifre", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 0))
        password_entry = ctk.CTkEntry(parent, placeholder_text="şifreniz", show="*", height=40)
        password_entry.pack(fill="x", pady=(5, 20))
        
        # Beni hatırla checkbox
        remember_frame = ctk.CTkFrame(parent, fg_color="transparent")
        remember_frame.pack(fill="x", pady=(0, 20))
        
        remember_var = ctk.BooleanVar(value=False)
        remember_checkbox = ctk.CTkCheckBox(
            remember_frame,
            text="Beni hatırla",
            variable=remember_var,
            font=ctk.CTkFont(size=11),
            onvalue=True,
            offvalue=False
        )
        remember_checkbox.pack(anchor="w")
        
        # Giriş butonu
        def login_clicked():
            username = username_entry.get().strip()
            password = password_entry.get()
            
            if not username or not password:
                messagebox.showerror("Hata", "Lütfen tüm alanları doldurun")
                return
            
            # Asenkron giriş
            def login_thread():
                result = self.auth.login_user(username, password)
                if result['success'] and remember_var.get():
                    self.credentials_manager.save_credentials(username, password)
                self.parent.after(0, lambda: self._handle_login_result(result))
            
            threading.Thread(target=login_thread, daemon=True).start()
        
        login_btn = ctk.CTkButton(
            parent,
            text="GİRİŞ YAP",
            command=login_clicked,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["primary"]
        )
        login_btn.pack(fill="x", pady=(20, 10))
        
        # Kaydedilmiş bilgileri yükle
        saved_creds = self.credentials_manager.load_credentials()
        if saved_creds:
            username_entry.insert(0, saved_creds['username'])
            password_entry.insert(0, saved_creds['password'])
            remember_checkbox.select()
        
        # Kayıt linki
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=10)
        
        label = ctk.CTkLabel(frame, text="Henüz hesabınız yok mu?", text_color="gray", font=ctk.CTkFont(size=11))
        label.pack(side="left")
        
        register_btn = ctk.CTkButton(
            frame,
            text="Şimdi Kaydolun",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["primary"],
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            command=self._switch_to_register
        )
        register_btn.pack(side="left", padx=(5, 0))
    
    def _create_register_form(self, parent):
        """Kayıt formu"""
        # Logo
        logo = ctk.CTkLabel(parent, text="📝 KAYDOL", font=ctk.CTkFont(size=24, weight="bold"))
        logo.pack(pady=(0, 30))
        
        # Kullanıcı adı
        ctk.CTkLabel(parent, text="Kullanıcı Adı", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 0))
        username_entry = ctk.CTkEntry(parent, placeholder_text="En az 3 karakter", height=40)
        username_entry.pack(fill="x", pady=(5, 15))
        
        # Email
        ctk.CTkLabel(parent, text="Email", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 0))
        email_entry = ctk.CTkEntry(parent, placeholder_text="ornek@email.com", height=40)
        email_entry.pack(fill="x", pady=(5, 15))
        
        # Şifre
        ctk.CTkLabel(parent, text="Şifre", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 0))
        password_entry = ctk.CTkEntry(parent, placeholder_text="En az 6 karakter", show="*", height=40)
        password_entry.pack(fill="x", pady=(5, 15))
        
        # Şifre tekrarı
        ctk.CTkLabel(parent, text="Şifre (Tekrarı)", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 0))
        password_repeat_entry = ctk.CTkEntry(parent, placeholder_text="Şifrenizi tekrar girin", show="*", height=40)
        password_repeat_entry.pack(fill="x", pady=(5, 20))
        
        # Kayıt butonu
        def register_clicked():
            username = username_entry.get().strip()
            email = email_entry.get().strip()
            password = password_entry.get()
            password_repeat = password_repeat_entry.get()
            
            if not username or not email or not password:
                messagebox.showerror("Hata", "Lütfen tüm alanları doldurun")
                return
            
            if password != password_repeat:
                messagebox.showerror("Hata", "Şifreler uyuşmuyor")
                return
            
            # Asenkron kayıt
            def register_thread():
                result = self.auth.register_user(username, email, password)
                self.parent.after(0, lambda: self._handle_register_result(result))
            
            threading.Thread(target=register_thread, daemon=True).start()
        
        register_btn = ctk.CTkButton(
            parent,
            text="KAYDOL",
            command=register_clicked,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=COLORS["success"]
        )
        register_btn.pack(fill="x", pady=(20, 10))
        
        # Giriş linki
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=10)
        
        label = ctk.CTkLabel(frame, text="Zaten hesabınız var mı?", text_color="gray", font=ctk.CTkFont(size=11))
        label.pack(side="left")
        
        login_btn = ctk.CTkButton(
            frame,
            text="Giriş Yapın",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["primary"],
            fg_color="transparent",
            hover_color=("gray70", "gray30"),
            command=self._switch_to_login
        )
        login_btn.pack(side="left", padx=(5, 0))
    
    def _switch_to_login(self):
        """Giriş sayfasına geç"""
        self.current_mode = "login"
        self.frame.destroy()
        self.create()
    
    def _switch_to_register(self):
        """Kayıt sayfasına geç"""
        self.current_mode = "register"
        self.frame.destroy()
        self.create()
    
    def _handle_login_result(self, result):
        """Giriş sonucunu işle"""
        if result['success']:
            messagebox.showinfo("Başarılı", "Giriş başarılı! Uygulama yüklenecek...")
            # Callback çağır (eğer varsa)
            if hasattr(self, 'on_login_success'):
                self.on_login_success(result)
        else:
            messagebox.showerror("Giriş Hatası", result.get('error', 'Bilinmeyen hata'))
    
    def _handle_register_result(self, result):
        """Kayıt sonucunu işle"""
        if result['success']:
            messagebox.showinfo("Başarılı", "Kayıt başarılı! Lütfen giriş yapın.")
            self._switch_to_login()
        else:
            messagebox.showerror("Kayıt Hatası", result.get('error', 'Bilinmeyen hata'))
