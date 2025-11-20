"""
Theme management system
Supports dark/light themes and custom color schemes
"""
import json
import logging
from typing import Dict
from pathlib import Path
from config.settings import DATA_DIR

logger = logging.getLogger(__name__)

class Theme:
    """Theme color scheme"""
    
    def __init__(self, name: str, colors: Dict[str, str]):
        self.name = name
        self.colors = colors
    
    def get(self, key: str, default: str = "#000000") -> str:
        """Get color by key"""
        return self.colors.get(key, default)


class ThemeManager:
    """Manage application themes"""
    
    THEMES = {
        'dark': Theme('Dark', {
            'bg_primary': '#0a0a0a',
            'bg_secondary': '#1e1e1e',
            'bg_tertiary': '#2d2d2d',
            'bg_button': '#4d4d4d',
            'fg_primary': '#ffffff',
            'fg_secondary': '#cccccc',
            'accent_green': '#00ff00',
            'accent_cyan': '#66ccff',
            'accent_yellow': '#ffff66',
            'accent_red': '#ff4444',
            'terminal_bg': '#0a0a0a',
            'terminal_fg': '#00ff00',
            'orb_color': '#00ffff',
            'orb_glow': '#003a3a',
        }),
        'light': Theme('Light', {
            'bg_primary': '#ffffff',
            'bg_secondary': '#f0f0f0',
            'bg_tertiary': '#e0e0e0',
            'bg_button': '#d0d0d0',
            'fg_primary': '#000000',
            'fg_secondary': '#333333',
            'accent_green': '#00aa00',
            'accent_cyan': '#0088cc',
            'accent_yellow': '#cc8800',
            'accent_red': '#cc0000',
            'terminal_bg': '#ffffff',
            'terminal_fg': '#000000',
            'orb_color': '#0088cc',
            'orb_glow': '#88ccff',
        }),
        'matrix': Theme('Matrix', {
            'bg_primary': '#000000',
            'bg_secondary': '#001100',
            'bg_tertiary': '#002200',
            'bg_button': '#003300',
            'fg_primary': '#00ff00',
            'fg_secondary': '#00cc00',
            'accent_green': '#00ff00',
            'accent_cyan': '#00ffaa',
            'accent_yellow': '#88ff00',
            'accent_red': '#ff0000',
            'terminal_bg': '#000000',
            'terminal_fg': '#00ff00',
            'orb_color': '#00ff00',
            'orb_glow': '#003300',
        }),
        'cyberpunk': Theme('Cyberpunk', {
            'bg_primary': '#0a0014',
            'bg_secondary': '#1a0033',
            'bg_tertiary': '#2a0052',
            'bg_button': '#3a0071',
            'fg_primary': '#ff00ff',
            'fg_secondary': '#cc00cc',
            'accent_green': '#00ff88',
            'accent_cyan': '#00ffff',
            'accent_yellow': '#ffff00',
            'accent_red': '#ff0088',
            'terminal_bg': '#0a0014',
            'terminal_fg': '#ff00ff',
            'orb_color': '#ff00ff',
            'orb_glow': '#880088',
        })
    }
    
    def __init__(self):
        path_mgr = Path(DATA_DIR)
        self.config_file = path_mgr / "theme_config.json"
        self.current_theme_name = self._load_theme_preference()
        self.current_theme = self.THEMES.get(self.current_theme_name, self.THEMES['dark'])
    
    def _load_theme_preference(self) -> str:
        """Load saved theme preference"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return data.get('theme', 'dark')
            except Exception as e:
                logger.error(f"Failed to load theme preference: {e}")
        return 'dark'
    
    def _save_theme_preference(self):
        """Save theme preference"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump({'theme': self.current_theme_name}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save theme preference: {e}")
    
    def set_theme(self, theme_name: str):
        """Set current theme"""
        if theme_name in self.THEMES:
            self.current_theme_name = theme_name
            self.current_theme = self.THEMES[theme_name]
            self._save_theme_preference()
            logger.info(f"🎨 Theme changed to: {theme_name}")
            return True
        return False
    
    def get_theme(self) -> Theme:
        """Get current theme"""
        return self.current_theme
    
    def get_theme_names(self) -> list:
        """Get list of available theme names"""
        return list(self.THEMES.keys())
    
    def apply_to_widget(self, widget, **color_keys):
        """
        Apply theme colors to a tkinter widget
        
        Args:
            widget: Tkinter widget
            **color_keys: Mapping of widget option to theme color key
                         e.g., bg='bg_primary', fg='fg_primary'
        """
        for option, color_key in color_keys.items():
            color = self.current_theme.get(color_key)
            try:
                widget.config(**{option: color})
            except Exception as e:
                logger.debug(f"Failed to apply theme to widget: {e}")


# Global theme manager
_theme_manager = None

def get_theme_manager() -> ThemeManager:
    """Get or create global theme manager"""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager