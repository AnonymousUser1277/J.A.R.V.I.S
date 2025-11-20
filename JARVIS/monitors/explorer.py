"""
File Explorer path monitoring
Tracks current folder in Windows Explorer
"""

import time
import win32gui
import pythoncom

def get_explorer_path(context_manager):
    """Get current File Explorer path"""
    try:
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None
        
        class_name = win32gui.GetClassName(hwnd)
        if 'CabinetWClass' not in class_name and 'ExploreWClass' not in class_name:
            return None
        
        shell = context_manager._shell_windows
        if not shell:
            return None
        
        try:
            windows = shell.Windows()
            for window in windows:
                try:
                    if window.HWND == hwnd:
                        path = window.Document.Folder.Self.Path
                        if path:
                            return path
                except:
                    continue
        except:
            pass
        
        return None
    except:
        return None

def explorer_path_monitor(context_manager, poll=...):
    """Monitor File Explorer path changes"""
    try:
        pythoncom.CoInitialize()
    except:
        pass
    
    # Initialize Shell.Application
    import win32com.client
    try:
        context_manager._shell_windows = win32com.client.Dispatch("Shell.Application")
    except:
        pass
    
    while True:
        try:
            path = get_explorer_path(context_manager)
            if path:
                context_manager.update_folder(path)
        except:
            pass
        time.sleep(poll)