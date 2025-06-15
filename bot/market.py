"""
Market operations for HayDay Bot

This module handles all market-related operations including
selling wheat, collecting sold items, and managing advertisements.
"""

import time
import numpy as np
from typing import Optional, Tuple, Callable

from core import BotState, ScreenCapture, TemplateManager
from config import BotConfig


class MarketOperations:
    """Handles market operations like selling wheat and collecting items"""
    
    def __init__(self, config: BotConfig, screen_capture: ScreenCapture,
                 template_manager: TemplateManager, bot_state: BotState,
                 log_callback: Callable[[str], None], safe_click_callback: Callable[[int, int, str], bool]):
        self.config = config
        self.screen_capture = screen_capture
        self.template_manager = template_manager
        self.bot_state = bot_state
        self.log = log_callback
        self.safe_click = safe_click_callback
    
    def check_silo_full_template(self, screen: np.ndarray) -> bool:
        """Check if silo is full using silo.png template"""
        silo_x, silo_y, confidence = self.template_manager.find_template(screen, 'silo', threshold=self.config.SILO_POPUP_THRESHOLD)
        if silo_x and silo_y:
            self.log(f"🏗️ SILO FULL detected via template (confidence: {confidence:.2f})")
            self.bot_state.silo_is_full = True
            self.bot_state.wheat_sold_this_session = False
            return True
        return False
    
    def close_silo_with_template(self, screen: np.ndarray) -> bool:
        """Close silo popup using close.png template"""
        close_x, close_y, confidence = self.template_manager.find_template(screen, 'close', threshold=self.config.CLOSE_BUTTON_THRESHOLD)
        if close_x and close_y:
            self.log(f"🔲 Closing silo popup via template (confidence: {confidence:.2f}) - keeping silo full state")
            self.safe_click(close_x, close_y, "close button")
            time.sleep(1)
            self.log("ℹ️ Silo popup closed but silo_is_full state maintained until wheat is sold")
            return True
        else:
            self.log("⚠️ Close button template not found")
            return False
    
    def go_to_market_template(self, screen: np.ndarray) -> bool:
        """Go to market using market_button.png template"""
        # Check for loading screen before trying to find market button
        if self._check_and_dismiss_loading_screen_with_click(screen):
            self.log("🔄 Loading screen dismissed before market button search")
            screen = self.screen_capture.capture_screen(use_cache=False)
        
        market_x, market_y, confidence = self.template_manager.find_template(screen, 'market_button', threshold=self.config.MARKET_BUTTON_THRESHOLD)
        if market_x and market_y:
            self.log(f"🏪 Going to market via template (confidence: {confidence:.2f})")
            self.safe_click(market_x, market_y, "market button")
            
            # Wait for market to load and verify we actually entered
            for attempt in range(5):
                time.sleep(0.5)
                screen = self.screen_capture.capture_screen(use_cache=False)
                
                # Check for loading screen during market loading
                if self._check_and_dismiss_loading_screen_with_click(screen):
                    self.log("🔄 Loading screen dismissed during market loading")
                    screen = self.screen_capture.capture_screen(use_cache=False)
                
                in_market, market_conf = self.is_in_market(screen)
                
                if in_market:
                    self.log(f"✅ Successfully entered market (confidence: {market_conf:.3f})")
                    return True
                else:
                    self.log(f"⏳ Waiting for market to load... attempt {attempt+1}/5 (confidence: {market_conf:.3f})")
            
            self.log("❌ Market didn't load after clicking market button")
            return False
        else:
            self.log(f"❌ Market button template not found (confidence: {confidence:.3f}, threshold: {self.config.MARKET_BUTTON_THRESHOLD})")
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
                self.safe_click(click_x, click_y, "escape loading screen")
                time.sleep(1.5)  # Wait for loading to dismiss
                return True
            else:
                self.log(f"⏳ Loading screen detected but no click escape found (click confidence: {click_conf:.2f}), waiting...")
                time.sleep(2)  # Wait for loading to complete naturally
                return True
        
        return False
    
    def collect_sold_items_template(self, screen: np.ndarray) -> bool:
        """Collect ALL sold items using templates"""
        total_collected = 0
        max_attempts = 10
        
        self.log("💰 Collecting all sold items...")
        
        for attempt in range(max_attempts):
            collected_this_round = False
            
            # Get fresh screen
            screen = self.screen_capture.capture_screen(use_cache=False)
            
            # Check for collect button first
            collect_x, collect_y, confidence = self.template_manager.find_template(screen, 'collect', threshold=self.config.COLLECT_BUTTON_THRESHOLD)
            if collect_x and collect_y:
                self.log(f"💰 Collecting money (confidence: {confidence:.2f})")
                self.safe_click(collect_x, collect_y, "collect button")
                time.sleep(self.config.MARKET_BUTTON_WAIT)
                collected_this_round = True
                total_collected += 1
            
            # Check for sold items
            screen = self.screen_capture.capture_screen(use_cache=False)
            sold_x, sold_y, confidence = self.template_manager.find_template(screen, 'sold', threshold=self.config.SOLD_ITEMS_THRESHOLD)
            if sold_x and sold_y:
                self.log(f"💸 Collecting sold items (confidence: {confidence:.2f})")
                self.safe_click(sold_x, sold_y, "sold items")
                time.sleep(self.config.MARKET_BUTTON_WAIT)
                collected_this_round = True
                total_collected += 1
            
            # If nothing was collected this round, we're done
            if not collected_this_round:
                break
        
        if total_collected > 0:
            self.log(f"✅ Collected {total_collected} sold items/money collections")
        else:
            self.log("ℹ️ No sold items to collect")
        
        return total_collected > 0
    
    def create_wheat_advertisement_template(self, offer_x: int, offer_y: int) -> bool:
        """Create wheat advertisement using templates"""
        self.log(f"📝 Creating wheat advertisement at slot ({offer_x}, {offer_y})")
        
        # Step 1: Click new offer slot
        self.safe_click(offer_x, offer_y, "new offer slot")
        time.sleep(self.config.MARKET_UI_WAIT)
        
        # Step 2: Check if we have wheat to sell
        screen = self.screen_capture.capture_screen(use_cache=False)
        if not self.check_wheat_availability(screen):
            self.log("🚫 No wheat available to sell - closing offer page")
            close_x, close_y, close_conf = self.template_manager.find_template(screen, 'close', threshold=self.config.CLOSE_BUTTON_THRESHOLD)
            if close_x and close_y:
                self.log(f"🔲 Clicking close button to exit offer creation (confidence: {close_conf:.3f})")
                self.safe_click(close_x, close_y, "close offer creation")
                time.sleep(self.config.MARKET_UI_WAIT)
            else:
                self.log("⚠️ Close button not found - cannot exit offer creation")
                time.sleep(self.config.MARKET_UI_WAIT)
            return False
        
        # Step 3: Click wheat market slot
        wheat_x, wheat_y, confidence = self.template_manager.find_template(screen, 'wheat_market', threshold=self.config.WHEAT_MARKET_THRESHOLD)
        if not wheat_x or not wheat_y:
            self.log("❌ Wheat market slot template not found after availability check!")
            return False
        
        self.safe_click(wheat_x, wheat_y, "wheat market slot")
        time.sleep(self.config.MARKET_STEP_DELAY)
        
        # Step 4: Maximize quantity
        if not self.maximize_quantity_step():
            self.log("⚠️ Could not maximize quantity, continuing anyway...")
        
        # Step 5: Maximize price
        if not self.maximize_price_step():
            self.log("⚠️ Could not maximize price, continuing anyway...")
        
        # Step 6: Click newspaper (if available)
        screen = self.screen_capture.capture_screen(use_cache=False)
        newspaper_x, newspaper_y, confidence = self.template_manager.find_template(screen, 'newspaper', threshold=self.config.NEWSPAPER_THRESHOLD)
        if newspaper_x and newspaper_y:
            self.log(f"📰 Clicking newspaper (confidence: {confidence:.2f})")
            self.safe_click(newspaper_x, newspaper_y, "newspaper")
            time.sleep(self.config.MARKET_STEP_DELAY)
        else:
            self.log("ℹ️ Newspaper not available (ads not available), skipping...")
        
        # Step 7: Click insert button
        screen = self.screen_capture.capture_screen(use_cache=False)
        insert_x, insert_y, confidence = self.template_manager.find_template(screen, 'insert_button', threshold=self.config.INSERT_BUTTON_THRESHOLD)
        if insert_x and insert_y:
            self.log(f"📥 Clicking insert button (confidence: {confidence:.2f})")
            self.safe_click(insert_x, insert_y, "insert button")
            time.sleep(self.config.MARKET_UI_WAIT)
            
            # Mark that we've posted wheat for sale
            self.bot_state.wheat_sold_this_session = True
            self.log("📊 Wheat posted to market - marking wheat as sold from silo")
            
            return True
        else:
            self.log("❌ Insert button template not found")
            return False
    
    def check_wheat_availability(self, screen: np.ndarray) -> bool:
        """Check if we have wheat to sell"""
        wheat_x, wheat_y, confidence = self.template_manager.find_template(screen, 'wheat_market', threshold=self.config.WHEAT_MARKET_THRESHOLD)
        
        if wheat_x and wheat_y and confidence >= self.config.WHEAT_MARKET_THRESHOLD:
            self.log(f"✅ Wheat available to sell (confidence: {confidence:.3f} >= {self.config.WHEAT_MARKET_THRESHOLD})")
            return True
        else:
            self.log(f"❌ No wheat available to sell (confidence: {confidence:.3f} < {self.config.WHEAT_MARKET_THRESHOLD})")
            return False
    
    def fill_market_with_wheat_template(self, screen: np.ndarray) -> bool:
        """Fill all available market slots with wheat"""
        self.log("📝 Filling market with wheat advertisements...")
        
        slots_filled = 0
        max_slots = 10
        wheat_offers_created = 0
        
        for slot_attempt in range(max_slots):
            # Get fresh screen
            screen = self.screen_capture.capture_screen(use_cache=False)
            
            # Find new offer slots
            offer_x, offer_y, confidence = self.template_manager.find_template(screen, 'new_offer', threshold=self.config.NEW_OFFER_THRESHOLD)
            
            if not offer_x or not offer_y:
                self.log(f"✅ Market is FULL! No more offer slots available. Filled {slots_filled} slots.")
                self.log("🏪 All slots filled - market is complete, ready to close and return to farming")
                break
            
            # Fill the slot
            if self.create_wheat_advertisement_template(offer_x, offer_y):
                slots_filled += 1
                wheat_offers_created += 1
                self.log(f"✅ Slot {slots_filled} filled successfully (total wheat offers: {wheat_offers_created})")
                time.sleep(self.config.MARKET_STEP_DELAY)
            else:
                self.log(f"❌ Failed to fill slot {slot_attempt + 1} after creating {wheat_offers_created} wheat offers")
                self.log("🚫 Stopping market filling (likely out of wheat or other error)")
                break
        
        self.log(f"📝 Market filling completed. {slots_filled} slots filled.")
        return slots_filled > 0
    
    def maximize_quantity_step(self) -> bool:
        """Maximize quantity using plus_button"""
        self.log("➕ Step 1: Maximizing wheat quantity...")
        
        for i in range(20):
            time.sleep(self.config.MARKET_STEP_DELAY)
            screen = self.screen_capture.capture_screen(use_cache=False)
            
            # Check button states
            deactive_x, deactive_y, deactive_conf = self.template_manager.find_template(screen, 'plus_button_deactive', threshold=self.config.PLUS_BUTTON_DEACTIVE_THRESHOLD)
            active_x, active_y, active_conf = self.template_manager.find_template(screen, 'plus_button_active', threshold=self.config.PLUS_BUTTON_ACTIVE_THRESHOLD)
            
            # If deactive confidence is high and clearly higher than active, we're done
            if deactive_conf >= self.config.PLUS_BUTTON_DEACTIVE_THRESHOLD and deactive_conf > active_conf:
                self.log(f"✅ Plus button is DEACTIVE - quantity maximized! (confidence: {deactive_conf:.2f})")
                self.log("🔄 Moving to STEP 2: Price maximization...")
                return True
            
            # If active confidence is high and clearly higher than deactive, click it
            if active_conf >= self.config.PLUS_BUTTON_ACTIVE_THRESHOLD and active_conf > deactive_conf:
                self.log(f"➕ Clicking ACTIVE plus button (confidence: {active_conf:.2f}) - attempt {i+1}")
                self.safe_click(active_x, active_y, "plus button active")
                continue
            
            # If we're getting mixed signals, try to determine which is which based on confidence
            if deactive_conf > 0.6 and deactive_conf > active_conf:
                self.log(f"🔧 Deactive confidence higher ({deactive_conf:.3f} vs {active_conf:.3f}), assuming maximized")
                return True
            elif active_conf > 0.6 and active_conf > deactive_conf:
                self.log(f"🔧 Active confidence higher ({active_conf:.3f} vs {deactive_conf:.3f}), clicking button")
                self.safe_click(active_x, active_y, "plus button active (higher confidence)")
                continue
            
            # If no clear detection, wait and try again
            self.log(f"⚠️ Unclear button state (attempt {i+1}), waiting...")
            time.sleep(self.config.MARKET_STEP_DELAY)
        
        self.log("⚠️ Could not determine plus button state after 20 attempts")
        return False
    
    def maximize_price_step(self) -> bool:
        """Maximize price using arrow_right"""
        self.log("💰 Step 2: Maximizing price...")
        
        for i in range(20):
            time.sleep(self.config.MARKET_STEP_DELAY)
            screen = self.screen_capture.capture_screen(use_cache=False)
            
            # Check button states
            deactive_x, deactive_y, deactive_conf = self.template_manager.find_template(screen, 'arrow_right_deactive', threshold=self.config.ARROW_BUTTON_DEACTIVE_THRESHOLD)
            active_x, active_y, active_conf = self.template_manager.find_template(screen, 'arrow_right_active', threshold=self.config.ARROW_BUTTON_ACTIVE_THRESHOLD)
            
            # If deactive confidence is high and clearly higher than active, we're done
            if deactive_conf >= self.config.ARROW_BUTTON_DEACTIVE_THRESHOLD and deactive_conf > active_conf:
                self.log(f"✅ Arrow right is DEACTIVE - price maximized! (confidence: {deactive_conf:.2f})")
                self.log("🔄 Both maximize steps completed! Moving to newspaper/insert...")
                return True
            
            # If active confidence is high and clearly higher than deactive, click it
            if active_conf >= self.config.ARROW_BUTTON_ACTIVE_THRESHOLD and active_conf > deactive_conf:
                self.log(f"💰 Clicking ACTIVE arrow right (confidence: {active_conf:.2f}) - attempt {i+1}")
                self.safe_click(active_x, active_y, "arrow right active")
                continue
            
            # If we're getting mixed signals, try to determine which is which based on confidence
            if deactive_conf > 0.6 and deactive_conf > active_conf:
                self.log(f"🔧 Deactive confidence higher ({deactive_conf:.3f} vs {active_conf:.3f}), assuming maximized")
                return True
            elif active_conf > 0.6 and active_conf > deactive_conf:
                self.log(f"🔧 Active confidence higher ({active_conf:.3f} vs {deactive_conf:.3f}), clicking button")
                self.safe_click(active_x, active_y, "arrow right active (higher confidence)")
                continue
            
            # If no clear detection, wait and try again
            self.log(f"⚠️ Unclear button state (attempt {i+1}), waiting...")
            time.sleep(self.config.MARKET_STEP_DELAY)
        
        self.log("⚠️ Could not determine arrow right state after 20 attempts")
        return False
    
    def close_market_template(self, screen: np.ndarray) -> bool:
        """Close market using close button template only"""
        close_x, close_y, confidence = self.template_manager.find_template(screen, 'close', threshold=self.config.CLOSE_BUTTON_THRESHOLD)
        
        if close_x and close_y:
            self.log(f"🔲 Closing market via template (confidence: {confidence:.2f})")
            self.safe_click(close_x, close_y, "close market")
            time.sleep(self.config.MARKET_UI_WAIT)
            
            # Verify we actually left the market
            new_screen = self.screen_capture.capture_screen(use_cache=False)
            in_market, _ = self.is_in_market(new_screen)
            
            if not in_market:
                self.log("✅ Successfully closed market and left")
                return True
            else:
                self.log("⚠️ Still in market after close attempt")
                return False
        else:
            self.log("⚠️ Close button template not found")
            return False
    
    def is_in_market(self, screen: np.ndarray) -> Tuple[bool, float]:
        """Check if we're currently in the market"""
        x, y, confidence = self.template_manager.find_template(screen, 'market', threshold=self.config.MARKET_PAGE_THRESHOLD)
        return (x is not None and y is not None), confidence
    
    def handle_market_workflow_template(self) -> bool:
        """Complete market workflow: collect ALL sold items first, then create new offers"""
        self.log("🏪 Starting template-based market workflow...")
        
        screen = self.screen_capture.capture_screen(use_cache=False)
        locations = self.analyze_current_location(screen)
        
        # Check current location and navigate appropriately
        if 'offer' in locations:
            self.log(f"📝 Currently in OFFER page (confidence: {locations['offer']:.2f}), returning to shop first...")
            # Close offer page to return to shop
            close_x, close_y, close_conf = self.template_manager.find_template(screen, 'close', threshold=self.config.CLOSE_BUTTON_THRESHOLD)
            if close_x and close_y:
                self.safe_click(close_x, close_y, "close offer page")
                time.sleep(0.5)
                screen = self.screen_capture.capture_screen(use_cache=False)
        elif 'market' in locations:
            self.log(f"✅ Already in SHOP page (confidence: {locations['market']:.2f}), proceeding with market workflow")
        else:
            # Step 1: Go to market
            self.log("🔄 Not in market yet, going to market...")
            if not self.go_to_market_template(screen):
                self.log("❌ Failed to enter market")
                return False
        
        # Step 2: Collect ALL sold items - make sure shop is completely clean
        screen = self.screen_capture.capture_screen(use_cache=False)
        collected_something = self.collect_sold_items_template(screen)
        
        if collected_something:
            self.log("✅ All sold items collected, shop is now clean")
        else:
            self.log("ℹ️ No sold items found, shop is already clean")
        
        # Step 3: Now create new offers since shop is clean
        screen = self.screen_capture.capture_screen(use_cache=False)
        self.fill_market_with_wheat_template(screen)
        
        # Step 4: Check for advertisement paper (same as normal shop logic)
        screen = self.screen_capture.capture_screen(use_cache=False)
        self.log("📰 Checking for advertisement paper...")
        if not self.check_and_create_advertisement(screen):
            self.log("⚠️ Advertisement creation failed or not needed")
        
        # Step 5: Close market
        screen = self.screen_capture.capture_screen(use_cache=False)
        self.close_market_template(screen)
        
        self.log("✅ Template-based market workflow completed")
        return True
    
    def analyze_current_location(self, screen: np.ndarray) -> dict:
        """Analyze where we currently are and return location info with priority logic"""
        confidences = {}
        
        # Get all detection confidences first
        is_main, main_conf = self.is_on_main_page(screen)
        confidences['main'] = main_conf
        
        in_offer, offer_conf = self.is_in_offer(screen)
        confidences['offer'] = offer_conf
        
        in_market, market_conf = self.is_in_market(screen)
        confidences['market'] = market_conf
        
        in_paper_page, paper_page_conf = self.is_in_paper_page(screen)
        confidences['paper_page'] = paper_page_conf
        
        silo_x, silo_y, silo_conf = self.template_manager.find_template(screen, 'silo', threshold=self.config.SILO_POPUP_THRESHOLD)
        confidences['silo'] = silo_conf
        
        close_x, close_y, close_conf = self.template_manager.find_template(screen, 'close', threshold=self.config.CLOSE_BUTTON_THRESHOLD)
        confidences['close'] = close_conf
        
        # PRIORITY-BASED LOCATION DETECTION
        # Higher priority locations override lower ones, even if multiple detections pass threshold
        locations = {}
        
        # Priority 1: Silo popup (highest priority - always handle first)
        if silo_x and silo_y and silo_conf >= self.config.SILO_POPUP_THRESHOLD:
            locations['silo_popup'] = silo_conf
            self.log(f"🏗️ PRIORITY: Silo popup detected (confidence: {silo_conf:.3f})")
            return locations
        
        # Priority 2: Paper page (highest priority after silo)
        if paper_page_conf >= self.config.PAPER_PAGE_THRESHOLD:
            locations['paper_page'] = paper_page_conf
            self.log(f"📰 PRIORITY: Paper creation page detected (confidence: {paper_page_conf:.3f})")
            return locations
        
        # Priority 3: Offer page (when confidence is high)
        if offer_conf >= getattr(self.config, 'OFFER_PAGE_PRIORITY_THRESHOLD', 0.8):
            locations['offer'] = offer_conf
            self.log(f"📝 PRIORITY: Offer page detected (confidence: {offer_conf:.3f})")
            return locations
        
        # Priority 4: Market page (when confidence is high and offer is not detected)
        if market_conf >= getattr(self.config, 'MARKET_PAGE_PRIORITY_THRESHOLD', 0.7) and offer_conf < getattr(self.config, 'OFFER_PAGE_PRIORITY_THRESHOLD', 0.8):
            locations['market'] = market_conf
            self.log(f"🏪 PRIORITY: Market page detected (confidence: {market_conf:.3f})")
            return locations
        
        # Priority 5: Main page (only when other specific pages are not clearly detected)
        if main_conf >= self.config.MAIN_PAGE_THRESHOLD and offer_conf < getattr(self.config, 'OFFER_PAGE_PRIORITY_THRESHOLD', 0.8) and market_conf < getattr(self.config, 'MARKET_PAGE_PRIORITY_THRESHOLD', 0.7) and paper_page_conf < self.config.PAPER_PAGE_THRESHOLD:
            locations['main'] = main_conf
            self.log(f"🏠 PRIORITY: Main page detected (confidence: {main_conf:.3f})")
            return locations
        
        # Priority 6: Any dialog with close button
        if close_x and close_y and close_conf >= self.config.CLOSE_BUTTON_THRESHOLD:
            locations['dialog_open'] = close_conf
            self.log(f"🔲 PRIORITY: Dialog with close button detected (confidence: {close_conf:.3f})")
            return locations
        
        # If we get here, location is unclear
        self.log(f"❓ UNCERTAIN LOCATION: All confidences below thresholds or conflicting detections")
        self.log(f"   Main: {main_conf:.3f} (threshold: {self.config.MAIN_PAGE_THRESHOLD})")
        self.log(f"   Market: {market_conf:.3f} (threshold: {self.config.MARKET_PAGE_THRESHOLD})")
        self.log(f"   Offer: {offer_conf:.3f} (threshold: {self.config.OFFER_PAGE_THRESHOLD})")
        self.log(f"   Paper: {paper_page_conf:.3f} (threshold: {self.config.PAPER_PAGE_THRESHOLD})")
        return locations
    
    def is_on_main_page(self, screen: np.ndarray) -> Tuple[bool, float]:
        """Check if we're on the main farm page"""
        main_x, main_y, confidence = self.template_manager.find_template(screen, 'main', threshold=self.config.MAIN_PAGE_THRESHOLD)
        return (main_x is not None and main_y is not None), confidence
    
    def is_in_offer(self, screen: np.ndarray) -> Tuple[bool, float]:
        """Check if we're currently in the offer page"""
        offer_x, offer_y, confidence = self.template_manager.find_template(screen, 'in_offer', threshold=self.config.OFFER_PAGE_THRESHOLD)
        return (offer_x is not None and offer_y is not None), confidence
    
    def is_in_paper_page(self, screen: np.ndarray) -> Tuple[bool, float]:
        """Check if we're currently in the paper creation page"""
        paper_x, paper_y, confidence = self.template_manager.find_template(screen, 'paper_page', threshold=self.config.PAPER_PAGE_THRESHOLD)
        return (paper_x is not None and paper_y is not None), confidence
    
    def check_and_create_advertisement(self, screen: np.ndarray) -> bool:
        """Check if we have advertisement paper, if not create one (unless in cooldown)"""
        self.log("📰 Checking for advertisement paper...")
        
        # Check if check_paper.png exists (means we have ads)
        check_paper_x, check_paper_y, confidence = self.template_manager.find_template(screen, 'check_paper', threshold=self.config.CHECK_PAPER_THRESHOLD)
        
        if check_paper_x and check_paper_y:
            self.log(f"✅ Advertisement paper found! (confidence: {confidence:.2f}) - ads are active")
            return True
        
        # Check if paper_cooldown.png exists (means paper feature is in cooldown)
        cooldown_x, cooldown_y, cooldown_conf = self.template_manager.find_template(screen, 'paper_cooldown', threshold=self.config.PAPER_COOLDOWN_THRESHOLD)
        
        if cooldown_x and cooldown_y:
            self.log(f"⏳ Paper advertisement is in COOLDOWN (confidence: {cooldown_conf:.2f}, threshold: {self.config.PAPER_COOLDOWN_THRESHOLD}) - cannot create ads right now")
            self.log("🕒 Skipping advertisement creation - will check again later")
            return True  # Return True to continue normal flow, just skip ad creation
        
        # No existing ads and no cooldown - try to create advertisement
        self.log(f"❌ No advertisement paper found (check_paper confidence: {confidence:.2f}) - need to create ads")
        return self.create_advertisement_workflow(screen)
    
    def create_advertisement_workflow(self, screen: np.ndarray) -> bool:
        """Create advertisement by clicking offer and using paper buttons"""
        self.log("📰 Starting advertisement creation workflow...")
        
        # Step 1: Click any existing offer in the market
        # Look for general offer template first (preferred) - with debug logging
        offer_x, offer_y, offer_conf = self.template_manager.find_template(screen, 'offer', threshold=self.config.ADVERT_OFFER_THRESHOLD)
        wheat_offer_x, wheat_offer_y, wheat_conf = self.template_manager.find_template(screen, 'wheat_market', threshold=self.config.ADVERT_WHEAT_OFFER_THRESHOLD)
        new_offer_x, new_offer_y, new_conf = self.template_manager.find_template(screen, 'new_offer', threshold=self.config.ADVERT_NEW_OFFER_THRESHOLD)
        
        if offer_x and offer_y and offer_conf >= self.config.ADVERT_OFFER_THRESHOLD:
            self.log(f"📄 Clicking offer to create advertisement (confidence: {offer_conf:.2f})")
            self.safe_click(offer_x, offer_y, "offer for advertisement")
        elif wheat_offer_x and wheat_offer_y and wheat_conf >= self.config.ADVERT_WHEAT_OFFER_THRESHOLD:
            self.log(f"🌾 Clicking wheat offer to create advertisement (confidence: {wheat_conf:.2f})")
            self.safe_click(wheat_offer_x, wheat_offer_y, "wheat offer for advertisement")
        elif new_offer_x and new_offer_y and new_conf >= self.config.ADVERT_NEW_OFFER_THRESHOLD:
            self.log(f"📝 Clicking new offer slot to create advertisement (confidence: {new_conf:.2f})")
            self.safe_click(new_offer_x, new_offer_y, "new offer for advertisement")
        else:
            self.log(f"❌ No offers found to create advertisement (thresholds too low: offer={offer_conf:.3f}, wheat={wheat_conf:.3f}, new={new_conf:.3f})")
            return False
        
        time.sleep(self.config.MARKET_UI_WAIT)
        
        # Step 2: Check if we're in the paper page, then click paper_button.png
        screen = self.screen_capture.capture_screen(use_cache=False)
        
        # Verify we're in the correct page (paper page) before proceeding
        in_paper_page, paper_page_conf = self.is_in_paper_page(screen)
        if not in_paper_page:
            self.log(f"❌ Not in paper page after clicking offer (confidence: {paper_page_conf:.2f})")
            return False
        
        self.log(f"✅ Confirmed we're in paper page (confidence: {paper_page_conf:.2f})")
        
        # Check for paper cooldown immediately after confirming we're in paper page
        cooldown_x, cooldown_y, cooldown_conf = self.template_manager.find_template(screen, 'paper_cooldown', threshold=self.config.PAPER_COOLDOWN_THRESHOLD)
        
        if cooldown_x and cooldown_y:
            self.log(f"⏳ Paper advertisement is in COOLDOWN (confidence: {cooldown_conf:.2f}, threshold: {self.config.PAPER_COOLDOWN_THRESHOLD}) - cannot create ads right now")
            self.log("🕒 Skipping advertisement creation - paper feature is in cooldown, closing paper page...")
            
            # Close the paper page since we can't create ads
            close_x, close_y, close_conf = self.template_manager.find_template(screen, 'close', threshold=self.config.CLOSE_BUTTON_THRESHOLD)
            if close_x and close_y:
                self.log(f"🔲 Closing paper page due to cooldown (confidence: {close_conf:.2f})")
                self.safe_click(close_x, close_y, "close paper page - cooldown")
                time.sleep(self.config.MARKET_UI_WAIT)
            else:
                self.log("⚠️ Could not find close button on paper page during cooldown")
            
            return True  # Return True to continue normal flow, just skip ad creation
        
        paper_button_x, paper_button_y, paper_conf = self.template_manager.find_template(screen, 'paper_button', threshold=self.config.PAPER_BUTTON_THRESHOLD)
        
        if not paper_button_x or not paper_button_y:
            self.log(f"❌ Paper button not found (confidence: {paper_conf:.2f})")
            return False
        
        self.log(f"📄 Clicking paper button (confidence: {paper_conf:.2f})")
        self.safe_click(paper_button_x, paper_button_y, "paper button")
        time.sleep(self.config.MARKET_UI_WAIT)
        
        # Step 3: Click paper_create.png to create the advertisement
        screen = self.screen_capture.capture_screen(use_cache=False)
        paper_create_x, paper_create_y, create_conf = self.template_manager.find_template(screen, 'paper_create', threshold=self.config.PAPER_CREATE_THRESHOLD)
        
        if not paper_create_x or not paper_create_y:
            self.log(f"❌ Paper create button not found (confidence: {create_conf:.2f})")
            return False
        
        self.log(f"📰 Clicking paper create button (confidence: {create_conf:.2f})")
        self.safe_click(paper_create_x, paper_create_y, "paper create")
        time.sleep(self.config.MARKET_UI_WAIT)
        
        self.log("✅ Advertisement created successfully!")
        return True