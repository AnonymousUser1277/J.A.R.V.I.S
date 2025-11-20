"""
STT Fallback System with Auto-Recovery
Uses speech_recognition as fallback when Selenium STT fails
Automatically attempts to recover primary STT in background
✅ FIXED: Gracefully handles missing microphone
"""

import time
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FallbackSTT:
    """Fallback STT using Google Speech Recognition"""
    
    def __init__(self):
        self.recognizer = None
        self.microphone = None
        self.is_listening = False
        self.stop_listening = False
        self.available = False
        
        # ✅ FIXED: Try to initialize but don't fail if no mic
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Test if microphone actually works
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            self.available = True
            logger.info("✅ Fallback STT initialized")
            
        except Exception as e:
            # ✅ FIXED: Not an error - just not available
            logger.info(f"ℹ️ Fallback STT not available (no microphone): {e}")
            self.available = False
            self.recognizer = None
            self.microphone = None
    
    def listen(self, timeout: int = 10) -> Optional[str]:
        """Listen and return transcribed text"""
        if not self.available or not self.microphone:
            logger.warning("Fallback STT not available - no microphone")
            return None
        
        try:
            import speech_recognition as sr
            
            with self.microphone as source:
                logger.debug("🎤 Listening (fallback)...")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=15)
            
            # Try Google first
            try:
                text = self.recognizer.recognize_google(audio)
                return text
            except sr.UnknownValueError:
                logger.warning("Could not understand audio")
                return None
            except sr.RequestError as e:
                logger.error(f"Google API error: {e}")
                
                # Try Sphinx offline as last resort
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    logger.info("Used offline recognition (Sphinx)")
                    return text
                except:
                    return None
        
        except Exception as e:
            logger.error(f"Fallback STT error: {e}")
            return None
    
    def listen_for_wake_word(self, wake_word: str = "jarvis", timeout: int = 5) -> bool:
        """Listen for wake word"""
        if not self.available or not self.microphone:
            return False
        
        try:
            import speech_recognition as sr
            
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=3)
            
            text = self.recognizer.recognize_google(audio)
            if wake_word.lower() in text.lower():
                return True
        except:
            pass
        
        return False


class STTManager:
    """
    Manages primary and fallback STT systems
    Automatically recovers from failures
    ✅ FIXED: Works even when fallback is unavailable
    """
    
    def __init__(self, primary_stt, gui_handler=None):
        self.primary = primary_stt
        self.gui_handler = gui_handler
        
        # ✅ FIXED: Initialize fallback but don't fail if unavailable
        try:
            self.fallback = FallbackSTT()
            self.fallback_available = self.fallback.available
        except Exception as e:
            logger.info(f"ℹ️ Fallback STT not available: {e}")
            self.fallback = None
            self.fallback_available = False
        
        # State tracking
        self.using_fallback = False
        self.primary_failed_at = None
        self.recovery_attempts = 0
        self.max_recovery_attempts = 5
        
        # Recovery thread
        self.recovery_thread = None
        self.stop_recovery = False
        
        # Statistics
        self.stats = {
            'primary_uses': 0,
            'fallback_uses': 0,
            'recovery_successes': 0,
            'recovery_failures': 0
        }
    
    def listen(self, timeout: int = 10) -> Optional[str]:
        """
        Listen using primary or fallback
        Automatically switches and recovers
        """
        # Try primary first
        if not self.using_fallback:
            try:
                result = self.primary.listen()
                self.stats['primary_uses'] += 1
                return result
            except Exception as e:
                logger.error(f"❌ Primary STT failed: {e}")
                self._switch_to_fallback()
        
        # ✅ FIXED: Only use fallback if available
        if self.using_fallback and self.fallback_available:
            try:
                result = self.fallback.listen(timeout=timeout)
                self.stats['fallback_uses'] += 1
                return result
            except Exception as e:
                logger.error(f"❌ Fallback STT also failed: {e}")
                return None
        elif self.using_fallback and not self.fallback_available:
            logger.warning("⚠️ Fallback not available - waiting for primary recovery")
            return None
        
        return None
    
    def listen_for_wake_word(self, wake_word: str = "jarvis") -> bool:
        """Listen for wake word with fallback"""
        if not self.using_fallback:
            try:
                return self.primary.listen_for_wake_word(wake_word)
            except Exception as e:
                logger.error(f"Primary wake word detection failed: {e}")
                self._switch_to_fallback()
        
        # ✅ FIXED: Only use fallback if available
        if self.using_fallback and self.fallback_available:
            try:
                return self.fallback.listen_for_wake_word(wake_word)
            except Exception as e:
                logger.error(f"Fallback wake word detection failed: {e}")
                return False
        elif self.using_fallback and not self.fallback_available:
            # Wait for primary recovery
            time.sleep(1)
            return False
        
        return False
    
    def _switch_to_fallback(self):
        """Switch to fallback STT and start recovery"""
        if self.using_fallback:
            return  # Already using fallback
        
        # ✅ FIXED: Better messaging based on fallback availability
        if self.fallback_available:
            logger.warning("⚠️ Switching to fallback STT")
            message = "⚠️ Primary STT failed - using backup system"
            color = "yellow"
        else:
            logger.warning("⚠️ Primary STT failed - no fallback available")
            message = "⚠️ Primary STT failed - attempting recovery..."
            color = "yellow"
        
        self.using_fallback = True
        self.primary_failed_at = time.time()
        
        # Show alert to user
        if self.gui_handler:
            self.gui_handler.show_terminal_output(message, color=color)
        
        # Start recovery in background
        if not self.recovery_thread or not self.recovery_thread.is_alive():
            self.stop_recovery = False
            self.recovery_thread = threading.Thread(
                target=self._recovery_loop,
                daemon=True,
                name="STT-Recovery"
            )
            self.recovery_thread.start()
    
    def _recovery_loop(self):
        """Background thread that attempts to recover primary STT"""
        logger.info("🔧 Starting STT recovery attempts...")
        
        while not self.stop_recovery and self.recovery_attempts < self.max_recovery_attempts:
            try:
                # Wait before attempting recovery
                wait_time = min(30 * (self.recovery_attempts + 1), 300)  # Max 5 minutes
                logger.info(f"⏳ Waiting {wait_time}s before recovery attempt {self.recovery_attempts + 1}")
                time.sleep(wait_time)
                
                if self.stop_recovery:
                    break
                
                # Attempt recovery
                logger.info(f"🔄 Recovery attempt {self.recovery_attempts + 1}/{self.max_recovery_attempts}")
                
                if self._attempt_primary_recovery():
                    logger.info("✅ Primary STT recovered!")
                    self.stats['recovery_successes'] += 1
                    
                    if self.gui_handler:
                        self.gui_handler.show_terminal_output(
                            "✅ Primary STT recovered!",
                            color="green"
                        )
                    
                    self.using_fallback = False
                    self.recovery_attempts = 0
                    break
                else:
                    self.recovery_attempts += 1
                    self.stats['recovery_failures'] += 1
                    logger.warning(f"❌ Recovery attempt {self.recovery_attempts} failed")
            
            except Exception as e:
                logger.error(f"Recovery error: {e}")
                self.recovery_attempts += 1
        
        if self.recovery_attempts >= self.max_recovery_attempts:
            # ✅ FIXED: Better message based on fallback availability
            if self.fallback_available:
                logger.error("❌ Max recovery attempts reached - staying on fallback")
                if self.gui_handler:
                    self.gui_handler.show_terminal_output(
                        "⚠️ Primary STT recovery failed - using fallback permanently",
                        color="red"
                    )
            else:
                logger.error("❌ Max recovery attempts reached - STT unavailable")
                if self.gui_handler:
                    self.gui_handler.show_terminal_output(
                        "❌ STT recovery failed - voice input unavailable",
                        color="red"
                    )
    
    def _attempt_primary_recovery(self) -> bool:
        """Attempt to recover primary STT"""
        try:
            # Try to restart the primary STT
            logger.info("🔧 Restarting primary STT...")
            
            # ✅ FIXED: Check if primary has restart method
            if not hasattr(self.primary, '_safe_restart_driver'):
                logger.error("Primary STT doesn't support restart")
                return False
            
            # Safe restart
            self.primary._safe_restart_driver()
            
            # Wait for initialization
            time.sleep(2)
            
            # Test if it works
            logger.info("🧪 Testing recovered STT...")
            
            # Quick test (don't wait for actual speech)
            try:
                _ = self.primary.driver.title
                logger.info("✅ Primary STT driver responsive")
                return True
            except:
                logger.warning("❌ Primary STT driver not responsive")
                return False
        
        except Exception as e:
            logger.error(f"Recovery attempt failed: {e}")
            return False
    
    def force_recovery(self):
        """Manually trigger recovery attempt"""
        logger.info("🔄 Manual recovery triggered")
        self.recovery_attempts = 0
        
        if self._attempt_primary_recovery():
            self.using_fallback = False
            return True
        return False
    
    def get_status(self) -> dict:
        """Get current status"""
        return {
            'using_fallback': self.using_fallback,
            'fallback_available': self.fallback_available,
            'primary_failed_at': self.primary_failed_at,
            'recovery_attempts': self.recovery_attempts,
            'stats': self.stats,
            'uptime_minutes': round((time.time() - (self.primary_failed_at or time.time())) / 60, 1)
        }
    
    def stop(self):
        """Stop recovery and cleanup"""
        self.stop_recovery = True
        if self.recovery_thread and self.recovery_thread.is_alive():
            self.recovery_thread.join(timeout=2)


# Example usage
if __name__ == "__main__":
    # Test fallback STT directly
    fallback = FallbackSTT()
    
    if not fallback.available:
        print("❌ Fallback STT not available (no microphone)")
        exit(1)
    
    print("Testing fallback STT...")
    print("Say something:")
    
    text = fallback.listen(timeout=10)
    if text:
        print(f"You said: {text}")
    else:
        print("Nothing heard")
    
    print("\nTesting wake word detection...")
    print("Say 'jarvis':")
    
    detected = fallback.listen_for_wake_word("jarvis", timeout=10)
    if detected:
        print("Wake word detected!")
    else:
        print("Wake word not detected")