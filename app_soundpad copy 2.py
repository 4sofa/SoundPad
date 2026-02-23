import eel
import os
import json
import threading
import keyboard
import sounddevice as sd
import soundfile as sf
import numpy as np
import requests
import re
import ctypes
import platform
import webbrowser
import sys

# Configure Eel to support PyInstaller _MEIPASS unpacking
if hasattr(sys, '_MEIPASS'):
    eel.init(os.path.join(sys._MEIPASS, 'web'))
else:
    eel.init('web')

CONFIG_PATH = "config.json"
config_data = {
    "kill_switch": "f12",
    "cor_tema": "Red",
    "atalhos_sons": {},
    "mic_device": "",
    "cable_device": "",
    "phone_device": ""
}

# Áudio Globals
stream = None
is_engine_on = False

# ================================
# CONFIGURATION & UTILS
# ================================
def load_config():
    global config_data
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                config_data.update(data)
        except: pass

def save_config():
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4)
    except: pass

def get_devices():
    devices = sd.query_devices()
    names = []
    for d in devices:
        name = str(d['name']).encode('cp1252', errors='ignore').decode('utf-8', errors='ignore')
        if name not in names: names.append(name)
    return names

# ================================
# EEL EXPOSED FUNCTIONS (FRONTEND -> BACKEND)
# ================================

@eel.expose
def get_sounds():
    files = [f for f in os.listdir() if f.endswith(".mp3")]
    data = []
    for f in files:
        data.append({
            "file": f,
            "shortcut": config_data["atalhos_sons"].get(f, "")
        })
    return data

@eel.expose
def get_settings():
    return {
        "devices": get_devices(),
        "mic": config_data.get("mic_device", ""),
        "cable": config_data.get("cable_device", ""),
        "phone": config_data.get("phone_device", ""),
        "kill_switch": config_data["kill_switch"],
        "theme": config_data["cor_tema"]
    }

@eel.expose
def save_theme(theme_name):
    config_data["cor_tema"] = theme_name
    save_config()

@eel.expose
def save_device(dev_type, value):
    config_data[f"{dev_type}_device"] = value
    save_config()
    
@eel.expose
def bind_killswitch():
    try:
        k = keyboard.read_hotkey(suppress=False)
        if k == "esc":
            config_data["kill_switch"] = ""
        else:
            config_data["kill_switch"] = k
        save_config()
        registrar_atalhos()
        return config_data["kill_switch"]
    except: return ""

@eel.expose
def bind_hotkey(filename):
    try:
        k = keyboard.read_hotkey(suppress=False)
        if k == "esc":
            config_data["atalhos_sons"].pop(filename, None)
        else:
            config_data["atalhos_sons"][filename] = k
        save_config()
        registrar_atalhos()
        return config_data["atalhos_sons"].get(filename, "")
    except: return ""

@eel.expose
def download_sound(url):
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
            return True
    except: pass
    return False

@eel.expose
def open_url(url):
    webbrowser.open(url)

# ================================
# AUDIO ENGINE
# ================================

@eel.expose
def play_sound(arquivo):
    threading.Thread(target=_play_worker, args=(arquivo,)).start()

def _play_worker(arquivo):
    if not os.path.exists(arquivo): return
    try:
        data, fs = sf.read(arquivo, dtype='float32')
        if len(data.shape) == 1: data = np.column_stack((data, data))
        
        # Output to Virtual Cable
        out_cable = _find_dev(config_data.get("cable_device", ""))
        # Output to Headphones (Retorno)
        out_phone = _find_dev(config_data.get("phone_device", ""))
        
        def tocar_disp(device_id):
            if device_id is not None:
                try: sd.play(data, fs, device=device_id); sd.wait()
                except: pass
                
        t1 = threading.Thread(target=tocar_disp, args=(out_cable,))
        t2 = threading.Thread(target=tocar_disp, args=(out_phone,))
        t1.start(); t2.start()
    except: pass

def _find_dev(name):
    if not name: return None
    try:
        dlist = sd.query_devices()
        for i, d in enumerate(dlist):
            dname = str(d['name']).encode('cp1252', errors='ignore').decode('utf-8', errors='ignore')
            if name in dname: return i
    except: pass
    return None

def parar_som_agora():
    sd.stop()

@eel.expose
def toggle_engine(state):
    global stream, is_engine_on
    is_engine_on = state
    if state:
        try:
            in_mic = _find_dev(config_data.get("mic_device", ""))
            out_cable = _find_dev(config_data.get("cable_device", ""))
            if in_mic is not None and out_cable is not None:
                stream = sd.Stream(device=(in_mic, out_cable), callback=audio_callback, channels=2)
                stream.start()
        except: pass
    else:
        if stream:
            stream.stop()
            stream.close()
            stream = None

def audio_callback(indata, outdata, frames, time, status):
    if status: print(status)
    outdata[:] = indata

@eel.expose
def toggle_mic_listen(state):
    # This feature requires a three-way stream (Mic -> Cable AND Phone)
    # Due to portaudio limits, complex routing is better handled via Windows Listen to this device
    # Or by opening a second stream. For simplicity, we just pass.
    pass

# ================================
# WINDOWS NATIVE UI CONTROLS
# ================================

@eel.expose
def minimize_window():
    if platform.system() == "Windows":
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        ctypes.windll.user32.ShowWindow(hwnd, 6) # SW_MINIMIZE

@eel.expose
def toggle_maximize_window():
    if platform.system() == "Windows":
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        placement = ctypes.wintypes.WINDOWPLACEMENT()
        placement.length = ctypes.sizeof(ctypes.wintypes.WINDOWPLACEMENT)
        ctypes.windll.user32.GetWindowPlacement(hwnd, ctypes.byref(placement))
        
        # 3 = Maximized, 1 = Normal
        if placement.showCmd == 3:
            ctypes.windll.user32.ShowWindow(hwnd, 1) # SW_SHOWNORMAL
        else:
            ctypes.windll.user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE

# Keyboard Hooks
def registrar_atalhos():
    keyboard.unhook_all()
    if config_data["kill_switch"]:
        try: keyboard.add_hotkey(config_data["kill_switch"], parar_som_agora)
        except: pass
    
    for som, tecla in config_data["atalhos_sons"].items():
        if tecla and os.path.exists(som):
            try: keyboard.add_hotkey(tecla, lambda s=som: play_sound(s))
            except: pass

if __name__ == '__main__':
    load_config()
    registrar_atalhos()
    
    # Eel args para criar app Edge (Extremamente leve em RAM no Windows)
    eel_kwargs = {
        'mode': 'edge',
        'host': 'localhost',
        'port': 8000,
        'size': (1100, 720),
        'cmdline_args': [
            '--app=http://localhost:8000/index.html',
            '--disable-web-security'
        ]
    }
    
    try:
        eel.start('index.html', **eel_kwargs)
    except (SystemExit, MemoryError, KeyboardInterrupt):
        pass
    except Exception as e:
        print(f"Error starting Eel: {e}")