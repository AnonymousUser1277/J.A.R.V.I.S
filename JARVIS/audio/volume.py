"""
System volume controller with auto-restore
"""

import atexit
import signal
import sys
import logging
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

logger = logging.getLogger(__name__)

class VolumeController:
    """Control system volume with auto-restore"""
    
    def __init__(self):
        self.original_volume = None
        self.is_lowered = False
        self.volume = None
        self._init_volume_control()
        
        # Register emergency restore
        atexit.register(self._emergency_restore)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _init_volume_control(self):
        """Initialize Windows volume control"""
        try:
            device = AudioUtilities.GetSpeakers()
            self.volume = cast(device.EndpointVolume, POINTER(IAudioEndpointVolume))
            
            # Test
            test_vol = self.volume.GetMasterVolumeLevelScalar()
            logger.info(f"Volume controller initialized (current: {int(test_vol*100)}%)")
        except Exception as e:
            logger.error(f"Volume controller failed: {e}")
            self.volume = None
    
    def _emergency_restore(self):
        """Restore volume on abnormal exit"""
        if self.is_lowered and self.original_volume:
            logger.warning("Emergency volume restore!")
            self.restore_volume()
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals"""
        self._emergency_restore()
        sys.exit(0)
    
    def get_current_volume(self):
        """Get current system volume (0.0 to 1.0)"""
        if not self.volume:
            return None
        
        try:
            return self.volume.GetMasterVolumeLevelScalar()
        except Exception as e:
            logger.error(f"Get volume error: {e}")
            return None
    
    def set_volume(self, level):
        """Set system volume (0.0 to 1.0)"""
        if not self.volume:
            logger.warning("Volume controller not initialized")
            return False
        
        try:
            level = max(0.0, min(1.0, level))
            self.volume.SetMasterVolumeLevelScalar(level, None)
            return True
        except Exception as e:
            logger.error(f"Set volume error: {e}")
            return False
    
    def lower_volume(self, target_percent=5):
        """Lower volume to target_percent"""
        if self.is_lowered:
            return False
        
        current = self.get_current_volume()
        if current is None:
            return False
        
        self.original_volume = current
        current_percent = current * 100
        
        if current_percent > target_percent:
            new_volume = target_percent / 100.0
            if self.set_volume(new_volume):
                self.is_lowered = True
                logger.info(f"Volume lowered: {current_percent:.0f}% → {target_percent}%")
                return True
        
        return False
    
    def restore_volume(self):
        """Restore original volume level"""
        if not self.is_lowered:
            return False
        
        if self.original_volume is None:
            return False
        
        if self.set_volume(self.original_volume):
            logger.info(f"Volume restored to {int(self.original_volume*100)}%")
            self.is_lowered = False
            self.original_volume = None
            return True
        
        return False
    
    def get_volume_percentage(self):
        """Get volume as integer percentage (0-100)"""
        vol = self.get_current_volume()
        return int(vol * 100) if vol is not None else None