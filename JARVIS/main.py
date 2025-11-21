"""
JARVIS main.py - Updated with Setup Wizard Integration
Replace your existing main.py with this version
"""
import sys
import ctypes
from pathlib import Path

# Hide console window IMMEDIATELY


# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# ✅ FIRST-TIME SETUP CHECK (NEW!)
# ⚠️ This MUST come BEFORE any other JARVIS imports
# because it creates config files if they don't exist
try:
    from utils.setup_wizard import check_first_time_setup
    
    if check_first_time_setup():
        print("✅ Setup completed! Starting JARVIS...")
        import time
        time.sleep(2)
except Exception as e:
    print(f"❌ Setup wizard error: {e}")
    # pass

# NOW it's safe to import config modules (files exist)
from config.loader import settings
from config.settings import setup_environment
from core.auth import authenticate_user
from ui.startup import StartupUI
from ui.gui import AIAssistantGUI
from core.notification import greeting
from audio.stt import SpeechToTextListener
from ai.providers import setup_ai_providers
from utils.logger import setup_logging
from utils.file_watcher import start_file_watcher
from utils.admin import is_admin
from ai.connection_pool import integrate_with_providers
import logging
import threading
import atexit
from config.settings import ENABLE_STT, ENABLE_TTS
import gc
def memory_maintenance():
    """Run garbage collection every 5 minutes"""
    import time
    while True:
        time.sleep(300)
        gc.collect()
# --- Hide console window if configured ---
HIDE_CONSOLE = settings.hide_console_window
if HIDE_CONSOLE:
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd != 0:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception as e:
        print("⚠️ Console hide failed:", e)
        input("Press Enter to continue...")
# ✅ Global TTS engine instance
_tts_engine = None

def Startup_cleanup():
    """Cleanup function to run on exit"""
    import os
    import shutil
    import subprocess
    # --- Kill Chrome & ChromeDriver ---
    for proc in ["chrome.exe", "chromedriver.exe"]:
        try:
            subprocess.run(["taskkill", "/F", "/IM", proc], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            pass

    # --- Clear %TEMP% folder ---
    temp_path = os.environ.get("TEMP")

    for item in os.listdir(temp_path):
        item_path = os.path.join(temp_path, item)
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path, ignore_errors=True)
            else:
                os.remove(item_path)
        except:
            pass

def initialize_tts():
    """Initialize Native TTS engine"""
    global _tts_engine
    
    if not ENABLE_TTS:
        logging.info("⚠️ TTS disabled")
        return None
    
    try:
        from audio.tts_native import NativeTTSEngine
        
        # Create native TTS engine
        logging.info("🎤 Initializing Native TTS...")
        _tts_engine = NativeTTSEngine(
            voice_name=settings.TTS_Voice, 
            rate=1,
            volume=100
        )
        
        # Set global engine
        import audio.tts as tts_module
        tts_module.set_tts_engine(_tts_engine)
        
        # Register cleanup
        atexit.register(cleanup_tts)
        
        logging.info("✅ Native TTS initialized")
        return _tts_engine
        
    except Exception as e:
        logging.error(f"❌ TTS initialization failed: {e}", exc_info=True)
        return None

def cleanup_tts():
    """Cleanup TTS engine"""
    global _tts_engine
    if _tts_engine:
        try:
            _tts_engine.cleanup()
        except Exception as e:
            logging.error(f"TTS cleanup error: {e}")

def main():
    """Main entry point with startup sequence"""
    
    admin_status = is_admin()
    listener = None
    tts_engine = None
    
    # 1. Setup logging
    logger = setup_logging()
    
    # 2. Setup environment
    setup_environment()
    
    # 3. Show startup UI
    startup_ui = StartupUI()
    startup_ui.update_status("Checking authentication...")
    print(f"Admin Status: {'Yes' if admin_status else 'No'}\n")
    startup_ui.update_status(f"Clearing old temporary files and processes...")
    Startup_cleanup()
    print("✔ Chrome killed & TEMP cleaned!\n")
    
    # 4. Authenticate user
    if not authenticate_user(startup_ui):
        startup_ui.close()
        return
    
    startup_ui.update_status("Loading AI providers...")
    
    # 5. Initialize AI providers
    client = setup_ai_providers(startup_ui)
    if not client:
        logger.critical("❌ No AI providers could be initialized! Application cannot function.")
        startup_ui.update_status("FATAL: No AI providers available.")
        import time
        time.sleep(5)
        startup_ui.close()
        return
    integrate_with_providers()
    # 6. Initialize TTS (if enabled) - BEFORE STT to avoid conflicts
    if ENABLE_TTS:
        startup_ui.update_status("Initializing text-to-speech...")
        tts_engine = initialize_tts()
        
        if tts_engine:
            import time
            time.sleep(2)
            logger.info("✅ TTS ready")
        else:
            startup_ui.update_status("⚠️ TTS initialization failed - continuing without TTS")
            logger.warning("⚠️ Continuing without TTS")
    
    # 7. Initialize speech listener (if enabled)
    if ENABLE_STT:
        startup_ui.update_status("Initializing speech recognition...")
        try:
            listener = SpeechToTextListener()
            logger.info("✅ STT ready")
        except Exception as e:
            logger.error(f"❌ STT initialization failed: {e}")
            startup_ui.update_status("⚠️ STT initialization failed")
    else:
        startup_ui.update_status("⚠️ STT disabled - voice input unavailable")
    
    startup_ui.update_status("Launching main interface...")
    
    # 8. Start main GUI
    gui = AIAssistantGUI(client, listener, startup_ui)
    
    # 9. Hide startup UI and run
    startup_ui.close()
    threading.Thread(target=memory_maintenance, daemon=True, name="GC-Maintenance").start()
    if ENABLE_TTS and tts_engine:
        threading.Thread(target=greeting, daemon=True).start()
    logger.info("🚀 JARVIS is now running")
    gui.run()
    
    return listener
    
if __name__ == "__main__":
    observer = None
    listener_instance = None
    
    # Only start the file watcher if in development mode
    if settings.dev_mode:
        observer = start_file_watcher()
        
    try:
        listener_instance = main()
        
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("⚠️ Keyboard interrupt received")
        
    except Exception as e:
        logging.getLogger(__name__).critical(f"Fatal error in main loop: {e}", exc_info=True)
        print("\n❌ FATAL ERROR OCCURRED!")
        print(e)
        print("\nThe program crashed. Check the logs for details.")
        input("Press Enter to exit...")
        
    finally:
        # Cleanup
        logging.info("🧹 Starting shutdown sequence...")
        
        try:
            if listener_instance:
                listener_instance.cleanup()
        except Exception as e:
            logging.error(f"STT cleanup error: {e}")
        
        try:
            cleanup_tts()
        except Exception as e:
            logging.error(f"TTS cleanup error: {e}")
        
        if observer:
            observer.stop()
            observer.join()
        
        logging.info("✅ Shutdown complete")
        sys.exit(0)
