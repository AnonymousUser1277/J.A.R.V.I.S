"""
Audio processing package
"""

from .tts import  speak
from .stt import SpeechToTextListener
from .volume import VolumeController
from .stt_fallback import STTManager
__all__ = [
  
    'speak',
    'SpeechToTextListener',
    'VolumeController',
    'STTManager'
]