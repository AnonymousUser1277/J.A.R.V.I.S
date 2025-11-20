"""
Helper utilities
"""

import sys
import os

def restart_program():
    """Restart the entire program"""
    print("🔄 Restarting program...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

def get_script_path():
    """Get current script path"""
    try:
        return os.path.abspath(__file__)
    except NameError:
        return os.path.abspath(sys.argv[0])