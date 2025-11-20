"""
Hotkey management system
"""

import time
import ctypes
import logging
import threading
from pynput import keyboard

logger = logging.getLogger(__name__)

class HotkeyManager:
    """Manage global hotkeys"""
    
    def __init__(self, gui_handler):
        self.gui_handler = gui_handler
        self.pressed_keys = set()
        self.last_activity_time = time.time()
        
        # Start key state monitor
        self._start_key_state_monitor()
        
        # Start hotkey listener
        self.hotkey_listener = keyboard.Listener(
            on_press=self._on_hotkey_press,
            on_release=self._on_hotkey_release
        )
        self.hotkey_listener.start()
    
    def _start_key_state_monitor(self):
        """Monitor for stuck keys and reset them"""
        def monitor():
            while True:
                try:
                    # Check if there's been no activity for 2 seconds
                    if time.time() - self.last_activity_time > 2.0:
                        # If Win key is still "pressed", clear it
                        if keyboard.Key.cmd_l in self.pressed_keys or keyboard.Key.cmd_r in self.pressed_keys:
                            self.gui_handler.root.after(0, self._reset_key_state)
                    
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(f"Key state monitor error: {e}")
                    time.sleep(1)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def _reset_key_state(self):
        """Reset stuck keys"""
        if self.pressed_keys:
            logger.info(f"🔧 Resetting stuck keys: {self.pressed_keys}")
            
            try:
                user32 = ctypes.windll.user32
                
                # Release Win keys
                user32.keybd_event(0x5B, 0, 0x0002, 0)  # Left Win key up
                user32.keybd_event(0x5C, 0, 0x0002, 0)  # Right Win key up
            except Exception as e:
                logger.error(f"Key release error: {e}")
            
            self.pressed_keys.clear()
    
    def _on_hotkey_press(self, key):
        """Handle key press"""
        self.pressed_keys.add(key)
        self.last_activity_time = time.time()
        
        # Win + Space: Toggle input dialog
        if (keyboard.Key.cmd_l in self.pressed_keys or keyboard.Key.cmd_r in self.pressed_keys) and key == keyboard.Key.space:
            self.gui_handler.root.after(0, self.gui_handler.toggle_input_dialog)
            
            # Clear Win key immediately
            self.gui_handler.root.after(100, lambda: self.pressed_keys.discard(keyboard.Key.cmd_l))
            self.gui_handler.root.after(100, lambda: self.pressed_keys.discard(keyboard.Key.cmd_r))
        
        # Win + Enter: Toggle mic button
        if (keyboard.Key.cmd_l in self.pressed_keys or keyboard.Key.cmd_r in self.pressed_keys) and key == keyboard.Key.enter:
            self.gui_handler.root.after(0, self.gui_handler.toggle_mic)
            
            # Clear Win key immediately
            self.gui_handler.root.after(100, lambda: self.pressed_keys.discard(keyboard.Key.cmd_l))
            self.gui_handler.root.after(100, lambda: self.pressed_keys.discard(keyboard.Key.cmd_r))
    
    def _on_hotkey_release(self, key):
        """Handle key release"""
        self.pressed_keys.discard(key)
        self.last_activity_time = time.time()
        
        # Extra safety: If Win key is released, ensure it's cleared
        if key in (keyboard.Key.cmd_l, keyboard.Key.cmd_r):
            self.pressed_keys.discard(keyboard.Key.cmd_l)
            self.pressed_keys.discard(keyboard.Key.cmd_r)
    
    def stop(self):
        """Stop hotkey listener"""
        try:
            self.hotkey_listener.stop()
        except:
            pass