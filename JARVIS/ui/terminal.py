"""
Persistent terminal - FIXED with memory limits and better cleanup
"""

import time
import threading
import tkinter as tk
import logging
from config.loader import settings
logger = logging.getLogger(__name__)

class PersistentTerminal:
    """Terminal with strict memory limits and aggressive cleanup"""
    
    def __init__(self, root):
        self.root = root
        self.lock = threading.RLock()
        self.message_dialogs = []
        self.max_messages = settings.TERMINAL_MAX_MESSAGES  # Reduced from 4
        self.message_spacing = 10
        self.fade_delay = 3000  # Reduced from 4000ms
        self.gui_handler = None
        self.max_message_lifetime = settings.TERMINAL_MESSAGE_LIFETIME  # Reduced from 8000ms
        
        # Cleanup tracking
        self.total_messages_created = 0
        self.total_messages_destroyed = 0
        
        # More aggressive watchdog
        self._start_watchdog()
        
        # Memory cleanup thread
        threading.Thread(target=self._memory_cleanup_loop, daemon=True).start()
    
    def _memory_cleanup_loop(self):
        """Aggressive memory cleanup every 15 seconds"""
        while True:
            try:
                time.sleep(15)
                with self.lock:
                    # Force destroy old messages
                    current_time = time.time()
                    for msg_data in self.message_dialogs[:]:
                        age = current_time - msg_data.get('created_at', current_time)
                        if age > 10:  # Force destroy after 10 seconds
                            self._force_remove_message(msg_data)
                    
                    # Log stats
                    if self.total_messages_created % 50 == 0 and self.total_messages_created > 0:
                        logger.info(
                            f"📊 Terminal stats: Created={self.total_messages_created}, "
                            f"Destroyed={self.total_messages_destroyed}, "
                            f"Active={len(self.message_dialogs)}"
                        )
            except Exception as e:
                logger.error(f"Memory cleanup error: {e}")
    
    def show_message(self, message, color="green"):
        """Create new message with strict limits"""
        with self.lock:
            # Hard limit enforcement
            while len(self.message_dialogs) >= self.max_messages:
                oldest = self.message_dialogs.pop(0)
                self._force_remove_message(oldest)
            
            color_map = {
                "green": "#00ff00",
                "yellow": "#ffff66",
                "cyan": "#66ccff",
                "red": "#ff4444"
            }
            text_color = color_map.get(color, "#00ff00")
            
            # Truncate long messages
            if len(message) > 200:
                message = message[:197] + "..."
            
            # Create dialog
            dialog = self._create_message_dialog(message, text_color)
            
            # Add to list
            msg_data = {
                'dialog': dialog,
                'label': dialog.label,
                'fade_job': None,
                'hover': False,
                'created_at': time.time(),
                'last_hover_time': time.time()
            }
            
            self.message_dialogs.append(msg_data)
            self.total_messages_created += 1
            
            # Reposition
            self._reposition_all_dialogs()
            
            # Schedule fade
            msg_data['fade_job'] = self.root.after(
                self.fade_delay,
                lambda: self._start_fade(msg_data)
            )
    
    def _create_message_dialog(self, message, text_color):
        """Create a single message dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.configure(bg='#1e1e1e')
        dialog.attributes('-topmost', True)
        dialog.overrideredirect(True)
        dialog.attributes('-alpha', 0.90)
        
        label = tk.Label(
            dialog,
            text=message,
            font=("Consolas", 18),
            bg='#1e1e1e',
            fg=text_color,
            padx=15,
            pady=8,
            wraplength=600,
            justify=tk.LEFT
        )
        label.pack()
        
        dialog.label = label
        dialog._destroyed = False
        
        return dialog
    
    def _reposition_all_dialogs(self):
        """Reposition all dialogs"""
        if not self.gui_handler or not hasattr(self.gui_handler, 'control_dialog'):
            return
        
        try:
            self.gui_handler.control_dialog.update_idletasks()
            
            mic_x = self.gui_handler.control_dialog.winfo_x()
            mic_y = self.gui_handler.control_dialog.winfo_y()
            mic_height = 100  # Updated for new orb size
            mic_width = 100
            gap = 20
            
            current_y = mic_y + (mic_height // 2)
            
            for i in range(len(self.message_dialogs) - 1, -1, -1):
                msg_data = self.message_dialogs[i]
                dialog = msg_data['dialog']
                
                if dialog._destroyed:
                    continue
                
                try:
                    if not dialog.winfo_exists():
                        dialog._destroyed = True
                        continue
                except tk.TclError:
                    dialog._destroyed = True
                    continue
                
                try:
                    dialog.update_idletasks()
                    terminal_width = dialog.winfo_reqwidth()
                    terminal_height = dialog.winfo_reqheight()
                    
                    if i == len(self.message_dialogs) - 1:
                        y = current_y - (terminal_height // 2)
                    else:
                        y = current_y - terminal_height - self.message_spacing
                    
                    x = mic_x - terminal_width - gap
                    if x < 10:
                        x = mic_x + mic_width + gap
                    
                    dialog.geometry(f"{terminal_width}x{terminal_height}+{x}+{y}")
                    current_y = y
                
                except tk.TclError:
                    dialog._destroyed = True
                    continue
                
                # Bind hover events
                if not hasattr(dialog, '_events_bound'):
                    self._bind_hover_events(dialog, msg_data)
        
        except Exception as e:
            logger.debug(f"Reposition error: {e}")
    
    def _bind_hover_events(self, dialog, msg_data):
        """Bind hover events to dialog"""
        def on_hover(e, m=msg_data):
            try:
                if m['dialog']._destroyed or not m['dialog'].winfo_exists():
                    return
                m['hover'] = True
                m['last_hover_time'] = time.time()
                if m['fade_job']:
                    try:
                        self.root.after_cancel(m['fade_job'])
                    except:
                        pass
                    m['fade_job'] = None
                try:
                    m['dialog'].attributes('-alpha', 0.95)
                except tk.TclError:
                    m['dialog']._destroyed = True
            except:
                pass
        
        def on_leave(e, m=msg_data):
            try:
                if m['dialog']._destroyed or not m['dialog'].winfo_exists():
                    return
                m['hover'] = False
                m['last_hover_time'] = time.time()
                if not m['hover']:
                    m['fade_job'] = self.root.after(
                        self.fade_delay,
                        lambda: self._start_fade(m)
                    )
            except:
                pass
        
        try:
            dialog.bind('<Enter>', on_hover)
            dialog.bind('<Leave>', on_leave)
            dialog.label.bind('<Enter>', on_hover)
            dialog.label.bind('<Leave>', on_leave)
            dialog._events_bound = True
        except:
            pass
    
    def _start_fade(self, msg_data):
        """Start fade animation"""
        try:
            dialog = msg_data['dialog']
            if not msg_data['hover'] and not dialog._destroyed and dialog.winfo_exists():
                self._fade_out(msg_data, 0.90)
        except:
            pass
    
    def _fade_out(self, msg_data, alpha):
        """Fade out animation"""
        try:
            dialog = msg_data['dialog']
            
            if dialog._destroyed:
                return
            
            try:
                if not dialog.winfo_exists():
                    dialog._destroyed = True
                    return
            except tk.TclError:
                dialog._destroyed = True
                return
            
            if msg_data['hover']:
                try:
                    dialog.attributes('-alpha', 0.95)
                except tk.TclError:
                    dialog._destroyed = True
                return
            
            if alpha > 0:
                try:
                    dialog.attributes('-alpha', alpha)
                    self.root.after(50, lambda: self._fade_out(msg_data, alpha - 0.10))
                except tk.TclError:
                    self._remove_message(msg_data)
            else:
                self._remove_message(msg_data)
        
        except Exception as e:
            logger.debug(f"Fade error: {e}")
            self._remove_message(msg_data)
    
    def _remove_message(self, msg_data):
        """Remove message safely"""
        try:
            dialog = msg_data['dialog']
            dialog._destroyed = True
            
            if msg_data['fade_job']:
                try:
                    self.root.after_cancel(msg_data['fade_job'])
                except:
                    pass
                msg_data['fade_job'] = None
            
            if msg_data in self.message_dialogs:
                self.message_dialogs.remove(msg_data)
            
            try:
                if dialog.winfo_exists():
                    dialog.destroy()
                    self.total_messages_destroyed += 1
            except (tk.TclError, RuntimeError):
                pass
            
            try:
                self._reposition_all_dialogs()
            except:
                pass
        
        except Exception as e:
            logger.debug(f"Remove error: {e}")
    
    def _force_remove_message(self, msg_data):
        """Force remove message without animations"""
        try:
            dialog = msg_data['dialog']
            dialog._destroyed = True
            
            if msg_data['fade_job']:
                try:
                    self.root.after_cancel(msg_data['fade_job'])
                except:
                    pass
            
            if msg_data in self.message_dialogs:
                self.message_dialogs.remove(msg_data)
            
            try:
                dialog.destroy()
                self.total_messages_destroyed += 1
            except:
                pass
        
        except:
            pass
    
    def clear_all(self):
        """Clear all messages"""
        with self.lock:
            for msg_data in self.message_dialogs[:]:
                self._force_remove_message(msg_data)
            self.message_dialogs.clear()
    
    def _start_watchdog(self):
        """Watchdog with memory stats"""
        def watchdog_loop():
            while True:
                try:
                    current_time = time.time()
                    
                    with self.lock:
                        for msg_data in self.message_dialogs[:]:
                            try:
                                dialog = msg_data['dialog']
                                
                                if dialog._destroyed or not dialog.winfo_exists():
                                    continue
                                
                                message_age = current_time - msg_data['created_at']
                                time_since_hover = current_time - msg_data.get('last_hover_time', msg_data['created_at'])
                                
                                should_fade = (
                                    message_age > self.max_message_lifetime / 1000 or
                                    (not msg_data['hover'] and time_since_hover > 8)
                                )
                                
                                if should_fade:
                                    msg_data['hover'] = False
                                    if msg_data['fade_job']:
                                        try:
                                            self.root.after_cancel(msg_data['fade_job'])
                                        except:
                                            pass
                                    self.root.after(0, lambda m=msg_data: self._start_fade(m))
                            
                            except:
                                pass
                    
                    time.sleep(1.5)  # More aggressive checking
                
                except:
                    time.sleep(2)
        
        threading.Thread(target=watchdog_loop, daemon=True).start()