import customtkinter as ctk
import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import os
import requests
import re
import keyboard
import json
from PIL import Image, ImageDraw, ImageTk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# --- THEME MANAGER ---
class ThemeManager:
    """Gerencia os temas da aplicação (Observer Pattern)"""
    THEMES = {
        "Red": {
            "bg_app": "#0b0b0f",
            "bg_sidebar": "#07070a",
            "bg_card": "#121218",
            "bg_input": "#000000",
            "border": "#272730",
            "accent": "#ff0048",
            "accent_hover": "#cc003a",
            "text_main": "#ffffff",
            "text_muted": "#8a8a98"
        },
        "Purple": {
            "bg_app": "#050505",
            "bg_sidebar": "#030303",
            "bg_card": "#0f0f12",
            "bg_input": "#08080a",
            "border": "#1f1f26",
            "accent": "#6d28d9",
            "accent_hover": "#5b21b6",
            "text_main": "#ffffff",
            "text_muted": "#8b8b99"
        },
        "Matrix Green": {
            "bg_app": "#020804",
            "bg_sidebar": "#010402",
            "bg_card": "#041208",
            "bg_input": "#000000",
            "border": "#0d3319",
            "accent": "#00ff41",
            "accent_hover": "#00cc33",
            "text_main": "#ffffff",
            "text_muted": "#4a7c59"
        },
        "Cyberpunk Cyan": {
            "bg_app": "#050a12",
            "bg_sidebar": "#02050a",
            "bg_card": "#091221",
            "bg_input": "#000000",
            "border": "#1a365d",
            "accent": "#00f0ff",
            "accent_hover": "#00c3cc",
            "text_main": "#ffffff",
            "text_muted": "#60a5fa"
        },
        "Solar Yellow": {
            "bg_app": "#0f0c05",
            "bg_sidebar": "#080602",
            "bg_card": "#1c160a",
            "bg_input": "#000000",
            "border": "#3d2f11",
            "accent": "#facc15",
            "accent_hover": "#eab308",
            "text_main": "#ffffff",
            "text_muted": "#a16207"
        },
        "Midnight Blue": {
            "bg_app": "#020617",
            "bg_sidebar": "#01030d",
            "bg_card": "#0f172a",
            "bg_input": "#000000",
            "border": "#1e293b",
            "accent": "#3b82f6",
            "accent_hover": "#2563eb",
            "text_main": "#ffffff",
            "text_muted": "#94a3b8"
        }
    }

    _current_theme_name = "Red"
    _subscribers = []

    @classmethod
    def get_color(cls, key):
        return cls.THEMES[cls._current_theme_name].get(key, "#ffffff")

    @classmethod
    def set_theme(cls, theme_name):
        if theme_name in cls.THEMES:
            cls._current_theme_name = theme_name
            cls.notify_all()

    @classmethod
    def subscribe(cls, widget_callback):
        if widget_callback not in cls._subscribers:
            cls._subscribers.append(widget_callback)

    @classmethod
    def notify_all(cls):
        dead_subs = []
        for sub in cls._subscribers:
            try:
                sub()
            except Exception:
                dead_subs.append(sub)
        for dead in dead_subs:
            cls._subscribers.remove(dead)

# --- CUSTOM WIDGETS ---

class NeonToggleSwitch(ctk.CTkFrame):
    def __init__(self, master, command=None, **kwargs):
        super().__init__(master, height=40, width=180, corner_radius=20, fg_color="transparent", **kwargs)
        self.command = command
        self.is_on = False
        self.pack_propagate(False)
        self.grid_propagate(False)

        self.canvas = ctk.CTkCanvas(self, width=180, height=40, bg=ThemeManager.get_color("bg_card"), highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Desenha a pílula de fundo
        self.bg_rect = self._round_rectangle(2, 2, 178, 38, radius=18, fill=ThemeManager.get_color("bg_card"), outline=ThemeManager.get_color("border"))
        
        # Desenha o círculo interno
        self.circle = self.canvas.create_oval(6, 6, 34, 34, fill=ThemeManager.get_color("text_muted"), outline="")
        self.text_id = self.canvas.create_text(90, 20, text="ENGINE OFF", fill=ThemeManager.get_color("text_muted"), font=("Segoe UI", 12, "bold"))

        self.canvas.bind("<Button-1>", self.toggle)
        ThemeManager.subscribe(self.update_theme)

    def _round_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
        points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius,
                  x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2,
                  x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius,
                  x1, y1+radius, x1, y1]
        return self.canvas.create_polygon(points, **kwargs, smooth=True)

    def update_theme(self):
        self.canvas.configure(bg=ThemeManager.get_color("bg_app"))
        if self.is_on:
            self.canvas.itemconfig(self.bg_rect, outline=ThemeManager.get_color("border"), fill=ThemeManager.get_color("bg_input"))
            self.canvas.itemconfig(self.circle, fill=ThemeManager.get_color("accent"))
            self.canvas.itemconfig(self.text_id, fill=ThemeManager.get_color("text_main"))
        else:
            self.canvas.itemconfig(self.bg_rect, outline=ThemeManager.get_color("border"), fill=ThemeManager.get_color("bg_card"))
            self.canvas.itemconfig(self.circle, fill=ThemeManager.get_color("text_muted"))
            self.canvas.itemconfig(self.text_id, fill=ThemeManager.get_color("text_muted"))

    def toggle(self, event=None):
        if self.command: self.command()

    def set_state(self, state):
        self.is_on = state
        self._animate()

    def _animate(self):
        # Para animações robustas no Tkinter, cancelamos a anterior se houver
        if hasattr(self, '_anim_id') and self._anim_id:
            try: self.after_cancel(self._anim_id)
            except: pass
            
        texto = "ENGINE ON" if self.is_on else "ENGINE OFF"
        self.canvas.itemconfig(self.text_id, text=texto)
        self.update_theme()
        
        target_circle_x = 146 if self.is_on else 6
        target_text_x = 75 if self.is_on else 105
        
        # Pega as coordenadas atuais confiantemente
        try:
            cur_circle = self.canvas.coords(self.circle)[0]
            cur_text = self.canvas.coords(self.text_id)[0]
        except:
            cur_circle = 6 if self.is_on else 146
            cur_text = 105 if self.is_on else 75
        
        import time
        self._anim_start_time = time.time()
        self._anim_duration = 0.25 # iOS-like speed (250ms)
        self._anim_time_step(cur_circle, target_circle_x, cur_text, target_text_x)

    def _anim_time_step(self, cx_start, cx_end, tx_start, tx_end):
        import time
        now = time.time()
        elapsed = now - self._anim_start_time
        progress = elapsed / self._anim_duration
        
        if progress >= 1.0:
            try:
                self.canvas.coords(self.circle, cx_end, 6, cx_end+28, 34)
                self.canvas.coords(self.text_id, tx_end, 20)
            except: pass
            return

        # iOS-like easing (Quartic Ease Out) for very smooth start and gentle stop
        ease = 1 - pow(1 - progress, 4)
        
        cur_cx = cx_start + (cx_end - cx_start) * ease
        cur_tx = tx_start + (tx_end - tx_start) * ease
        
        try:
            self.canvas.coords(self.circle, cur_cx, 6, cur_cx+28, 34)
            self.canvas.coords(self.text_id, cur_tx, 20)
            self.canvas.update_idletasks()
        except: pass
        
        self._anim_id = self.after(8, lambda: self._anim_time_step(cx_start, cx_end, tx_start, tx_end))


class InteractiveCard(ctk.CTkFrame):
    def __init__(self, master, title, shortcut, play_cmd, shortcut_cmd, **kwargs):
        super().__init__(master, height=120, corner_radius=12, fg_color="transparent", border_width=2, **kwargs)
        self.play_cmd = play_cmd
        self.shortcut_cmd = shortcut_cmd
        self.pack_propagate(False)
        self.grid_propagate(False)

        self.title_lbl = ctk.CTkLabel(self, text=title, font=("Segoe UI", 14, "bold"))
        self.title_lbl.pack(pady=(20, 5))

        self.badge = ctk.CTkLabel(self, text=shortcut if shortcut else "Sem Atalho", corner_radius=4, height=20, font=("Segoe UI", 10, "bold"))
        self.badge.pack(pady=(0, 10))

        # Action Buttons (Hidden by default)
        self.actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.btn_play = ctk.CTkButton(self.actions_frame, text="▶ Play", width=60, height=28, corner_radius=6, command=self.play_cmd, font=("Segoe UI", 12, "bold"))
        self.btn_play.pack(side="left", padx=5)

        self.btn_bind = ctk.CTkButton(self.actions_frame, text="Bind", width=60, height=28, corner_radius=6, command=self.shortcut_cmd, font=("Segoe UI", 12))
        self.btn_bind.pack(side="right", padx=5)

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        for w in self.winfo_children():
            w.bind("<Enter>", self.on_enter)
            w.bind("<Leave>", self.on_leave)

        ThemeManager.subscribe(self.update_theme)
        self.update_theme()

    def update_theme(self):
        self.configure(fg_color=ThemeManager.get_color("bg_card"), border_color=ThemeManager.get_color("border"))
        self.title_lbl.configure(text_color=ThemeManager.get_color("text_main"))
        self.badge.configure(fg_color=ThemeManager.get_color("bg_input"), text_color=ThemeManager.get_color("text_muted"))
        
        self.btn_play.configure(fg_color=ThemeManager.get_color("accent"), hover_color=ThemeManager.get_color("accent_hover"), text_color="#ffffff")
        self.btn_bind.configure(fg_color=ThemeManager.get_color("border"), hover_color=ThemeManager.get_color("bg_input"), text_color=ThemeManager.get_color("text_main"))

    def on_enter(self, event):
        self.configure(border_color=ThemeManager.get_color("accent"))
        self.actions_frame.pack(side="bottom", pady=10)
        self.title_lbl.pack_configure(pady=(15, 0))
        self.badge.pack_forget()

    def on_leave(self, event):
        # Prevent flickering if mouse goes to child widgets
        x, y = self.winfo_pointerx() - self.winfo_rootx(), self.winfo_pointery() - self.winfo_rooty()
        if 0 <= x <= self.winfo_width() and 0 <= y <= self.winfo_height(): return
        
        self.configure(border_color=ThemeManager.get_color("border"))
        self.actions_frame.pack_forget()
        self.badge.pack(pady=(0, 10))
        self.title_lbl.pack_configure(pady=(20, 5))


class ToastNotification:
    def __init__(self, master, message, type="success"):
        self.toplevel = ctk.CTkToplevel(master)
        self.toplevel.overrideredirect(True)
        self.toplevel.attributes("-topmost", True)
        self.toplevel.geometry("300x60")
        
        bg_col = ThemeManager.get_color("bg_card")
        border_col = ThemeManager.get_color("accent") if type=="success" else "#ef4444"
        
        frame = ctk.CTkFrame(self.toplevel, fg_color=bg_col, border_color=border_col, border_width=2, corner_radius=8)
        frame.pack(fill="both", expand=True)
        
        ctk.CTkLabel(frame, text=message, font=("Segoe UI", 14), text_color=ThemeManager.get_color("text_main")).pack(expand=True)

        # Position at bottom right
        master.update_idletasks()
        x = master.winfo_x() + master.winfo_width() - 320
        y = master.winfo_y() + master.winfo_height() - 80
        self.toplevel.geometry(f"+{x}+{y}")
        
        self.toplevel.after(3000, self.toplevel.destroy)


# --- MAIN APP ---

class SoundPadApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SoundPad Ultimate")
        self.geometry("1100x720")
        
        # --- CUSTOM TITLE BAR ---
        self.overrideredirect(True) # Remove OS title bar completely avoiding white borders
        self.after(10, self._set_appwindow) # Fix taskbar icon issue when overrideredirect
        
        self.title_bar = ctk.CTkFrame(self, height=35, corner_radius=0, fg_color="#000000")
        self.title_bar.pack(fill="x", side="top")
        self.title_bar.pack_propagate(False)
        
        # Title interaction
        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)
        
        logo_top = ctk.CTkLabel(self.title_bar, text=" SoundPad Ultimate", font=("Segoe UI", 12), text_color="grey", image=self.get_icon("logo", "grey", size=(16, 16)), compound="left")
        logo_top.pack(side="left", padx=10)
        logo_top.bind("<ButtonPress-1>", self.start_move)
        logo_top.bind("<B1-Motion>", self.do_move)
        
        # Window Controls
        btn_close = ctk.CTkButton(self.title_bar, text="✕", width=40, corner_radius=0, fg_color="transparent", hover_color="#ef4444", command=self.destroy)
        btn_close.pack(side="right")
        
        self.is_maximized = False
        self.btn_maximize = ctk.CTkButton(self.title_bar, text="⬜", width=40, font=("Segoe UI", 10), corner_radius=0, fg_color="transparent", hover_color="#333333", command=self.toggle_maximize)
        self.btn_maximize.pack(side="right")
        
        btn_minimize = ctk.CTkButton(self.title_bar, text="—", width=40, corner_radius=0, fg_color="transparent", hover_color="#333333", command=self.minimize)
        btn_minimize.pack(side="right")
        
        # Main App Container (after title bar)
        self.app_content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.app_content.pack(fill="both", expand=True)

        # Core Variables
        self.stream = None
        self.is_running = False
        self.is_playing_sound = False
        self.audio_data = None
        self.audio_index = 0
        self.vol_mic = 1.0
        self.vol_music_discord = 0.5
        self.vol_music_me = 0.2
        self.all_files = [] 
        
        self.config_path = "config.json"
        self.config_data = {"kill_switch": "f12", "cor_tema": "Red", "atalhos_sons": {}}
        self.load_config()

        # Layout Main (3 Columns emulation via Grid)
        self.app_content.grid_columnconfigure(1, weight=1)
        self.app_content.grid_rowconfigure(0, weight=1)

        self.setup_sidebar()

        self.center_frame = ctk.CTkFrame(self.app_content, fg_color="transparent")
        self.center_frame.grid(row=0, column=1, sticky="nsew")

        self.setup_header()
        
        self.main_container = ctk.CTkFrame(self.center_frame, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)

        ThemeManager.subscribe(self.update_theme)
        self.update_theme()

        self.devices = self.get_device_list()
        self.show_home()
        
    # --- CUSTOM WINDOW CONTROLS ---
    def _set_appwindow(self):
        # Quando overrideredirect(True), o Windows esconde o app da barra de tarefas. 
        # Este hack via ctypes força o reaparecimento do ícone lá embaixo.
        import ctypes
        import platform
        if platform.system() == "Windows":
            try:
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                GWL_EXSTYLE = -20
                WS_EX_APPWINDOW = 0x00040000
                WS_EX_TOOLWINDOW = 0x00000080
                
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                new_style = style & ~WS_EX_TOOLWINDOW | WS_EX_APPWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            except Exception as e: 
                print(f"Erro ao estilizar ícone: {e}")

    def start_move(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        # MÁGICA: Em vez do Python calcular o arrasto e travar (tearing), passamos
        # o comando nativo pro Windows (Desktop Window Manager) tratar suavemente!
        import platform
        if platform.system() == "Windows":
            import ctypes
            try:
                # Libera o clique do Tkinter
                ctypes.windll.user32.ReleaseCapture()
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                # Constante do Windows: WM_NCLBUTTONDOWN = 0x00A1
                # HTCAPTION = 2 (Simula que clicou no título)
                # PostMessage no lugar de SendMessage evita o travamento do GIL e threads!
                x = self.winfo_pointerx()
                y = self.winfo_pointery()
                lparam = (y << 16) | (x & 0xFFFF)
                ctypes.windll.user32.PostMessageW(hwnd, 0x00A1, 2, lparam)
            except Exception as e: print(e)

    def do_move(self, event):
        import platform
        if platform.system() == "Windows": return # O Windows já está fazendo isso nativamente!
        
        if self.is_maximized: return
        x = self.winfo_pointerx() - self._drag_start_x
        y = self.winfo_pointery() - self._drag_start_y
        self.geometry(f"+{x}+{y}")

    def toggle_maximize(self):
        if self.is_maximized:
            self.state('normal')
            self.is_maximized = False
            self.btn_maximize.configure(text="⬜")
        else:
            self.state('zoomed')
            self.is_maximized = True
            self.btn_maximize.configure(text="❐")
            
    def minimize(self):
        self.state('iconic')

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config_data.update(data)
            except: pass
        if self.config_data["cor_tema"] in ThemeManager.THEMES:
            ThemeManager._current_theme_name = self.config_data["cor_tema"]
        self.registrar_atalhos()

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=4)
        except: pass
        
    def registrar_atalhos(self):
        keyboard.unhook_all()
        try: keyboard.add_hotkey(self.config_data["kill_switch"], self.parar_som_agora)
        except: pass
        
        for som, tecla in self.config_data["atalhos_sons"].items():
            if tecla and os.path.exists(som):
                try: keyboard.add_hotkey(tecla, lambda s=som: self.preparar_som(s))
                except: pass

    def update_theme(self):
        self.configure(fg_color=ThemeManager.get_color("bg_app"))
        self.app_content.configure(fg_color=ThemeManager.get_color("bg_app"))
        self.title_bar.configure(fg_color=ThemeManager.get_color("bg_sidebar"))
        self.sidebar.configure(fg_color=ThemeManager.get_color("bg_sidebar"))
        self.header_frame.configure(fg_color=ThemeManager.get_color("bg_app"))
        self.entry_search.configure(fg_color=ThemeManager.get_color("bg_input"), border_color=ThemeManager.get_color("border"), text_color=ThemeManager.get_color("text_main"))
        self.combo_theme.configure(fg_color=ThemeManager.get_color("bg_input"), button_color=ThemeManager.get_color("border"), button_hover_color=ThemeManager.get_color("bg_card"), text_color=ThemeManager.get_color("text_main"))

    # --- SIDEBAR ---
    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.app_content, width=200, corner_radius=0, border_width=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Logo Icon top
        logo_lbl = ctk.CTkLabel(self.sidebar, text=" SoundPad", font=("Segoe UI", 18, "bold"), image=self.get_icon("logo", "#ffffff", size=(30, 30)), compound="left", text_color="#ffffff")
        logo_lbl.pack(pady=(20, 40), padx=20, anchor="w")

        self.nav_btns = []
        self.btn_home = self.create_nav_btn("home", "Dashboard", self.show_home)
        self.btn_settings = self.create_nav_btn("settings", "Configurações", self.show_settings)
        
        spacer = ctk.CTkLabel(self.sidebar, text="")
        spacer.pack(expand=True, fill="y")
        
        self.btn_help = self.create_nav_btn("help", "Help", self.show_help)
        self.btn_credits = self.create_nav_btn("user", "Créditos", self.show_credits)
        ctk.CTkLabel(self.sidebar, text="").pack(pady=10) # extra padding at bottom

    def create_nav_btn(self, icon_name, text, command):
        frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=50)
        frame.pack(fill="x", pady=5)
        frame.pack_propagate(False)
        frame.grid_propagate(False)

        indicator = ctk.CTkFrame(frame, width=4, corner_radius=2, fg_color="transparent")
        indicator.pack(side="left", fill="y", pady=5, padx=2)

        icon_lbl = ctk.CTkLabel(frame, text=f"  {text}", font=("Segoe UI", 14, "bold"), image=self.get_icon(icon_name, "#8a8a98", size=(24,24)), compound="left", text_color="#8a8a98")
        icon_lbl.pack(side="left", padx=10)

        def on_click(e): command()
        
        def on_enter(e):
            if frame.cget("fg_color") == "transparent":
                frame.configure(fg_color=ThemeManager.get_color("bg_card"))
        def on_leave(e):
            if indicator.cget("fg_color") == "transparent":
                frame.configure(fg_color="transparent")

        for w in [frame, indicator, icon_lbl]:
            w.bind("<Button-1>", on_click)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        btn_data = {"frame": frame, "indicator": indicator, "icon_lbl": icon_lbl, "icon_name": icon_name}
        self.nav_btns.append(btn_data)
        return btn_data

    def select_nav_btn(self, active_data):
        for data in self.nav_btns:
            data["frame"].configure(fg_color="transparent")
            data["indicator"].configure(fg_color="transparent")
            data["icon_lbl"].configure(image=self.get_icon(data["icon_name"], ThemeManager.get_color("text_muted"), size=(24,24)), text_color=ThemeManager.get_color("text_muted"))
        
        active_data["frame"].configure(fg_color=ThemeManager.get_color("bg_card"))
        active_data["indicator"].configure(fg_color=ThemeManager.get_color("accent"))
        active_data["icon_lbl"].configure(image=self.get_icon(active_data["icon_name"], "#ffffff", size=(24,24)), text_color="#ffffff")

    # --- HEADER ---
    def setup_header(self):
        self.header_frame = ctk.CTkFrame(self.center_frame, height=80, corner_radius=0)
        self.header_frame.pack(fill="x")
        self.header_frame.pack_propagate(False)

        # Engine Toggle
        toggle_container = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        toggle_container.pack(side="left", padx=30, pady=20)
        self.switch_engine = NeonToggleSwitch(toggle_container, command=self.toggle_engine)
        self.switch_engine.pack()

        # Search Bar
        self.entry_search = ctk.CTkEntry(self.header_frame, placeholder_text="Buscar sons...", width=200, height=36, corner_radius=18, border_width=1)
        self.entry_search.pack(side="left", padx=20, pady=22)
        self.entry_search.bind("<KeyRelease>", self.filtrar_sons)
        
        # Como Usar Button
        self.btn_help_header = ctk.CTkButton(self.header_frame, text="✨ Como Usar", width=120, height=36, corner_radius=8, font=("Segoe UI", 13, "bold"), command=self.show_help)
        self.btn_help_header.pack(side="left", padx=10, pady=22)
        ThemeManager.subscribe(lambda: self.btn_help_header.configure(fg_color="transparent", border_color=ThemeManager.get_color("accent"), border_width=1, text_color=ThemeManager.get_color("text_main"), hover_color=ThemeManager.get_color("bg_card")))

        # Theme Selector
        self.combo_theme = ctk.CTkOptionMenu(self.header_frame, values=list(ThemeManager.THEMES.keys()), width=150, height=36, corner_radius=8, command=self.on_theme_select)
        self.combo_theme.set(ThemeManager._current_theme_name)
        self.combo_theme.pack(side="right", padx=30, pady=22)

    def on_theme_select(self, val):
        ThemeManager.set_theme(val)
        self.config_data["cor_tema"] = val
        self.save_config()
        self.select_nav_btn(self.current_nav)

    # --- HOME / DASHBOARD ---
    def show_home(self):
        self.entry_search.pack(side="left", padx=20, pady=22) # Show search
        self.current_nav = self.btn_home
        self.select_nav_btn(self.btn_home)
        for w in self.main_container.winfo_children(): w.destroy()

        content = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=20)

        # Top Action Bar
        action_bar = ctk.CTkFrame(content, fg_color="transparent", height=50)
        action_bar.pack(fill="x", pady=(0, 20))
        
        ThemeManager.subscribe(lambda: self._update_home_texts(title_lbl, desc_lbl, btn_add))
        
        title_lbl = ctk.CTkLabel(action_bar, text="Dashboard", font=("Segoe UI", 24, "bold"), text_color=ThemeManager.get_color("text_main"))
        title_lbl.pack(side="left")
        
        desc_lbl = ctk.CTkLabel(action_bar, text=" | Gerencie seus sons rápidos", font=("Segoe UI", 14), text_color=ThemeManager.get_color("text_muted"))
        desc_lbl.pack(side="left", padx=5, pady=(5,0))

        btn_add = ctk.CTkButton(action_bar, text="+ Novo Som", height=36, corner_radius=8, font=("Segoe UI", 13, "bold"), 
                                fg_color=ThemeManager.get_color("accent"), hover_color=ThemeManager.get_color("accent_hover"), text_color="#ffffff",
                                command=self.abrir_modal_adicionar)
        btn_add.pack(side="right")

        self.scroll_sounds = ctk.CTkScrollableFrame(content, fg_color="transparent", label_text="")
        self.scroll_sounds.pack(fill="both", expand=True)

        # Responsive Grid
        for i in range(5): self.scroll_sounds.grid_columnconfigure(i, weight=1)

        self.listar_sons()

    def _update_home_texts(self, l1, l2, b1):
        try:
            l1.configure(text_color=ThemeManager.get_color("text_main"))
            l2.configure(text_color=ThemeManager.get_color("text_muted"))
            b1.configure(fg_color=ThemeManager.get_color("accent"), hover_color=ThemeManager.get_color("accent_hover"))
        except: pass

    def listar_sons(self):
        for widget in self.scroll_sounds.winfo_children(): widget.destroy()
        self.all_files = [f for f in os.listdir() if f.endswith(".mp3")]
        self.filtrar_sons()

    def filtrar_sons(self, event=None):
        termo = self.entry_search.get().lower() if hasattr(self, 'entry_search') else ""
        for widget in self.scroll_sounds.winfo_children(): widget.destroy()
        match_files = [f for f in self.all_files if termo in f.lower()]
        
        cols = 5 # Depending on resolution
        for idx, file in enumerate(match_files):
            nome_display = file.replace(".mp3", "").replace("-", " ").replace("_", " ").upper()[:20]
            shortcut = self.config_data["atalhos_sons"].get(file, "")
            
            card = InteractiveCard(self.scroll_sounds, title=nome_display, shortcut=shortcut.upper() if shortcut else "", 
                                   play_cmd=lambda f=file: self.preparar_som(f), 
                                   shortcut_cmd=None)
            card.btn_bind.configure(command=lambda f=file, btn=card.btn_bind: self.iniciar_bind_som(f, btn))
            
            row = idx // cols
            col = idx % cols
            card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")

    def iniciar_bind_som(self, arquivo, btn):
        btn.configure(text="Pressione...", fg_color=ThemeManager.get_color("accent"), text_color=ThemeManager.get_color("bg_app"))
        threading.Thread(target=self._key_worker_som, args=(arquivo, btn)).start()
        
    def _key_worker_som(self, arquivo, btn):
        try:
            k = keyboard.read_hotkey(suppress=False)
            if k == "esc":
                self.config_data["atalhos_sons"].pop(arquivo, None)
            else:
                self.config_data["atalhos_sons"][arquivo] = k
            
            self.save_config()
            self.registrar_atalhos()
            self.after(0, self.listar_sons)
            self.after(0, lambda: ToastNotification(self, "Atalho salvo!", "success"))
        except: pass

    # --- MODAL ADICIONAR ---
    def abrir_modal_adicionar(self):
        dialog = ctk.CTkInputDialog(text="Cole o link do MyInstants para baixar o áudio:", title="Adicionar Som")
        dialog.attributes("-topmost", True)
        link = dialog.get_input()
        if link:
            threading.Thread(target=self._worker_download_modal, args=(link,)).start()

    def _worker_download_modal(self, url):
        try:
            if "<iframe" in url:
                m = re.search(r'src="([^"]+)"', url)
                if m: url = m.group(1)
            html = requests.get(url).text
            m = re.search(r"https://.*?\.mp3", html)
            if m:
                mp3_url = m.group(0)
                name = mp3_url.split("/")[-1]
                if not name.endswith(".mp3"): name += ".mp3"
                content = requests.get(mp3_url).content
                with open(name, 'wb') as f: f.write(content)
                self.after(0, self.listar_sons)
                self.after(0, lambda: ToastNotification(self, "Download Concluído!", "success"))
            else: self.after(0, lambda: ToastNotification(self, "Erro: MP3 não encontrado", "error"))
        except: self.after(0, lambda: ToastNotification(self, "Erro de Conexão", "error"))

    # --- MODAL IMAGEM ZOOM ---
    def abrir_zoom_imagem(self, img_path):
        zoom_modal = ctk.CTkToplevel(self)
        zoom_modal.title("Zoom na Imagem")
        zoom_modal.geometry("1000x800")
        zoom_modal.configure(fg_color=ThemeManager.get_color("bg_app"))
        zoom_modal.transient(self); zoom_modal.grab_set()
        
        # Centralizar Modal
        x = self.winfo_x() + (self.winfo_width()//2) - 500
        y = self.winfo_y() + (self.winfo_height()//2) - 400
        zoom_modal.geometry(f"+{x}+{y}")
        
        # Area de Imagem
        lbl = ctk.CTkLabel(zoom_modal, text="")
        lbl.pack(fill="both", expand=True)
        
        try:
            img = Image.open(img_path)
            # Fazer a imagem caber em 1000x800 sem destorcer
            ratio = min(980/img.width, 780/img.height)
            img = img.resize((int(img.width*ratio), int(img.height*ratio)), Image.LANCZOS)
            ctk_img = ctk.CTkImage(img, size=(img.width, img.height))
            lbl.configure(image=ctk_img)
        except Exception as e:
            lbl.configure(text=f"Erro ao carregar imagem: {e}")
            
        zoom_modal.bind("<Escape>", lambda e: zoom_modal.destroy())
        lbl.bind("<Button-1>", lambda e: zoom_modal.destroy())

    # --- HELP / FAQ ---
    def show_help(self):
        self.entry_search.pack_forget() # Hide search
        self.current_nav = self.btn_help
        self.select_nav_btn(self.btn_help)
        for w in self.main_container.winfo_children(): w.destroy()
        
        scroll = ctk.CTkScrollableFrame(self.main_container, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        t1 = ctk.CTkLabel(scroll, text="Central de Ajuda (FAQ)", font=("Segoe UI", 28, "bold"), text_color=ThemeManager.get_color("text_main"))
        t1.pack(anchor="w", pady=(0, 20))
        ThemeManager.subscribe(lambda: t1.configure(text_color=ThemeManager.get_color("text_main")))
        
        faqs = [
            {
                "title": "🎵 Ouvindo a Própria Voz ao Iniciar (Retorno)",
                "desc": "Se você ligar a Engine e começar a ouvir sua própria voz (retorno infinito), ocorreu um pequeno bug no roteamento do Windows.",
                "note": "Como resolver: Na aba Configurações, troque seus 3 dispositivos (Microfone, Cabo Virtual e Fone) para QUALQUER outra opção aleatória da lista. Depois, volte-os para a opção correta.\nFeito isso, o áudio será destravado do cache do Windows!",
                "color_type": "error",
                "image": None
            },
            {
                "title": "🎙️ Passo 1: Anti-Lag Discord",
                "desc": "Siga estas configurações no Discord para o áudio sair vivo e sem cortes.",
                "note": "Desligue todos os filtros do Discord (Krisp, Eco, Supressão de Ruído) pois eles cortam 100% o áudio do SoundPad achando que é ruído!",
                "color_type": "warning",
                "image": "Discord.png"
            },
            {
                "title": "🔌 Passo 2: Cabo Virtual (A Mágica)",
                "desc": "Como o áudio vai do SoundPad para o Microfone do Discord?",
                "note": "1. Instale o 'VB-Audio Virtual Cable'.\n2. Na aba Configurações do app, coloque 'Cabo Virtual' como CABLE Input.\n3. Vá no Discord e coloque 'Dispositivo de Entrada' como CABLE Output.",
                "color_type": "accent",
                "image": "vb-audio.png"
            },
            {
                "title": "📥 Passo 3: Adicionando Sons",
                "desc": "Como usar o botão '+ Novo Som'?",
                "note": "Copie o link no MyInstants e cole na caixa de texto. O Soundpad fará o Download do MP3 direto para a pasta do aplicativo e ele aparecerá na lista automaticamente!",
                "color_type": "muted",
                "image": "myinstants.png"
            }
        ]
        
        for faq in faqs:
            self.create_faq_card(scroll, faq)

    def create_faq_card(self, parent, data):
        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=ThemeManager.get_color("bg_card"), border_color=ThemeManager.get_color("border"), border_width=1)
        card.pack(fill="x", pady=(0, 15))
        ThemeManager.subscribe(lambda c=card: c.configure(fg_color=ThemeManager.get_color("bg_card"), border_color=ThemeManager.get_color("border")))
        
        pad = ctk.CTkFrame(card, fg_color="transparent")
        pad.pack(fill="both", expand=True, padx=25, pady=25)
        
        t = ctk.CTkLabel(pad, text=data["title"], font=("Segoe UI", 18, "bold"), text_color=ThemeManager.get_color("text_main"))
        t.pack(anchor="w", pady=(0, 5))
        ThemeManager.subscribe(lambda lbl=t: lbl.configure(text_color=ThemeManager.get_color("text_main")))
        
        d = ctk.CTkLabel(pad, text=data["desc"], font=("Segoe UI", 14), text_color=ThemeManager.get_color("text_muted"), justify="left", wraplength=700)
        d.pack(anchor="w", pady=(0, 15))
        ThemeManager.subscribe(lambda lbl=d: lbl.configure(text_color=ThemeManager.get_color("text_muted")))
        
        note_frame = ctk.CTkFrame(pad, fg_color="#18181b", corner_radius=8, border_width=1)
        note_frame.pack(fill="x", pady=(0, 15))
        
        n = ctk.CTkLabel(note_frame, text=data["note"], font=("Segoe UI", 13), justify="left", wraplength=650)
        n.pack(padx=15, pady=15, anchor="w")
        
        def update_colors():
            try:
                if not note_frame.winfo_exists(): return
                cmap = {"error": "#ef4444", "warning": "#facc15", "accent": ThemeManager.get_color("accent"), "muted": ThemeManager.get_color("text_muted")}
                c = cmap.get(data["color_type"], "#ffffff")
                note_frame.configure(border_color=c)
                n.configure(text_color=c)
            except: pass
        
        update_colors()
        ThemeManager.subscribe(update_colors)
        
        if data["image"]:
            img_name = data["image"]
            try:
                import os
                from PIL import Image
                if os.path.exists(img_name):
                    img = Image.open(img_name)
                    ratio = min(600/img.width, 250/img.height)
                    img = img.resize((int(img.width*ratio), int(img.height*ratio)), Image.LANCZOS)
                    ctk_img = ctk.CTkImage(img, size=(img.width, img.height))
                    img_lbl = ctk.CTkLabel(pad, text="", image=ctk_img, cursor="hand2")
                    img_lbl.pack(anchor="w", pady=(10, 0))
                    img_lbl.bind("<Button-1>", lambda e, f=img_name: self.abrir_zoom_imagem(f))
                    
                    hint = ctk.CTkLabel(pad, text="🔍 Clique para expandir imagem", font=("Segoe UI", 11, "bold"))
                    hint.pack(anchor="w")
                    ThemeManager.subscribe(lambda h=hint: h.configure(text_color=ThemeManager.get_color("accent")))
            except: pass

    # --- SETTINGS / CONFIGURATION ---
    def show_settings(self):
        self.entry_search.pack_forget() # Hide search
        self.current_nav = self.btn_settings
        self.select_nav_btn(self.btn_settings)
        for w in self.main_container.winfo_children(): w.destroy()

        content = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=20)

        # Header
        ThemeManager.subscribe(lambda: self._update_settings_texts(t1, t2))
        t1 = ctk.CTkLabel(content, text="Hardware & Mixagem", font=("Segoe UI", 24, "bold"), text_color=ThemeManager.get_color("text_main"))
        t1.pack(anchor="w", pady=(0, 20))

        frame = ctk.CTkFrame(content, corner_radius=12)
        frame.pack(fill="both", expand=True)
        ThemeManager.subscribe(lambda: frame.configure(fg_color=ThemeManager.get_color("bg_card"), border_color=ThemeManager.get_color("border"), border_width=1))

        # Coluna Esq
        col1 = ctk.CTkFrame(frame, fg_color="transparent")
        col1.pack(side="left", fill="both", expand=True, padx=40, pady=30)
        t2 = ctk.CTkLabel(col1, text="Dispositivos", font=("Segoe UI", 16, "bold"), text_color=ThemeManager.get_color("accent"))
        t2.pack(anchor="w", pady=(0,20))
        
        self.combo_mic = self.create_combo(col1, "Microfone", list(self.devices['input'].keys()))
        self.combo_cable = self.create_combo(col1, "Cabo Virtual", list(self.devices['output'].keys()))
        self.combo_fone = self.create_combo(col1, "Seu Fone", list(self.devices['output'].keys()))
        self.auto_select_devices_ui()

        # Coluna Dir
        col2 = ctk.CTkFrame(frame, fg_color="transparent")
        col2.pack(side="left", fill="both", expand=True, padx=40, pady=30)
        t3 = ctk.CTkLabel(col2, text="Mixagem", font=("Segoe UI", 16, "bold"), text_color=ThemeManager.get_color("accent"))
        t3.pack(anchor="w", pady=(0,20))
        ThemeManager.subscribe(lambda: t3.configure(text_color=ThemeManager.get_color("accent")))

        self.create_slider(col2, "Sua Voz (Boost)", 0, 2, self.vol_mic, lambda v: setattr(self, 'vol_mic', v))
        self.create_slider(col2, "Música (Para os outros)", 0, 1, self.vol_music_discord, lambda v: setattr(self, 'vol_music_discord', v))
        self.create_slider(col2, "Música (Para você)", 0, 1, self.vol_music_me, lambda v: setattr(self, 'vol_music_me', v))

        ctk.CTkLabel(col2, text="Kill Switch (Parar Tudo):").pack(anchor="w", pady=(20, 5))
        ThemeManager.subscribe(lambda: col2.winfo_children()[-1].configure(text_color=ThemeManager.get_color("text_muted")))
        
        btn_kill = ctk.CTkButton(col2, text=self.config_data["kill_switch"].upper(), width=100, height=35)
        btn_kill.pack(anchor="w")
        ThemeManager.subscribe(lambda: btn_kill.configure(fg_color=ThemeManager.get_color("bg_input"), border_color=ThemeManager.get_color("border"), border_width=1, text_color=ThemeManager.get_color("accent")))
        btn_kill.configure(command=lambda: self.change_kill_switch(btn_kill))
        
        ThemeManager.notify_all()

    def change_kill_switch(self, btn):
        btn.configure(text="Pressione...", text_color=ThemeManager.get_color("bg_app"), fg_color=ThemeManager.get_color("accent"))
        threading.Thread(target=self._key_worker_kill, args=(btn,)).start()
        
    def _key_worker_kill(self, btn):
        try:
            k = keyboard.read_hotkey(suppress=False)
            self.config_data["kill_switch"] = k
            self.save_config()
            self.registrar_atalhos()
            self.after(0, lambda: btn.configure(text=k.upper(), text_color=ThemeManager.get_color("accent"), fg_color=ThemeManager.get_color("bg_input")))
        except: pass

    def create_combo(self, parent, title, values):
        lbl = ctk.CTkLabel(parent, text=title, font=("Segoe UI", 13, "bold"))
        lbl.pack(anchor="w", pady=(10,5))
        c = ctk.CTkOptionMenu(parent, values=values, width=300, height=40, corner_radius=8)
        if values: c.set(values[0])
        c.pack(anchor="w")
        ThemeManager.subscribe(lambda: lbl.configure(text_color=ThemeManager.get_color("text_muted")))
        ThemeManager.subscribe(lambda: c.configure(fg_color=ThemeManager.get_color("bg_input"), border_color=ThemeManager.get_color("border"), button_color=ThemeManager.get_color("bg_input"), button_hover_color=ThemeManager.get_color("border"), text_color=ThemeManager.get_color("text_main")))
        return c

    def create_slider(self, parent, title, min_v, max_v, default, cmd):
        lbl = ctk.CTkLabel(parent, text=title)
        lbl.pack(anchor="w", pady=(10,0))
        s = ctk.CTkSlider(parent, width=300, from_=min_v, to=max_v)
        s.set(default); s.configure(command=cmd); s.pack(anchor="w", pady=(5, 10))
        ThemeManager.subscribe(lambda: lbl.configure(text_color=ThemeManager.get_color("text_muted")))
        ThemeManager.subscribe(lambda: s.configure(progress_color=ThemeManager.get_color("accent"), button_color=ThemeManager.get_color("text_main"), button_hover_color=ThemeManager.get_color("text_main")))

    # --- CREDITOS ---
    def show_credits(self):
        self.entry_search.pack_forget() # Hide search
        self.current_nav = self.btn_credits
        self.select_nav_btn(self.btn_credits)
        for w in self.main_container.winfo_children(): w.destroy()
        
        content = ctk.CTkFrame(self.main_container, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=20)
        
        t1 = ctk.CTkLabel(content, text="Créditos & Criador", font=("Segoe UI", 28, "bold"), text_color=ThemeManager.get_color("text_main"))
        t1.pack(anchor="w", pady=(0, 20))
        ThemeManager.subscribe(lambda: t1.configure(text_color=ThemeManager.get_color("text_main")))
        
        card = ctk.CTkFrame(content, corner_radius=12, fg_color=ThemeManager.get_color("bg_card"), border_color=ThemeManager.get_color("border"), border_width=1)
        card.pack(fill="x", pady=20)
        ThemeManager.subscribe(lambda: card.configure(fg_color=ThemeManager.get_color("bg_card"), border_color=ThemeManager.get_color("border")))
        
        inner_pad = ctk.CTkFrame(card, fg_color="transparent")
        inner_pad.pack(fill="both", expand=True, padx=40, pady=40)
        
        ctk.CTkLabel(inner_pad, text="GUSTAVO FOGLIATI", font=("Segoe UI", 24, "bold"), text_color=ThemeManager.get_color("accent")).pack(anchor="w", pady=(0, 5))
        ctk.CTkLabel(inner_pad, text="Desenvolvedor do SoundPad Ultimate 🚀", font=("Segoe UI", 16), text_color=ThemeManager.get_color("text_main")).pack(anchor="w", pady=(0, 30))
        
        links_frame = ctk.CTkFrame(inner_pad, fg_color="transparent")
        links_frame.pack(fill="x")
        
        import webbrowser
        self.create_social_btn(links_frame, "LinkedIn", "https://www.linkedin.com/in/gustavo-barreto-fogliati-46732b23b/")
        self.create_social_btn(links_frame, "GitHub", "https://github.com/4sofa/")
        self.create_social_btn(links_frame, "Discord: SOFA#8304", "")
        
    def create_social_btn(self, parent, platform, url):
        btn = ctk.CTkButton(parent, text=f"🔗 {platform}", height=50, width=200, corner_radius=8, font=("Segoe UI", 14, "bold"), fg_color="transparent", border_width=2)
        btn.pack(side="left", padx=(0, 15))
        if url: btn.configure(command=lambda: webbrowser.open(url))
        ThemeManager.subscribe(lambda: btn.configure(border_color=ThemeManager.get_color("border"), text_color=ThemeManager.get_color("text_main"), hover_color=ThemeManager.get_color("accent")))
        
        # Hover effect simulate CSS transform
        btn.bind("<Enter>", lambda e: btn.configure(border_color=ThemeManager.get_color("accent")))
        btn.bind("<Leave>", lambda e: btn.configure(border_color=ThemeManager.get_color("border")))
    # --- ENGINE DE AUDIO CORRESPONDENTE ---
    def get_device_list(self):
        inputs, outputs = {}, {}
        mme = 0
        try:
            for i, api in enumerate(sd.query_hostapis()):
                if "MME" in api['name']: mme = i
            for i, dev in enumerate(sd.query_devices()):
                if dev['hostapi'] == mme:
                    name = f"{i}: {dev['name']}"[:35]
                    if dev['max_input_channels']>0: inputs[name]=i
                    if dev['max_output_channels']>0: outputs[name]=i
        except: pass
        return {'input': inputs, 'output': outputs}

    def toggle_engine(self):
        if self.is_running:
            self.is_running = False
            if self.stream: self.stream.stop(); self.stream.close()
            self.switch_engine.set_state(False)
        else:
            try:
                mic_name = self.combo_mic.get() if hasattr(self, 'combo_mic') else list(self.devices['input'].keys())[0]
                cab_name = self.combo_cable.get() if hasattr(self, 'combo_cable') else list(self.devices['output'].keys())[0]
                self.stream = sd.Stream(device=(self.devices['input'][mic_name], self.devices['output'][cab_name]),
                                        channels=1, callback=self.audio_callback, samplerate=48000, blocksize=512, latency='high')
                self.stream.start(); self.is_running = True; 
                self.switch_engine.set_state(True)
                ToastNotification(self, "Engine de Áudio Iniciada!", "success")
            except Exception as e: 
                print(e)
                ToastNotification(self, "Falha ao iniciar Engine", "error")

    def audio_callback(self, indata, outdata, frames, time, status):
        try: outdata[:] = indata * self.vol_mic
        except: outdata.fill(0)
        if self.is_playing_sound:
            rem = len(self.audio_mono) - self.audio_index
            if rem > 0:
                chunk = min(frames, rem)
                mix = self.audio_mono[self.audio_index:self.audio_index+chunk] * self.vol_music_discord
                if outdata.shape[1] == mix.shape[1]: outdata[:chunk] += mix
                else: outdata[:chunk, 0] += mix.flatten()
                self.audio_index += chunk
            else: self.is_playing_sound = False

    def preparar_som(self, arquivo):
        try:
            if not os.path.exists(arquivo): return
            data, fs = sf.read(arquivo, dtype='float32')
            if data.ndim > 1: self.audio_mono = np.mean(data, axis=1).reshape(-1, 1)
            else: self.audio_mono = data.reshape(-1, 1)
            self.audio_fone = data; self.fs_fone = fs
            self.audio_index = 0; self.is_playing_sound = True
            if hasattr(self, 'combo_fone'):
                dev = self.combo_fone.get()
                if dev in self.devices['output']: sd.play(self.audio_fone*self.vol_music_me, samplerate=fs, device=self.devices['output'][dev])
        except Exception as e: print(f"Erro ao tocar: {e}")

    def parar_som_agora(self):
        self.is_playing_sound = False; self.audio_index = 0; sd.stop()

    def auto_select_devices_ui(self):
        for n in self.devices['input']: 
            if "SF-VOICE" in n: self.combo_mic.set(n)
        for n in self.devices['output']:
            if "CABLE Input" in n: self.combo_cable.set(n)
            if "Realtek" in n or "Fone" in n: self.combo_fone.set(n)

    def get_icon(self, name, color, size=(20, 20)):
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        # Simplified icons generated programatically
        if name == "home": d.rectangle([(4,6),(20,20)], outline=color, width=2); d.polygon([(12,2),(22,10),(2,10)], fill=color)
        elif name == "settings": d.ellipse([(4,4),(20,20)], outline=color, width=3); d.ellipse([(10,10),(14,14)], fill=color)
        elif name == "help": d.ellipse([(4,4),(20,20)], outline=color, width=2); d.rectangle([(11,14),(13,16)], fill=color); d.rectangle([(11,7),(13,12)], fill=color)
        elif name == "user": d.ellipse([(7,3),(17,13)], fill=color); d.ellipse([(3,22),(21,22)], outline=color, width=6)
        elif name == "logo": d.polygon([(4,4), (20,10), (4,26)], fill=color); d.polygon([(12,4), (28,10), (12,26)], outline=color, width=2)
        return ctk.CTkImage(img, size=size)

if __name__ == "__main__":
    app = SoundPadApp()
    app.mainloop()