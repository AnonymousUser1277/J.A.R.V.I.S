"""
Audio Coordinator - Prevents STT/TTS conflicts
Ensures only one audio operation at a time
"""

import threading
import time
import logging
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class AudioCoordinator:
    """Thread-safe coordinator for STT and TTS"""
    
    def __init__(self):
        self.lock = threading.RLock()
        self.is_speaking = False
        self.is_listening = False
        self.operation_start_time = None
        
        # Statistics
        self.stats = {
            'speak_calls': 0,
            'listen_calls': 0,
            'conflicts_prevented': 0
        }
    
    def speak(self, text: str, wait_time: Optional[float] = None, **kwargs) -> bool:
        """Thread-safe TTS with STT coordination"""
        from audio.tts import speak as _tts_speak
        
        # Wait if currently listening
        max_wait = 5  # seconds
        waited = 0
        while self.is_listening and waited < max_wait:
            time.sleep(0.1)
            waited += 0.1
        
        if self.is_listening:
            logger.warning("⚠️ Still listening after 5s - forcing TTS")
            self.stats['conflicts_prevented'] += 1
        
        with self.lock:
            self.is_speaking = True
            self.operation_start_time = time.time()
            self.stats['speak_calls'] += 1
            
            try:
                result = _tts_speak(text, wait_time, **kwargs)
                return result
            
            except Exception as e:
                logger.error(f"❌ TTS error: {e}")
                return False
            
            finally:
                self.is_speaking = False
                self.operation_start_time = None
                time.sleep(0.2)  # Small gap before allowing listening
    
    def listen(self, stt_listener, check_stop_words: bool = False, stop_words=None) -> Optional[str]:
        """Thread-safe STT with TTS coordination"""
        # Wait if currently speaking
        max_wait = 10  # seconds
        waited = 0
        while self.is_speaking and waited < max_wait:
            time.sleep(0.1)
            waited += 0.1
        
        if self.is_speaking:
            logger.warning("⚠️ Still speaking after 10s - forcing STT")
            self.stats['conflicts_prevented'] += 1
        
        with self.lock:
            self.is_listening = True
            self.operation_start_time = time.time()
            self.stats['listen_calls'] += 1
            
            try:
                result = stt_listener.listen(
                    check_stop_words=check_stop_words,
                    stop_words=stop_words
                )
                return result
            
            except Exception as e:
                logger.error(f"❌ STT error: {e}")
                return None
            
            finally:
                self.is_listening = False
                self.operation_start_time = None
    
    def force_release(self):
        """Emergency release of all locks"""
        logger.warning("🚨 Force releasing audio coordinator locks")
        self.is_speaking = False
        self.is_listening = False
        self.operation_start_time = None
    
    def get_status(self) -> dict:
        """Get current status"""
        return {
            'is_speaking': self.is_speaking,
            'is_listening': self.is_listening,
            'operation_duration': time.time() - self.operation_start_time if self.operation_start_time else 0,
            'stats': self.stats.copy()
        }
    
    def cleanup(self):
        """Cleanup coordinator"""
        logger.info("🧹 Cleaning up audio coordinator...")
        
        # Force release locks
        self.force_release()
        
        # Cleanup TTS
        # try:
        #     from audio.tts_selenium import TextToSpeechEngine
        #     TextToSpeechEngine.cleanup()
        #     logger.info("✅ TTS cleaned up")
        # except Exception as e:
        #     logger.error(f"❌ TTS cleanup error: {e}")
        
        # # Wait before STT cleanup (TTS cleans first)
        # time.sleep(1)
        
        logger.info("✅ Audio coordinator cleanup complete")


# Global instance (optional - can also be created in gui.py)
_coordinator = None

def get_coordinator() -> AudioCoordinator:
    """Get or create global coordinator"""
    global _coordinator
    if _coordinator is None:
        _coordinator = AudioCoordinator()
    return _coordinator