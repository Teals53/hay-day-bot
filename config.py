# HayDay Bot Configuration - Clean & Optimized
class BotConfig:
    """Centralized configuration for HayDay Bot"""
    
    # ==================== CORE TIMING ====================
    WHEAT_HARVEST_TIME = 110
    DEFAULT_CLICK_DELAY = 0.2      # Faster clicks for better performance
    DEFAULT_MOVEMENT_SPEED = 0.05   # Faster mouse movement
    SCREEN_CENTER_DELAY = 2         # Reduced delay
    CYCLE_PAUSE = 3                 # Pause between farming cycles
    PLANT_DELAY = 2                 # Delay after clicking field center
    HARVEST_DELAY = 1               # Delay before starting harvest
    
    # ==================== DETECTION THRESHOLDS ====================
    MAIN_PAGE_THRESHOLD = 0.7
    MARKET_PAGE_THRESHOLD = 0.7
    OFFER_PAGE_THRESHOLD = 0.5
    SILO_POPUP_THRESHOLD = 0.7
    CLOSE_BUTTON_THRESHOLD = 0.4
    MARKET_BUTTON_THRESHOLD = 0.7
    WHEAT_MARKET_THRESHOLD = 0.8
    LOADING_SCREEN_THRESHOLD = 0.7
    CLICK_ESCAPE_THRESHOLD = 0.8
    
    # Market operations
    COLLECT_BUTTON_THRESHOLD = 0.7
    SOLD_ITEMS_THRESHOLD = 0.7
    NEWSPAPER_THRESHOLD = 0.6
    NEW_OFFER_THRESHOLD = 0.7
    INSERT_BUTTON_THRESHOLD = 0.7
    PLUS_BUTTON_ACTIVE_THRESHOLD = 0.7
    PLUS_BUTTON_DEACTIVE_THRESHOLD = 0.7
    ARROW_BUTTON_ACTIVE_THRESHOLD = 0.7
    ARROW_BUTTON_DEACTIVE_THRESHOLD = 0.7
    
    # Paper/Advertisement thresholds
    PAPER_BUTTON_THRESHOLD = 0.7
    PAPER_CREATE_THRESHOLD = 0.7
    PAPER_PAGE_THRESHOLD = 0.7
    OFFER_THRESHOLD = 0.7
    PAPER_COOLDOWN_THRESHOLD = 0.8
    CHECK_PAPER_THRESHOLD = 0.6
    
    # Priority thresholds
    OFFER_PAGE_PRIORITY_THRESHOLD = 0.8
    MARKET_PAGE_PRIORITY_THRESHOLD = 0.7
    PAPER_PAGE_PRIORITY_THRESHOLD = 0.7
    
    # Advertisement creation thresholds
    ADVERT_OFFER_THRESHOLD = 0.7
    ADVERT_WHEAT_OFFER_THRESHOLD = 0.7
    ADVERT_NEW_OFFER_THRESHOLD = 0.7
    
    # ==================== UI OFFSETS ====================
    WHEAT_X_OFFSET = -100
    WHEAT_Y_OFFSET = -150
    HARVEST_X_OFFSET = -260
    HARVEST_Y_OFFSET = -40
    INITIAL_PLANT_X_OFFSET = 25
    INITIAL_PLANT_Y_OFFSET = 80
    INITIAL_HARVEST_X_OFFSET = 15
    INITIAL_HARVEST_Y_OFFSET = 25
    
    # ==================== PERFORMANCE SETTINGS ====================
    DETECTION_UPDATE_INTERVAL = 0.3  # Faster updates
    STOP_CHECK_INTERVAL = 0.1
    MAX_SLEEP_CHUNK = 1.0            # Maximum sleep chunk size
    THREAD_SHUTDOWN_TIMEOUT = 3.0    # Faster shutdown
    MOVEMENT_SPEED = 0.03            # Faster movement
    PLANT_STEPS = 25                 # Fewer steps for speed
    HARVEST_STEPS = 20
    JIGGLE_AMPLITUDE = 45
    
    # Movement limits
    MIN_CLICK_DELAY = 0.2
    MAX_CLICK_DELAY = 5.0
    MIN_MOVEMENT_SPEED = 0.02
    MAX_MOVEMENT_SPEED = 1.0
    
    # ==================== KEYBOARD SHORTCUTS ====================
    START_BOT_HOTKEY = 'F4'
    STOP_BOT_HOTKEY = 'F5'
    
    # ==================== MARKET SETTINGS ====================
    MARKET_CHECK_INTERVAL = 12       # Faster market checks
    MARKET_CLICK_DELAY = 0.2         # Faster market operations
    MARKET_STEP_DELAY = 0.1
    MARKET_UI_WAIT = 0.4
    MARKET_BUTTON_WAIT = 0.2
    ENABLE_GROWTH_MARKET_MANAGEMENT = True
    
    # ==================== RESOLUTION & TEMPLATES ====================
    TEMPLATE_1K_DIR = "templates/1ktemplates"
    TEMPLATE_2K_DIR = "templates/2ktemplates"
    TEMPLATE_DEFAULT_DIR = "templates"
    RESOLUTION_1K_WIDTH = 1920
    RESOLUTION_1K_HEIGHT = 1080
    RESOLUTION_2K_WIDTH = 2560
    RESOLUTION_2K_HEIGHT = 1440
    ENABLE_RESOLUTION_DETECTION = True
    
    # ==================== SYSTEM SETTINGS ====================
    WHEAT_MIN_AREA = 2000
    FAILSAFE_ENABLED = False
    ENABLE_PROGRESS_LOGGING = True
    PROGRESS_LOG_INTERVAL = 15       # Less spam
    ENABLE_PATH_LOGGING = False
    RETRY_DELAY = 10
    
    # ==================== POPUP HANDLING ====================
    ENABLE_UNKNOWN_POPUP_HANDLING = True
    UNKNOWN_POPUP_DETECTION_THRESHOLD = 0.6
    UNKNOWN_POPUP_MAX_ATTEMPTS = 3
    UNKNOWN_POPUP_CLOSE_DELAY = 1.0
    UNKNOWN_POPUP_TIMEOUT = 10.0
    POPUP_SAFE_MODE = True
    POPUP_HIGH_CONFIDENCE_THRESHOLD = 0.95
    POPUP_PROTECTED_PAGES = ['market', 'offer', 'paper_page']
    CLOSE_BUTTON_VARIANTS = ["close.png"] 