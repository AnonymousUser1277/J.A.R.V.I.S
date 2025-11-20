"""
TTS Compatibility Wrapper
This file maintains backward compatibility with your existing speak() calls
while using the new Selenium-based TTS engine under the hood.

REPLACE your existing audio/tts.py with this file.
"""

import logging

logger = logging.getLogger(__name__)

# Global reference to the TTS engine (initialized by main.py)
_global_tts_engine = None

def set_tts_engine(engine):
    """
    Set the global TTS engine instance.
    Called by main.py during initialization.
    """
    global _global_tts_engine
    _global_tts_engine = engine
    logger.info("✅ Global TTS engine set")

def speak(text, wait=False):
    """
    Speak text using the global TTS engine.
    This maintains compatibility with all existing code.
    
    Args:
        text: Text to speak
        wait: If True, wait for speech to complete
        
    Returns:
        bool: True if successful, False otherwise
        
    Usage:
        from audio.tts import speak
        speak("Hello, I am Jarvis")
    """
    global _global_tts_engine
    
    if not text or not text.strip():
        return False
    
    # If engine not set, try to import from main
    if _global_tts_engine is None:
        try:
            import main
            if hasattr(main, '_tts_engine') and main._tts_engine:
                _global_tts_engine = main._tts_engine
            else:
                logger.warning("⚠️ TTS engine not initialized yet")
                return False
        except Exception as e:
            logger.error(f"❌ Cannot access TTS engine: {e}")
            return False
    
    try:
        result = _global_tts_engine.speak(text)
        
        if wait:
            _global_tts_engine.wait_until_done()
        
        return result
    except Exception as e:
        logger.error(f"Speech error: {e}")
        return False

def stop_speaking():
    """Stop current speech"""
    global _global_tts_engine
    if _global_tts_engine:
        try:
            _global_tts_engine.stop_speaking()
        except Exception as e:
            logger.error(f"Stop speaking error: {e}")

def clear_queue():
    """Clear speech queue"""
    global _global_tts_engine
    if _global_tts_engine:
        try:
            _global_tts_engine.clear_queue()
        except Exception as e:
            logger.error(f"Clear queue error: {e}")

def wait_until_done(timeout=30):
    """Wait for speech to complete"""
    global _global_tts_engine
    if _global_tts_engine:
        try:
            return _global_tts_engine.wait_until_done(timeout)
        except Exception as e:
            logger.error(f"Wait error: {e}")
            return False
    return False

# Legacy compatibility - these were in your original tts.py
def open_browser():
    """
    Legacy function - no longer needed with Selenium implementation.
    Kept for backward compatibility.
    """
    pass

# For backward compatibility with Flask-based approach
app = None
speech_queue = None

logger.info("✅ TTS compatibility wrapper loaded")