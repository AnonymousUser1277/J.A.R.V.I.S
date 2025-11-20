"""
Automation package
"""

from .screen import click_on_any_text_on_screen, move_cursor_to_text
from .executor import run_generated_code
from .hotkeys import HotkeyManager
__all__ = [
    'click_on_any_text_on_screen',
    'move_cursor_to_text',
    'run_generated_code',
    'HotkeyManager'
]