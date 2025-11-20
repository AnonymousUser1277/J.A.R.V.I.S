"""
Optimized clipboard monitoring using Windows events
No polling - reacts immediately to clipboard changes
"""
import threading
import logging
import win32clipboard
import win32con
import ctypes
from ctypes import wintypes

logger = logging.getLogger(__name__)

# Windows API constants
WM_CLIPBOARDUPDATE = 0x031D

class ClipboardMonitor:
    """
    Event-driven clipboard monitor using Windows messages
    Much more efficient than polling
    """
    
    def __init__(self, context_manager):
        self.context_manager = context_manager
        self.hwnd = None
        self.running = False
        self.thread = None
    
    def start(self):
        """Start monitoring"""
        self.running = True
        self.thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="Clipboard-Monitor"
        )
        self.thread.start()
    
    def _monitor_loop(self):
        """Main monitoring loop using Windows messages"""
        import win32gui
        import win32api
        
        # Create message-only window
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._window_proc
        wc.lpszClassName = "ClipboardMonitor"
        wc.hInstance = win32api.GetModuleHandle(None)
        
        try:
            class_atom = win32gui.RegisterClass(wc)
            self.hwnd = win32gui.CreateWindow(
                class_atom,
                "ClipboardMonitor",
                0,
                0, 0, 0, 0,
                win32con.HWND_MESSAGE,
                0,
                wc.hInstance,
                None
            )
            
            # Register for clipboard notifications
            ctypes.windll.user32.AddClipboardFormatListener(self.hwnd)
            
            logger.info("✅ Event-driven clipboard monitor started")
            
            # Message loop
            win32gui.PumpMessages()
        
        except Exception as e:
            logger.error(f"Clipboard monitor error: {e}")
    
    def _window_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure to handle messages"""
        if msg == WM_CLIPBOARDUPDATE:
            # Clipboard changed!
            self._on_clipboard_change()
        
        return 0
    
    def _on_clipboard_change(self):
        """Handle clipboard change event"""
        try:
            content = get_clipboard_content()
            if content:
                self.context_manager.update_clipboard(content)
                logger.debug(f"📋 Clipboard updated: {content[0]}")
        except Exception as e:
            logger.debug(f"Clipboard read error: {e}")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.hwnd:
            try:
                ctypes.windll.user32.RemoveClipboardFormatListener(self.hwnd)
            except:
                pass


def get_clipboard_content():
    """Get current clipboard content (unchanged)"""
    try:
        win32clipboard.OpenClipboard()
        try:
            # Text
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                return ('text', data[:200])
            
            # Files
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_HDROP):
                files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                return ('files', files)
            
            # Image
            elif win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                return ('image', '[Image Data]')
        finally:
            win32clipboard.CloseClipboard()
    except:
        pass
    
    return None


def clipboard_monitor(context_manager, poll=2.0):
    """
    Start event-driven clipboard monitor
    'poll' parameter kept for compatibility but not used
    """
    monitor = ClipboardMonitor(context_manager)
    monitor.start()
    
    # Keep thread alive
    import time
    while True:
        time.sleep(60)