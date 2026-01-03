# utils/notification_service.py

import os
import sys
import threading
import time
import warnings

# Uyarıları bastır
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

class NotificationService:
    """Cross-platform bildirim servisi - Geliştirilmiş"""
    
    def __init__(self, settings_manager=None):
        self.settings = settings_manager
        self.notification_backend = self._get_backend()
    
    def _get_backend(self):
        """Platform'a göre bildirim backend'i seç"""
        if sys.platform == 'win32':
            # Önce winotify dene (modern, hatasız)
            try:
                return WinotifyNotifier()
            except ImportError:
                pass
            
            # Sonra plyer dene
            try:
                return PlyerNotifier()
            except ImportError:
                pass
            
            # Son çare: win10toast
            try:
                return SafeWin10ToastNotifier()
            except ImportError:
                pass
            
            # En son fallback
            return FallbackNotifier()
        
        elif sys.platform == 'darwin':
            return MacOSNotifier()
        else:
            return LinuxNotifier()
    
    def send(self, title, message, icon="info", sound=True):
        """Bildirim gönder"""
        # Ayarlardan bildirim kontrolü
        if self.settings:
            if not self.settings.settings.get("notifications_enabled", True):
                return False
            sound = self.settings.settings.get("sound_alerts", True)
        
        # Bildirimi gönder
        try:
            success = self.notification_backend.show(title, message, icon)
        except Exception as e:
            print(f"Bildirim hatası: {e}")
            # Fallback'e geç
            success = FallbackNotifier().show(title, message, icon)
        
        # Ses çal
        if success and sound:
            self._play_sound()
        
        return success
    
    def _play_sound(self):
        """Bildirim sesi çal"""
        try:
            if sys.platform == 'win32':
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            elif sys.platform == 'darwin':
                os.system('afplay /System/Library/Sounds/Glass.aiff')
            else:
                os.system('paplay /usr/share/sounds/freedesktop/stereo/message.oga 2>/dev/null')
        except Exception as e:
            print(f"Ses çalma hatası: {e}")


# ========== WİNOTİFY (En İyi Seçenek) ==========

class WinotifyNotifier:
    """Windows Modern Toast - Winotify (Hatasız)"""
    
    def __init__(self):
        try:
            from winotify import Notification, audio
            self.Notification = Notification
            self.audio = audio
            print("✓ Winotify backend yüklendi")
        except ImportError:
            raise ImportError("winotify not available")
    
    def show(self, title, message, icon="info"):
        try:
            toast = self.Notification(
                app_id="Hisse Takip Programı",
                title=title,
                msg=message,
                duration="short"
            )
            
            # Icon ekle
            icon_path = self._get_icon_path()
            if icon_path and os.path.exists(icon_path):
                toast.set_icon(icon_path)
            
            # Ses ayarla
            toast.set_audio(self.audio.Default, loop=False)
            
            # Göster (async)
            toast.show()
            
            return True
        except Exception as e:
            print(f"Winotify hatası: {e}")
            raise
    
    def _get_icon_path(self):
        """Icon path bul"""
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, 'icon.ico')
        elif os.path.exists('icon.ico'):
            return os.path.abspath('icon.ico')
        return None


# ========== PLYER (Cross-platform) ==========

class PlyerNotifier:
    """Plyer - Cross-platform"""
    
    def __init__(self):
        try:
            from plyer import notification
            self.notification = notification
            print("✓ Plyer backend yüklendi")
        except ImportError:
            raise ImportError("plyer not available")
    
    def show(self, title, message, icon="info"):
        try:
            self.notification.notify(
                title=title,
                message=message,
                app_name="Hisse Takip",
                timeout=10
            )
            return True
        except Exception as e:
            print(f"Plyer hatası: {e}")
            raise


# ========== WIN10TOAST (Güvenli Mod) ==========

class SafeWin10ToastNotifier:
    """Win10Toast - Güvenli Mod"""
    
    def __init__(self):
        try:
            from win10toast import ToastNotifier
            self.toaster = ToastNotifier()
            print("✓ Win10Toast backend yüklendi (güvenli mod)")
        except ImportError:
            raise ImportError("win10toast not available")
    
    def show(self, title, message, icon="info"):
        try:
            icon_path = self._get_icon_path()
            
            def show_toast_safe():
                try:
                    self.toaster.show_toast(
                        title,
                        message,
                        icon_path=icon_path,
                        duration=10,
                        threaded=False
                    )
                except Exception as e:
                    print(f"Toast thread hatası: {e}")
            
            # Daemon thread'de çalıştır
            thread = threading.Thread(target=show_toast_safe, daemon=True)
            thread.start()
            
            # Thread'in tamamlanmasını bekleme (non-blocking)
            return True
            
        except Exception as e:
            print(f"Win10Toast hatası: {e}")
            raise
    
    def _get_icon_path(self):
        if hasattr(sys, '_MEIPASS'):
            return os.path.join(sys._MEIPASS, 'icon.ico')
        elif os.path.exists('icon.ico'):
            return os.path.abspath('icon.ico')
        return None


# ========== FALLBACK (tkinter) ==========

class FallbackNotifier:
    """Fallback - tkinter MessageBox"""
    
    def __init__(self):
        print("⚠ Fallback backend yüklendi (tkinter)")
    
    def show(self, title, message, icon="info"):
        try:
            def show_in_thread():
                try:
                    import tkinter as tk
                    from tkinter import messagebox
                    
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    
                    if icon == "error":
                        messagebox.showerror(title, message, parent=root)
                    elif icon == "warning":
                        messagebox.showwarning(title, message, parent=root)
                    else:
                        messagebox.showinfo(title, message, parent=root)
                    
                    root.destroy()
                except Exception as e:
                    print(f"Fallback messagebox hatası: {e}")
                    # Son çare: Console
                    print(f"\n{'='*60}")
                    print(f"📢 {title}")
                    print(f"{message}")
                    print(f"{'='*60}\n")
            
            # Thread'de göster
            threading.Thread(target=show_in_thread, daemon=True).start()
            return True
            
        except Exception as e:
            print(f"Fallback hatası: {e}")
            # Console'a yazdır
            print(f"\n{'='*60}")
            print(f"📢 {title}")
            print(f"{message}")
            print(f"{'='*60}\n")
            return False


# ========== MACOS ==========

class MacOSNotifier:
    """macOS Notification Center"""
    
    def __init__(self):
        print("✓ macOS backend yüklendi")
    
    def show(self, title, message, icon="info"):
        try:
            import subprocess
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(['osascript', '-e', script], check=True)
            return True
        except Exception as e:
            print(f"macOS notification hatası: {e}")
            return False


# ========== LINUX ==========

class LinuxNotifier:
    """Linux notify-send"""
    
    def __init__(self):
        print("✓ Linux backend yüklendi")
    
    def show(self, title, message, icon="info"):
        try:
            import subprocess
            icon_map = {
                "info": "dialog-information",
                "warning": "dialog-warning",
                "error": "dialog-error",
                "success": "dialog-information"
            }
            
            subprocess.run([
                'notify-send',
                '-u', 'normal',
                '-i', icon_map.get(icon, "dialog-information"),
                '-a', 'Hisse Takip',
                title,
                message
            ], check=True)
            return True
        except Exception as e:
            print(f"Linux notification hatası: {e}")
            return False


# ========== HIZLI KULLANIM ==========

def notify(title, message, icon="info", sound=True):
    """Hızlı bildirim gönder"""
    service = NotificationService()
    return service.send(title, message, icon, sound)


# ========== TEST ==========

def test_notifications():
    """Bildirim sistemini test et"""
    print("\n🧪 Bildirim sistemi test ediliyor...\n")
    
    service = NotificationService()
    backend_name = service.notification_backend.__class__.__name__
    
    print(f"✓ Aktif backend: {backend_name}\n")
    print("Test bildirimi gönderiliyor...")
    
    try:
        service.send(
            "🧪 Test Bildirimi",
            "Bildirim sistemi çalışıyor!",
            icon="info",
            sound=True
        )
        print("✅ Bildirim başarıyla gönderildi!\n")
    except Exception as e:
        print(f"❌ Hata: {e}\n")


if __name__ == "__main__":
    test_notifications()