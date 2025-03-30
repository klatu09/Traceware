# Traceware
This project is a Python-based monitoring tool that logs user activity, including system startup and shutdown events, active window changes, and keystrokes. The tool sends real-time logs to a Discord webhook, differentiating each type of log with color-coded messages. It also captures the user's IPv4 and IPv6 addresses for tracking purposes.

██╗  ██╗██╗      █████╗ ████████╗██╗   ██╗
██║ ██╔╝██║     ██╔══██╗╚══██╔══╝██║   ██║
█████╔╝ ██║     ███████║   ██║   ██║   ██║
██╔═██╗ ██║     ██╔══██║   ██║   ██║   ██║
██║  ██╗███████╗██║  ██║   ██║   ╚██████╔╝
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ 
                                          

✦ Project 3: Traceware
✦ Author: K1atu
✦ Motto: "you get some, you hack some"

# Features
1. System Event Logging: Detects system startup and shutdown, logging the timestamp.
2. Active Window Tracking: Logs changes in active applications.
3. Keystroke Logging: Captures user keystrokes and sends logs when the "Enter" key is pressed.
4. Real-Time Logging: Sends logs instantly to a configured Discord webhook.
5. IP Address Detection: Retrieves and logs both IPv4 and IPv6 addresses.
6. Color-Coded Logs: Uses distinct colors for different log types.

# Installation
## Prerequisites
Required Libraries
1. psutil
2. requests
3. keyboard
4. pywin32
5. Usage

## Configuration

1. Edit the WEBHOOK_URL variable in the script to point to your Discord webhook:

# Disclaimer

This tool is intended for educational and security research purposes only. Ensure you have permission before using it in any environment.
