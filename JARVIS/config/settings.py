"""
Configuration and constants
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from .loader import settings

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "Data"
CACHE_DIR = DATA_DIR / "Cache"
HISTORY_DIR = DATA_DIR / "History"
LOG_DIR = DATA_DIR / "logs"

# Ensure directories exist
for directory in [DATA_DIR, CACHE_DIR, HISTORY_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Constants
MAX_HISTORY = 50
HISTORY_FILE = HISTORY_DIR / "command_history.json"

# Get values from the central config loader instead of hardcoding them
AUTO_TTS = settings.auto_tts_output
CONFIRM_AI_EXECUTION = settings.confirm_ai_execution
ENABLE_STT = settings.enable_stt
ENABLE_TTS = settings.enable_tts

STOP_WORDS = [
    "jarvis stop", "jarvis wait", "jarvis pause",
    "mute yourself", "stop jarvis", "wait jarvis"
]

IGNORE_WORDS = [
    "jar", "jarvis", "jarvis jarvis", "hey jarvis", 
    "hello jarvis", "hi jarvis"
]
# Replace simple list with context-aware function:

def is_destructive_command(prompt: str) -> tuple[bool, str]:
    """
    Check if command is destructive with context awareness
    
    Returns:
        (is_destructive, keyword_found)
    """
    prompt_lower = prompt.lower().strip()
    
    # Destructive keywords with context
    destructive_patterns = {
        'delete': ['delete file', 'delete folder', 'delete all', 'delete everything'],
        'remove': ['remove file', 'remove folder', 'remove all'],
        'format': ['format drive', 'format disk', 'format c:', 'format partition'],
        'wipe': ['wipe disk', 'wipe drive', 'wipe data'],
        'destroy': ['destroy data', 'destroy file'],
        'kill': ['kill process', 'kill all', 'kill task'],
        'terminate': ['terminate process', 'terminate all'],
        'reset': ['reset system', 'reset windows', 'factory reset']
    }
    
    # Safe contexts (these are NOT destructive)
    safe_contexts = [
        'format text',
        'format this',
        'format code',
        'format document',
        'delete line',
        'delete word',
        'remove duplicates',
        'remove spaces',
        'kill time',  # idiom
    ]
    
    # Check safe contexts first
    for safe_context in safe_contexts:
        if safe_context in prompt_lower:
            return False, ""
    
    # Check destructive patterns
    for keyword, patterns in destructive_patterns.items():
        for pattern in patterns:
            if pattern in prompt_lower:
                return True, keyword
    
    # Check standalone dangerous keywords only if they're the main action
    dangerous_standalone = ['delete', 'remove', 'format', 'wipe', 'destroy']
    words = prompt_lower.split()
    
    if len(words) >= 2:
        first_word = words[0]
        if first_word in dangerous_standalone:
            # Check if second word is a file/folder indicator
            file_indicators = ['file', 'folder', 'directory', 'drive', 'disk', 'all', 'everything']
            if any(indicator in words[1] for indicator in file_indicators):
                return True, first_word
    
    return False, ""
EXCLUDE_KEYWORDS = {
        'click on','bookmar','save','create','write','exit','suggest','tell','move to','download','move cursor',
        'live','make','realtime','zoom',"play","close all","improve","new","present",
        "current price",'what','where','who','how','whom','when''explain','describe','which','do',
        'does','did','can', "time","previous","again","next","back","forward","switch to","open last",
        "open previous","open next","open back","open forward","go back","go forward",
        "go previous","go next","close","search","repeat","re",'re-','rerun','do it',
        'it','this','that'
    
}

# DESTRUCTIVE_KEYWORDS = [
#     'delete', 'remove', 'format', 'wipe', 'destroy', 
#     'kill', 'terminate', 'reset'
# ]

def setup_environment():
    """Setup environment variables and configuration"""
    load_dotenv()
    
    # Hide pygame support prompt
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
    
    # Set process priority
    try:
        import psutil
        p = psutil.Process()
        p.nice(psutil.HIGH_PRIORITY_CLASS)
    except:
        pass

def get_os_info():
    """Get operating system information"""
    import platform
    
    os_name = platform.system()
    os_release = platform.release()
    
    if os_name == "Windows":
        return f"Windows {os_release}"
    elif os_name == "Darwin":
        return "macOS"
    elif os_name == "Linux":
        if "ANDROID_ROOT" in os.environ:
            return "Android"
        return "Linux"
    else:
        return f"Unknown OS ({os_name})"