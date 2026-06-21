import sys
import os
import threading
import time
import customtkinter as ctk
from tkinter import messagebox
from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button, Controller as MouseController

# CustomTkinter Ayarları
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Global Değişkenler ve Kontrolcüler
mouse_controller = MouseController()
keyboard_controller = keyboard.Controller()

# Varsayılan Tuş Atamaları
mouse_hotkey = Key.f7
keyboard_hotkey = Key.f6
keyboard_target_keys = [KeyCode.from_char('e')]  # Birden fazla tuş destekleyen liste

# Tuş Dinleme Durumları
binding_mode = None  # "mouse_hotkey", "keyboard_hotkey", "keyboard_target"

# Karşılaştırma Yardımcısı
def compare_keys(key1, key2):
    if key1 is None or key2 is None:
        return False
    if key1 == key2:
        return True
    
    char1 = getattr(key1, 'char', None)
    char2 = getattr(key2, 'char', None)
    if char1 is not None and char2 is not None:
        return char1.lower() == char2.lower()
        
    vk1 = getattr(key1, 'vk', None)
    vk2 = getattr(key2, 'vk', None)
    if vk1 is not None and vk2 is not None:
        return vk1 == vk2
        
    return False

# Tuş İsimlerini Türkçeleştirme
def key_to_string(key):
    if key is None:
        return "Atanmadı"
    if isinstance(key, Key):
        name = key.name
        translations = {
            "space": "Boşluk (Space)",
            "enter": "Enter",
            "backspace": "Geri (Backspace)",
            "tab": "Tab",
            "shift": "Shift",
            "ctrl": "Ctrl",
            "alt": "Alt",
            "caps_lock": "Caps Lock",
            "esc": "Esc",
            "up": "Yukarı Ok",
            "down": "Aşağı Ok",
            "left": "Sol Ok",
            "right": "Sağ Ok",
            "num_lock": "Num Lock",
            "scroll_lock": "Scroll Lock",
            "print_screen": "Print Screen",
            "insert": "Insert",
            "delete": "Delete",
            "home": "Home",
            "end": "End",
            "page_up": "Page Up",
            "page_down": "Page Down"
        }
        return translations.get(name.lower(), name.upper())
    elif hasattr(key, 'char') and key.char is not None:
        return key.char.upper()
    elif hasattr(key, 'vk') and key.vk is not None:
        if 96 <= key.vk <= 105:
            return f"Numpad {key.vk - 96}"
        return f"VK {key.vk}"
    else:
        return str(key)

# Fare Tıklayıcı Sınıfı
class MouseClicker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.cps = 10
        self.button = Button.left
        self.running = False
        self.program_running = True
        self.daemon = True

    def toggle(self):
        if self.running:
            self.stop_clicking()
        else:
            self.start_clicking()

    def start_clicking(self):
        self.running = True

    def stop_clicking(self):
        self.running = False

    def run(self):
        while self.program_running:
            if self.running:
                try:
                    mouse_controller.click(self.button)
                except Exception:
                    pass
                time.sleep(1.0 / self.cps)
            else:
                time.sleep(0.01)

# Klavye Makrosu Sınıfı (Çoklu Tuş Destekli)
class KeyboardKeyer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.target_keys = list(keyboard_target_keys)
        self.mode = "hold"  # "hold" veya "tap"
        self.tap_type = "together"  # "together" (Aynı Anda) veya "sequence" (Sırayla)
        self.delay = 0.1  # Saniye
        self.running = False
        self.program_running = True
        self.daemon = True
        self.held_keys = []

    def toggle(self):
        if self.running:
            self.stop_keyer()
        else:
            self.start_keyer()

    def start_keyer(self):
        if not self.target_keys:
            return
        self.running = True
        if self.mode == "hold":
            for key in self.target_keys:
                try:
                    keyboard_controller.press(key)
                    self.held_keys.append(key)
                except Exception:
                    pass

    def stop_keyer(self):
        self.running = False
        for key in list(self.held_keys):
            try:
                keyboard_controller.release(key)
            except Exception:
                pass
        self.held_keys.clear()

    def run(self):
        while self.program_running:
            if self.running and self.mode == "tap" and self.target_keys:
                if self.tap_type == "together":
                    # Tüm tuşlara aynı anda bas
                    for key in self.target_keys:
                        try:
                            keyboard_controller.press(key)
                        except Exception:
                            pass
                    # Tüm tuşları bırak
                    for key in self.target_keys:
                        try:
                            keyboard_controller.release(key)
                        except Exception:
                            pass
                    time.sleep(self.delay)
                else:
                    # Tuşlara sırayla bas-bırak yap
                    for key in self.target_keys:
                        if not self.running:
                            break
                        try:
                            keyboard_controller.press(key)
                            keyboard_controller.release(key)
                        except Exception:
                            pass
                        time.sleep(self.delay)
            else:
                time.sleep(0.01)

# Motor Nesnelerini Başlat
clicker = MouseClicker()
clicker.start()

keyer = KeyboardKeyer()
keyer.start()


class AutoClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mantı Clicker & Keyer")
        self.geometry("560x520")
        self.resizable(False, False)

        # Kapatıldığında temizlik yapması için protokol ekleme
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Başlık Bölümü
        self.title_label = ctk.CTkLabel(
            self, text="Auto Clicker & Keyboard Keyer",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold")
        )
        self.title_label.pack(pady=(15, 5))

        self.subtitle_label = ctk.CTkLabel(
            self, text="Çoklu Tuş Destekli Gelişmiş Makro Aracı",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="gray"
        )
        self.subtitle_label.pack(pady=(0, 5))

        # Sekme Yapısı
        self.tabview = ctk.CTkTabview(self, width=520, height=380)
        self.tabview.pack(padx=20, pady=(5, 10))

        self.tab_mouse = self.tabview.add("Fare Makrosu (Clicker)")
        self.tab_keyboard = self.tabview.add("Klavye Makrosu (Keyer)")

        self.setup_mouse_tab()
        self.setup_keyboard_tab()

        # Alt Bilgi / Durum Barı
        self.status_bar = ctk.CTkLabel(
            self, text="Hazır - Kısayol tuşlarını kullanarak arka planda çalıştırabilirsiniz.",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="gray"
        )
        self.status_bar.pack(side="bottom", pady=5)

        # Global Klavye Dinleyicisini Başlat
        self.listener = keyboard.Listener(on_press=self.on_global_key_press)
        self.listener.start()

    def setup_mouse_tab(self):
        # Sol/Sağ Tık Seçimi
        self.lbl_btn = ctk.CTkLabel(self.tab_mouse, text="Fare Tuşu:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_btn.grid(row=0, column=0, padx=20, pady=12, sticky="w")
        
        self.combo_btn = ctk.CTkOptionMenu(
            self.tab_mouse, values=["Sol Tık (Left)", "Sağ Tık (Right)"],
            command=self.update_mouse_settings
        )
        self.combo_btn.grid(row=0, column=1, padx=20, pady=12, sticky="e")
        self.combo_btn.set("Sol Tık (Left)")

        # CPS Tıklama Hızı Slider & Entry
        self.lbl_cps = ctk.CTkLabel(self.tab_mouse, text="CPS (Tıklama Hızı):", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_cps.grid(row=1, column=0, padx=20, pady=12, sticky="w")

        cps_frame = ctk.CTkFrame(self.tab_mouse, fg_color="transparent")
        cps_frame.grid(row=1, column=1, padx=20, pady=12, sticky="e")

        self.slider_cps = ctk.CTkSlider(cps_frame, from_=1, to=60, number_of_steps=59, width=120, command=self.on_cps_slider_move)
        self.slider_cps.pack(side="left", padx=(0, 10))
        self.slider_cps.set(10)

        self.entry_cps = ctk.CTkEntry(cps_frame, width=50, justify="center")
        self.entry_cps.pack(side="left")
        self.entry_cps.insert(0, "10")
        self.entry_cps.bind("<FocusOut>", self.on_cps_entry_change)
        self.entry_cps.bind("<Return>", self.on_cps_entry_change)

        # Kısayol Tuşu Belirleme
        self.lbl_m_hk = ctk.CTkLabel(self.tab_mouse, text="Çalıştırma Kısayolu:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_m_hk.grid(row=2, column=0, padx=20, pady=12, sticky="w")

        self.btn_m_hk = ctk.CTkButton(
            self.tab_mouse, text=key_to_string(mouse_hotkey),
            width=140, fg_color="#34495e", hover_color="#2c3e50",
            command=lambda: self.start_binding("mouse_hotkey")
        )
        self.btn_m_hk.grid(row=2, column=1, padx=20, pady=12, sticky="e")

        # Durum Göstergesi
        self.lbl_m_status_title = ctk.CTkLabel(self.tab_mouse, text="Durum:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_m_status_title.grid(row=3, column=0, padx=20, pady=12, sticky="w")

        self.lbl_m_status = ctk.CTkLabel(self.tab_mouse, text="PASİF", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#e74c3c")
        self.lbl_m_status.grid(row=3, column=1, padx=20, pady=12, sticky="e")

        # Başlat/Durdur Butonu
        self.btn_m_toggle = ctk.CTkButton(
            self.tab_mouse, text=f"BAŞLAT ({key_to_string(mouse_hotkey)})",
            height=40, font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.toggle_mouse_macro
        )
        self.btn_m_toggle.grid(row=4, column=0, columnspan=2, padx=20, pady=(15, 10), sticky="ew")

    def setup_keyboard_tab(self):
        # Basılacak Hedef Tuşlar Listesi
        self.lbl_k_target_title = ctk.CTkLabel(self.tab_keyboard, text="Basılacak Tuşlar:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_k_target_title.grid(row=0, column=0, padx=20, pady=(10, 5), sticky="w")

        self.lbl_k_target_list = ctk.CTkLabel(
            self.tab_keyboard, text=self.get_keys_list_string(),
            font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"),
            text_color="#3498db", wraplength=220, justify="right"
        )
        self.lbl_k_target_list.grid(row=0, column=1, padx=20, pady=(10, 5), sticky="e")

        # Tuş Ekle / Temizle Butonları
        btn_frame = ctk.CTkFrame(self.tab_keyboard, fg_color="transparent")
        btn_frame.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")

        self.btn_k_add = ctk.CTkButton(
            btn_frame, text="Tuş Ekle (+)", width=120, height=28,
            fg_color="#2ecc71", hover_color="#27ae60",
            command=lambda: self.start_binding("keyboard_target")
        )
        self.btn_k_add.pack(side="left", padx=(0, 10), expand=True)

        self.btn_k_clear = ctk.CTkButton(
            btn_frame, text="Listeyi Temizle", width=120, height=28,
            fg_color="#95a5a6", hover_color="#7f8c8d",
            command=self.clear_target_keys
        )
        self.btn_k_clear.pack(side="right", padx=(10, 0), expand=True)

        # Çalışma Modu Seçimi (Hold veya Tap)
        self.lbl_k_mode = ctk.CTkLabel(self.tab_keyboard, text="Çalışma Modu:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_k_mode.grid(row=2, column=0, padx=20, pady=8, sticky="w")

        self.seg_k_mode = ctk.CTkSegmentedButton(
            self.tab_keyboard, values=["Basılı Tut", "Bas-Bırak"],
            command=self.on_keyboard_mode_change
        )
        self.seg_k_mode.grid(row=2, column=1, padx=20, pady=8, sticky="e")
        self.seg_k_mode.set("Basılı Tut")

        # Tıklama Çalışma Tipi (Aynı Anda / Sırayla)
        self.lbl_k_type = ctk.CTkLabel(self.tab_keyboard, text="Basma Tipi:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_k_type.grid(row=3, column=0, padx=20, pady=8, sticky="w")

        self.combo_k_type = ctk.CTkOptionMenu(
            self.tab_keyboard, values=["Aynı Anda (Together)", "Sırayla (Sequence)"],
            command=self.update_keyboard_settings,
            state="disabled" # Varsayılan mod "Basılı Tut" olduğu için başta pasif
        )
        self.combo_k_type.grid(row=3, column=1, padx=20, pady=8, sticky="e")
        self.combo_k_type.set("Aynı Anda (Together)")

        # Bas-Bırak Modu Gecikmesi (Milisaniye)
        self.lbl_k_delay = ctk.CTkLabel(self.tab_keyboard, text="Hız / Gecikme (ms):", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_k_delay.grid(row=4, column=0, padx=20, pady=8, sticky="w")

        self.entry_k_delay = ctk.CTkEntry(self.tab_keyboard, width=80, justify="center")
        self.entry_k_delay.grid(row=4, column=1, padx=20, pady=8, sticky="e")
        self.entry_k_delay.insert(0, "100")
        self.entry_k_delay.configure(state="disabled") # Varsayılan mod "Basılı Tut" olduğu için başta pasif
        self.entry_k_delay.bind("<FocusOut>", self.update_keyboard_settings)
        self.entry_k_delay.bind("<Return>", self.update_keyboard_settings)

        # Kısayol Tuşu Belirleme
        self.lbl_k_hk = ctk.CTkLabel(self.tab_keyboard, text="Çalıştırma Kısayolu:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_k_hk.grid(row=5, column=0, padx=20, pady=8, sticky="w")

        self.btn_k_hk = ctk.CTkButton(
            self.tab_keyboard, text=key_to_string(keyboard_hotkey),
            width=140, fg_color="#34495e", hover_color="#2c3e50",
            command=lambda: self.start_binding("keyboard_hotkey")
        )
        self.btn_k_hk.grid(row=5, column=1, padx=20, pady=8, sticky="e")

        # Durum Göstergesi
        self.lbl_k_status_title = ctk.CTkLabel(self.tab_keyboard, text="Durum:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_k_status_title.grid(row=6, column=0, padx=20, pady=6, sticky="w")

        self.lbl_k_status = ctk.CTkLabel(self.tab_keyboard, text="PASİF", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color="#e74c3c")
        self.lbl_k_status.grid(row=6, column=1, padx=20, pady=6, sticky="e")

        # Başlat/Durdur Butonu
        self.btn_k_toggle = ctk.CTkButton(
            self.tab_keyboard, text=f"BAŞLAT ({key_to_string(keyboard_hotkey)})",
            height=38, font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.toggle_keyboard_macro
        )
        self.btn_k_toggle.grid(row=7, column=0, columnspan=2, padx=20, pady=(10, 5), sticky="ew")

    # Hedef tuşlar listesini metin haline getirme
    def get_keys_list_string(self):
        if not keyboard_target_keys:
            return "Boş (Hiçbiri)"
        return ", ".join(key_to_string(k) for k in keyboard_target_keys)

    def clear_target_keys(self):
        global keyboard_target_keys
        keyboard_target_keys.clear()
        self.lbl_k_target_list.configure(text=self.get_keys_list_string())
        self.update_keyboard_settings()

    # Arayüz Etkileşim Fonksiyonları
    def on_cps_slider_move(self, value):
        self.entry_cps.delete(0, "end")
        self.entry_cps.insert(0, str(int(value)))
        self.update_mouse_settings()

    def on_cps_entry_change(self, event=None):
        val = self.entry_cps.get()
        try:
            cps = int(val)
            if 1 <= cps <= 200:
                self.slider_cps.set(cps)
                self.update_mouse_settings()
            else:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Geçersiz Değer", "Lütfen 1 ile 200 arasında geçerli bir tam sayı girin.")
            self.entry_cps.delete(0, "end")
            self.entry_cps.insert(0, str(int(self.slider_cps.get())))

    def on_keyboard_mode_change(self, value):
        if value == "Basılı Tut":
            self.entry_k_delay.configure(state="disabled")
            self.combo_k_type.configure(state="disabled")
        else:
            self.entry_k_delay.configure(state="normal")
            self.combo_k_type.configure(state="normal")
        self.update_keyboard_settings()

    # Ayarları Motorlara Aktarma
    def update_mouse_settings(self, event=None):
        btn_text = self.combo_btn.get()
        if "Sol" in btn_text:
            clicker.button = Button.left
        else:
            clicker.button = Button.right
        
        try:
            clicker.cps = int(self.slider_cps.get())
        except ValueError:
            clicker.cps = 10

    def update_keyboard_settings(self, event=None):
        global keyboard_target_keys
        keyer.target_keys = list(keyboard_target_keys)
        
        mode = self.seg_k_mode.get()
        if mode == "Basılı Tut":
            keyer.mode = "hold"
        else:
            keyer.mode = "tap"
            
        k_type = self.combo_k_type.get()
        if "Aynı Anda" in k_type:
            keyer.tap_type = "together"
        else:
            keyer.tap_type = "sequence"
            
        try:
            delay_ms = float(self.entry_k_delay.get())
            if delay_ms < 1:
                delay_ms = 1
                self.entry_k_delay.delete(0, "end")
                self.entry_k_delay.insert(0, "1")
            keyer.delay = delay_ms / 1000.0
        except ValueError:
            keyer.delay = 0.1
            self.entry_k_delay.delete(0, "end")
            self.entry_k_delay.insert(0, "100")

    # Kısayol / Tuş Atama Yönetimi
    def start_binding(self, mode):
        global binding_mode
        binding_mode = mode
        
        if mode == "mouse_hotkey":
            self.status_bar.configure(text="Kısayol Tuşu bekleniyor... İptal için ESC.", text_color="#f39c12")
            self.btn_m_hk.configure(text="Basın...", fg_color="#e67e22")
        elif mode == "keyboard_hotkey":
            self.status_bar.configure(text="Kısayol Tuşu bekleniyor... İptal için ESC.", text_color="#f39c12")
            self.btn_k_hk.configure(text="Basın...", fg_color="#e67e22")
        elif mode == "keyboard_target":
            self.status_bar.configure(text="Eklenecek Hedef Tuşu basın... İptal için ESC.", text_color="#f39c12")
            self.btn_k_add.configure(text="Tuşa Basın...", fg_color="#e67e22")

    def stop_binding_ui(self):
        self.status_bar.configure(text="Hazır - Kısayol tuşlarını kullanarak arka planda çalıştırabilirsiniz.", text_color="gray")
        self.btn_m_hk.configure(text=key_to_string(mouse_hotkey), fg_color="#34495e", hover_color="#2c3e50")
        self.btn_k_hk.configure(text=key_to_string(keyboard_hotkey), fg_color="#34495e", hover_color="#2c3e50")
        self.btn_k_add.configure(text="Tuş Ekle (+)", fg_color="#2ecc71", hover_color="#27ae60")
        self.lbl_k_target_list.configure(text=self.get_keys_list_string())
        self.btn_m_toggle.configure(text=f"BAŞLAT ({key_to_string(mouse_hotkey)})")
        self.btn_k_toggle.configure(text=f"BAŞLAT ({key_to_string(keyboard_hotkey)})")

    # Global Kısayol Yakalayıcı
    def on_global_key_press(self, key):
        global binding_mode, mouse_hotkey, keyboard_hotkey, keyboard_target_keys

        # 1. Tuş Atama Modu Açıksa
        if binding_mode is not None:
            if key == Key.esc:
                binding_mode = None
                self.after(0, self.stop_binding_ui)
                return
            
            # Aynı tuşların çakışmasını engelleme kontrolleri
            if binding_mode == "mouse_hotkey":
                if compare_keys(key, keyboard_hotkey):
                    self.after(0, lambda: messagebox.showwarning("Kısayol Çakışması", "Bu kısayol tuşu Klavye Makrosu tarafından kullanılmaktadır."))
                else:
                    mouse_hotkey = key
            elif binding_mode == "keyboard_hotkey":
                if compare_keys(key, mouse_hotkey):
                    self.after(0, lambda: messagebox.showwarning("Kısayol Çakışması", "Bu kısayol tuşu Fare Makrosu tarafından kullanılmaktadır."))
                else:
                    keyboard_hotkey = key
            elif binding_mode == "keyboard_target":
                # Kısayollar ile hedef tuş çakışmamalıdır
                if compare_keys(key, keyboard_hotkey) or compare_keys(key, mouse_hotkey):
                    self.after(0, lambda: messagebox.showwarning("Çakışma Hatası", "Hedef tuş, Kısayol Tuşları ile aynı olamaz."))
                else:
                    # Listede zaten varsa mükerrer eklemesini engelle
                    exists = any(compare_keys(key, k) for k in keyboard_target_keys)
                    if not exists:
                        keyboard_target_keys.append(key)
                    else:
                        self.after(0, lambda: messagebox.showinfo("Tuş Zaten Ekli", "Bu tuş zaten hedef tuşlar listenizde bulunuyor."))

            binding_mode = None
            self.after(0, self.stop_binding_ui)
            self.after(0, self.update_keyboard_settings)
            return

        # 2. Normal Makro Çalıştırma Kısayol Kontrolleri
        if compare_keys(key, mouse_hotkey):
            self.after(0, self.toggle_mouse_macro)
        elif compare_keys(key, keyboard_hotkey):
            self.after(0, self.toggle_keyboard_macro)

    # Fare Makrosu Başlat / Durdur
    def toggle_mouse_macro(self):
        if clicker.running:
            clicker.stop_clicking()
            self.lbl_m_status.configure(text="PASİF", text_color="#e74c3c")
            self.btn_m_toggle.configure(text=f"BAŞLAT ({key_to_string(mouse_hotkey)})", fg_color=["#3b82f6", "#1d4ed8"])
            self.combo_btn.configure(state="normal")
            self.slider_cps.configure(state="normal")
            self.entry_cps.configure(state="normal")
            self.btn_m_hk.configure(state="normal")
        else:
            self.update_mouse_settings()
            clicker.start_clicking()
            self.lbl_m_status.configure(text="AKTİF", text_color="#2ecc71")
            self.btn_m_toggle.configure(text=f"DURDUR ({key_to_string(mouse_hotkey)})", fg_color="#e74c3c", hover_color="#c0392b")
            self.combo_btn.configure(state="disabled")
            self.slider_cps.configure(state="disabled")
            self.entry_cps.configure(state="disabled")
            self.btn_m_hk.configure(state="disabled")

    # Klavye Makrosu Başlat / Durdur
    def toggle_keyboard_macro(self):
        if keyer.running:
            keyer.stop_keyer()
            self.lbl_k_status.configure(text="PASİF", text_color="#e74c3c")
            self.btn_k_toggle.configure(text=f"BAŞLAT ({key_to_string(keyboard_hotkey)})", fg_color=["#3b82f6", "#1d4ed8"])
            self.btn_k_add.configure(state="normal")
            self.btn_k_clear.configure(state="normal")
            self.seg_k_mode.configure(state="normal")
            if self.seg_k_mode.get() == "Bas-Bırak":
                self.entry_k_delay.configure(state="normal")
                self.combo_k_type.configure(state="normal")
            self.btn_k_hk.configure(state="normal")
        else:
            if not keyboard_target_keys:
                messagebox.showwarning("Hedef Tuş Yok", "Lütfen önce basılacak en az bir hedef tuş belirleyin.")
                return
            self.update_keyboard_settings()
            keyer.start_keyer()
            self.lbl_k_status.configure(text="AKTİF", text_color="#2ecc71")
            self.btn_k_toggle.configure(text=f"DURDUR ({key_to_string(keyboard_hotkey)})", fg_color="#e74c3c", hover_color="#c0392b")
            self.btn_k_add.configure(state="disabled")
            self.btn_k_clear.configure(state="disabled")
            self.seg_k_mode.configure(state="disabled")
            self.entry_k_delay.configure(state="disabled")
            self.combo_k_type.configure(state="disabled")
            self.btn_k_hk.configure(state="disabled")

    def on_closing(self):
        # Arka plan iş parçacıklarını durdur
        clicker.program_running = False
        clicker.stop_clicking()
        
        keyer.program_running = False
        keyer.stop_keyer()
        
        # Listener'ı durdur
        try:
            self.listener.stop()
        except Exception:
            pass
            
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = AutoClickerApp()
    app.mainloop()
