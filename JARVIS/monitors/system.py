"""
System monitoring
Performance, battery, network, idle time, downloads
"""

import time
import ctypes
import subprocess
import psutil
from pathlib import Path
import logging
logger = logging.getLogger(__name__)
# ============= PERFORMANCE MONITOR =============

def performance_monitor(context_manager, poll=...):
    """Monitor system performance"""
    while True:
        try:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage('/').percent
            
            context_manager.update_performance(cpu, ram, disk)
        except:
            pass
        time.sleep(poll)

# ============= BATTERY MONITOR =============

def battery_monitor(context_manager, poll=...):
    """Monitor battery status"""
    while True:
        try:
            battery = psutil.sensors_battery()
            if battery:
                percent = battery.percent
                plugged = battery.power_plugged
                status = "Charging" if plugged else "Discharging"
                context_manager.update_battery(percent, status)
            else:
                context_manager.update_battery(None, "No Battery")
        except:
            pass
        time.sleep(poll)

# ============= NETWORK MONITOR =============

def get_wifi_ssid():
    """Get current WiFi SSID"""
    try:
        out = subprocess.check_output(
            ["netsh", "wlan", "show", "interfaces"],
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        for line in out.splitlines():
            if "SSID" in line and ":" in line:
                k, v = line.split(":", 1)
                if k.strip().startswith("SSID") and not k.strip().startswith("BSSID"):
                    return v.strip()
    except:
        pass
    return None


# ============= IDLE TIME MONITOR =============

def get_idle_time():
    """Get system idle time in seconds"""
    try:
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_uint)]
        
        lastInputInfo = LASTINPUTINFO()
        lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
        ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))
        millis = ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime
        return millis / 1000.0
    except:
        return 0

def idle_monitor(context_manager, poll=...):
    """Monitor user idle time"""
    while True:
        try:
            idle_secs = get_idle_time()
            context_manager.update_idle_time(idle_secs)
        except:
            pass
        time.sleep(poll)

# ============= DOWNLOADS MONITOR =============

def downloads_monitor(context_manager, poll=...):
    """Monitor Downloads folder for new files"""
    downloads_path = Path.home() / "Downloads"
    
    if downloads_path.exists():
        context_manager.known_downloads = set(
            f.name for f in downloads_path.iterdir() if f.is_file()
        )
    
    while True:
        try:
            if downloads_path.exists():
                current_files = set(
                    f.name for f in downloads_path.iterdir() if f.is_file()
                )
                new_files = current_files - context_manager.known_downloads
                
                for filename in new_files:
                    context_manager.add_download(filename)
                
                context_manager.known_downloads = current_files
        except:
            pass
        time.sleep(poll)
def check_internet_connectivity():
    """
    Check internet connectivity using multiple endpoints
    More reliable than single ping
    More reliable than single ping
    """
    import socket
    
    # Test multiple endpoints
    endpoints = [
        ("8.8.8.8", 53),      # Google DNS
        ("1.1.1.1", 53),      # Cloudflare DNS
        ("208.67.222.222", 53) # OpenDNS
    ]
    
    for host, port in endpoints:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2.0)
            sock.connect((host, port))
            sock.close()
            return True  # At least one endpoint reachable
        except:
            continue
    
    return False  # All endpoints failed


def network_monitor(context_manager, poll=...):
    """Monitor network status with improved reliability"""
    last_state = None
    consecutive_failures = 0
    consecutive_successes = 0
    
    while True:
        try:
            # Check connectivity
            connected = check_internet_connectivity()
            
            # Require 2 consecutive state changes to confirm
            if connected:
                consecutive_successes += 1
                consecutive_failures = 0
                
                if consecutive_successes >= 2 and last_state != True:
                    # Confirmed connected
                    ssid = get_wifi_ssid()
                    context_manager.update_network(True, ssid)
                    last_state = True
            else:
                consecutive_failures += 1
                consecutive_successes = 0
                
                if consecutive_failures >= 2 and last_state != False:
                    # Confirmed disconnected
                    context_manager.update_network(False, None)
                    last_state = False
        
        except Exception as e:
            logger.error(f"Network monitor error: {e}")
        
        time.sleep(poll)