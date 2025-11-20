"""
Native Windows TTS using SAPI (Speech API)
10x faster than Selenium, zero memory leaks
"""
import logging
import threading
import queue
import time
from typing import Optional
import win32com.client

logger = logging.getLogger(__name__)

class NativeTTSEngine:
    """Windows SAPI 5.4 TTS - Fast, reliable, native"""
    
    def __init__(self, voice_name: Optional[str] = None, rate: int = 1, volume: int = 100):
        """
        Args:
            voice_name: Voice name (e.g., "Microsoft David Desktop")
            rate: Speech rate (-10 to 10, 0 is normal)
            volume: Volume (0 to 100)
        """
        self.lock = threading.RLock()
        self.speech_queue = queue.Queue(maxsize=50)
        self.is_speaking = False
        self.shutdown_flag = False
        
        # Initialize SAPI
        try:
            self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
            self.speaker.Rate = rate
            self.speaker.Volume = volume
            
            # Set voice if specified
            if voice_name:
                voices = self.speaker.GetVoices()
                for i in range(voices.Count):
                    voice = voices.Item(i)
                    if voice_name.lower() in voice.GetDescription().lower():
                        self.speaker.Voice = voice
                        logger.info(f"✅ Using voice: {voice.GetDescription()}")
                        break
            
            logger.info(f"✅ Native TTS initialized with {self.speaker.Voice.GetDescription()}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize SAPI: {e}")
            raise
        
        # Start speech processor thread
        self.processor_thread = threading.Thread(
            target=self._speech_processor,
            daemon=True,
            name="TTS-Processor"
        )
        self.processor_thread.start()
    
    def _speech_processor(self):
        """Background thread to process speech queue"""
        while not self.shutdown_flag:
            try:
                text = self.speech_queue.get(timeout=1)
                if text and text.strip():
                    self._speak_internal(text)
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Speech processor error: {e}")
    
    def _speak_internal(self, text: str):
        """Internal method to actually speak text"""
        with self.lock:
            self.is_speaking = True
            try:
                # Synchronous speech (blocks until done)
                self.speaker.Speak(text, 0)  # 0 = synchronous
            except Exception as e:
                logger.error(f"Speech error: {e}")
            finally:
                self.is_speaking = False
    
    def speak(self, text: str, priority: bool = False) -> bool:
        """
        Queue text for speaking
        
        Args:
            text: Text to speak
            priority: If True, clear queue and speak immediately
            
        Returns:
            True if queued successfully
        """
        if not text or not text.strip() or self.shutdown_flag:
            return False
        
        try:
            if priority:
                # Clear queue
                while not self.speech_queue.empty():
                    try:
                        self.speech_queue.get_nowait()
                    except queue.Empty:
                        break
                
                # Stop current speech
                self.stop_speaking()
            
            self.speech_queue.put(text, block=False)
            return True
            
        except queue.Full:
            logger.warning("TTS queue full, dropping message")
            return False
        except Exception as e:
            logger.error(f"Failed to queue speech: {e}")
            return False
    
    def stop_speaking(self):
        """Stop current speech immediately"""
        try:
            # Purge queue (2 = SVSFPurgeBeforeSpeak)
            self.speaker.Speak("", 2)
            self.is_speaking = False
        except Exception as e:
            logger.error(f"Stop speaking error: {e}")
    
    def wait_until_done(self, timeout: float = 30) -> bool:
        """Wait until all queued speech is complete"""
        start = time.time()
        while (not self.speech_queue.empty() or self.is_speaking) and (time.time() - start < timeout):
            time.sleep(0.1)
        return self.speech_queue.empty() and not self.is_speaking
    
    def set_rate(self, rate: int):
        """Set speech rate (-10 to 10)"""
        self.speaker.Rate = max(-10, min(10, rate))
    
    def set_volume(self, volume: int):
        """Set volume (0 to 100)"""
        self.speaker.Volume = max(0, min(100, volume))
    
    def get_available_voices(self):
        """Get list of available voices"""
        voices = []
        try:
            voice_list = self.speaker.GetVoices()
            for i in range(voice_list.Count):
                voice = voice_list.Item(i)
                voices.append({
                    'name': voice.GetDescription(),
                    'id': voice.Id
                })
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
        return voices
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("🧹 Cleaning up Native TTS...")
        self.shutdown_flag = True
        self.stop_speaking()
        
        # Wait for processor to finish
        if self.processor_thread.is_alive():
            self.processor_thread.join(timeout=2)
        
        try:
            self.speaker = None
        except:
            pass
        
        logger.info("✅ Native TTS cleanup complete")


# Compatibility wrapper for existing code
def speak(text: str, wait: bool = False) -> bool:
    """
    Global speak function (maintains compatibility)
    Must call set_tts_engine() first from main.py
    """
    global _global_tts_engine
    
    if _global_tts_engine is None:
        logger.warning("TTS engine not initialized")
        return False
    
    result = _global_tts_engine.speak(text)
    
    if wait:
        _global_tts_engine.wait_until_done()
    
    return result


def set_tts_engine(engine):
    """Set global TTS engine instance"""
    global _global_tts_engine
    _global_tts_engine = engine
    logger.info("✅ Global TTS engine set (Native)")


def stop_speaking():
    """Stop current speech"""
    global _global_tts_engine
    if _global_tts_engine:
        _global_tts_engine.stop_speaking()


def wait_until_done(timeout: float = 30):
    """Wait for speech to complete"""
    global _global_tts_engine
    if _global_tts_engine:
        return _global_tts_engine.wait_until_done(timeout)
    return False


_global_tts_engine = None
# Example usage
if __name__ == "__main__":
    tts = NativeTTSEngine(voice_name="Microsoft Ryan Desktop", rate=0, volume=100)
    set_tts_engine(tts)
    speak("Hello! Native TTS module loaded.", wait=True)