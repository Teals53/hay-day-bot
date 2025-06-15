"""
Detection manager for HayDay Bot

This module handles the detection loop, field detection, and visual updates.
"""

import time
import threading
import numpy as np
from typing import Optional, Callable

from core import DetectionState, BotState, ScreenCapture, TemplateManager
from core import SoilDetector
from config import BotConfig


class DetectionManager:
    """Manages field detection and visual updates"""
    
    def __init__(self, config: BotConfig, screen_capture: ScreenCapture,
                 soil_detector: SoilDetector, template_manager: TemplateManager,
                 detection_state: DetectionState, bot_state: BotState,
                 detection_lock: threading.Lock, stop_event: threading.Event,
                 log_callback: Callable[[str], None],
                 update_detection_status_callback: Callable[[Optional[int], Optional[int]], None],
                 update_storage_status_callback: Callable[[], None]):
        self.config = config
        self.screen_capture = screen_capture
        self.soil_detector = soil_detector
        self.template_manager = template_manager
        self.detection_state = detection_state
        self.bot_state = bot_state
        self.detection_lock = detection_lock
        self.stop_event = stop_event
        self.log = log_callback
        self.update_detection_status = update_detection_status_callback
        self.update_storage_status = update_storage_status_callback
    
    def detection_loop(self, visual_display=None):
        """Continuous detection loop - always runs visual updates"""
        while not self.stop_event.is_set():
            try:
                # Always run detection and visual updates when detection is active
                if self.bot_state.detection_active:
                    # Skip detection during path execution but continue visual updates
                    if not self.bot_state.path_execution_active:
                        self._capture_and_detect(visual_display)
                    else:
                        # During path execution, still update visual with current screen
                        if visual_display:
                            screen = self.screen_capture.capture_screen(use_cache=True)
                            with self.detection_lock:
                                cx, cy = self.detection_state.center if self.detection_state.center else (None, None)
                                contour = self.detection_state.contour
                            visual_display.update_display(screen, cx, cy, contour)
                else:
                    # When detection is disabled, show disabled message
                    if visual_display:
                        visual_display.show_disabled_message()
                    
                # Use interruptible sleep
                if self._interruptible_sleep(self.config.DETECTION_UPDATE_INTERVAL):
                    break
                    
            except Exception as e:
                self.log(f"Detection loop error: {e}")
                if self._interruptible_sleep(1):
                    break
                    
        self.log("🔍 Detection thread stopped")
    
    def _interruptible_sleep(self, total_time: float) -> bool:
        """Sleep for given time but check for stop signal periodically"""
        elapsed = 0
        chunk_size = min(self.config.STOP_CHECK_INTERVAL, self.config.MAX_SLEEP_CHUNK)
        
        while elapsed < total_time and not self.stop_event.is_set():
            sleep_time = min(chunk_size, total_time - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time
            
        return self.stop_event.is_set()
    
    def _capture_and_detect(self, visual_display=None):
        """Capture screen and run detection with optimized caching"""
        try:
            # Use cached screen capture
            screen = self.screen_capture.capture_screen(use_cache=True)
            
            # Run detection
            cx, cy, contour = self.soil_detector.detect_field(screen)
            
            # Check wheat coverage if field is detected
            wheat_coverage = 0
            is_ready = False
            if contour is not None:
                wheat_coverage = self.soil_detector.count_wheat_coverage(screen, contour)
                is_ready = self.soil_detector.is_ready_for_harvest(screen, contour)
            
            # Check for storage full popup - ONLY check for silo.png template
            silo_x, silo_y, confidence = self.template_manager.find_template(screen, 'silo', threshold=0.6)
            storage_full = silo_x is not None and silo_y is not None
            storage_keyword = "SILO_TEMPLATE_DETECTED" if storage_full else None
            
            # Thread-safe update of shared data
            with self.detection_lock:
                self.detection_state.screen = screen
                self.detection_state.center = (cx, cy) if cx is not None else None
                self.detection_state.contour = contour
                self.detection_state.wheat_coverage = wheat_coverage
                self.detection_state.is_wheat_ready = is_ready
                self.detection_state.storage_full = storage_full
                self.detection_state.storage_keyword = storage_keyword
            
            # Always update visual display when detection is active
            if visual_display:
                visual_display.update_display(screen, cx, cy, contour)
                
            # Update status
            self.update_detection_status(cx, cy)
            self.update_storage_status()
                
        except Exception as e:
            self.log(f"Detection error: {e}") 