"""
Utilities package
⚠️ UPDATED: Safe imports that won't break first-time setup
"""

# ⚠️ Don't import setup_wizard here - it's imported directly in main.py
# to avoid circular dependencies during first-time setup

# These imports are safe because they're only used AFTER setup completes
from .decorators import safe_execute, timing_decorator
from .helpers import restart_program
from .admin import is_admin

# These require config files, so wrapped in try-except
try:
    from .logger import setup_logging, GuiLogger
    from .file_watcher import start_file_watcher
except (ImportError, FileNotFoundError):
    # Config files don't exist yet (first-time setup)
    # These will be available after setup completes
    setup_logging = None
    GuiLogger = None
    start_file_watcher = None

__all__ = [
    'setup_logging',
    'GuiLogger',
    'safe_execute',
    'restart_program',
    'start_file_watcher',
    'timing_decorator',
    'is_admin'
]