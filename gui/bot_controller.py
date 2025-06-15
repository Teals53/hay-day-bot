"""
Bot controller for HayDay Bot

This module handles the main bot loop, coordinates all bot operations,
and manages the overall bot workflow and state.
"""

import time
import threading
import numpy as np
from typing import Optional, Callable

from core import DetectionState, BotState, ScreenCapture, TemplateManager
from bot import BotOperations, MarketOperations
from config import BotConfig


class BotController:
    """Controls the main bot operations and workflow"""
    
    def __init__(self, config: BotConfig, screen_capture: ScreenCapture,
                 template_manager: TemplateManager, detection_state: DetectionState,
                 bot_state: BotState, detection_lock: threading.Lock,
                 stop_event: threading.Event, log_callback: Callable[[str], None],
                 update_status_callback: Callable[[str, str], None]):
        self.config = config
        self.screen_capture = screen_capture
        self.template_manager = template_manager
        self.detection_state = detection_state
        self.bot_state = bot_state
        self.detection_lock = detection_lock
        self.stop_event = stop_event
        self.log = log_callback
        self.update_status = update_status_callback
        
        # Initialize bot operations
        self.bot_operations = BotOperations(
            config, screen_capture, template_manager, detection_state,
            bot_state, detection_lock, stop_event, log_callback
        )
        
        # Initialize market operations
        self.market_operations = MarketOperations(
            config, screen_capture, template_manager, bot_state,
            log_callback, self.bot_operations.safe_click
        )
        
        # Bot thread
        self.bot_thread: Optional[threading.Thread] = None
    
    def start_bot(self) -> bool:
        """Start the bot with improved thread management"""
        if self.detection_state.center is None:
            self.log("⚠️ No field detected! Make sure HayDay is visible and the field is clear.")
            return False
            
        self.bot_state.running = True
        self.stop_event.clear()  # Clear stop signal
        
        self.update_status("Bot Running", "green")
        self.log("🤖 Bot started! Beginning infinite farming cycle...")
        
        # Start bot thread with proper management
        if self.bot_thread is None or not self.bot_thread.is_alive():
            self.bot_thread = threading.Thread(target=self.bot_loop, daemon=True)
            self.bot_thread.start()
            self.log("🤖 Bot thread started")
        
        return True
    
    def stop_bot(self):
        """Stop the bot with proper thread management"""
        self.log("🛑 Stopping bot...")
        
        # Signal all threads to stop
        self.stop_event.set()
        self.bot_state.running = False
        self.bot_state.path_execution_active = False  # Unlock any locked paths
        
        # Only try to join thread if we're not calling from within the bot thread itself
        if self.bot_thread and self.bot_thread.is_alive():
            current_thread = threading.current_thread()
            if current_thread != self.bot_thread:
                try:
                    self.bot_thread.join(timeout=self.config.THREAD_SHUTDOWN_TIMEOUT)
                    if self.bot_thread.is_alive():
                        self.log("⚠️ Bot thread did not stop gracefully")
                    else:
                        self.log("✅ Bot thread stopped")
                except Exception as e:
                    self.log(f"❌ Error stopping bot thread: {e}")
            else:
                # We're being called from within the bot thread, just signal to stop
                self.log("🔄 Stop signal sent from bot thread")
        
        self.update_status("Bot Stopped", "red")
        self.log("⏹️ Bot stopped - All threads terminated")
    
    def bot_loop(self):
        """NEW TEMPLATE-BASED MAIN BOT LOOP - follows exact specifications"""
        cycle_count = 0
        
        try:
            while self.bot_state.running and not self.stop_event.is_set():
                
                cycle_count += 1
                self.log(f"\n🔄 === TEMPLATE-BASED CYCLE {cycle_count} ===")
                
                # STEP 0: Capture screen and handle loading screens
                screen = self._get_screen_with_loading_check()
                if self.bot_operations.interruptible_sleep(1):  # Brief pause after loading check
                    break
                
                # STEP 0.5: Check for and handle unknown popups
                if self._check_and_handle_unknown_popups(screen):
                    self.log("✅ Unknown popup handled, refreshing screen")
                    screen = self._get_screen_with_loading_check()
                    if self.bot_operations.interruptible_sleep(1):
                        break
                
                # STEP 1: Check for silo full popup
                silo_popup_detected = self.market_operations.check_silo_full_template(screen)
                
                # Check if silo is persistently full
                with self.detection_lock:
                    persistent_silo_full = self.bot_state.silo_is_full
                    wheat_sold = self.bot_state.wheat_sold_this_session
                
                if silo_popup_detected:
                    self.log("🏗️ Silo popup detected! Closing popup and checking persistent state...")
                    if self.market_operations.close_silo_with_template(screen):
                        self.log("✅ Silo popup closed")
                        # Reset storage detection state but keep persistent silo state
                        with self.detection_lock:
                            self.detection_state.storage_full = False
                            self.detection_state.storage_keyword = None
                    else:
                        self.log("❌ Failed to close silo popup")
                        if self.bot_operations.interruptible_sleep(5):
                            break
                        continue
                
                # Check persistent silo full state
                if persistent_silo_full and not wheat_sold:
                    self.log("🏗️ SILO IS PERSISTENTLY FULL - must go to market first before planting!")
                    self.log("📊 Wheat not yet sold this session - preventing planting until market visit")
                    
                    # Check for loading screen before market workflow
                    screen = self.screen_capture.capture_screen(use_cache=False)
                    if self._check_and_dismiss_loading_screen_with_click(screen):
                        self.log("🔄 Loading screen dismissed before market workflow")
                        screen = self.screen_capture.capture_screen(use_cache=False)
                    
                    # Go to market workflow to sell wheat
                    if self._handle_market_workflow():
                        self.log("✅ Market workflow completed - checking if we can clear silo state")
                        # Only clear silo state if we actually posted wheat to market
                        with self.detection_lock:
                            if self.bot_state.wheat_sold_this_session:
                                self.bot_state.silo_is_full = False
                                self.bot_state.wheat_sold_this_session = False
                                self.log("🔄 Silo state cleared - wheat was posted to market")
                            else:
                                self.log("⚠️ No wheat posted - keeping silo full state")
                    else:
                        self.log("❌ Market workflow failed - keeping silo full state")
                    
                    # FORCE return to main page after market workflow to prevent getting stuck
                    self.log("🏠 Forcing return to main page after market workflow...")
                    self._smart_return_to_main()
                    continue
                elif persistent_silo_full and wheat_sold:
                    self.log("✅ Silo was full but wheat was posted - clearing silo state")
                    with self.detection_lock:
                        self.bot_state.silo_is_full = False
                        self.bot_state.wheat_sold_this_session = False
                
                # STEP 2: Ensure we're on main page before field operations  
                if not self._ensure_on_main_page():
                    self.log("❌ Cannot ensure main page access, skipping cycle")
                    if self.bot_operations.interruptible_sleep(10):
                        break
                    continue
                
                # STEP 3: Check if fields need planting ONLY when on main page
                if self.bot_operations.check_fields_need_planting_cv(screen):
                    self.log("🌱 Fields need planting, using comprehensive planting to ensure complete coverage...")
                    
                    # Use comprehensive planting method that retries until all fields are planted
                    if self._comprehensive_field_planting():
                        self.log("✅ All fields planted successfully with comprehensive method")
                        # Wait for wheat to grow WITH PRODUCTIVE MARKET MANAGEMENT
                        self.log(f"⏰ Wheat planted! Managing market during {self.config.WHEAT_HARVEST_TIME}s growth period...")
                        
                        self._smart_wait_with_market_management(self.config.WHEAT_HARVEST_TIME)
                    else:
                        self.log("❌ Comprehensive field planting failed after multiple attempts")
                        if self.bot_operations.interruptible_sleep(10):
                            break
                        continue
                
                # STEP 4: Check if wheat is ready to harvest (ensure on main page)
                if not self._ensure_on_main_page():
                    self.log("❌ Cannot access main page for harvest, skipping...")
                    if self.bot_operations.interruptible_sleep(5):
                        break
                    continue
                
                # Only check wheat/fields when definitely on main page
                with self.detection_lock:
                    cx, cy = self.detection_state.center if self.detection_state.center else (None, None)
                    contour = self.detection_state.contour
                    wheat_ready = self.detection_state.is_wheat_ready
                    current_coverage = self.detection_state.wheat_coverage
                
                if cx and cy and contour is not None and wheat_ready and current_coverage > 30:
                    self.log(f"🚜 Wheat is ready! Harvesting... (coverage: {current_coverage:.1f}%)")
                    if self.bot_operations.harvest_wheat(cx, cy, contour):
                        self.log("✅ Wheat harvested successfully")
                    else:
                        self.log("❌ Failed to harvest wheat")
                        if self.bot_operations.interruptible_sleep(10):
                            break
                        continue
                
                # STEP 5: Check for collect button (sold items ready) - TEMPLATE DETECTION
                screen = self._get_screen_with_loading_check()
                
                collect_x, collect_y, confidence = self.template_manager.find_template(screen, 'collect', threshold=self.config.COLLECT_BUTTON_THRESHOLD)
                if collect_x and collect_y:
                    self.log(f"💰 COLLECT BUTTON detected! Items sold, going to market... (confidence: {confidence:.2f})")
                    if self._handle_market_workflow():
                        self.log("✅ Market workflow completed successfully")
                    else:
                        self.log("❌ Market workflow failed")
                        if self.bot_operations.interruptible_sleep(10):
                            break
                        continue
                
                # STEP 6: If no urgent actions needed, brief pause
                self.log("😴 Cycle completed, waiting before next cycle...")
                self.update_status("Waiting for next cycle...", "green")
                if self.bot_operations.interruptible_sleep(self.config.CYCLE_PAUSE):
                    break
                
        except Exception as e:
            self.log(f"💥 Critical bot error: {e}")
            self.stop_bot()
        
        self.log("🤖 Bot thread stopped")
    
    def _get_screen_with_loading_check(self) -> np.ndarray:
        """Capture screen and handle loading screens automatically with click escape"""
        screen = self.screen_capture.capture_screen(use_cache=False)
        if self._check_and_dismiss_loading_screen_with_click(screen):
            self.log("🔄 Loading screen dismissed, refreshing capture...")
            time.sleep(0.5)  # Brief wait for loading to complete
            screen = self.screen_capture.capture_screen(use_cache=False)
        return screen
    
    def _ensure_on_main_page(self) -> bool:
        """Ensure we're on the main page before field operations"""
        max_attempts = 5
        
        for attempt in range(max_attempts):
            screen = self.screen_capture.capture_screen(use_cache=False)
            locations = self._analyze_current_location(screen)
            
            if 'main' in locations:
                self.log(f"✅ Confirmed on main page (confidence: {locations['main']:.3f})")
                return True
            
            self.log(f"⚠️ Not on main page (attempt {attempt+1}/{max_attempts}), attempting return...")
            if not self._smart_return_to_main():
                self.log(f"❌ Failed to return to main page on attempt {attempt+1}")
                if self.bot_operations.interruptible_sleep(2):
                    return False
                continue
            
            # Brief pause after successful return
            if self.bot_operations.interruptible_sleep(1):
                return False
        
        self.log("❌ Could not ensure main page access after multiple attempts")
        return False
    
    def _analyze_current_location(self, screen: np.ndarray) -> dict:
        """Analyze where we currently are and return location info with priority logic"""
        return self.market_operations.analyze_current_location(screen)
    
    def _smart_return_to_main(self) -> bool:
        """Smart return to main page with multiple strategies"""
        self.log("🔄 Attempting to return to main page...")
        
        max_attempts = 10
        for attempt in range(max_attempts):
            screen = self.screen_capture.capture_screen(use_cache=False)
            locations = self._analyze_current_location(screen)
            
            if 'main' in locations:
                self.log(f"✅ Successfully on main page (confidence: {locations['main']:.3f})")
                return True
            
            # Handle different locations
            if 'silo_popup' in locations:
                self.log("🏗️ Silo popup blocking return, closing...")
                if self.market_operations.close_silo_with_template(screen):
                    time.sleep(0.5)
                    continue
            
            if 'offer' in locations:
                self.log("📝 In offer page, closing...")
                close_x, close_y, close_conf = self.template_manager.find_template(screen, 'close', threshold=self.config.CLOSE_BUTTON_THRESHOLD)
                if close_x and close_y:
                    self.bot_operations.safe_click(close_x, close_y, "close offer page")
                    time.sleep(0.5)
                    continue
            
            if 'market' in locations:
                self.log("🏪 In market, closing...")
                if self.market_operations.close_market_template(screen):
                    time.sleep(0.5)
                    continue
            
            if 'paper_page' in locations:
                self.log("📰 In paper page, closing...")
                close_x, close_y, close_conf = self.template_manager.find_template(screen, 'close', threshold=self.config.CLOSE_BUTTON_THRESHOLD)
                if close_x and close_y:
                    self.bot_operations.safe_click(close_x, close_y, "close paper page")
                    time.sleep(0.5)
                    continue
            
            if 'dialog_open' in locations:
                self.log("🔲 Dialog open, closing...")
                close_x, close_y, close_conf = self.template_manager.find_template(screen, 'close', threshold=self.config.CLOSE_BUTTON_THRESHOLD)
                if close_x and close_y:
                    self.bot_operations.safe_click(close_x, close_y, "close dialog")
                    time.sleep(0.5)
                    continue
            
            # If no specific location detected, wait and try again
            self.log(f"❓ Unknown location (attempt {attempt+1}/{max_attempts}), waiting...")
            time.sleep(1)
        
        self.log("❌ Could not return to main page after multiple attempts")
        return False
    
    def _comprehensive_field_planting(self, max_attempts: int = 5) -> bool:
        """Comprehensive field planting that ensures all fields are properly planted"""
        self.log("🌱 Starting comprehensive field planting process...")
        
        for attempt in range(max_attempts):
            self.log(f"🔄 Planting attempt {attempt + 1}/{max_attempts}")
            
            # Ensure we're on main page before each attempt
            screen = self.screen_capture.capture_screen(use_cache=False)
            locations = self._analyze_current_location(screen)
            
            if 'main' not in locations:
                self.log("⚠️ Not on main page, returning to main before planting...")
                if not self._smart_return_to_main():
                    self.log("❌ Cannot return to main page for planting")
                    continue
                # Refresh screen after returning
                screen = self.screen_capture.capture_screen(use_cache=False)
            
            # Check if fields still need planting
            if not self.bot_operations.check_fields_need_planting_cv(screen):
                self.log("✅ All fields are sufficiently planted!")
                return True
            
            # Get current field detection data
            with self.detection_lock:
                cx, cy = self.detection_state.center if self.detection_state.center else (None, None)
                contour = self.detection_state.contour
                current_coverage = self.detection_state.wheat_coverage
            
            if cx and cy and contour is not None:
                self.log(f"🎯 Planting field at ({cx}, {cy}) with {current_coverage:.1f}% coverage")
                
                # Attempt to plant this field
                if self.bot_operations.plant_wheat(cx, cy, contour):
                    self.log(f"✅ Planting attempt {attempt + 1} completed successfully")
                    
                    # Wait a moment for the system to update
                    time.sleep(2)
                    
                    # Check if coverage improved significantly
                    screen = self.screen_capture.capture_screen(use_cache=False)
                    if not self.bot_operations.check_fields_need_planting_cv(screen):
                        self.log("✅ Field planting successful - all fields now planted!")
                        return True
                    else:
                        with self.detection_lock:
                            new_coverage = self.detection_state.wheat_coverage
                        improvement = new_coverage - current_coverage
                        if improvement > 10:  # At least 10% improvement
                            self.log(f"📈 Good progress: coverage improved by {improvement:.1f}%")
                        else:
                            self.log(f"📉 Limited progress: coverage improved by {improvement:.1f}%")
                else:
                    self.log(f"❌ Planting attempt {attempt + 1} failed")
                    time.sleep(1)  # Brief pause before retry
            else:
                self.log("❌ No field detected for planting")
                time.sleep(1)
        
        # Final check after all attempts
        screen = self.screen_capture.capture_screen(use_cache=False)
        if self.bot_operations.check_fields_need_planting_cv(screen):
            with self.detection_lock:
                final_coverage = self.detection_state.wheat_coverage
            self.log(f"⚠️ Field planting incomplete after {max_attempts} attempts (final coverage: {final_coverage:.1f}%)")
            return False
        else:
            self.log("✅ All fields successfully planted!")
            return True
    
    def _handle_market_workflow(self) -> bool:
        """Complete market workflow using template-based approach with timeout"""
        self.log("🏪 Starting SIMPLE market workflow for silo full...")
        
        try:
            # Simple workflow: go to market, collect items, post wheat, check paper, and leave
            screen = self.screen_capture.capture_screen(use_cache=False)
            
            # Step 1: Go to market
            if not self.market_operations.go_to_market_template(screen):
                self.log("❌ Failed to enter market")
                return False
            
            # Step 2: Collect sold items (simple)
            screen = self.screen_capture.capture_screen(use_cache=False)
            self.market_operations.collect_sold_items_template(screen)
            
            # Step 3: Fill market with wheat (simple)
            screen = self.screen_capture.capture_screen(use_cache=False)
            self.market_operations.fill_market_with_wheat_template(screen)
            
            # Step 4: Check paper (simple - don't get stuck)
            screen = self.screen_capture.capture_screen(use_cache=False)
            self.log("📰 Checking for advertisement paper (simple)...")
            try:
                self.market_operations.check_and_create_advertisement(screen)
            except Exception as paper_error:
                self.log(f"⚠️ Paper check failed, continuing: {paper_error}")
            
            # Step 5: Close market and return
            screen = self.screen_capture.capture_screen(use_cache=False)
            self.market_operations.close_market_template(screen)
            
            self.log("✅ SIMPLE market workflow completed")
            return True
            
        except Exception as e:
            self.log(f"❌ Market workflow error: {e}")
            return False
    
    def _smart_wait_with_market_management(self, total_wait_seconds: int):
        """Intelligently wait while managing market during wheat growth"""
        if not self.config.ENABLE_GROWTH_MARKET_MANAGEMENT:
            # If disabled, use simple wait
            self.log("📈 Market management disabled, using simple wait...")
            start_time = time.time()
            while time.time() - start_time < total_wait_seconds:
                if not self.bot_state.running or self.stop_event.is_set():
                    break
                elapsed = int(time.time() - start_time)
                self.update_status(f"Growing wheat... {elapsed}s/{total_wait_seconds}s", "blue")
                if self.bot_operations.interruptible_sleep(10):
                    break
            return
        
        self.log("📈 Starting intelligent wait with market management...")
        
        start_time = time.time()
        last_market_check = 0
        market_check_interval = self.config.MARKET_CHECK_INTERVAL
        
        while time.time() - start_time < total_wait_seconds:
            if not self.bot_state.running or self.stop_event.is_set():
                break
            
            elapsed = int(time.time() - start_time)
            remaining = total_wait_seconds - elapsed
            
            # Update status
            self.update_status(f"Growing wheat... {elapsed}s/{total_wait_seconds}s (Managing market)", "blue")
            
            # Check if it's time for market management
            if elapsed - last_market_check >= market_check_interval:
                self.log(f"🏪 Market check #{elapsed//market_check_interval} - {remaining}s remaining for wheat growth")
                
                try:
                    # Capture screen for market checks
                    screen = self.screen_capture.capture_screen(use_cache=False)
                    
                    # Check if we have a collect button (items sold)
                    collect_x, collect_y, confidence = self.template_manager.find_template(screen, 'collect', threshold=self.config.COLLECT_BUTTON_THRESHOLD)
                    if collect_x and collect_y:
                        self.log(f"💰 COLLECT button found during growth! Collecting sold items... (confidence: {confidence:.2f})")
                        self.market_operations.handle_market_workflow_template()
                        self.log("✅ Market management completed, resuming wheat growth wait")
                    else:
                        # No urgent items to collect, check if market needs filling
                        # Check if market needs more offers
                        
                        # Go to market to check for available slots
                        if self.market_operations.go_to_market_template(screen):
                            time.sleep(0.6)  # Wait for market UI to load
                            screen = self.screen_capture.capture_screen(use_cache=False)
                            
                            in_market, market_confidence = self.market_operations.is_in_market(screen)
                            if not in_market:
                                self.log(f"⚠️ Market didn't load properly (confidence: {market_confidence:.3f}), skipping")
                                continue
                            
                            self.log(f"✅ In market (confidence: {market_confidence:.3f}), managing offers...")
                            
                            # Collect sold items first
                            collected_something = self.market_operations.collect_sold_items_template(screen)
                            if collected_something:
                                screen = self.screen_capture.capture_screen(use_cache=False)
                            
                            # Check for new offer slots
                            offer_x, offer_y, conf = self.template_manager.find_template(screen, 'new_offer', threshold=self.config.NEW_OFFER_THRESHOLD)
                            if offer_x and offer_y:
                                self.log(f"📝 Found empty slots, filling... (confidence: {conf:.2f})")
                                self.market_operations.fill_market_with_wheat_template(screen)
                                self.log("✅ Market slots filled during growth period")
                            else:
                                self.log("✅ Market is full")
                            
                            # Check for advertisement paper
                            screen = self.screen_capture.capture_screen(use_cache=False)
                            if not self.market_operations.check_and_create_advertisement(screen):
                                self.log("⚠️ Advertisement creation not needed")
                            
                            # Close market
                            screen = self.screen_capture.capture_screen(use_cache=False)
                            self.market_operations.close_market_template(screen)
                        else:
                            self.log("⚠️ Could not access market during growth period")
                    
                except Exception as e:
                    self.log(f"⚠️ Error during market management: {e}")
                
                last_market_check = elapsed
            
            # Sleep for a short period before next check
            if self.bot_operations.interruptible_sleep(5):  # Check every 5 seconds for responsive control
                break
        
        self.log(f"✅ Growth period completed! Wheat should be ready for harvest after {total_wait_seconds}s")
    
    def _check_and_handle_unknown_popups(self, screen: np.ndarray) -> bool:
        """Check for and handle unknown popups using close button detection"""
        # Look for close button that might indicate an unknown popup
        close_x, close_y, close_conf = self.template_manager.find_template(screen, 'close', threshold=self.config.CLOSE_BUTTON_THRESHOLD)
        
        # Only handle if we're not in a known location and there's a close button
        locations = self._analyze_current_location(screen)
        
        # If we detect a close button but we're not in any known location, it might be an unknown popup
        if close_x and close_y and not locations:
            self.log(f"🔲 Unknown popup detected, attempting to close (confidence: {close_conf:.2f})")
            self.bot_operations.safe_click(close_x, close_y, "close unknown popup")
            time.sleep(0.8)
            return True
        
        return False
    
    def _check_and_dismiss_loading_screen(self, screen: np.ndarray) -> bool:
        """Check for and dismiss loading screens"""
        loading_x, loading_y, confidence = self.template_manager.find_template(screen, 'loading', threshold=0.7)
        if loading_x and loading_y:
            self.log(f"🔄 Loading screen detected (confidence: {confidence:.2f}), waiting...")
            time.sleep(2)
            return True
        return False
    
    def _check_and_dismiss_loading_screen_with_click(self, screen: np.ndarray) -> bool:
        """Check for loading screens and try to dismiss them with click template"""
        # First check for loading screen
        loading_x, loading_y, loading_conf = self.template_manager.find_template(screen, 'loading', threshold=self.config.LOADING_SCREEN_THRESHOLD)
        
        if loading_x and loading_y:
            self.log(f"🔄 Loading screen detected (confidence: {loading_conf:.2f})")
            
            # Look for click template to escape loading screen
            click_x, click_y, click_conf = self.template_manager.find_template(screen, 'click', threshold=self.config.CLICK_ESCAPE_THRESHOLD)
            
            if click_x and click_y:
                self.log(f"🖱️ Found click escape point (confidence: {click_conf:.2f}), clicking to dismiss loading...")
                self.bot_operations.safe_click(click_x, click_y, "escape loading screen")
                time.sleep(1.5)  # Wait for loading to dismiss
                return True
            else:
                self.log(f"⏳ Loading screen detected but no click escape found (click confidence: {click_conf:.2f}), waiting...")
                time.sleep(2)  # Wait for loading to complete naturally
                return True
        
        return False 