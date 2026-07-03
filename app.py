import sys
import os
import threading
import time
import json
import random
import math
import winsound
import customtkinter as ctk
from tkinter import messagebox, filedialog
from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button, Controller as MouseController
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw, ImageFilter

try:
    import pywinstyles
except ImportError:
    pywinstyles = None

# ══════════════════════════════════════════════════════════════
#  RENK PALETİ & TASARIM SİSTEMİ
# ══════════════════════════════════════════════════════════════

COLORS = {
    "bg_deep":       "#0a0e1a",    # En derin arka plan
    "bg_dark":       "#111827",    # Ana arka plan (slate-900)
    "bg_card":       "#1e293b",    # Kart/Panel arka planı (slate-800)
    "bg_card_hover": "#334155",    # Hover durumundaki kart
    "bg_input":      "#0f172a",    # Input/Entry arka planı
    "border":        "#334155",    # Kenarlıklar (slate-700)
    "border_glow":   "#3b82f6",    # Neon kenarlık glow

    "accent":        "#3b82f6",    # Ana vurgu – Mavi
    "accent_hover":  "#60a5fa",    # Hover mavi
    "accent_dark":   "#1d4ed8",    # Koyu mavi
    "cyan":          "#06b6d4",    # Siyan vurgu
    "cyan_glow":     "#22d3ee",    # Siyan parlama

    "success":       "#10b981",    # Yeşil – Aktif
    "success_glow":  "#34d399",    # Yeşil parlama
    "danger":        "#ef4444",    # Kırmızı – Pasif / Durdur
    "danger_hover":  "#dc2626",    # Koyu kırmızı
    "warning":       "#f59e0b",    # Sarı – Uyarı
    "amber":         "#f59e0b",    # Amber – Logo

    "text_primary":  "#f1f5f9",    # Ana metin (slate-100)
    "text_secondary":"#94a3b8",    # İkincil metin (slate-400)
    "text_muted":    "#64748b",    # Soluk metin (slate-500)
    "text_accent":   "#93c5fd",    # Vurgulu metin (blue-300)
}

FONT_FAMILY = "Segoe UI"

# ══════════════════════════════════════════════════════════════
#  TUŞ / BUTON SERİLEŞTİRME YARDIMCILARI
# ══════════════════════════════════════════════════════════════

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

# ══════════════════════════════════════════════════════════════
#  PREMIUM LOGO ÜRETİCİ (HİGH-TECH NEON)
# ══════════════════════════════════════════════════════════════

def create_premium_logo():
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    c = size // 2  # 128

    # Outer soft glow rings (cyan/blue gradient)
    for r in range(120, 100, -1):
        alpha = int(100 * (1 - (120 - r) / 20))
        ratio = (120 - r) / 20.0
        gc = int(180 * (1 - ratio) + 214 * ratio)
        bc = int(255 * (1 - ratio) + 230 * ratio)
        draw.ellipse([c-r, c-r, c+r, c+r], outline=(6, gc, bc, alpha), width=2)

    # Middle ring – subtle blue
    for r in range(104, 98, -1):
        alpha = int(160 * (1 - (104 - r) / 6))
        draw.ellipse([c-r, c-r, c+r, c+r], outline=(59, 130, 246, alpha), width=2)

    # Dark central disk with subtle gradient edge
    draw.ellipse([c-96, c-96, c+96, c+96], fill=(15, 23, 42, 255))
    draw.ellipse([c-94, c-94, c+94, c+94], fill=(17, 24, 39, 255))

    # Inner subtle ring
    draw.ellipse([c-90, c-90, c+90, c+90], outline=(30, 41, 59, 180), width=1)

    # ── Mantı (Dumpling) Shape ──
    # Main body (amber-golden)
    draw.chord([c-44, c-16, c+44, c+48], start=0, end=180, fill=(245, 158, 11, 255))
    # Left fold wing
    draw.polygon([(c-36, c+16), (c-44, c-24), (c-20, c-6)], fill=(251, 191, 36, 255))
    # Right fold wing
    draw.polygon([(c+36, c+16), (c+44, c-24), (c+20, c-6)], fill=(251, 191, 36, 255))
    # Center triangle highlight
    draw.polygon([(c-22, c+6), (c, c-36), (c+22, c+6)], fill=(252, 211, 77, 255))
    # Top knot
    draw.ellipse([c-6, c-40, c+6, c-28], fill=(245, 158, 11, 255))

    # Crimp texture lines
    for i in range(-2, 3):
        x_off = i * 12
        draw.line([(c+x_off-4, c+10), (c+x_off, c-2), (c+x_off+4, c+10)],
                  fill=(234, 138, 0, 200), width=1)

    # ── Neon Cursor Arrow ──
    cursor_pts = [
        (c+10, c+10),
        (c+10, c+52),
        (c+22, c+40),
        (c+36, c+54),
        (c+42, c+48),
        (c+28, c+34),
        (c+42, c+28),
    ]
    # Glow shadow
    shadow_pts = [(x+3, y+3) for x, y in cursor_pts]
    draw.polygon(shadow_pts, fill=(6, 182, 212, 60))
    # White fill
    draw.polygon(cursor_pts, fill=(255, 255, 255, 250))
    # Neon cyan outline
    draw.polygon(cursor_pts, outline=(6, 182, 212, 255), width=3)

    return img.resize((128, 128), Image.LANCZOS)

# ══════════════════════════════════════════════════════════════
#  MODERN GLOWING LED INDICATOR
# ══════════════════════════════════════════════════════════════

class NeonStatusLED(ctk.CTkCanvas):
    """Animasyonlu neon LED durum göstergesi"""
    def __init__(self, parent, size=28, **kwargs):
        # bg_color parametresini özel olarak ele al
        bg = kwargs.pop('bg_color', COLORS["bg_card"])
        super().__init__(parent, width=size, height=size,
                         bg=bg, highlightthickness=0, **kwargs)
        self.size = size
        self.active = False
        self._pulse_phase = 0.0
        self._draw()
        self._animate()

    def set_status(self, active):
        self.active = active
        self._pulse_phase = 0.0
        self._draw()

    def _draw(self):
        self.delete("all")
        cx = self.size / 2
        cy = self.size / 2
        r_core = 5

        if self.active:
            # Dış glow halkası (pulsing)
            pulse = 0.5 + 0.5 * math.sin(self._pulse_phase)
            r_glow = r_core + 4 + pulse * 5
            glow_alpha = 0.15 + 0.25 * pulse

            # Glow renk karışımı (bg ile yeşil arası)
            bg_r, bg_g, bg_b = 30, 41, 59
            gl_r, gl_g, gl_b = 16, 185, 129
            mr = int(bg_r * (1 - glow_alpha) + gl_r * glow_alpha)
            mg = int(bg_g * (1 - glow_alpha) + gl_g * glow_alpha)
            mb = int(bg_b * (1 - glow_alpha) + gl_b * glow_alpha)
            self.create_oval(cx-r_glow, cy-r_glow, cx+r_glow, cy+r_glow,
                             fill=f"#{mr:02x}{mg:02x}{mb:02x}", outline="")

            # Orta parlama
            r_mid = r_core + 2
            self.create_oval(cx-r_mid, cy-r_mid, cx+r_mid, cy+r_mid,
                             fill="#059669", outline="")

            # Çekirdek
            self.create_oval(cx-r_core, cy-r_core, cx+r_core, cy+r_core,
                             fill=COLORS["success"], outline="")

            # İç parlak nokta (highlight)
            self.create_oval(cx-2, cy-3, cx+1, cy-1, fill="#6ee7b7", outline="")
        else:
            # Pasif – sabit koyu kırmızı
            self.create_oval(cx-r_core-1, cy-r_core-1, cx+r_core+1, cy+r_core+1,
                             fill="#7f1d1d", outline="")
            self.create_oval(cx-r_core, cy-r_core, cx+r_core, cy+r_core,
                             fill=COLORS["danger"], outline="")
            self.create_oval(cx-2, cy-3, cx+1, cy-1, fill="#fca5a5", outline="")

    def _animate(self):
        if self.active:
            self._pulse_phase += 0.12
            self._draw()
        self.after(30, self._animate)

# ══════════════════════════════════════════════════════════════
#  CustomTkinter TEMELLERİ
# ══════════════════════════════════════════════════════════════

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ══════════════════════════════════════════════════════════════
#  GLOBAL DEĞİŞKENLER VE KONTROLCÜLER
# ══════════════════════════════════════════════════════════════

mouse_controller = MouseController()
keyboard_controller = keyboard.Controller()

# Varsayılan Tuş Atamaları
mouse_hotkey_left = Key.f7
mouse_hotkey_right = Key.f8
keyboard_hotkey = Key.f6
keyboard_target_keys = [KeyCode.from_char('e')]

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

# ══════════════════════════════════════════════════════════════
#  FARE TIKLAYICI SINIFI
# ══════════════════════════════════════════════════════════════

class MouseClicker(threading.Thread):
    def __init__(self, button=Button.left):
        super().__init__()
        self.cps = 10
        self.button = button
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
                    mouse_controller.click(self.button)
                except Exception:
                    pass
                delay = 1.0 / self.cps
                if self.jitter:
                    delay *= random.uniform(0.85, 1.15)
                time.sleep(delay)
            else:
                time.sleep(0.01)

# ══════════════════════════════════════════════════════════════
#  KLAVYE MAKROSU SINIFI (ÇOKLU TUŞ DESTEKLİ)
# ══════════════════════════════════════════════════════════════

class KeyboardKeyer(threading.Thread):
    def __init__(self):
        super().__init__()
        self.target_keys = list(keyboard_target_keys)
        self.mode = "hold"
        self.tap_type = "together"
        self.delay = 0.1
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
                    for key in self.target_keys:
                        try:
                            keyboard_controller.press(key)
                        except Exception:
                            pass
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
clicker_left = MouseClicker(button=Button.left)
clicker_left.start()

clicker_right = MouseClicker(button=Button.right)
clicker_right.start()

keyer = KeyboardKeyer()
keyer.start()


# ══════════════════════════════════════════════════════════════
#  YARDIMCI WİDGET'LAR – GLASSMORPHISM PANELLERİ
# ══════════════════════════════════════════════════════════════

class GlassCard(ctk.CTkFrame):
    """Yarı saydam glassmorphism paneli"""
    def __init__(self, parent, **kwargs):
        super().__init__(
            parent,
            fg_color=COLORS["bg_card"],
            corner_radius=12,
            border_width=1,
            border_color=COLORS["border"],
            **kwargs
        )

class SectionTitle(ctk.CTkLabel):
    """Bölüm başlığı (ince bir alt çizgi ile)"""
    def __init__(self, parent, text, icon="", **kwargs):
        display = f"{icon}  {text}" if icon else text
        super().__init__(
            parent,
            text=display,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=COLORS["text_accent"],
            anchor="w",
            **kwargs
        )

class FieldLabel(ctk.CTkLabel):
    """Satır içi alan etiketi"""
    def __init__(self, parent, text, **kwargs):
        super().__init__(
            parent,
            text=text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            text_color=COLORS["text_secondary"],
            anchor="w",
            **kwargs
        )

class NeonButton(ctk.CTkButton):
    """Neon glow efektli buton"""
    def __init__(self, parent, text, accent=None, **kwargs):
        color = accent or COLORS["accent"]
        # Hover rengi hesapla (biraz daha açık)
        hover = kwargs.pop("hover_color", COLORS["accent_hover"])
        height = kwargs.pop("height", 36)
        super().__init__(
            parent,
            text=text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            corner_radius=10,
            height=height,
            fg_color=color,
            hover_color=hover,
            border_width=0,
            **kwargs
        )

class BigActionButton(ctk.CTkButton):
    """Ana aksiyon butonu – geniş, dikkat çekici, pulse animasyonlu"""
    def __init__(self, parent, text, **kwargs):
        height = kwargs.pop("height", 48)
        super().__init__(
            parent,
            text=text,
            font=ctk.CTkFont(family=FONT_FAMILY, size=15, weight="bold"),
            corner_radius=12,
            height=height,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_width=2,
            border_color=COLORS["accent"],
            **kwargs
        )
        self._is_active = False
        self._pulse_phase = 0.0
        self._animate_pulse()

    def set_active(self, active):
        self._is_active = active

    def _animate_pulse(self):
        if self._is_active:
            self._pulse_phase += 0.08
            pulse = 0.5 + 0.5 * math.sin(self._pulse_phase)
            # Kırmızı tonlarında border glow
            r = int(239 * (0.7 + 0.3 * pulse))
            g = int(68 * (0.5 + 0.5 * pulse))
            b = int(68 * (0.5 + 0.5 * pulse))
            border_col = f"#{min(r,255):02x}{min(g,255):02x}{min(b,255):02x}"
            try:
                self.configure(border_color=border_col)
            except Exception:
                pass
        self.after(40, self._animate_pulse)

# ══════════════════════════════════════════════════════════════
#  ANA UYGULAMA – MantıClickerApp
# ══════════════════════════════════════════════════════════════

class MantıClickerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── Pencere Ayarları ──
        self.title("MantıClicker")
        self.geometry("600x620")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg_deep"])

        # Fade-in Başlangıcı
        self.attributes('-alpha', 0.0)

        # Pencere İkonunu Ayarla
        if os.path.exists("logo.ico"):
            try:
                self.iconbitmap("logo.ico")
            except Exception:
                pass

        # Windows Glassmorphism / Acrylic Efektlerini Uygula
        if pywinstyles:
            try:
                pywinstyles.apply_style(self, "acrylic")
                pywinstyles.change_header_color(self, COLORS["bg_deep"])
                pywinstyles.change_border_color(self, COLORS["accent"])
                pywinstyles.change_title_color(self, "white")
            except Exception:
                pass

        # Genel Ayar Değişkenleri
        self.var_sound_enabled = ctk.BooleanVar(value=True)
        self.var_tray_enabled = ctk.BooleanVar(value=False)

        # Kapatıldığında temizlik yapması için protokol ekleme
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # ── ANA İÇERİK ──
        self._build_header()
        self._build_tabs()
        self._build_status_bar()

        # Fade-in Animasyonunu Tetikle
        self.fade_in()

        # Global Klavye Dinleyicisini Başlat
        self.listener = keyboard.Listener(on_press=self.on_global_key_press)
        self.listener.start()

        # Global Fare Dinleyicisini Başlat
        self.mouse_listener = mouse.Listener(on_click=self.on_global_mouse_click)
        self.mouse_listener.start()

    # ──────────────────────────────────────────────────────
    #  HEADER – Logo + Başlık + Alt Başlık
    # ──────────────────────────────────────────────────────

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=28, pady=(20, 4))

        # Logo
        self.logo_image = ctk.CTkImage(
            light_image=create_premium_logo(),
            dark_image=create_premium_logo(),
            size=(48, 48)
        )
        logo_lbl = ctk.CTkLabel(header, image=self.logo_image, text="")
        logo_lbl.pack(side="left", padx=(0, 14))

        # Başlık alanı
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", fill="y")

        ctk.CTkLabel(
            title_frame,
            text="MantıClicker",
            font=ctk.CTkFont(family=FONT_FAMILY, size=26, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_frame,
            text="Çoklu Tuş Destekli Gelişmiş Makro Aracı",
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_muted"],
        ).pack(anchor="w", pady=(0, 0))

        # Başlığın altında ince neon çizgi
        neon_line = ctk.CTkFrame(self, height=2, fg_color=COLORS["accent"], corner_radius=1)
        neon_line.pack(fill="x", padx=28, pady=(8, 0))

        # Gradient fade (çizgi altı solma efekti)
        fade_line = ctk.CTkFrame(self, height=1, fg_color=COLORS["border"], corner_radius=0)
        fade_line.pack(fill="x", padx=60, pady=(0, 4))

    # ──────────────────────────────────────────────────────
    #  TABS – Sekmeler
    # ──────────────────────────────────────────────────────

    def _build_tabs(self):
        self.tabview = ctk.CTkTabview(
            self,
            width=556, height=460,
            fg_color=COLORS["bg_dark"],
            segmented_button_fg_color=COLORS["bg_card"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color=COLORS["accent_hover"],
            segmented_button_unselected_color=COLORS["bg_card"],
            segmented_button_unselected_hover_color=COLORS["bg_card_hover"],
            corner_radius=14,
            border_width=1,
            border_color=COLORS["border"],
        )
        self.tabview.pack(padx=22, pady=(8, 6))

        self.tab_mouse = self.tabview.add("  🖱  Fare Makrosu  ")
        self.tab_keyboard = self.tabview.add("  ⌨  Klavye Makrosu  ")
        self.tab_settings = self.tabview.add("  ⚙  Genel Ayarlar  ")

        # Her sekmeye koyu arka plan
        for tab in [self.tab_mouse, self.tab_keyboard, self.tab_settings]:
            tab.configure(fg_color=COLORS["bg_dark"])

        self.setup_mouse_tab()
        self.setup_keyboard_tab()
        self.setup_settings_tab()

    # ──────────────────────────────────────────────────────
    #  STATUS BAR
    # ──────────────────────────────────────────────────────

    def _build_status_bar(self):
        bar_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=8, height=30)
        bar_frame.pack(fill="x", padx=22, pady=(0, 10))

        self.status_bar = ctk.CTkLabel(
            bar_frame,
            text="⚡  Hazır — Kısayol tuşlarıyla arka planda çalıştırabilirsiniz.",
            font=ctk.CTkFont(family=FONT_FAMILY, size=11),
            text_color=COLORS["text_muted"],
        )
        self.status_bar.pack(padx=12, pady=6)

    # ══════════════════════════════════════════════════════
    #  FARE MAKROSU SEKMESİ
    # ══════════════════════════════════════════════════════

    def setup_mouse_tab(self):
        container = self.tab_mouse

        # ── Kart 1: Tıklama Ayarları ──
        card1 = GlassCard(container)
        card1.pack(fill="x", padx=16, pady=(12, 6))

        SectionTitle(card1, "Tıklama Ayarları", icon="🎯").pack(
            fill="x", padx=16, pady=(12, 8))

        # CPS Satırı
        row_cps = ctk.CTkFrame(card1, fg_color="transparent")
        row_cps.pack(fill="x", padx=16, pady=(0, 12))

        FieldLabel(row_cps, text="CPS (Tıklama Hızı)").pack(side="left")

        cps_right = ctk.CTkFrame(row_cps, fg_color="transparent")
        cps_right.pack(side="right")

        self.entry_cps = ctk.CTkEntry(
            cps_right, width=48, height=32, justify="center",
            corner_radius=8, font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["cyan_glow"],
        )
        self.entry_cps.pack(side="right", padx=(8, 0))
        self.entry_cps.insert(0, "10")
        self.entry_cps.bind("<FocusOut>", self.on_cps_entry_change)
        self.entry_cps.bind("<Return>", self.on_cps_entry_change)

        self.slider_cps = ctk.CTkSlider(
            cps_right, from_=1, to=60, number_of_steps=59, width=160,
            command=self.on_cps_slider_move,
            button_color=COLORS["cyan"],
            button_hover_color=COLORS["cyan_glow"],
            progress_color=COLORS["accent"],
            fg_color=COLORS["border"],
        )
        self.slider_cps.pack(side="right")
        self.slider_cps.set(10)

        # ── Kart 2: Kontrol ──
        card2 = GlassCard(container)
        card2.pack(fill="x", padx=16, pady=(6, 6))

        SectionTitle(card2, "Kontrol", icon="⚡").pack(
            fill="x", padx=16, pady=(12, 8))

        # Sol Tık Kısayol Satırı
        row_hk_left = ctk.CTkFrame(card2, fg_color="transparent")
        row_hk_left.pack(fill="x", padx=16, pady=(0, 8))

        FieldLabel(row_hk_left, text="Sol Tık Kısayolu").pack(side="left")
        self.btn_m_hk_left = ctk.CTkButton(
            row_hk_left, text=key_to_string(mouse_hotkey_left),
            width=140, height=32, corner_radius=8,
            fg_color=COLORS["bg_input"], hover_color=COLORS["bg_card_hover"],
            border_width=1, border_color=COLORS["border"],
            text_color=COLORS["text_primary"], font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            command=lambda: self.start_binding("mouse_hotkey_left")
        )
        self.btn_m_hk_left.pack(side="right")

        # Sağ Tık Kısayol Satırı
        row_hk_right = ctk.CTkFrame(card2, fg_color="transparent")
        row_hk_right.pack(fill="x", padx=16, pady=(0, 8))

        FieldLabel(row_hk_right, text="Sağ Tık Kısayolu").pack(side="left")
        self.btn_m_hk_right = ctk.CTkButton(
            row_hk_right, text=key_to_string(mouse_hotkey_right),
            width=140, height=32, corner_radius=8,
            fg_color=COLORS["bg_input"], hover_color=COLORS["bg_card_hover"],
            border_width=1, border_color=COLORS["border"],
            text_color=COLORS["text_primary"], font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            command=lambda: self.start_binding("mouse_hotkey_right")
        )
        self.btn_m_hk_right.pack(side="right")

        # Durum Satırı - Sol
        row_status_l = ctk.CTkFrame(card2, fg_color="transparent")
        row_status_l.pack(fill="x", padx=16, pady=(0, 4))
        FieldLabel(row_status_l, text="Sol Tık Durum").pack(side="left")
        status_l_right = ctk.CTkFrame(row_status_l, fg_color="transparent")
        status_l_right.pack(side="right")
        self.m_status_l_ind = NeonStatusLED(status_l_right, size=20, bg_color=COLORS["bg_dark"])
        self.m_status_l_ind.pack(side="right", padx=(8, 0))
        self.lbl_m_status_l = ctk.CTkLabel(status_l_right, text="PASİF", font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=COLORS["danger"])
        self.lbl_m_status_l.pack(side="right")

        # Durum Satırı - Sağ
        row_status_r = ctk.CTkFrame(card2, fg_color="transparent")
        row_status_r.pack(fill="x", padx=16, pady=(0, 8))
        FieldLabel(row_status_r, text="Sağ Tık Durum").pack(side="left")
        status_r_right = ctk.CTkFrame(row_status_r, fg_color="transparent")
        status_r_right.pack(side="right")
        self.m_status_r_ind = NeonStatusLED(status_r_right, size=20, bg_color=COLORS["bg_dark"])
        self.m_status_r_ind.pack(side="right", padx=(8, 0))
        self.lbl_m_status_r = ctk.CTkLabel(status_r_right, text="PASİF", font=ctk.CTkFont(family=FONT_FAMILY, size=12, weight="bold"), text_color=COLORS["danger"])
        self.lbl_m_status_r.pack(side="right")

        # Anti-Cheat Checkbox
        self.var_m_jitter = ctk.BooleanVar(value=False)
        self.chk_m_jitter = ctk.CTkCheckBox(
            card2, text="  Anti-Cheat Koruması (Rastgele Jitter Tıklama)",
            variable=self.var_m_jitter, command=self.update_mouse_settings,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12), text_color=COLORS["text_secondary"],
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"], checkmark_color=COLORS["text_primary"], corner_radius=6,
        )
        self.chk_m_jitter.pack(padx=16, pady=(0, 12), anchor="w")

        # ── Ana Aksiyon Butonları ──
        self.btn_m_toggle_left = BigActionButton(
            container, text=f"▶  SOL TIK BAŞLAT  ({key_to_string(mouse_hotkey_left)})",
            command=self.toggle_mouse_left, height=40
        )
        self.btn_m_toggle_left.pack(fill="x", padx=16, pady=(4, 4))
        
        self.btn_m_toggle_right = BigActionButton(
            container, text=f"▶  SAĞ TIK BAŞLAT  ({key_to_string(mouse_hotkey_right)})",
            command=self.toggle_mouse_right, height=40
        )
        self.btn_m_toggle_right.pack(fill="x", padx=16, pady=(0, 8))

    # ══════════════════════════════════════════════════════
    #  KLAVYE MAKROSU SEKMESİ
    # ══════════════════════════════════════════════════════

    def setup_keyboard_tab(self):
        container = self.tab_keyboard

        # ── Kart 1: Hedef Tuşlar ──
        card1 = GlassCard(container)
        card1.pack(fill="x", padx=16, pady=(12, 6))

        SectionTitle(card1, "Hedef Tuşlar", icon="🎹").pack(
            fill="x", padx=16, pady=(12, 8))

        row_keys = ctk.CTkFrame(card1, fg_color="transparent")
        row_keys.pack(fill="x", padx=16, pady=(0, 8))

        FieldLabel(row_keys, text="Basılacak Tuşlar").pack(side="left")
        self.lbl_k_target_list = ctk.CTkLabel(
            row_keys, text=self.get_keys_list_string(),
            font=ctk.CTkFont(family=FONT_FAMILY, size=12, slant="italic"),
            text_color=COLORS["cyan_glow"], wraplength=200, justify="right"
        )
        self.lbl_k_target_list.pack(side="right")

        # Tuş Ekle / Temizle
        btn_frame = ctk.CTkFrame(card1, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 12))

        self.btn_k_add = NeonButton(
            btn_frame, text="＋  Tuş Ekle", accent=COLORS["success"],
            hover_color=COLORS["success_glow"],
            command=lambda: self.start_binding("keyboard_target"),
            width=130, height=32,
        )
        self.btn_k_add.pack(side="left", padx=(0, 8))

        self.btn_k_clear = NeonButton(
            btn_frame, text="✕  Listeyi Temizle", accent=COLORS["text_muted"],
            hover_color=COLORS["bg_card_hover"],
            command=self.clear_target_keys,
            width=130, height=32,
        )
        self.btn_k_clear.pack(side="left")

        # ── Kart 2: Mod ve Hız Ayarları ──
        card2 = GlassCard(container)
        card2.pack(fill="x", padx=16, pady=(6, 6))

        SectionTitle(card2, "Mod & Hız Ayarları", icon="⏱").pack(
            fill="x", padx=16, pady=(12, 8))

        # Çalışma Modu
        row_mode = ctk.CTkFrame(card2, fg_color="transparent")
        row_mode.pack(fill="x", padx=16, pady=(0, 8))

        FieldLabel(row_mode, text="Çalışma Modu").pack(side="left")
        self.seg_k_mode = ctk.CTkSegmentedButton(
            row_mode, values=["Basılı Tut", "Bas-Bırak"],
            command=self.on_keyboard_mode_change,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            fg_color=COLORS["bg_input"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            unselected_color=COLORS["bg_card"],
            unselected_hover_color=COLORS["bg_card_hover"],
            corner_radius=8,
        )
        self.seg_k_mode.pack(side="right")
        self.seg_k_mode.set("Basılı Tut")

        # Basma Tipi
        row_type = ctk.CTkFrame(card2, fg_color="transparent")
        row_type.pack(fill="x", padx=16, pady=(0, 8))

        FieldLabel(row_type, text="Basma Tipi").pack(side="left")
        self.combo_k_type = ctk.CTkOptionMenu(
            row_type, values=["Aynı Anda (Together)", "Sırayla (Sequence)"],
            command=self.update_keyboard_settings,
            state="disabled",
            width=180, height=32, corner_radius=8,
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        )
        self.combo_k_type.pack(side="right")
        self.combo_k_type.set("Aynı Anda (Together)")

        # Gecikme
        row_delay = ctk.CTkFrame(card2, fg_color="transparent")
        row_delay.pack(fill="x", padx=16, pady=(0, 12))

        FieldLabel(row_delay, text="Hız / Gecikme (ms)").pack(side="left")
        self.entry_k_delay = ctk.CTkEntry(
            row_delay, width=80, height=32, justify="center",
            corner_radius=8, font=ctk.CTkFont(family=FONT_FAMILY, size=13),
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
        )
        self.entry_k_delay.pack(side="right")
        self.entry_k_delay.insert(0, "100")
        self.entry_k_delay.configure(state="disabled")
        self.entry_k_delay.bind("<FocusOut>", self.update_keyboard_settings)
        self.entry_k_delay.bind("<Return>", self.update_keyboard_settings)

        # ── Kart 3: Kontrol ──
        card3 = GlassCard(container)
        card3.pack(fill="x", padx=16, pady=(6, 6))

        inner3 = ctk.CTkFrame(card3, fg_color="transparent")
        inner3.pack(fill="x", padx=16, pady=10)

        # Kısayol
        row_hk = ctk.CTkFrame(inner3, fg_color="transparent")
        row_hk.pack(fill="x", pady=(0, 8))

        FieldLabel(row_hk, text="Çalıştırma Kısayolu").pack(side="left")
        self.btn_k_hk = ctk.CTkButton(
            row_hk, text=key_to_string(keyboard_hotkey),
            width=140, height=32, corner_radius=8,
            fg_color=COLORS["bg_input"],
            hover_color=COLORS["bg_card_hover"],
            border_width=1, border_color=COLORS["border"],
            text_color=COLORS["text_primary"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            command=lambda: self.start_binding("keyboard_hotkey")
        )
        self.btn_k_hk.pack(side="right")

        # Durum
        row_status = ctk.CTkFrame(inner3, fg_color="transparent")
        row_status.pack(fill="x", pady=(0, 4))

        FieldLabel(row_status, text="Durum").pack(side="left")

        status_right = ctk.CTkFrame(row_status, fg_color="transparent")
        status_right.pack(side="right")

        self.k_status_indicator = NeonStatusLED(status_right, size=24,
                                                bg_color=COLORS["bg_dark"])
        self.k_status_indicator.pack(side="right", padx=(8, 0))

        self.lbl_k_status = ctk.CTkLabel(
            status_right, text="PASİF",
            font=ctk.CTkFont(family=FONT_FAMILY, size=13, weight="bold"),
            text_color=COLORS["danger"]
        )
        self.lbl_k_status.pack(side="right")

        # Anti-Cheat
        self.var_k_jitter = ctk.BooleanVar(value=False)
        self.chk_k_jitter = ctk.CTkCheckBox(
            container, text="  Anti-Cheat Koruması (Rastgele Jitter Basım)",
            variable=self.var_k_jitter,
            command=self.update_keyboard_settings,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_secondary"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            checkmark_color=COLORS["text_primary"],
            corner_radius=6,
        )
        self.chk_k_jitter.pack(padx=16, pady=(6, 4), anchor="w")

        # Ana Buton
        self.btn_k_toggle = BigActionButton(
            container, text=f"▶  BAŞLAT  ({key_to_string(keyboard_hotkey)})",
            command=self.toggle_keyboard_macro
        )
        self.btn_k_toggle.pack(fill="x", padx=16, pady=(6, 6))

    # ══════════════════════════════════════════════════════
    #  GENEL AYARLAR SEKMESİ
    # ══════════════════════════════════════════════════════

    def setup_settings_tab(self):
        container = self.tab_settings

        # ── Kart 1: Profil Yönetimi ──
        card1 = GlassCard(container)
        card1.pack(fill="x", padx=16, pady=(12, 6))

        SectionTitle(card1, "Profil Yönetimi", icon="💾").pack(
            fill="x", padx=16, pady=(12, 10))

        pbf = ctk.CTkFrame(card1, fg_color="transparent")
        pbf.pack(fill="x", padx=16, pady=(0, 14))

        self.btn_save_profile = NeonButton(
            pbf, text="📥  Profil Kaydet", accent=COLORS["accent"],
            command=self.save_profile
        )
        self.btn_save_profile.pack(side="left", padx=(0, 8), expand=True, fill="x")

        self.btn_load_profile = NeonButton(
            pbf, text="📤  Profil Yükle", accent=COLORS["success"],
            hover_color=COLORS["success_glow"],
            command=self.load_profile
        )
        self.btn_load_profile.pack(side="left", padx=(8, 0), expand=True, fill="x")

        # ── Kart 2: Sesli Bildirim ──
        card2 = GlassCard(container)
        card2.pack(fill="x", padx=16, pady=(6, 6))

        SectionTitle(card2, "Sesli Bildirim Ayarları", icon="🔊").pack(
            fill="x", padx=16, pady=(12, 10))

        sound_row = ctk.CTkFrame(card2, fg_color="transparent")
        sound_row.pack(fill="x", padx=16, pady=(0, 14))

        self.sw_sound = ctk.CTkSwitch(
            sound_row, text="  Sesli Bildirim Aktif",
            variable=self.var_sound_enabled,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_secondary"],
            fg_color=COLORS["border"],
            progress_color=COLORS["accent"],
            button_color=COLORS["text_primary"],
            button_hover_color=COLORS["accent_hover"],
        )
        self.sw_sound.pack(side="left")

        self.combo_sound = ctk.CTkOptionMenu(
            sound_row, values=["Klasik", "Melodik", "Çift Tık", "Bas"],
            width=120, height=32, corner_radius=8,
            fg_color=COLORS["bg_input"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            dropdown_hover_color=COLORS["bg_card_hover"],
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
        )
        self.combo_sound.pack(side="right")
        self.combo_sound.set("Klasik")

        # ── Kart 3: Sistem Tepsisi ──
        card3 = GlassCard(container)
        card3.pack(fill="x", padx=16, pady=(6, 6))

        SectionTitle(card3, "Sistem Tepsisi", icon="📌").pack(
            fill="x", padx=16, pady=(12, 10))

        tray_row = ctk.CTkFrame(card3, fg_color="transparent")
        tray_row.pack(fill="x", padx=16, pady=(0, 14))

        self.sw_tray = ctk.CTkSwitch(
            tray_row, text="  Kapatınca Arka Plana At (Sistem Tepsisi)",
            variable=self.var_tray_enabled,
            font=ctk.CTkFont(family=FONT_FAMILY, size=12),
            text_color=COLORS["text_secondary"],
            fg_color=COLORS["border"],
            progress_color=COLORS["accent"],
            button_color=COLORS["text_primary"],
            button_hover_color=COLORS["accent_hover"],
        )
        self.sw_tray.pack(side="left")

    # ══════════════════════════════════════════════════════
    #  BACKEND FONKSİYONLARI (KORUNDU)
    # ══════════════════════════════════════════════════════

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
        try:
            cps = int(self.slider_cps.get())
        except ValueError:
            cps = 10

        clicker_left.cps = cps
        clicker_right.cps = cps

        jitter = self.var_m_jitter.get() if hasattr(self, 'var_m_jitter') else False
        clicker_left.jitter = jitter
        clicker_right.jitter = jitter

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

        keyer.jitter = self.var_k_jitter.get() if hasattr(self, 'var_k_jitter') else False

    # ── Kısayol / Tuş Atama Yönetimi ──

    def start_binding(self, mode):
        global binding_mode
        binding_mode = mode

        if mode == "mouse_hotkey_left":
            self.status_bar.configure(text="⏳  Sol Tık Kısayol Tuşu bekleniyor... İptal için ESC.", text_color=COLORS["warning"])
            self.btn_m_hk_left.configure(text="⌛ Basın...", fg_color=COLORS["warning"], text_color=COLORS["bg_deep"])
        elif mode == "mouse_hotkey_right":
            self.status_bar.configure(text="⏳  Sağ Tık Kısayol Tuşu bekleniyor... İptal için ESC.", text_color=COLORS["warning"])
            self.btn_m_hk_right.configure(text="⌛ Basın...", fg_color=COLORS["warning"], text_color=COLORS["bg_deep"])
        elif mode == "keyboard_hotkey":
            self.status_bar.configure(
                text="⏳  Kısayol Tuşu bekleniyor... İptal için ESC.",
                text_color=COLORS["warning"])
            self.btn_k_hk.configure(text="⌛ Basın...",
                                    fg_color=COLORS["warning"],
                                    text_color=COLORS["bg_deep"])
        elif mode == "keyboard_target":
            self.status_bar.configure(
                text="⏳  Eklenecek Hedef Tuşu basın... İptal için ESC.",
                text_color=COLORS["warning"])
            self.btn_k_add.configure(text="⌛ Tuşa Basın...",
                                     fg_color=COLORS["warning"])

    def stop_binding_ui(self):
        self.status_bar.configure(
            text="⚡  Hazır — Kısayol tuşlarıyla arka planda çalıştırabilirsiniz.",
            text_color=COLORS["text_muted"])
        self.btn_m_hk_left.configure(
            text=key_to_string(mouse_hotkey_left),
            fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"], hover_color=COLORS["bg_card_hover"])
        self.btn_m_hk_right.configure(
            text=key_to_string(mouse_hotkey_right),
            fg_color=COLORS["bg_input"], text_color=COLORS["text_primary"], hover_color=COLORS["bg_card_hover"])
        self.btn_k_hk.configure(
            text=key_to_string(keyboard_hotkey),
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text_primary"],
            hover_color=COLORS["bg_card_hover"])
        self.btn_k_add.configure(
            text="＋  Tuş Ekle",
            fg_color=COLORS["success"],
            hover_color=COLORS["success_glow"])
        self.lbl_k_target_list.configure(text=self.get_keys_list_string())
        self.btn_m_toggle_left.configure(text=f"▶  SOL TIK BAŞLAT  ({key_to_string(mouse_hotkey_left)})")
        self.btn_m_toggle_right.configure(text=f"▶  SAĞ TIK BAŞLAT  ({key_to_string(mouse_hotkey_right)})")
        self.btn_k_toggle.configure(text=f"▶  BAŞLAT  ({key_to_string(keyboard_hotkey)})")

    # ── Global Fare Tıklama Yakalayıcı ──

    def on_global_mouse_click(self, x, y, button, pressed):
        if pressed:
            global binding_mode
            if binding_mode is not None:
                if binding_mode == "keyboard_target":
                    return
                if button in [Button.left, Button.right]:
                    return
            self.on_global_key_press(button)

    # ── Global Kısayol Yakalayıcı ──

    def on_global_key_press(self, key):
        global binding_mode, mouse_hotkey_left, mouse_hotkey_right, keyboard_hotkey, keyboard_target_keys

        if binding_mode is not None:
            if key == Key.esc:
                binding_mode = None
                self.after(0, self.stop_binding_ui)
                return

            if binding_mode == "mouse_hotkey_left":
                if compare_keys(key, keyboard_hotkey) or compare_keys(key, mouse_hotkey_right):
                    self.after(0, lambda: messagebox.showwarning("Çakışma", "Bu tuş zaten kullanımda."))
                else:
                    mouse_hotkey_left = key
            elif binding_mode == "mouse_hotkey_right":
                if compare_keys(key, keyboard_hotkey) or compare_keys(key, mouse_hotkey_left):
                    self.after(0, lambda: messagebox.showwarning("Çakışma", "Bu tuş zaten kullanımda."))
                else:
                    mouse_hotkey_right = key
            elif binding_mode == "keyboard_hotkey":
                if compare_keys(key, mouse_hotkey_left) or compare_keys(key, mouse_hotkey_right):
                    self.after(0, lambda: messagebox.showwarning("Çakışma", "Bu tuş Fare Makrosu tarafından kullanılmaktadır."))
                else:
                    keyboard_hotkey = key
            elif binding_mode == "keyboard_target":
                if compare_keys(key, keyboard_hotkey) or compare_keys(key, mouse_hotkey_left) or compare_keys(key, mouse_hotkey_right):
                    self.after(0, lambda: messagebox.showwarning(
                        "Çakışma Hatası",
                        "Hedef tuş, Kısayol Tuşları ile aynı olamaz."))
                else:
                    exists = any(compare_keys(key, k) for k in keyboard_target_keys)
                    if not exists:
                        keyboard_target_keys.append(key)
                    else:
                        self.after(0, lambda: messagebox.showinfo(
                            "Tuş Zaten Ekli",
                            "Bu tuş zaten hedef tuşlar listenizde bulunuyor."))

            binding_mode = None
            self.after(0, self.stop_binding_ui)
            self.after(0, self.update_keyboard_settings)
            return

        if compare_keys(key, mouse_hotkey_left):
            self.after(0, self.toggle_mouse_left)
        elif compare_keys(key, mouse_hotkey_right):
            self.after(0, self.toggle_mouse_right)
        elif compare_keys(key, keyboard_hotkey):
            self.after(0, self.toggle_keyboard_macro)

    # ── Fare Makrosu Başlat / Durdur ──

    # ── Fare Makrosu Başlat / Durdur (SOL TIK) ──
    def toggle_mouse_left(self):
        if clicker_left.running:
            clicker_left.stop_clicking()
            self.trigger_sound("stop")
            self.lbl_m_status_l.configure(text="PASİF", text_color=COLORS["danger"])
            self.m_status_l_ind.set_status(False)
            self.btn_m_toggle_left.configure(
                text=f"▶  SOL TIK BAŞLAT  ({key_to_string(mouse_hotkey_left)})",
                fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], border_color=COLORS["accent"])
            self.btn_m_toggle_left.set_active(False)
            self.slider_cps.configure(state="normal")
            self.entry_cps.configure(state="normal")
            self.btn_m_hk_left.configure(state="normal")
            self.chk_m_jitter.configure(state="normal")
        else:
            self.update_mouse_settings()
            clicker_left.start_clicking()
            self.trigger_sound("start")
            self.lbl_m_status_l.configure(text="AKTİF", text_color=COLORS["success"])
            self.m_status_l_ind.set_status(True)
            self.btn_m_toggle_left.configure(
                text=f"⏹  DURDUR  ({key_to_string(mouse_hotkey_left)})",
                fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], border_color=COLORS["danger"])
            self.btn_m_toggle_left.set_active(True)
            self.slider_cps.configure(state="disabled")
            self.entry_cps.configure(state="disabled")
            self.btn_m_hk_left.configure(state="disabled")
            self.chk_m_jitter.configure(state="disabled")

    # ── Fare Makrosu Başlat / Durdur (SAĞ TIK) ──
    def toggle_mouse_right(self):
        if clicker_right.running:
            clicker_right.stop_clicking()
            self.trigger_sound("stop")
            self.lbl_m_status_r.configure(text="PASİF", text_color=COLORS["danger"])
            self.m_status_r_ind.set_status(False)
            self.btn_m_toggle_right.configure(
                text=f"▶  SAĞ TIK BAŞLAT  ({key_to_string(mouse_hotkey_right)})",
                fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"], border_color=COLORS["accent"])
            self.btn_m_toggle_right.set_active(False)
            self.slider_cps.configure(state="normal")
            self.entry_cps.configure(state="normal")
            self.btn_m_hk_right.configure(state="normal")
            self.chk_m_jitter.configure(state="normal")
        else:
            self.update_mouse_settings()
            clicker_right.start_clicking()
            self.trigger_sound("start")
            self.lbl_m_status_r.configure(text="AKTİF", text_color=COLORS["success"])
            self.m_status_r_ind.set_status(True)
            self.btn_m_toggle_right.configure(
                text=f"⏹  DURDUR  ({key_to_string(mouse_hotkey_right)})",
                fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"], border_color=COLORS["danger"])
            self.btn_m_toggle_right.set_active(True)
            self.slider_cps.configure(state="disabled")
            self.entry_cps.configure(state="disabled")
            self.btn_m_hk_right.configure(state="disabled")
            self.chk_m_jitter.configure(state="disabled")

    # ── Klavye Makrosu Başlat / Durdur ──

    def toggle_keyboard_macro(self):
        if keyer.running:
            keyer.stop_keyer()
            self.trigger_sound("stop")
            self.lbl_k_status.configure(text="PASİF", text_color=COLORS["danger"])
            self.k_status_indicator.set_status(False)
            self.btn_k_toggle.configure(
                text=f"▶  BAŞLAT  ({key_to_string(keyboard_hotkey)})",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                border_color=COLORS["accent"])
            self.btn_k_toggle.set_active(False)
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
                messagebox.showwarning("Hedef Tuş Yok",
                                       "Lütfen önce basılacak en az bir hedef tuş belirleyin.")
                return
            self.update_keyboard_settings()
            keyer.start_keyer()
            self.trigger_sound("start")
            self.lbl_k_status.configure(text="AKTİF", text_color=COLORS["success"])
            self.k_status_indicator.set_status(True)
            self.btn_k_toggle.configure(
                text=f"⏹  DURDUR  ({key_to_string(keyboard_hotkey)})",
                fg_color=COLORS["danger"],
                hover_color=COLORS["danger_hover"],
                border_color=COLORS["danger"])
            self.btn_k_toggle.set_active(True)
            self.btn_k_add.configure(state="disabled")
            self.btn_k_clear.configure(state="disabled")
            self.seg_k_mode.configure(state="disabled")
            self.entry_k_delay.configure(state="disabled")
            self.combo_k_type.configure(state="disabled")
            self.btn_k_hk.configure(state="disabled")
            self.chk_k_jitter.configure(state="disabled")

    # ── Pencere Animasyonları ──

    def fade_in(self):
        alpha = self.attributes('-alpha')
        if alpha < 1.0:
            alpha += 0.05
            self.attributes('-alpha', alpha)
            self.after(10, self.fade_in)

    def fade_out_to_tray(self):
        alpha = self.attributes('-alpha')
        if alpha > 0.0:
            alpha -= 0.08
            self.attributes('-alpha', alpha)
            self.after(10, self.fade_out_to_tray)
        else:
            self.withdraw()
            self.attributes('-alpha', 1.0)

    def on_closing(self):
        if self.var_tray_enabled.get():
            self.fade_out_to_tray()
            self.minimize_to_tray()
        else:
            self.quit_app_completely()

    def quit_app_completely(self):
        clicker_left.program_running = False
        clicker_left.stop_clicking()
        
        clicker_right.program_running = False
        clicker_right.stop_clicking()

        keyer.program_running = False
        keyer.stop_keyer()

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
        def show_window(icon, item):
            icon.stop()
            self.after(0, self.deiconify_with_fade)

        def quit_app(icon, item):
            icon.stop()
            self.after(0, self.quit_app_completely)

        icon_image = create_premium_logo()
        menu = (item('Göster', show_window), item('Çıkış', quit_app))
        self.tray_icon = pystray.Icon("MantıClicker", icon_image, "MantıClicker", menu)

        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def deiconify_with_fade(self):
        self.deiconify()
        self.attributes('-alpha', 0.0)
        self.fade_in()

    # ── Profil Kaydet / Yükle ──

    def save_profile(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            title="Profili Kaydet"
        )
        if not file_path:
            return

        try:
            global mouse_hotkey_left, mouse_hotkey_right, keyboard_hotkey, keyboard_target_keys

            profile_data = {
                "mouse_cps": int(self.slider_cps.get()),
                "mouse_hotkey_left": serialize_key(mouse_hotkey_left),
                "mouse_hotkey_right": serialize_key(mouse_hotkey_right),
                "mouse_jitter": self.var_m_jitter.get(),
                "keyboard_target_keys": [serialize_key(k) for k in keyboard_target_keys],
                "keyboard_mode": self.seg_k_mode.get(),
                "keyboard_tap_type": self.combo_k_type.get(),
                "keyboard_delay": self.entry_k_delay.get(),
                "keyboard_hotkey": serialize_key(keyboard_hotkey),
                "keyboard_jitter": self.var_k_jitter.get(),
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
            global mouse_hotkey_left, mouse_hotkey_right, keyboard_hotkey, keyboard_target_keys

            with open(file_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)

            if "mouse_cps" in profile_data:
                cps = profile_data["mouse_cps"]
                self.slider_cps.set(cps)
                self.entry_cps.delete(0, "end")
                self.entry_cps.insert(0, str(cps))
                
            if "mouse_hotkey_left" in profile_data:
                loaded_m_hk_l = deserialize_key(profile_data["mouse_hotkey_left"])
                if loaded_m_hk_l:
                    mouse_hotkey_left = loaded_m_hk_l
            if "mouse_hotkey_right" in profile_data:
                loaded_m_hk_r = deserialize_key(profile_data["mouse_hotkey_right"])
                if loaded_m_hk_r:
                    mouse_hotkey_right = loaded_m_hk_r
                    
            # Eski profiller için geriye dönük uyumluluk
            if "mouse_hotkey" in profile_data and "mouse_hotkey_left" not in profile_data:
                loaded_m_hk = deserialize_key(profile_data["mouse_hotkey"])
                if loaded_m_hk:
                    mouse_hotkey_left = loaded_m_hk

            if "mouse_jitter" in profile_data:
                self.var_m_jitter.set(profile_data["mouse_jitter"])

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

            if "sound_enabled" in profile_data:
                self.var_sound_enabled.set(profile_data["sound_enabled"])
            if "sound_profile" in profile_data:
                self.combo_sound.set(profile_data["sound_profile"])
            if "minimize_to_tray" in profile_data:
                self.var_tray_enabled.set(profile_data["minimize_to_tray"])

            self.update_mouse_settings()
            self.update_keyboard_settings()
            self.stop_binding_ui()

            messagebox.showinfo("Başarılı", "Profil başarıyla yüklendi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Profil yüklenirken bir hata oluştu:\n{e}")

    # ── Ses Efektleri ──

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


# ══════════════════════════════════════════════════════════════
#  PROGRAM GİRİŞ NOKTASI
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not os.path.exists("logo.ico"):
        try:
            create_premium_logo().save("logo.ico", format="ICO")
        except Exception:
            pass

    app = MantıClickerApp()
    app.mainloop()
