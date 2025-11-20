"""
Monitor configuration and preferences
Stores user's preferred monitor for UI elements
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict
from config.settings import DATA_DIR

logger = logging.getLogger(__name__)

class MonitorConfig:
    """Manage monitor preferences"""
    
    def __init__(self):
        self.config_file = DATA_DIR / "monitor_preferences.json"
        self.preferences = self._load_preferences()
    
    def _load_preferences(self) -> Dict:
        """Load monitor preferences from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load monitor preferences: {e}")
        
        # Default preferences
        return {
            'preferred_monitor': None,  # None = auto-detect
            'control_orb_position': 'bottom-right',
            'terminal_position': 'left',
            'remember_positions': True
        }
    
    def _save_preferences(self):
        """Save preferences to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save monitor preferences: {e}")
    
    def set_preferred_monitor(self, monitor_index: int):
        """Set preferred monitor by index"""
        self.preferences['preferred_monitor'] = monitor_index
        self._save_preferences()
        logger.info(f"✅ Preferred monitor set to #{monitor_index}")
    
    def get_preferred_monitor(self) -> Optional[int]:
        """Get preferred monitor index"""
        return self.preferences.get('preferred_monitor')
    
    def set_control_position(self, position: str):
        """Set control orb position (bottom-right, bottom-left, etc.)"""
        self.preferences['control_orb_position'] = position
        self._save_preferences()
    
    def get_control_position(self) -> str:
        """Get control orb position"""
        return self.preferences.get('control_orb_position', 'bottom-right')


# Global instance
_config = None

def get_monitor_config() -> MonitorConfig:
    """Get global monitor config"""
    global _config
    if _config is None:
        _config = MonitorConfig()
    return _config