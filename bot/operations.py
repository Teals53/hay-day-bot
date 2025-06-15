"""
Optimized bot operations for HayDay Bot
Fast and efficient farming operations with minimal delays
"""

import time
import threading
import pyautogui as pag
import numpy as np
from typing import Optional, Tuple, Callable

from core import DetectionState, BotState, ScreenCapture, TemplateManager, PathGenerator
from config import BotConfig


class BotOperations:
    """Fast bot operations with optimized performance"""
    
    def __init__(self, config: BotConfig, screen_capture: ScreenCapture, 
                 template_manager: TemplateManager, detection_state: DetectionState,
                 bot_state: BotState, detection_lock: threading.Lock,
                 stop_event: threading.Event, log_callback: Callable[[str], None]):
        self.config = config
        self.screen_capture = screen_capture
        self.template_manager = template_manager
        self.detection_state = detection_state
        self.bot_state = bot_state
        self.detection_lock = detection_lock
        self.stop_event = stop_event
        self.log = log_callback
    
    def interruptible_sleep(self, total_time: float) -> bool:
        """Fast interruptible sleep with stop signal checking"""
        elapsed = 0
        chunk_size = min(self.config.STOP_CHECK_INTERVAL, 1.0)  # Max 1 second chunks
        
        while elapsed < total_time and not self.stop_event.is_set():
            sleep_time = min(chunk_size, total_time - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time
            
        return self.stop_event.is_set()
    
    def safe_click(self, x: int, y: int, description: str = "") -> bool:
        """Fast click with minimal delay"""
        if not self.bot_state.running or self.stop_event.is_set():
            return False
            
        self.log(f"🖱️ {description} at ({x}, {y})")
        pag.click(x, y, duration=self.config.DEFAULT_MOVEMENT_SPEED)
        return not self.interruptible_sleep(self.config.DEFAULT_CLICK_DELAY)
        
    def safe_move(self, x: int, y: int, duration: Optional[float] = None) -> bool:
        """Fast mouse movement"""
        if not self.bot_state.running or self.stop_event.is_set():
            return False
            
        if duration is None:
            duration = self.config.DEFAULT_MOVEMENT_SPEED
            
        pag.moveTo(x, y, duration=duration)
        return True
    
    def plant_wheat(self, cx: int, cy: int, contour: Optional[np.ndarray]) -> bool:
        """Optimized wheat planting with proper recentering and path updates"""
        if not self.bot_state.running:
            return False
            
        self.log("🌱 Starting planting...")
        
        # Click field center
        if not self.safe_click(cx, cy, "field center"):
            return False
            
        # Wait for game to center screen and update our position after clicking empty field
        self.log("⏱️ Waiting for game to center screen after clicking empty field...")
        if self.interruptible_sleep(self.config.SCREEN_CENTER_DELAY):
            return False
        
        # Update screen position after centering
        screen = self.screen_capture.capture_screen(use_cache=False)
        if screen is not None:
            # Update our field center position after screen movement
            with self.detection_lock:
                updated_center = self.detection_state.center
                
            # Use updated position for wheat selection if available, otherwise use original
            if updated_center:
                updated_cx, updated_cy = updated_center
                self.log(f"🎯 Updated field center position after screen centering: ({updated_cx}, {updated_cy})")
                wheat_x = updated_cx + self.config.WHEAT_X_OFFSET
                wheat_y = updated_cy + self.config.WHEAT_Y_OFFSET
                # Update cx, cy for the rest of the function
                cx, cy = updated_cx, updated_cy
            else:
                self.log("⚠️ Using original position as backup")
                wheat_x = cx + self.config.WHEAT_X_OFFSET
                wheat_y = cy + self.config.WHEAT_Y_OFFSET
        else:
            # Fallback to original position
            wheat_x = cx + self.config.WHEAT_X_OFFSET
            wheat_y = cy + self.config.WHEAT_Y_OFFSET
        
        # Click wheat option with updated position
        if not self.safe_click(wheat_x, wheat_y, "wheat selection"):
            return False
            
        self.log("🖱️ Starting drag planting...")
        time.sleep(0.8)  # Wait for wheat selection to register
        
        # First, click on field center to ensure we start on a plantable area
        self.log("🎯 Starting drag from field center (planted area)")
        pag.mouseDown()
        
        # Start from center and make a small initial plant to ensure we're on valid soil
        # Use configurable offsets to ensure we hit plantable area
        initial_plant_x = cx + self.config.INITIAL_PLANT_X_OFFSET
        initial_plant_y = cy + self.config.INITIAL_PLANT_Y_OFFSET
        if not self.safe_move(initial_plant_x, initial_plant_y, duration=0.5):
            pag.mouseUp()
            return False
        
        time.sleep(0.2)  # Wait for initial plant to register
        
        try:
            if contour is not None:
                # Update contour coordinates to match the new centered position
                # Calculate the offset between old and new center positions
                screen = self.screen_capture.capture_screen(use_cache=False)
                if screen is not None:
                    # Get the current field detection with updated coordinates
                    with self.detection_lock:
                        updated_contour = self.detection_state.contour if self.detection_state.contour is not None else contour
                    
                    if updated_contour is not None:
                        self.log("🎯 Using updated contour after screen centering")
                        contour = updated_contour
                    else:
                        self.log("⚠️ Using original contour as fallback")
                
                # Create planting path with UPDATED coordinates after screen centering
                planting_path = PathGenerator.create_linear_path(cx, cy, contour, "plant")
                
                # Lock the path - no updates during execution!
                self.bot_state.path_execution_active = True
                self.log(f"🌱 Following locked planting path with {len(planting_path)} points (no dynamic updates)...")
                
                for i, (x, y) in enumerate(planting_path):
                    if not self.bot_state.running or self.stop_event.is_set():
                        break
                    
                    # Progress logging with configurable interval
                    if self.config.ENABLE_PROGRESS_LOGGING:
                        if i % self.config.PROGRESS_LOG_INTERVAL == 0:
                            progress_pct = int((i+1) / len(planting_path) * 100)
                            self.log(f"🌾 Planting progress {progress_pct}%")
                    
                    # Move at maximum speed using config setting
                    move_duration = min(0.02, self.config.DEFAULT_MOVEMENT_SPEED)  # Ultra fast movement
                    if not self.safe_move(int(x), int(y), duration=move_duration):
                        break
                        
                    # No sleep between points for maximum speed
            
            # Return to center before releasing
            self.log("🎯 Returning to center before release")
            self.safe_move(cx, cy, duration=self.config.DEFAULT_MOVEMENT_SPEED)
            pag.mouseUp()
            
            # Unlock path execution
            self.bot_state.path_execution_active = False
            self.log("✅ Planting completed successfully! Path unlocked.")
            return True
            
        except Exception as e:
            pag.mouseUp()
            # Always unlock path on error
            self.bot_state.path_execution_active = False
            self.log(f"❌ Planting error: {e} - Path unlocked.")
            return False
    
    def harvest_wheat(self, cx: int, cy: int, contour: Optional[np.ndarray]) -> bool:
        """Optimized wheat harvesting with proper recentering and path updates"""
        if not self.bot_state.running:
            return False
            
        self.log("🚜 Starting harvest...")
        
        # Click field center
        if not self.safe_click(cx, cy, "field center"):
            return False
            
        # Move to harvest tool and wait for it to appear
        harvest_x = cx + self.config.HARVEST_X_OFFSET
        harvest_y = cy + self.config.HARVEST_Y_OFFSET
        
        self.log(f"🔧 Moving to harvest tool position...")
        if not self.safe_move(harvest_x, harvest_y, duration=self.config.DEFAULT_MOVEMENT_SPEED):
            return False
            
        time.sleep(0.8)  # Wait for harvest tool
        self.log("🖱️ Starting harvest drag...")
        
        # Start harvesting from field center (where crops should be)
        self.log("🎯 Starting harvest from field center")
        pag.mouseDown()
        
        # Start from center and make a small initial harvest to ensure we're on valid crops
        # Use configurable offsets for consistency
        initial_harvest_x = cx + self.config.INITIAL_HARVEST_X_OFFSET
        initial_harvest_y = cy + self.config.INITIAL_HARVEST_Y_OFFSET
        if not self.safe_move(initial_harvest_x, initial_harvest_y, duration=0.5):
            pag.mouseUp()
            return False
        
        time.sleep(0.2)  # Wait for initial harvest to register
        
        try:
            if contour is not None:
                # Update contour coordinates to match the current field position
                screen = self.screen_capture.capture_screen(use_cache=False)
                if screen is not None:
                    # Get the current field detection with updated coordinates
                    with self.detection_lock:
                        updated_contour = self.detection_state.contour if self.detection_state.contour is not None else contour
                        updated_cx, updated_cy = self.detection_state.center if self.detection_state.center else (cx, cy)
                    
                    if updated_contour is not None:
                        self.log("🎯 Using updated contour for harvesting")
                        contour = updated_contour
                        cx, cy = updated_cx, updated_cy  # Use updated center too
                    else:
                        self.log("⚠️ Using original contour for harvesting as fallback")
                
                # Create harvest path with UPDATED coordinates
                harvest_path = PathGenerator.create_linear_path(cx, cy, contour, "harvest")
                
                # Lock the path - no updates during execution!
                self.bot_state.path_execution_active = True
                self.log(f"🚜 Following locked harvest path with {len(harvest_path)} points (no dynamic updates)...")
                
                for i, (x, y) in enumerate(harvest_path):
                    if not self.bot_state.running or self.stop_event.is_set():
                        break
                    
                    # Progress logging with configurable interval
                    if self.config.ENABLE_PROGRESS_LOGGING:
                        if i % self.config.PROGRESS_LOG_INTERVAL == 0:
                            progress_pct = int((i+1) / len(harvest_path) * 100)
                            self.log(f"🚜 Harvest progress {progress_pct}%")
                    
                    # Move at maximum speed for harvesting
                    move_duration = min(0.02, self.config.DEFAULT_MOVEMENT_SPEED)  # Ultra fast movement
                    if not self.safe_move(int(x), int(y), duration=move_duration):
                        break
                        
                    # No sleep between points for maximum speed
            
            # Return to center before releasing
            self.log("🎯 Returning to center before release")
            self.safe_move(cx, cy, duration=self.config.DEFAULT_MOVEMENT_SPEED)
            pag.mouseUp()
            
            # Unlock path execution
            self.bot_state.path_execution_active = False
            self.log("✅ Harvest completed successfully! Path unlocked.")
            return True
            
        except Exception as e:
            pag.mouseUp()
            # Always unlock path on error
            self.bot_state.path_execution_active = False
            self.log(f"❌ Harvest error: {e} - Path unlocked.")
            return False
    
    def check_fields_need_planting_cv(self, screen: np.ndarray) -> bool:
        """Check if fields need planting using computer vision"""
        # Get current detection data
        with self.detection_lock:
            cx, cy = self.detection_state.center if self.detection_state.center else (None, None)
            current_coverage = self.detection_state.wheat_coverage
        
        if cx is None or cy is None:
            self.log("⚠️ No field detected")
            return False
        
        self.log(f"🌾 Current wheat coverage: {current_coverage:.1f}%")
        
        # If coverage is low, we need to plant
        if current_coverage < 80:  # Less than 80% coverage means we should plant
            self.log(f"🌱 Fields need planting (coverage: {current_coverage:.1f}%)")
            return True
        else:
            self.log(f"✅ Fields are well planted (coverage: {current_coverage:.1f}%)")
            return False 