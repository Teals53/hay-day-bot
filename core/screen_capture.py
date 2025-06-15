"""
Optimized screen capture for HayDay Bot
Fast screen capture with intelligent caching for better performance
"""

import time
import numpy as np
import mss
import cv2
from typing import Optional


class ScreenCapture:
    """Fast screen capture with optimized caching"""
    
    def __init__(self):
        self._last_capture_time = 0
        self._cached_screen: Optional[np.ndarray] = None
        self._cache_duration = 0.05  # 50ms cache for better performance
        
    def capture_screen(self, use_cache: bool = True) -> np.ndarray:
        """Fast screen capture with caching - thread-safe"""
        current_time = time.time()
        
        # Return cached screen if valid
        if (use_cache and self._cached_screen is not None and 
            (current_time - self._last_capture_time) < self._cache_duration):
            return self._cached_screen
        
        # Create new MSS instance for each capture to avoid threading issues
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            
            # Convert to OpenCV format (faster method)
            img = np.frombuffer(screenshot.rgb, dtype=np.uint8)
            img = img.reshape(screenshot.height, screenshot.width, 3)
            screen = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        # Update cache
        if use_cache:
            self._cached_screen = screen
            self._last_capture_time = current_time
        
        return screen
    
    def invalidate_cache(self) -> None:
        """Clear the screen cache"""
        self._cached_screen = None
        self._last_capture_time = 0
        
    def cleanup(self):
        """Cleanup resources safely"""
        # No persistent MSS instance to cleanup
        self._cached_screen = None
        self._last_capture_time = 0 