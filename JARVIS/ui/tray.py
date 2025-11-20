"""
System tray icon with menu
"""

from datetime import datetime
import os
import pystray
from PIL import Image, ImageDraw

def create_tray_icon(gui_handler):
    """Create system tray icon with menu"""
    
    # Create icon
    image = Image.new("RGB", (64, 64), (30, 30, 30))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 8, 56, 56), fill=(80, 80, 80))
    draw.text((20, 18), "AI", fill=(255, 255, 255))
    
    def on_restart(icon, item):
        """Restart program"""
        print("🔄 Restarting from system tray...")
        from utils.helpers import restart_program
        restart_program()
        
    def on_edit_cache(icon, item):
        """Open cache editor"""
        print("📝 Opening cache editor...")
        try:
            from .cache_editor import create_redis_cache_editor
            # Schedule on main thread using the gui_handler we have
            gui_handler.root.after(0, lambda: create_redis_cache_editor(gui_handler))
        except Exception as e:
            print(f"⚠️ Failed to open cache editor: {e}")
    def on_settings(icon, item):
        '''Open settings dialog'''
        print("⚙️ Opening settings...")
        try:
            
            from ui.settings_dialog import open_settings_dialog
            gui_handler.root.after(0, lambda: open_settings_dialog(None))
        except Exception as e:
            print(f"⚠️ Failed to open settings: {e}")
    def on_show_context(icon, item):
        """Show current context"""
        context_info = gui_handler.context_manager.get_context_string()
        print(context_info)
    
    def on_edit_code(icon, item):
        """Open JARVIS project folder in VS Code"""
        try:
            # Get the project root directory (where main.py is located)
            from config.loader import settings
            # project_root = r"C:\\Users\\Nandlal\\Documents\\.NANDLAL\\python"
            PROJECT_ROOT = settings.Program_path
            os.system(f'code "{PROJECT_ROOT}"')
        except Exception as e :
            print(f"Error occured while opening project file: {e} ")
            
    
    def on_open_logs(icon, item):
        """Open log"""
        try:
            from config.settings import LOG_DIR
            from datetime import datetime
            today_log = datetime.now().strftime("%Y-%m-%d") + ".log"
            log_file = LOG_DIR / today_log
            if os.path.exists(LOG_DIR):
                # os.startfile(str(LOG_DIR))
                os.startfile(str(log_file))
                print("opened logs")
        except Exception as e:
            print(f"Failed to open logs folder: {e}")
    
    def on_exit(icon, item):
        """Exit program"""
        print("❌ Exiting from system tray...")
        gui_handler.cleanup()
        icon.stop()
        gui_handler.root.after(0, gui_handler.root.quit)
    def on_select_monitor(icon, item):
        """Show monitor selection dialog"""
        try:
            from ui.monitor_selector import show_monitor_selector
            gui_handler.root.after(0, lambda: show_monitor_selector(gui_handler))
        except Exception as e:
            print(f"Monitor selector error: {e}")
    def on_show_tasks(icon, item):
        """Show upcoming tasks"""
        from core.task_scheduler import get_task_scheduler
        scheduler = get_task_scheduler()
        tasks = scheduler.get_upcoming_tasks(limit=5)
        
        if not tasks:
            print("📅 No upcoming tasks")
        else:
            print(f"📅 Upcoming Tasks ({len(tasks)}):")
            for task in tasks:
                next_run = datetime.fromtimestamp(task.next_run)
                print(f"  - {task.name} at {next_run.strftime('%Y-%m-%d %H:%M')}")
    
    def on_change_theme(icon, item):
        """Show theme selector"""
        from ui.theme_selector import show_theme_selector
        gui_handler.root.after(0, lambda: show_theme_selector(gui_handler))
    def on_backup_manager(icon, item):
        """Show backup manager"""
        from ui.cache_manager import show_backup_manager
        gui_handler.root.after(0, lambda: show_backup_manager(gui_handler))
    def on_alias_editor(icon, item):
        """Show alias editor"""
        from ui.alias_editor import show_alias_editor
        gui_handler.root.after(0, lambda: show_alias_editor(gui_handler))
    def on_show_suggestions(icon, item):
        """Show proactive suggestions"""
        from ui.suggestion_panel import show_suggestions_panel
        gui_handler.root.after(0, lambda: show_suggestions_panel(gui_handler))
    # Menu
    menu = pystray.Menu(
        pystray.MenuItem("📅 Show Tasks", on_show_tasks),
        pystray.MenuItem("📊 Show Context", on_show_context),
        pystray.MenuItem("📺 Select Monitor", on_select_monitor),
        pystray.MenuItem("📝 Edit Cache", on_edit_cache),
        pystray.MenuItem("💻 Edit Code", on_edit_code),
        pystray.MenuItem("🗄️ Open Log", on_open_logs),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("💡 Suggestions", on_show_suggestions),
        pystray.MenuItem("⚡ Command Aliases", on_alias_editor),
        pystray.MenuItem("🎨 Change Theme", on_change_theme),
        pystray.MenuItem("⚙️ Settings", on_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("💾 Cache Backups", on_backup_manager),
        pystray.MenuItem("🔄 Restart", on_restart),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("❌ Exit", on_exit)
    )
    
    icon = pystray.Icon("AI_Assistant", image, "AI Assistant", menu)
    
    # Run in background
    import threading
    threading.Thread(target=icon.run, daemon=True).start()