"""
Context monitoring system
"""
import time
from config.loader import settings
from .explorer import explorer_path_monitor
from .browser import browser_url_monitor
from .clipboard import clipboard_monitor
from .window import window_title_monitor
from .system import (
    performance_monitor,
    battery_monitor,
    network_monitor,
    idle_monitor,
    downloads_monitor
)
from .devices import port_monitor, bluetooth_monitor
import threading
import logging
logger = logging.getLogger(__name__)

class MonitorHealthTracker:
    """Track monitor thread health"""
    
    def __init__(self):
        self.monitors = {}
        self.lock = threading.Lock()
    
    def register(self, name, thread):
        """Register a monitor thread"""
        with self.lock:
            self.monitors[name] = {
                'thread': thread,
                'last_seen': time.time(),
                'restarts': 0
            }
    
    def heartbeat(self, name):
        """Update monitor heartbeat"""
        with self.lock:
            if name in self.monitors:
                self.monitors[name]['last_seen'] = time.time()
    
    def check_health(self):
        """Check if monitors are alive"""
        with self.lock:
            dead_monitors = []
            for name, info in self.monitors.items():
                if not info['thread'].is_alive():
                    dead_monitors.append(name)
                elif time.time() - info['last_seen'] > 60:
                    logger.warning(f"⚠️ Monitor '{name}' hasn't sent heartbeat in 60s")
            
            for name in dead_monitors:
                logger.error(f"❌ Monitor '{name}' died!")
                # Could implement restart logic here
            
            return len(dead_monitors) == 0

# Start health checker
health_tracker = MonitorHealthTracker()

def start_health_checker():
    def checker():
        while True:
            time.sleep(30)
            health_tracker.check_health()
    
    threading.Thread(target=checker, daemon=True).start()
def start_all_monitors(context_manager):
    """Start all context monitoring threads"""
    import threading
    
    monitors = [
        ("Browser URL", browser_url_monitor, (context_manager, settings.browser_url_poll)),
        ("File Explorer", explorer_path_monitor, (context_manager, settings.explorer_path_poll)),
        ("Clipboard", clipboard_monitor, (context_manager, settings.clipboard_poll)),
        ("Active Window", window_title_monitor, (context_manager, settings.active_window_poll)),
        ("Downloads", downloads_monitor, (context_manager, settings.downloads_poll)),
        ("Performance", performance_monitor, (context_manager, settings.performance_poll)),
        ("Idle Time", idle_monitor, (context_manager, settings.idle_time_poll)),
        ("Network", network_monitor, (context_manager, settings.network_poll)),
        ("USB/Ports", port_monitor, (context_manager, settings.usb_ports_poll)),
        ("Bluetooth", bluetooth_monitor, (context_manager, settings.bluetooth_poll)),
        ("Battery", battery_monitor, (context_manager, settings.battery_poll)),
    ]
    
    for name, func, args in monitors:
        thread = threading.Thread(
            target=func,
            args=args,
            daemon=True,
            name=f"Monitor-{name}"
        )
        thread.start()
    
    print(f"✅ All {len(monitors)} context monitors active!")

__all__ = [
    'start_all_monitors',
    'explorer_path_monitor',
    'clipboard_monitor',
    'window_title_monitor',
    'performance_monitor',
    'battery_monitor',
    'network_monitor',
    'idle_monitor',
    'downloads_monitor',
    'port_monitor',
    'bluetooth_monitor'
]