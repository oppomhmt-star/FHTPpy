    def create_advanced_settings(self):
        """Gelişmiş ayarlar"""
        # API Sağlayıcı Ayarları
        self.create_setting_group("API Sağlayıcı Seçimi")
        
        provider_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        provider_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(provider_frame, text="Tercih Edilen API Sağlayıcısı:", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        ctk.CTkLabel(provider_frame, text="Fiyat verilerini hangi kaynaktan alınacağını seçin", 
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack(anchor="w", pady=(0, 5))
        
        provider_combo_frame = ctk.CTkFrame(provider_frame, fg_color="transparent")
        provider_combo_frame.pack(fill="x", pady=(5, 0))
        
        provider_var = ctk.StringVar(value=self.temp_settings.get("api_provider", "tefas"))
        providers_display = ["TEFAS", "Yahoo Finance", "Advanced API"]
        providers_values = ["tefas", "yfinance", "advanced_api"]
        
        try:
            default_idx = providers_values.index(provider_var.get())
            default_display = providers_display[default_idx]
        except:
            default_display = providers_display[0]
        
        provider_var.set(default_display)
        combo = ctk.CTkComboBox(provider_combo_frame, values=providers_display, variable=provider_var, width=250)
        combo.pack(side="left", padx=(0, 10))
        
        self.settings_widgets["api_provider"] = {
            "var": provider_var,
            "values": providers_values,
            "display_values": providers_display
        }
        
        # API Anahtarları
        self.create_setting_group("API Anahtarları")
        
        ctk.CTkLabel(self.settings_container, text="TEFAS API", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        
        self.create_entry_setting(
            "TEFAS Anahtarı",
            "tefas_api_key",
            self.temp_settings.get("tefas_api_key", ""),
            "TEFAS (Türkiye Elektronik Fon Bilgi Sistemi) API anahtarı"
        )
        
        ctk.CTkLabel(self.settings_container, text="Yahoo Finance API", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        
        self.create_entry_setting(
            "YFinance Anahtarı",
            "yfinance_api_key",
            self.temp_settings.get("yfinance_api_key", ""),
            "Yahoo Finance API erişim anahtarı (opsiyonel)"
        )
        
        ctk.CTkLabel(self.settings_container, text="Diğer API Sağlayıcıları", 
                    font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 5))
        
        self.create_entry_setting(
            "Advanced API Anahtarı",
            "advanced_api_key",
            self.temp_settings.get("advanced_api_key", ""),
            "Advanced API servisine erişim anahtarı"
        )
        
        self.create_entry_setting(
            "Hisse API Anahtarı",
            "hisse_api_key",
            self.temp_settings.get("hisse_api_key", ""),
            "Hisse takip API anahtarı"
        )
        
        self.create_entry_setting(
            "Finnhub API Anahtarı",
            "finnhub_api_key",
            self.temp_settings.get("finnhub_api_key", ""),
            "Finnhub API anahtarı"
        )
        
        self.create_entry_setting(
            "Alpha Vantage API Anahtarı",
            "alpha_vantage_api_key",
            self.temp_settings.get("alpha_vantage_api_key", ""),
            "Alpha Vantage API anahtarı"
        )
        
        # API Doğrulama
        self.create_setting_group("API Doğrulama")
        
        validation_frame = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        validation_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(validation_frame, text="API Anahtarlarını Doğrula", 
                    font=ctk.CTkFont(size=14)).pack(anchor="w")
        
        ctk.CTkLabel(validation_frame, text="Girilen API anahtarlarının geçerli olup olmadığını kontrol et", 
                    font=ctk.CTkFont(size=11),
                    text_color=("gray50", "gray70")).pack(anchor="w", pady=(0, 10))
        
        btn_frame = ctk.CTkFrame(validation_frame, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        ctk.CTkButton(btn_frame, text="✓ Tüm API'leri Test Et",
                     command=self.validate_all_apis, width=200, height=40,
                     fg_color=COLORS["success"]).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(btn_frame, text="🔄 Seçili API'yi Test Et",
                     command=self.validate_selected_api, width=200, height=40,
                     fg_color=COLORS["primary"]).pack(side="left")
        
        # Veri Yönetimi
        self.create_setting_group("Veri Yönetimi")
        
        data_buttons = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        data_buttons.pack(fill="x", pady=10)
        
        ctk.CTkButton(data_buttons, text="📤 Tüm Veriyi Dışa Aktar",
                     command=self.export_data, width=180, height=40).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(data_buttons, text="📥 Veriyi İçe Aktar",
                     command=self.import_data, width=180, height=40).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(data_buttons, text="🗑️ Tüm Verileri Sil",
                     command=self.clear_all_data, width=180, height=40,
                     fg_color=COLORS["danger"]).pack(side="left")
        
        self.create_setting_group("Ayar Yönetimi")
        
        settings_buttons = ctk.CTkFrame(self.settings_container, fg_color="transparent")
        settings_buttons.pack(fill="x", pady=10)
        
        ctk.CTkButton(settings_buttons, text="📤 Ayarları Dışa Aktar",
                     command=self.export_settings, width=180, height=40).pack(side="left", padx=(0, 10))
        
        ctk.CTkButton(settings_buttons, text="📥 Ayarları İçe Aktar",
                     command=self.import_settings, width=180, height=40).pack(side="left")
    
    def validate_all_apis(self):
        """Tüm API anahtarlarını test et"""
        try:
            # Test sonuçlarını göster
            showinfo("Bilgi", "API anahtarları kontrol ediliyor...")
            # Implement actual validation logic
        except Exception as e:
            showerror("Hata", f"API doğrulama hatası: {str(e)}")
    
    def validate_selected_api(self):
        """Seçili API'yi test et"""
        try:
            # Test sonuçlarını göster
            showinfo("Bilgi", "Seçili API kontrol ediliyor...")
            # Implement actual validation logic
        except Exception as e:
            showerror("Hata", f"API doğrulama hatası: {str(e)}")
