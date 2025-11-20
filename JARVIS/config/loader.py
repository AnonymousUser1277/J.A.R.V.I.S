"""
Central configuration loader from config.ini
"""

import configparser
from pathlib import Path

# Build the path to config.ini relative to this file
# config/loader.py -> config/ -> project_root/ -> config.ini
CONFIG_FILE_PATH = Path(__file__).parent.parent / 'config.ini'

class Config:
    """A class to hold all configuration settings, read from config.ini."""
    def __init__(self):
        parser = configparser.ConfigParser(interpolation=None)
        if not CONFIG_FILE_PATH.exists():
            raise FileNotFoundError(f"Configuration file not found at: {CONFIG_FILE_PATH}")
        
        parser.read(CONFIG_FILE_PATH)

        # [Paths]
        self.Program_path = parser.get('Paths', 'Program_path')
        self.tesseract_cmd = parser.get('Paths', 'tesseract_cmd')
        

        # [Audio]
        self.enable_stt = parser.getboolean('Audio', 'enable_stt')
        self.enable_tts = parser.getboolean('Audio', 'enable_tts')
        self.stt_website_url = parser.get('Audio', 'stt_website_url')
        self.stt_language = parser.get('Audio', 'stt_language')
        self.TTS_Voice = parser.get('Audio', 'TTS_Voice')
        self.Wake_word = parser.get('Audio', 'Wake_word')

        # [Behavior]
        self.confirm_ai_execution = parser.getboolean('Behavior', 'confirm_ai_execution')
        self.auto_tts_output = parser.getboolean('Behavior', 'auto_tts_output')
        self.notifier_grace_period = parser.getfloat('Behavior', 'notifier_grace_period')
        self.dev_mode = parser.getboolean('Behavior', 'dev_mode')
        self.hide_console_window = parser.getboolean('Behavior', 'hide_console_window')
        # --- FIX: Read as float, then convert to int to handle decimals ---
        self.TERMINAL_MAX_MESSAGES = int(parser.getfloat('Behavior', 'TERMINAL_MAX_MESSAGES'))
        self.TERMINAL_MESSAGE_LIFETIME = int(parser.getfloat('Behavior', 'TERMINAL_MESSAGE_LIFETIME'))

        # [Monitors]
        self.browser_url_poll = parser.getfloat('Monitors', 'browser_url_poll')
        self.explorer_path_poll = parser.getfloat('Monitors', 'explorer_path_poll')
        self.clipboard_poll = parser.getfloat('Monitors', 'clipboard_poll')
        self.active_window_poll = parser.getfloat('Monitors', 'active_window_poll')
        self.downloads_poll = parser.getfloat('Monitors', 'downloads_poll')
        self.performance_poll = parser.getfloat('Monitors', 'performance_poll')
        self.idle_time_poll = parser.getfloat('Monitors', 'idle_time_poll')
        self.network_poll = parser.getfloat('Monitors', 'network_poll')
        self.usb_ports_poll = parser.getfloat('Monitors', 'usb_ports_poll')
        self.bluetooth_poll = parser.getfloat('Monitors', 'bluetooth_poll')
        self.battery_poll = parser.getfloat('Monitors', 'battery_poll')

        # [Integrations]
        self.calendar_url = parser.get('Integrations', 'calendar_url')
        self.google_app_password = parser.get('Integrations', 'google_app_password')
        self.your_email_address = parser.get('Integrations', 'your_email_address')

# Create a single, global instance of the Config class to be imported elsewhere
settings = Config()