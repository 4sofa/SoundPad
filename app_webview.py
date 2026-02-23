import sys
print("Imports starting...")
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
print("Imports finished.")

class DummyStream:
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass
    
# if sys.stdout is None: sys.stdout = DummyStream()
# if sys.stderr is None: sys.stderr = DummyStream()

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
stream_mic_listen = None
is_engine_on = False
is_playing_sound = False
audio_mono = None
audio_fone = None
fs_fone = 48000
audio_index = 0
vol_mic = 1.0
vol_discord = 0.5
vol_me = 0.5

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
    names = []
    mme = 0
    try:
        for i, api in enumerate(sd.query_hostapis()):
            if "MME" in api['name']: mme = i
        for d in sd.query_devices():
            if d['hostapi'] == mme:
                name = str(d['name']).encode('cp1252', errors='ignore').decode('utf-8', errors='ignore')
                if name not in names: names.append(name)
    except: pass
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
    global audio_mono, audio_fone, fs_fone, audio_index, is_playing_sound
    if not os.path.exists(arquivo): return
    try:
        data, fs = sf.read(arquivo, dtype='float32')
        if len(data.shape) > 1: audio_mono = np.mean(data, axis=1).reshape(-1, 1)
        else: audio_mono = data.reshape(-1, 1)
        
        audio_fone = data; fs_fone = fs
        audio_index = 0; is_playing_sound = True
        
        out_phone = _find_dev(config_data.get("phone_device", ""))
        if out_phone is not None:
            sd.play(audio_fone * vol_me, fs, device=out_phone)
    except Exception as e: print("Erro play:", e)

def _find_dev(name):
    if not name: return None
    mme = 0
    try:
        for i, api in enumerate(sd.query_hostapis()):
            if "MME" in api['name']: mme = i
        for i, d in enumerate(sd.query_devices()):
            if d['hostapi'] == mme:
                dname = str(d['name']).encode('cp1252', errors='ignore').decode('utf-8', errors='ignore')
                if name in dname: return i
    except: pass
    return None

def parar_som_agora():
    global is_playing_sound, audio_index
    is_playing_sound = False
    audio_index = 0
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
                stream = sd.Stream(device=(in_mic, out_cable),
                                   channels=1, callback=audio_callback,
                                   samplerate=48000, blocksize=512, latency='high')
                stream.start()
        except Exception as e: print("Engine err:", e)
    else:
        if stream:
            stream.stop()
            stream.close()
            stream = None

def audio_callback(indata, outdata, frames, time, status):
    global audio_index, is_playing_sound, audio_mono
    try: outdata[:] = indata * vol_mic
    except: outdata.fill(0)
    
    if is_playing_sound and audio_mono is not None:
        rem = len(audio_mono) - audio_index
        if rem > 0:
            chunk = min(frames, rem)
            mix = audio_mono[audio_index:audio_index+chunk] * vol_discord
            if outdata.shape[1] == mix.shape[1]: outdata[:chunk] += mix
            else: outdata[:chunk, 0] += mix.flatten()
            audio_index += chunk
        else:
            is_playing_sound = False

@eel.expose
def toggle_mic_listen(state):
    global stream_mic_listen
    if state:
        in_mic = _find_dev(config_data.get("mic_device", ""))
        out_phone = _find_dev(config_data.get("phone_device", ""))
        if in_mic is not None and out_phone is not None:
            try:
                def passthrough(indata, outdata, frames, time, status): outdata[:] = indata
                stream_mic_listen = sd.Stream(device=(in_mic, out_phone), channels=1, callback=passthrough)
                stream_mic_listen.start()
            except Exception as e: print("Retorno erro:", e)
    else:
        if stream_mic_listen:
            stream_mic_listen.stop(); stream_mic_listen.close(); stream_mic_listen = None

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
def _invoke_sound(som):
    try: eel.showToast(f"Tocando: {som}", "success")()
    except: pass
    play_sound(som)

def registrar_atalhos():
    keyboard.unhook_all()
    if config_data["kill_switch"]:
        try: keyboard.add_hotkey(config_data["kill_switch"], parar_som_agora)
        except: pass
    
    for som, tecla in config_data["atalhos_sons"].items():
        if tecla and os.path.exists(som):
            try: keyboard.add_hotkey(tecla, lambda s=som: _invoke_sound(s))
            except: pass

if __name__ == '__main__':
    print("Main block started")
    load_config()
    registrar_atalhos()
    print("Config and shortcuts loaded")
    
    # Eel args para criar app Chrome
    eel_kwargs = {
        'mode': 'edge',
        'host': 'localhost',
        'port': 8000,
        'size': (1100, 720),
        'cmdline_args': [
            '--disable-web-security'
        ]
    }
    
    try:
        print("Starting eel...")
        eel.start('index.html', **eel_kwargs)
        print("Eel finished")
    except (SystemExit, MemoryError, KeyboardInterrupt):
        print("Caught standard exit")
    except Exception as e:
        print(f"Error starting Eel: {e}")