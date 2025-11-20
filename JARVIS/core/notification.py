"""
Proactive notification system
Monitors context and sends automatic alerts
"""

import threading
import time
from pathlib import Path
from audio.tts import speak
from config.settings import ENABLE_TTS
from config.loader import settings
def greeting():
    """Greeting logic with UI update"""
    if not ENABLE_TTS:
        return  # TTS disabled, skip greeting
    # speak("JARVIS Voice activated successfully")
    from datetime import datetime
    hour = datetime.now().hour
    if 5 <= hour < 12:
        speak("Good Morning Sir")
    elif 12 <= hour < 17:
        speak("Good Afternoon Sir")
    elif 17 <= hour < 21:
        speak("Good Evening Sir")
    else:
        speak("Good Evening Sir")
    return
class ProactiveNotifier:
    """Monitors context and sends automatic notifications"""
    
    def __init__(self, context_manager, gui_handler):
        self.context = context_manager
        self.gui = gui_handler
        self.lock = threading.RLock()
        self.startup_time = time.time()
        self.startup_grace_period = settings.notifier_grace_period  # seconds
        
        # Notification state tracking
        self.last_notifications = {
            'battery_low': 0,
            'battery_full': 0,
            'download_complete': set(),
            'webcam_active': 0,
            'network_disconnect': 0,
            'device_connected': 0,
            'bluetooth_connected': 0,
        }
        
        # Notification cooldowns (seconds)
        self.cooldowns = {
            'battery_low': 300,      # 5 minutes
            'battery_full': 600,     # 10 minutes
            'webcam_active': 60,     # 1 minute
            'network_disconnect': 60, # 1 minute
        }
        
        # Start monitoring thread
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
    def _is_startup_period(self):
        """Check if we're still in startup grace period"""
        return (time.time() - self.startup_time) < self.startup_grace_period
    
    def _monitor_loop(self):
        """Main monitoring loop - checks every 2 seconds"""
        while self.running:
            try:
                self._check_battery()
                self._check_downloads()
                self._check_webcam()
                self._check_network()
                self._check_devices()
                self._check_bluetooth()
                self._check_system_performance()
            except Exception as e:
                print(f"Notifier error: {e}")
            
            time.sleep(2)
    
    def _can_notify(self, notification_type):
        """Check if enough time has passed since last notification"""
        last_time = self.last_notifications.get(notification_type, 0)
        cooldown = self.cooldowns.get(notification_type, 60)
        return (time.time() - last_time) > cooldown
    
    # In core/notification.py

    def _notify(self, notification_type, message, color="yellow", speak_text=None):
        """Send notification to user - WITH COORDINATION"""
        with self.lock:
            if self._can_notify(notification_type):
                self.last_notifications[notification_type] = time.time()
                self.gui.queue_gui_task(
                    lambda: self.gui.show_terminal_output(message, color=color)
                )
                
                # ✅ Check ENABLE_TTS before speaking
                if speak_text and ENABLE_TTS:
                    # ✅ Use coordinator instead of direct TTS
                    threading.Thread(
                        target=lambda: self.gui.audio_coordinator.speak(speak_text),
                        daemon=True
                    ).start()
    
    def _check_battery(self):
        """Enhanced battery alerts with better thresholds"""
        percent = self.context.battery_percent
        status = self.context.charging_status
        
        if percent is None:
            return
        
        # Critical battery alert (immediate)
        if percent < 15 and status != "Charging":
            self._notify(
                'battery_critical',
                f"🔋 CRITICAL BATTERY: {percent}% - Plug in NOW!",
                color="red",
                speak_text=f"Critical battery at {percent} percent"
            )
        # Low battery alert
        elif percent < 30 and status != "Charging":
            self._notify(
                'battery_low',
                f"🔋 Battery Low: {percent}% - Consider plugging in",
                color="yellow",
                speak_text=f"Battery low at {percent} percent"
            )
        # Battery full alert
        elif percent == 100 and status == "Charging":
            self._notify(
                'battery_full',
                f"🔌 Battery at {percent}% - You can unplug",
                color="green",
                speak_text="Battery is fully charged"
            )
    
    def _check_downloads(self):
        """Enhanced download detection with file type info"""
        recent = self.context.recent_downloads
        
        if not recent:
            return
        
        for filename in recent[-3:]:
            if filename not in self.last_notifications['download_complete']:
                downloads_path = Path.home() / "Downloads" / filename
                
                if downloads_path.exists():
                    size_mb = downloads_path.stat().st_size / (1024 * 1024)
                    
                    # Only notify for files > 100KB (filter out tiny files)
                    if size_mb > 0.1:
                        self.last_notifications['download_complete'].add(filename)
                        
                        ext = downloads_path.suffix.lower()
                        icon = {
                            '.exe': '⚙️', '.msi': '⚙️',
                            '.zip': '📦', '.rar': '📦', '.7z': '📦',
                            '.pdf': '📄', '.docx': '📄', '.doc': '📄',
                            '.jpg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
                            '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬',
                            '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵',
                        }.get(ext, '📁')
                        
                        # Determine file category for better message
                        if ext in ['.exe', '.msi']:
                            category = "Installer"
                        elif ext in ['.zip', '.rar', '.7z']:
                            category = "Archive"
                        elif ext in ['.pdf', '.docx', '.doc']:
                            category = "Document"
                        elif ext in ['.jpg', '.png', '.gif']:
                            category = "Image"
                        elif ext in ['.mp4', '.avi', '.mkv']:
                            category = "Video"
                        elif ext in ['.mp3', '.wav', '.flac']:
                            category = "Audio"
                        else:
                            category = "File"
                        
                        self.gui.queue_gui_task(
                            lambda: self.gui.show_terminal_output(
                                f"{icon} {category} Downloaded: {filename} ({size_mb:.1f} MB)",
                                color="green"
                            )
                        )
                        
                        # Only speak for larger downloads
                        if size_mb > 10:
                            from config.settings import ENABLE_TTS
                            if ENABLE_TTS:
                                from audio.tts import speak
                                speak(f"{category} download complete")
    
    def _check_system_performance(self):
        """NEW: Alert on high system resource usage"""
        cpu = self.context.cpu_percent
        ram = self.context.ram_percent
        
        # High CPU alert
        if cpu > 90:
            if self._can_notify('high_cpu'):
                self._notify(
                    'high_cpu',
                    f"⚡ High CPU Usage: {cpu}% - System may be slow",
                    color="yellow"
                )
        
        # High RAM alert
        if ram > 90:
            if self._can_notify('high_ram'):
                self._notify(
                    'high_ram',
                    f"💾 High Memory Usage: {ram}% - Consider closing apps",
                    color="yellow"
                )
    
    
    def _check_webcam(self):
        """Alert when webcam becomes active"""
        if self.context.webcam_active:
            self._notify(
                'webcam_active',
                "📷 WEBCAM IS ACTIVE - Check if this is expected",
                color="red",
                speak_text="Warning! Webcam is active"
            )
    
    def _check_network(self):
        """Alert on network disconnection"""
        if not self.context.network_connected:
            if hasattr(self, '_was_connected') and self._was_connected:
                self._notify(
                    'network_disconnect',
                    "📡 Internet Disconnected",
                    color="red",
                    speak_text="Internet connection lost"
                )
        else:
            if hasattr(self, '_was_connected') and not self._was_connected:
                if self._can_notify('network_disconnect'):
                    self.gui.queue_gui_task(
                        lambda: self.gui.show_terminal_output(
                            "🌐 Internet Connected",
                            color="green"
                        )
                    )
        
        self._was_connected = self.context.network_connected
    
    def _check_devices(self):
        """Alert on USB/HDMI device changes"""
        devices = self.context.connected_devices
        
        if not hasattr(self, '_last_device_count'):
            self._last_device_count = len(devices)
            return
        
        if self._is_startup_period():
            self._last_device_count = len(devices)
            return
        
        current_count = len(devices)
        
        if current_count > self._last_device_count:
            if self._can_notify('device_connected'):
                new_devices = [info for info in devices.values()]
                if new_devices:
                    latest = new_devices[-1]
                    icon = {
                        'USB Storage': '💾',
                        'USB Mouse': '🖱️',
                        'USB Keyboard': '⌨️',
                        'HDMI Monitor': '🖥️'
                    }.get(latest['type'], '🔌')
                    
                    self._notify(
                        'device_connected',
                        f"{icon} Device Connected: {latest['name']}",
                        color="green",
                        speak_text=f"{latest['type']} connected"
                    )
        
        elif current_count < self._last_device_count:
            if self._can_notify('device_connected'):
                self._notify(
                    'device_connected',
                    "🔌 Device Disconnected",
                    color="yellow"
                )
        
        self._last_device_count = current_count
    
    def _check_bluetooth(self):
        """Alert on Bluetooth device changes"""
        bt_devices = self.context.bluetooth_devices
        
        if not hasattr(self, '_last_bt_count'):
            self._last_bt_count = len(bt_devices)
            return
        
        if self._is_startup_period():
            self._last_bt_count = len(bt_devices)
            return
        
        current_count = len(bt_devices)
        
        if current_count > self._last_bt_count:
            if self._can_notify('bluetooth_connected'):
                new_devices = [info for info in bt_devices.values()]
                if new_devices:
                    latest = new_devices[-1]
                    icon = {
                        'Bluetooth Mouse': '🖱️',
                        'Bluetooth Keyboard': '⌨️',
                        'Bluetooth Headset': '🎧',
                        'Bluetooth Speaker': '🔊'
                    }.get(latest['type'], '📶')
                    
                    self._notify(
                        'bluetooth_connected',
                        f"{icon} Bluetooth Connected: {latest['name']}",
                        color="cyan",
                        speak_text=f"{latest['type']} connected"
                    )
        
        elif current_count < self._last_bt_count:
            if self._can_notify('bluetooth_connected'):
                self._notify(
                    'bluetooth_connected',
                    "📶 Bluetooth Device Disconnected",
                    color="yellow"
                )
        
        self._last_bt_count = current_count
    
    def stop(self):
        """Stop the notifier"""
        self.running = False