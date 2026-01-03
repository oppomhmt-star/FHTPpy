# ui_utils.py (Düzeltilmiş Versiyon)

import customtkinter as ctk

class CustomMessagebox(ctk.CTkToplevel):
    def __init__(self, title="Bildirim", message="Mesaj", icon="info", option_type="ok"):
        super().__init__()

        self.title(title)
        
        # <<< DÜZELTME 1: Değişkenleri widget'lar oluşturulmadan önce ata >>>
        self._message = message
        self._icon = icon
        self._option_type = option_type
        self._result = None

        self.lift()
        self.attributes("-topmost", True)
        self.grab_set()
        
        # <<< DÜZELTME 2: resizable doğru kullanımı >>>
        self.resizable(False, False)

        self._create_widgets()
        self._center_window()

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self, corner_radius=15)
        main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        main_frame.grid_columnconfigure(1, weight=1)

        # İkon
        icon_text = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "question": "❓"}.get(self._icon, "•")
        icon_label = ctk.CTkLabel(main_frame, text=icon_text, font=ctk.CTkFont(size=48))
        icon_label.grid(row=0, column=0, rowspan=2, padx=20, pady=20)

        # Mesaj
        message_label = ctk.CTkLabel(main_frame, text=self._message, font=ctk.CTkFont(size=14), wraplength=300, justify="left")
        message_label.grid(row=0, column=1, columnspan=2, padx=20, pady=20, sticky="ew")

        # Butonlar
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.grid(row=1, column=1, columnspan=2, padx=20, pady=(0, 20), sticky="e")

        if self._option_type == "ok":
            ok_button = ctk.CTkButton(button_frame, text="Tamam", command=self._ok_event, width=100, height=35)
            ok_button.pack(padx=5)
            self.bind("<Return>", self._ok_event)
            ok_button.focus() # Butona focus yap
        
        elif self._option_type == "yesno":
            yes_button = ctk.CTkButton(button_frame, text="Evet", command=self._yes_event, width=100, height=35)
            yes_button.pack(side="left", padx=5)
            
            no_button = ctk.CTkButton(button_frame, text="Hayır", command=self._no_event, width=100, height=35, fg_color="#E53935", hover_color="#C62828")
            no_button.pack(side="left", padx=5)
            
            self.bind("<Return>", self._yes_event)
            yes_button.focus() # Evet butonuna focus yap

    def _ok_event(self, event=None):
        self._result = True
        self.grab_release()
        self.destroy()

    def _yes_event(self, event=None):
        self._result = True
        self.grab_release()
        self.destroy()

    def _no_event(self, event=None):
        self._result = False
        self.grab_release()
        self.destroy()

    def _center_window(self):
        """Pencereyi ekranın ortasında konumlandır"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        self.geometry(f"+{x}+{y}")

    def get(self):
        self.master.wait_window(self)
        return self._result

# Yardımcı fonksiyonlar
def showinfo(title, message):
    msg = CustomMessagebox(title, message, icon="info", option_type="ok")
    return msg.get()

def showerror(title, message):
    msg = CustomMessagebox(title, message, icon="error", option_type="ok")
    return msg.get()

def askyesno(title, message):
    msg = CustomMessagebox(title, message, icon="question", option_type="yesno")
    return msg.get()
