import sys
import os
import threading
import time
import json
import random
import winsound
import customtkinter as ctk
from tkinter import messagebox, filedialog
from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button, Controller as MouseController
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

# Tuş / Buton serileştirme yardımcıları
def serialize_key(key):
    if key is None:
        return None
    if isinstance(key, Key):
        return {"type": "Key", "name": key.name}
    elif isinstance(key, KeyCode):
        return {"type": "KeyCode", "char": key.char, "vk": key.vk}
    elif isinstance(key, Button):
        return {"type": "Button", "name": key.name}
    return str(key)

def deserialize_key(data):
    if not data:
        return None
    if isinstance(data, dict):
        t = data.get("type")
        if t == "Key":
            return getattr(Key, data["name"], None)
        elif t == "KeyCode":
            char = data.get("char")
            vk = data.get("vk")
            if char is not None:
                return KeyCode.from_char(char)
            elif vk is not None:
                return KeyCode(vk=vk)
        elif t == "Button":
            return getattr(Button, data["name"], None)
    return None

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
    if isinstance(key, Button):
        translations = {
            "left": "Sol Tık",
            "right": "Sağ Tık",
            "middle": "Orta Tık (Scroll)",
            "x1": "Yan Tuş 1 (Mouse 4)",
            "x2": "Yan Tuş 2 (Mouse 5)"
        }
        name = key.name if hasattr(key, 'name') else str(key)
        return translations.get(name.lower(), name.upper())
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
        self.buttons = [Button.left]
        self.jitter = False
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
                    for button in self.buttons:
                        mouse_controller.click(button)
                except Exception:
                    pass
                delay = 1.0 / self.cps
                if self.jitter:
                    delay *= random.uniform(0.85, 1.15)
                time.sleep(delay)
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
        self.jitter = False
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
                    delay = self.delay
                    if self.jitter:
                        delay *= random.uniform(0.85, 1.15)
                    time.sleep(delay)
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
                        delay = self.delay
                        if self.jitter:
                            delay *= random.uniform(0.85, 1.15)
                        time.sleep(delay)
            else:
                time.sleep(0.01)

# Motor Nesnelerini Başlat
clicker = MouseClicker()
clicker.start()

keyer = KeyboardKeyer()
keyer.start()


class MantıClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MantıClicker")
        self.geometry("560x550")
        self.resizable(False, False)

        # Genel Ayar Değişkenleri
        self.var_sound_enabled = ctk.BooleanVar(value=True)
        self.var_tray_enabled = ctk.BooleanVar(value=False)

        # Kapatıldığında temizlik yapması için protokol ekleme
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Başlık Bölümü
        self.title_label = ctk.CTkLabel(
            self, text="MantıClicker",
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
        self.tabview = ctk.CTkTabview(self, width=520, height=410)
        self.tabview.pack(padx=20, pady=(5, 10))

        self.tab_mouse = self.tabview.add("Fare Makrosu (Clicker)")
        self.tab_keyboard = self.tabview.add("Klavye Makrosu (Keyer)")
        self.tab_settings = self.tabview.add("Genel Ayarlar")

        self.setup_mouse_tab()
        self.setup_keyboard_tab()
        self.setup_settings_tab()

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

        # Global Fare Dinleyicisini Başlat
        self.mouse_listener = mouse.Listener(on_click=self.on_global_mouse_click)
        self.mouse_listener.start()

    def setup_mouse_tab(self):
        # Sol/Sağ Tık Seçimi
        self.lbl_btn = ctk.CTkLabel(self.tab_mouse, text="Fare Tuşu:", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_btn.grid(row=0, column=0, padx=20, pady=12, sticky="w")
        
        self.combo_btn = ctk.CTkOptionMenu(
            self.tab_mouse, values=["Sol Tık (Left)", "Sağ Tık (Right)", "Sol & Sağ Tık (Both)"],
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

        # Jitter / Anti-Cheat
        self.var_m_jitter = ctk.BooleanVar(value=False)
        self.chk_m_jitter = ctk.CTkCheckBox(
            self.tab_mouse, text="Anti-Cheat Koruması (Rastgele Jitter Tıklama)",
            variable=self.var_m_jitter,
            command=self.update_mouse_settings
        )
        self.chk_m_jitter.grid(row=4, column=0, columnspan=2, padx=20, pady=(5, 5), sticky="w")

        # Başlat/Durdur Butonu
        self.btn_m_toggle = ctk.CTkButton(
            self.tab_mouse, text=f"BAŞLAT ({key_to_string(mouse_hotkey)})",
            height=40, font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.toggle_mouse_macro
        )
        self.btn_m_toggle.grid(row=5, column=0, columnspan=2, padx=20, pady=(10, 10), sticky="ew")

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

        # Jitter / Anti-Cheat
        self.var_k_jitter = ctk.BooleanVar(value=False)
        self.chk_k_jitter = ctk.CTkCheckBox(
            self.tab_keyboard, text="Anti-Cheat Koruması (Rastgele Jitter Basım)",
            variable=self.var_k_jitter,
            command=self.update_keyboard_settings
        )
        self.chk_k_jitter.grid(row=7, column=0, columnspan=2, padx=20, pady=(5, 5), sticky="w")

        # Başlat/Durdur Butonu
        self.btn_k_toggle = ctk.CTkButton(
            self.tab_keyboard, text=f"BAŞLAT ({key_to_string(keyboard_hotkey)})",
            height=38, font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            command=self.toggle_keyboard_macro
        )
        self.btn_k_toggle.grid(row=8, column=0, columnspan=2, padx=20, pady=(10, 5), sticky="ew")

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
        if "Sol & Sağ" in btn_text:
            clicker.buttons = [Button.left, Button.right]
        elif "Sol" in btn_text:
            clicker.buttons = [Button.left]
        else:
            clicker.buttons = [Button.right]
        
        try:
            clicker.cps = int(self.slider_cps.get())
        except ValueError:
            clicker.cps = 10
            
        # Jitter Güncelleme
        clicker.jitter = self.var_m_jitter.get() if hasattr(self, 'var_m_jitter') else False

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
            
        # Jitter Güncelleme
        keyer.jitter = self.var_k_jitter.get() if hasattr(self, 'var_k_jitter') else False

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

    # Global Fare Tıklama Yakalayıcı
    def on_global_mouse_click(self, x, y, button, pressed):
        if pressed:
            global binding_mode
            if binding_mode is not None:
                if binding_mode == "keyboard_target":
                    return
                if button in [Button.left, Button.right]:
                    return
            self.on_global_key_press(button)

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
            self.trigger_sound("stop")
            self.lbl_m_status.configure(text="PASİF", text_color="#e74c3c")
            self.btn_m_toggle.configure(text=f"BAŞLAT ({key_to_string(mouse_hotkey)})", fg_color=["#3b82f6", "#1d4ed8"])
            self.combo_btn.configure(state="normal")
            self.slider_cps.configure(state="normal")
            self.entry_cps.configure(state="normal")
            self.btn_m_hk.configure(state="normal")
            self.chk_m_jitter.configure(state="normal")
        else:
            self.update_mouse_settings()
            clicker.start_clicking()
            self.trigger_sound("start")
            self.lbl_m_status.configure(text="AKTİF", text_color="#2ecc71")
            self.btn_m_toggle.configure(text=f"DURDUR ({key_to_string(mouse_hotkey)})", fg_color="#e74c3c", hover_color="#c0392b")
            self.combo_btn.configure(state="disabled")
            self.slider_cps.configure(state="disabled")
            self.entry_cps.configure(state="disabled")
            self.btn_m_hk.configure(state="disabled")
            self.chk_m_jitter.configure(state="disabled")

    # Klavye Makrosu Başlat / Durdur
    def toggle_keyboard_macro(self):
        if keyer.running:
            keyer.stop_keyer()
            self.trigger_sound("stop")
            self.lbl_k_status.configure(text="PASİF", text_color="#e74c3c")
            self.btn_k_toggle.configure(text=f"BAŞLAT ({key_to_string(keyboard_hotkey)})", fg_color=["#3b82f6", "#1d4ed8"])
            self.btn_k_add.configure(state="normal")
            self.btn_k_clear.configure(state="normal")
            self.seg_k_mode.configure(state="normal")
            if self.seg_k_mode.get() == "Bas-Bırak":
                self.entry_k_delay.configure(state="normal")
                self.combo_k_type.configure(state="normal")
            self.btn_k_hk.configure(state="normal")
            self.chk_k_jitter.configure(state="normal")
        else:
            if not keyboard_target_keys:
                messagebox.showwarning("Hedef Tuş Yok", "Lütfen önce basılacak en az bir hedef tuş belirleyin.")
                return
            self.update_keyboard_settings()
            keyer.start_keyer()
            self.trigger_sound("start")
            self.lbl_k_status.configure(text="AKTİF", text_color="#2ecc71")
            self.btn_k_toggle.configure(text=f"DURDUR ({key_to_string(keyboard_hotkey)})", fg_color="#e74c3c", hover_color="#c0392b")
            self.btn_k_add.configure(state="disabled")
            self.btn_k_clear.configure(state="disabled")
            self.seg_k_mode.configure(state="disabled")
            self.entry_k_delay.configure(state="disabled")
            self.combo_k_type.configure(state="disabled")
            self.btn_k_hk.configure(state="disabled")
            self.chk_k_jitter.configure(state="disabled")

    def on_closing(self):
        if self.var_tray_enabled.get():
            self.minimize_to_tray()
        else:
            self.quit_app_completely()

    def quit_app_completely(self):
        # Arka plan iş parçacıklarını durdur
        clicker.program_running = False
        clicker.stop_clicking()
        
        keyer.program_running = False
        keyer.stop_keyer()
        
        # Listener'ları durdur
        try:
            self.listener.stop()
        except Exception:
            pass
        try:
            self.mouse_listener.stop()
        except Exception:
            pass
            
        self.destroy()
        sys.exit()

    def minimize_to_tray(self):
        self.withdraw()
        
        def create_image():
            image = Image.new('RGB', (64, 64), color=(30, 41, 59))
            dc = ImageDraw.Draw(image)
            dc.ellipse([8, 8, 56, 56], fill=(59, 130, 246))
            dc.line([(20, 44), (20, 20), (32, 32), (44, 20), (44, 44)], fill=(255, 255, 255), width=4)
            return image

        def show_window(icon, item):
            icon.stop()
            self.after(0, self.deiconify)

        def quit_app(icon, item):
            icon.stop()
            self.after(0, self.quit_app_completely)

        icon_image = create_image()
        menu = (item('Göster', show_window), item('Çıkış', quit_app))
        self.tray_icon = pystray.Icon("MantıClicker", icon_image, "MantıClicker", menu)
        
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def setup_settings_tab(self):
        # Profil Bölümü
        self.profile_frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        self.profile_frame.pack(fill="x", padx=20, pady=15)
        
        self.lbl_profile_title = ctk.CTkLabel(self.profile_frame, text="Profil Yönetimi (Profil Kaydet/Yükle)", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_profile_title.pack(anchor="w", pady=(0, 10))
        
        self.profile_buttons_frame = ctk.CTkFrame(self.profile_frame, fg_color="transparent")
        self.profile_buttons_frame.pack(fill="x")
        
        self.btn_save_profile = ctk.CTkButton(
            self.profile_buttons_frame, text="Profil Kaydet",
            fg_color="#3498db", hover_color="#2980b9",
            command=self.save_profile
        )
        self.btn_save_profile.pack(side="left", padx=(0, 10), expand=True, fill="x")
        
        self.btn_load_profile = ctk.CTkButton(
            self.profile_buttons_frame, text="Profil Yükle",
            fg_color="#2ecc71", hover_color="#27ae60",
            command=self.load_profile
        )
        self.btn_load_profile.pack(side="left", padx=(10, 0), expand=True, fill="x")
        
        # Çizgi ayırıcı
        separator = ctk.CTkFrame(self.tab_settings, height=2, fg_color="#34495e")
        separator.pack(fill="x", padx=20, pady=10)
        
        # Ses Ayarları Bölümü
        self.sound_frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        self.sound_frame.pack(fill="x", padx=20, pady=10)
        
        self.lbl_sound_title = ctk.CTkLabel(self.sound_frame, text="Sesli Bildirim Ayarları", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_sound_title.pack(anchor="w", pady=(0, 10))
        
        self.sound_controls_frame = ctk.CTkFrame(self.sound_frame, fg_color="transparent")
        self.sound_controls_frame.pack(fill="x")
        
        self.sw_sound = ctk.CTkSwitch(self.sound_controls_frame, text="Sesli Bildirim Aktif", variable=self.var_sound_enabled)
        self.sw_sound.pack(side="left")
        
        self.combo_sound = ctk.CTkOptionMenu(
            self.sound_controls_frame, values=["Klasik", "Melodik", "Çift Tık", "Bas"],
            width=120
        )
        self.combo_sound.pack(side="right")
        self.combo_sound.set("Klasik")
        
        # Çizgi ayırıcı 2
        separator2 = ctk.CTkFrame(self.tab_settings, height=2, fg_color="#34495e")
        separator2.pack(fill="x", padx=20, pady=10)
        
        # Sistem Tepsisi Ayarları Bölümü
        self.tray_frame = ctk.CTkFrame(self.tab_settings, fg_color="transparent")
        self.tray_frame.pack(fill="x", padx=20, pady=10)
        
        self.lbl_tray_title = ctk.CTkLabel(self.tray_frame, text="Sistem Tepsisi Ayarları", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"))
        self.lbl_tray_title.pack(anchor="w", pady=(0, 10))
        
        self.sw_tray = ctk.CTkSwitch(self.tray_frame, text="Kapatınca Arka Plana At (Sistem Tepsisi)", variable=self.var_tray_enabled)
        self.sw_tray.pack(anchor="w")

    def save_profile(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Profili Kaydet"
        )
        if not file_path:
            return
        
        try:
            global mouse_hotkey, keyboard_hotkey, keyboard_target_keys
            
            profile_data = {
                # Fare Ayarları
                "mouse_button": self.combo_btn.get(),
                "mouse_cps": int(self.slider_cps.get()),
                "mouse_hotkey": serialize_key(mouse_hotkey),
                "mouse_jitter": self.var_m_jitter.get(),
                
                # Klavye Ayarları
                "keyboard_target_keys": [serialize_key(k) for k in keyboard_target_keys],
                "keyboard_mode": self.seg_k_mode.get(),
                "keyboard_tap_type": self.combo_k_type.get(),
                "keyboard_delay": self.entry_k_delay.get(),
                "keyboard_hotkey": serialize_key(keyboard_hotkey),
                "keyboard_jitter": self.var_k_jitter.get(),
                
                # Genel Ayarlar
                "sound_enabled": self.var_sound_enabled.get(),
                "sound_profile": self.combo_sound.get(),
                "minimize_to_tray": self.var_tray_enabled.get()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=4, ensure_ascii=False)
                
            messagebox.showinfo("Başarılı", "Profil başarıyla kaydedildi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Profil kaydedilirken bir hata oluştu:\n{e}")

    def load_profile(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")],
            title="Profili Yükle"
        )
        if not file_path:
            return
        
        try:
            global mouse_hotkey, keyboard_hotkey, keyboard_target_keys
            
            with open(file_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                
            # Fare Ayarlarını Yükleme
            if "mouse_button" in profile_data:
                self.combo_btn.set(profile_data["mouse_button"])
            if "mouse_cps" in profile_data:
                cps = profile_data["mouse_cps"]
                self.slider_cps.set(cps)
                self.entry_cps.delete(0, "end")
                self.entry_cps.insert(0, str(cps))
            if "mouse_hotkey" in profile_data:
                loaded_m_hk = deserialize_key(profile_data["mouse_hotkey"])
                if loaded_m_hk:
                    mouse_hotkey = loaded_m_hk
            if "mouse_jitter" in profile_data:
                self.var_m_jitter.set(profile_data["mouse_jitter"])
                
            # Klavye Ayarlarını Yükleme
            if "keyboard_target_keys" in profile_data:
                keyboard_target_keys = [deserialize_key(k) for k in profile_data["keyboard_target_keys"] if deserialize_key(k) is not None]
            if "keyboard_mode" in profile_data:
                self.seg_k_mode.set(profile_data["keyboard_mode"])
                self.on_keyboard_mode_change(profile_data["keyboard_mode"])
            if "keyboard_tap_type" in profile_data:
                self.combo_k_type.set(profile_data["keyboard_tap_type"])
            if "keyboard_delay" in profile_data:
                self.entry_k_delay.delete(0, "end")
                self.entry_k_delay.insert(0, profile_data["keyboard_delay"])
            if "keyboard_hotkey" in profile_data:
                loaded_k_hk = deserialize_key(profile_data["keyboard_hotkey"])
                if loaded_k_hk:
                    keyboard_hotkey = loaded_k_hk
            if "keyboard_jitter" in profile_data:
                self.var_k_jitter.set(profile_data["keyboard_jitter"])
                
            # Genel Ayarları Yükleme
            if "sound_enabled" in profile_data:
                self.var_sound_enabled.set(profile_data["sound_enabled"])
            if "sound_profile" in profile_data:
                self.combo_sound.set(profile_data["sound_profile"])
            if "minimize_to_tray" in profile_data:
                self.var_tray_enabled.set(profile_data["minimize_to_tray"])
                
            # Ayarları motorlara ve arayüze yansıtma
            self.update_mouse_settings()
            self.update_keyboard_settings()
            self.stop_binding_ui()
            
            messagebox.showinfo("Başarılı", "Profil başarıyla yüklendi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Profil yüklenirken bir hata oluştu:\n{e}")

    def play_sound_async(self, action):
        if not self.var_sound_enabled.get():
            return
        try:
            profile = self.combo_sound.get()
            if profile == "Klasik":
                if action == "start":
                    winsound.Beep(1000, 150)
                else:
                    winsound.Beep(750, 150)
            elif profile == "Melodik":
                if action == "start":
                    winsound.Beep(600, 80)
                    winsound.Beep(900, 80)
                else:
                    winsound.Beep(900, 80)
                    winsound.Beep(600, 80)
            elif profile == "Çift Tık":
                if action == "start":
                    winsound.Beep(1200, 50)
                    time.sleep(0.03)
                    winsound.Beep(1200, 50)
                else:
                    winsound.Beep(600, 50)
                    time.sleep(0.03)
                    winsound.Beep(600, 50)
            elif profile == "Bas":
                if action == "start":
                    winsound.Beep(400, 200)
                else:
                    winsound.Beep(300, 200)
        except Exception:
            pass

    def trigger_sound(self, action):
        threading.Thread(target=self.play_sound_async, args=(action,), daemon=True).start()

if __name__ == "__main__":
    app = MantıClickerApp()
    app.mainloop()
