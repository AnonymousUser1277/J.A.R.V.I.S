"""
Browser URL monitoring - HYBRID APPROACH
Primary: Extension-based (fast, reliable)
Fallback: UI Automation (slower but works always)
"""
import time
import logging
try:
    import uiautomation as auto
    UI_AUTOMATION_AVAILABLE = True
except ImportError:
    UI_AUTOMATION_AVAILABLE = False

logger = logging.getLogger(__name__)

def get_active_browser_url():
    """Get URL from active browser's address bar using UI Automation"""
    if not UI_AUTOMATION_AVAILABLE:
        return None
    
    try:
        foreground = auto.GetForegroundControl()
        if not foreground:
            return None
        
        window_name = foreground.Name.lower()
        class_name = foreground.ClassName
        
        # Chrome/Edge
        if 'chrome' in window_name or 'edge' in window_name or class_name == 'Chrome_WidgetWin_1':
            try:
                # Try new Chrome UI first
                address_bar = foreground.EditControl(AutomationId='omnibox')
                if not address_bar.Exists(0, 0):
                    # Fallback to old UI
                    address_bar = foreground.EditControl(Name='Address and search bar')
                
                if address_bar.Exists(0, 0):
                    url = address_bar.GetValuePattern().Value
                    if url and len(url) > 0:
                        return url
            except Exception as e:
                logger.debug(f"Chrome URL extraction failed: {e}")
        
        # Firefox
        elif 'firefox' in window_name:
            try:
                address_bar = foreground.EditControl(AutomationId='urlbar-input')
                if address_bar.Exists(0, 0):
                    url = address_bar.GetValuePattern().Value
                    if url and len(url) > 0:
                        return url
            except Exception as e:
                logger.debug(f"Firefox URL extraction failed: {e}")
    
    except Exception as e:
        logger.debug(f"Browser URL extraction error: {e}")
    
    return None

def browser_url_monitor(context_manager, poll=...):
    """
    Monitor active browser URL changes
    Uses hybrid approach: extension + UI automation fallback
    """
    last_url_from_extension = None
    last_url_from_ui = None
    extension_timeout = 10  # seconds
    last_extension_update = time.time()
    
    while True:
        try:
            current_time = time.time()
            
            # Check if extension has sent update recently
            current_url = context_manager.current_url
            if current_url != last_url_from_extension:
                last_url_from_extension = current_url
                last_extension_update = current_time
            
            # If extension hasn't updated in 10 seconds, use UI automation fallback
            if current_time - last_extension_update > extension_timeout:
                ui_url = get_active_browser_url()
                if ui_url and ui_url != last_url_from_ui:
                    last_url_from_ui = ui_url
                    context_manager.update_url(ui_url)
                    logger.debug(f"📡 Browser URL (UI fallback): {ui_url[:50]}...")
            
        except Exception as e:
            logger.error(f"Browser monitor error: {e}")
        
        time.sleep(poll)