import sys
import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def is_admin():
    """Check if running with admin privileges"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

class ReloadHandler(FileSystemEventHandler):
    def __init__(self, watched_dirs):
        self.watched_dirs = watched_dirs
        super().__init__()
        # timers for debouncing per-file
        self._timers = {}
        # store last seen (mtime, size) snapshots
        self._snapshots = {}
    
    def on_modified(self, event):
        # Only care about files (not directories)
        try:
            if event.is_directory:
                return
        except Exception:
            pass

        path = event.src_path
        if any(x in path for x in ['Data\\logs', 'Data\\Cache', '__pycache__', '.git', 'scheduled_tasks.db']):
            return
        # Only Python files
        if not path.endswith('.py'):
            return

        # Ignore editor/temp files by name patterns
        if self._is_temporary_file(path):
            return

        rel_path = os.path.relpath(path)
        # Check if file is in watched directories or is main.py
        is_watched = any(rel_path.startswith(d + os.sep) or rel_path == d for d in self.watched_dirs) or rel_path == 'main.py'
        if not is_watched:
            return

        # Debounce and wait for file to stabilize (common when editors save via temp files)
        # Capture current snapshot
        try:
            stat = os.stat(path)
            snapshot = (stat.st_mtime, stat.st_size)
        except Exception:
            snapshot = None

        # Cancel existing timer for this path
        if path in self._timers:
            try:
                self._timers[path].cancel()
            except Exception:
                pass

        # store snapshot and schedule confirmation
        self._snapshots[path] = snapshot
        t = threading.Timer(0.6, self._confirm_and_reload, args=(path, rel_path))
        t.daemon = True
        self._timers[path] = t
        t.start()

    def _is_temporary_file(self, path):
        """Return True for known editor/temp file name patterns to ignore."""
        fname = os.path.basename(path)
        lower = fname.lower()
        # common patterns
        tmp_patterns = ['.swp', '.swx', '~', '.tmp', '.part', '.~', '___jb_', '.kate-swp', '.goutputstream', '~$']
        for p in tmp_patterns:
            if lower.startswith(p) or lower.endswith(p) or p in lower:
                return True
        # hidden files starting with dot
        if fname.startswith('.'):
            return True
        return False

    def _confirm_and_reload(self, path, rel_path):
        """Confirm file is stable (mtime/size unchanged) before reloading."""
        try:
            # get previous snapshot
            prev = self._snapshots.get(path)
            try:
                stat = os.stat(path)
                now = (stat.st_mtime, stat.st_size)
            except Exception:
                now = None

            # if snapshot missing or file changed since snapshot, don't reload yet
            if prev is None or now is None:
                return

            if prev != now:
                # file still changing — wait a bit more; schedule another check
                t = threading.Timer(0.6, self._confirm_and_reload, args=(path, rel_path))
                t.daemon = True
                self._timers[path] = t
                self._snapshots[path] = now
                t.start()
                return

            # At this point file seems stable — treat as a manual save
            print(f"🔄 File saved: {rel_path}. Reloading main.py...")

            if is_admin():
                print("✓ Reloading with Administrator privileges")
            else:
                print("⚠ Reloading WITHOUT Administrator privileges")

            python = sys.executable
            # Restart main.py specifically
            os.execl(python, python, "main.py")

        finally:
            # cleanup timer and snapshot
            try:
                if path in self._timers:
                    del self._timers[path]
            except Exception:
                pass
            try:
                if path in self._snapshots:
                    del self._snapshots[path]
            except Exception:
                pass

def start_file_watcher():
    """Start watching for file changes in specific directories only"""
    # Define which directories to watch
    watched_dirs = [
        "ai",
        "audio",
        "automation",
        "config",
        "core",
        "monitors",
        "ui",
        "utils"
    ]
    
    observer = Observer()
    handler = ReloadHandler(watched_dirs)
    observer.schedule(handler, path=".", recursive=True)
    observer.start()
    print(f"👁 File watcher started - monitoring: {', '.join(watched_dirs)} and main.py")
    return observer
