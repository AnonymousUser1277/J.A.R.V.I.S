"""
Lightweight offline intent classifier for basic commands
Works without internet, ~50ms response time
"""
import re
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class OfflineIntentClassifier:
    """
    Rule-based classifier for common intents
    No AI models required - uses pattern matching
    """
    
    def __init__(self):
        # Intent patterns (regex + keywords)
        self.intents = {
            'time_query': {
                'patterns': [
                    r'\b(what|tell me|show)\s+(time|current time)\b',
                    r'\bwhat[\'s]?\s+the\s+time\b'
                ],
                'handler': self._handle_time
            },
            'date_query': {
                'patterns': [
                    r'\b(what|tell me)\s+(date|today[\'s]? date)\b',
                    r'\bwhat\s+day\s+is\s+it\b'
                ],
                'handler': self._handle_date
            },
            'volume_control': {
                'patterns': [
                    r'\b(increase|decrease|raise|lower|set)\s+volume\b',
                    r'\bvolume\s+(up|down|to\s+\d+)\b',
                    r'\b(mute|unmute)\b'
                ],
                'handler': self._handle_volume
            },
            'window_control': {
                'patterns': [
                    r'\b(close|minimize|maximize)\s+(window|this|current)\b',
                    r'\b(switch to|open)\s+\w+\b'
                ],
                'handler': self._handle_window
            },
            'system_control': {
                'patterns': [
                    r'\b(shutdown|restart|sleep|lock)\s+(computer|pc|system)\b',
                    r'\b(log out|sign out)\b'
                ],
                'handler': self._handle_system
            },
            'calculator': {
                'patterns': [
                    r'\bcalculate\s+.+',
                    r'\bwhat\s+is\s+\d+.*[\+\-\*\/].*\d+',
                    r'\b\d+\s*(plus|minus|times|divided by)\s*\d+\b'
                ],
                'handler': self._handle_calculator
            },
            'file_operations': {
                'patterns': [
                    r'\b(create|delete|copy|move|rename)\s+(file|folder)\b',
                    r'\b(open|close)\s+file\b'
                ],
                'handler': self._handle_files
            },
            'greeting': {
                'patterns': [
                    r'\b(hello|hi|hey)\s+jarvis\b',
                    r'\bgood\s+(morning|afternoon|evening)\b'
                ],
                'handler': self._handle_greeting
            },
            'thanks': {
                'patterns': [
                    r'\b(thank you|thanks|appreciate it)\b'
                ],
                'handler': self._handle_thanks
            }
        }
        
        # Compile patterns
        for intent_data in self.intents.values():
            intent_data['compiled'] = [
                re.compile(p, re.IGNORECASE) 
                for p in intent_data['patterns']
            ]
    
    def classify(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Classify intent and execute if offline-capable
        
        Returns:
            Dict with 'intent', 'confidence', 'result' if handled offline
            None if needs online AI
        """
        text_lower = text.lower().strip()
        
        # Check each intent
        for intent_name, intent_data in self.intents.items():
            for pattern in intent_data['compiled']:
                if pattern.search(text_lower):
                    logger.info(f"🎯 Offline intent detected: {intent_name}")
                    
                    # Execute handler
                    try:
                        result = intent_data['handler'](text, text_lower)
                        return {
                            'intent': intent_name,
                            'confidence': 0.95,
                            'result': result,
                            'offline': True
                        }
                    except Exception as e:
                        logger.error(f"Handler error for {intent_name}: {e}")
                        return None
        
        # No offline intent matched - needs online AI
        return None
    
    # ==================== HANDLERS ====================
    
    def _handle_time(self, text, text_lower):
        """Handle time queries"""
        from datetime import datetime
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        return f"It's {time_str}"
    
    def _handle_date(self, text, text_lower):
        """Handle date queries"""
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        return f"Today is {date_str}"
    
    def _handle_volume(self, text, text_lower):
        """Handle volume control"""
        import subprocess
        
        if 'up' in text_lower or 'increase' in text_lower or 'raise' in text_lower:
            # Increase volume
            subprocess.run(['nircmd.exe', 'changesysvolume', '5000'], 
                         shell=True, check=False, capture_output=True)
            return "Volume increased"
        
        elif 'down' in text_lower or 'decrease' in text_lower or 'lower' in text_lower:
            # Decrease volume
            subprocess.run(['nircmd.exe', 'changesysvolume', '-5000'], 
                         shell=True, check=False, capture_output=True)
            return "Volume decreased"
        
        elif 'mute' in text_lower:
            subprocess.run(['nircmd.exe', 'mutesysvolume', '1'], 
                         shell=True, check=False, capture_output=True)
            return "Volume muted"
        
        elif 'unmute' in text_lower:
            subprocess.run(['nircmd.exe', 'mutesysvolume', '0'], 
                         shell=True, check=False, capture_output=True)
            return "Volume unmuted"
        
        # Extract number if setting specific volume
        match = re.search(r'to\s+(\d+)', text_lower)
        if match:
            volume = int(match.group(1))
            volume = max(0, min(100, volume))
            # nircmd uses 0-65535 scale
            nircmd_vol = int((volume / 100) * 65535)
            subprocess.run(['nircmd.exe', 'setsysvolume', str(nircmd_vol)], 
                         shell=True, check=False, capture_output=True)
            return f"Volume set to {volume}%"
        
        return "Volume adjusted"
    
    def _handle_window(self, text, text_lower):
        """Handle window operations"""
        import pyautogui
        
        if 'close' in text_lower:
            pyautogui.hotkey('alt', 'f4')
            return "Closing window"
        
        elif 'minimize' in text_lower:
            pyautogui.hotkey('win', 'down')
            return "Minimizing window"
        
        elif 'maximize' in text_lower:
            pyautogui.hotkey('win', 'up')
            return "Maximizing window"
        
        return "Window command executed"
    
    def _handle_system(self, text, text_lower):
        """Handle system commands"""
        import subprocess
        
        if 'shutdown' in text_lower:
            subprocess.Popen(['shutdown', '/s', '/t', '60'])
            return "Shutting down in 60 seconds. Say 'cancel shutdown' to abort."
        
        elif 'restart' in text_lower:
            subprocess.Popen(['shutdown', '/r', '/t', '60'])
            return "Restarting in 60 seconds"
        
        elif 'sleep' in text_lower:
            subprocess.Popen(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'])
            return "Entering sleep mode"
        
        elif 'lock' in text_lower:
            subprocess.Popen(['rundll32.exe', 'user32.dll,LockWorkStation'])
            return "Locking computer"
        
        return "System command executed"
    
    def _handle_calculator(self, text, text_lower):
        """Handle basic calculations"""
        # Replace words with operators
        text_lower = text_lower.replace('plus', '+')
        text_lower = text_lower.replace('minus', '-')
        text_lower = text_lower.replace('times', '*')
        text_lower = text_lower.replace('multiplied by', '*')
        text_lower = text_lower.replace('divided by', '/')
        
        # Extract math expression
        match = re.search(r'([\d\+\-\*/\.\(\)\s]+)', text_lower)
        if match:
            try:
                expression = match.group(1).strip()
                result = eval(expression)
                return f"{expression} equals {result}"
            except Exception as e:
                logger.error(f"Calculation error: {e}")
                return "Sorry, I couldn't calculate that"
        
        return "Please provide a valid calculation"
    
    def _handle_files(self, text, text_lower):
        """Handle basic file operations"""
        # This is intentionally basic - complex operations go to AI
        if 'open file' in text_lower:
            import subprocess
            subprocess.Popen(['explorer.exe'])
            return "Opening file explorer"
        
        return "File operation requires more context"
    
    def _handle_greeting(self, text, text_lower):
        """Handle greetings"""
        from datetime import datetime
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return "Good morning! How can I help you?"
        elif 12 <= hour < 17:
            return "Good afternoon! What can I do for you?"
        elif 17 <= hour < 21:
            return "Good evening! How may I assist you?"
        else:
            return "Hello! What do you need?"
    
    def _handle_thanks(self, text, text_lower):
        """Handle thanks"""
        responses = [
            "You're welcome!",
            "Happy to help!",
            "Anytime!",
            "My pleasure!",
            "Glad I could help!"
        ]
        import random
        return random.choice(responses)


# Global classifier instance
_classifier = None

def get_offline_classifier() -> OfflineIntentClassifier:
    """Get or create global classifier"""
    global _classifier
    if _classifier is None:
        _classifier = OfflineIntentClassifier()
    return _classifier