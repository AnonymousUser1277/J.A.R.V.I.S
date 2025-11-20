"""
Command alias system
Allows users to define shortcuts for common commands
"""
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from config.settings import DATA_DIR

logger = logging.getLogger(__name__)

class AliasManager:
    """Manage command aliases"""
    
    # Default aliases
    DEFAULT_ALIASES = {
        'lights off': 'turn off bedroom lights',
        'lights on': 'turn on bedroom lights',
        'email': 'open gmail',
        'music': 'play spotify',
        'break': 'remind me to take a break in 1 hour',
        'meeting': 'open calendar',
        'code': 'open visual studio code',
        'work': 'open chrome and slack',
    }
    
    def __init__(self):
        path_mgr = DATA_DIR
        self.aliases_file = path_mgr / "command_aliases.json"
        self.aliases: Dict[str, str] = self.DEFAULT_ALIASES.copy()
        
        # Load saved aliases
        self._load_aliases()
    
    def _load_aliases(self):
        """Load aliases from disk"""
        if self.aliases_file.exists():
            try:
                with open(self.aliases_file, 'r', encoding='utf-8') as f:
                    saved_aliases = json.load(f)
                    self.aliases.update(saved_aliases)
                logger.info(f"Loaded {len(saved_aliases)} custom aliases")
            except Exception as e:
                logger.error(f"Failed to load aliases: {e}")
    
    def _save_aliases(self):
        """Save aliases to disk"""
        try:
            # Only save custom aliases (not defaults)
            custom_aliases = {
                k: v for k, v in self.aliases.items()
                if k not in self.DEFAULT_ALIASES or self.aliases[k] != self.DEFAULT_ALIASES[k]
            }
            
            with open(self.aliases_file, 'w', encoding='utf-8') as f:
                json.dump(custom_aliases, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save aliases: {e}")
    
    def add_alias(self, alias: str, command: str):
        """Add or update an alias"""
        alias = alias.lower().strip()
        command = command.strip()
        
        self.aliases[alias] = command
        self._save_aliases()
        logger.info(f"Alias added: '{alias}' → '{command}'")
    
    def remove_alias(self, alias: str) -> bool:
        """Remove an alias"""
        alias = alias.lower().strip()
        
        if alias in self.aliases:
            del self.aliases[alias]
            self._save_aliases()
            logger.info(f"Alias removed: '{alias}'")
            return True
        return False
    
    def expand(self, command: str) -> str:
        """
        Expand alias if it exists
        
        Args:
            command: User's command
            
        Returns:
            Expanded command or original if no alias
        """
        command_lower = command.lower().strip()
        
        # Check exact match first
        if command_lower in self.aliases:
            expanded = self.aliases[command_lower]
            logger.debug(f"Alias expanded: '{command}' → '{expanded}'")
            return expanded
        
        # Check if command starts with an alias
        for alias, expansion in self.aliases.items():
            if command_lower.startswith(alias + " "):
                # Preserve rest of command
                rest = command[len(alias):].strip()
                expanded = f"{expansion} {rest}"
                logger.debug(f"Partial alias expanded: '{command}' → '{expanded}'")
                return expanded
        
        return command
    
    def list_aliases(self) -> Dict[str, str]:
        """Get all aliases"""
        return self.aliases.copy()


# Global alias manager
_alias_manager = None

def get_alias_manager() -> AliasManager:
    """Get global alias manager"""
    global _alias_manager
    if _alias_manager is None:
        _alias_manager = AliasManager()
    return _alias_manager