"""
Modern GUI for HayDay Bot - Clean & Lightweight
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from typing import Optional

from core import DetectionState, BotState, ScreenCapture, TemplateManager
from gui.detection_manager import DetectionManager
from gui.visual_display import VisualDisplay
from gui.bot_controller import BotController
from core import SoilDetector
from config import BotConfig

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class HayDayBotGUI:
    """Modern GUI for HayDay Bot"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.config = BotConfig()
        
        # Initialize state objects
        self.detection_state = DetectionState()
        self.bot_state = BotState()
        self.detection_lock = threading.Lock()
        # Separate stop events - detection continues when bot stops
        self.bot_stop_event = threading.Event()
        self.detection_stop_event = threading.Event()
        
        # Initialize core systems
        self.screen_capture = ScreenCapture()
        self.template_manager = TemplateManager(self.config)
        self.soil_detector = SoilDetector()
        
        # GUI variables
        self.show_path_var = tk.BooleanVar(value=True)
        
        # Initialize managers
        self.detection_manager: Optional[DetectionManager] = None
        self.bot_controller: Optional[BotController] = None
        self.visual_display: Optional[VisualDisplay] = None
        
        # Threads
        self.detection_thread: Optional[threading.Thread] = None
        
        # Setup modern GUI
        self._setup_modern_gui()
        self._initialize_systems()
        self._setup_keyboard_shortcuts()
        
        self.log("✅ HayDay Bot initialized successfully!")
    
    def _setup_modern_gui(self):
        """Setup modern, clean GUI"""
        self.root.title("🤖 HayDay Bot - Clean & Fast")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Configure modern style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Custom colors
        style.configure('Title.TLabel', font=('Arial', 12, 'bold'), foreground='#2c3e50')
        style.configure('Status.TLabel', font=('Arial', 10), foreground='#27ae60')
        style.configure('Error.TLabel', font=('Arial', 10), foreground='#e74c3c')
        style.configure('Modern.TButton', font=('Arial', 10, 'bold'))
        
        # Main container
        main_container = ttk.Frame(self.root, padding=15)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Top status bar
        self._create_status_bar(main_container)
        
        # Main content area
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Left panel (controls)
        left_panel = ttk.Frame(content_frame, width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_panel.pack_propagate(False)
        
        # Right panel (visual display)
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Setup panels
        self._setup_control_panel(left_panel)
        self.visual_display = VisualDisplay(right_panel, self.config, self.show_path_var)
    
    def _create_status_bar(self, parent):
        """Create modern status bar"""
        status_frame = ttk.Frame(parent, relief='solid', borderwidth=1)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Status indicator
        indicator_frame = ttk.Frame(status_frame, padding=10)
        indicator_frame.pack(fill=tk.X)
        
        self.status_indicator = tk.Canvas(indicator_frame, width=20, height=20, highlightthickness=0)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        self._update_status_indicator("ready")
        
        self.main_status = ttk.Label(indicator_frame, text="Ready to start", style='Title.TLabel')
        self.main_status.pack(side=tk.LEFT)
        
        # System info on right
        info_frame = ttk.Frame(indicator_frame)
        info_frame.pack(side=tk.RIGHT)
        
        self.resolution_info = ttk.Label(info_frame, text="Resolution: Detecting...", font=('Arial', 9))
        self.resolution_info.pack(anchor='e')
        
        self.template_info = ttk.Label(info_frame, text="Templates: Loading...", font=('Arial', 9))
        self.template_info.pack(anchor='e')
    
    def _setup_control_panel(self, parent):
        """Setup clean control panel"""
        # Bot controls
        control_frame = ttk.LabelFrame(parent, text="🎮 Bot Controls", padding=15)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Main buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = ttk.Button(
            button_frame, text="▶ Start Bot (F4)", 
            command=self.start_bot, style='Modern.TButton'
        )
        self.start_button.pack(fill=tk.X, pady=(0, 5))
        
        self.stop_button = ttk.Button(
            button_frame, text="⏹ Stop Bot (F5)", 
            command=self.stop_bot, state="disabled", style='Modern.TButton'
        )
        self.stop_button.pack(fill=tk.X)
        
        # Detection status
        detection_frame = ttk.LabelFrame(parent, text="🔍 Detection Status", padding=15)
        detection_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.detection_status = ttk.Label(detection_frame, text="Initializing detection...", style='Status.TLabel')
        self.detection_status.pack(anchor="w")
        
        self.field_status = ttk.Label(detection_frame, text="Field: Not detected", font=('Arial', 9))
        self.field_status.pack(anchor="w")
        
        self.storage_status = ttk.Label(detection_frame, text="Storage: Checking...", font=('Arial', 9))
        self.storage_status.pack(anchor="w")
        
        # Options
        options_frame = ttk.LabelFrame(parent, text="⚙️ Options", padding=15)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.show_path_checkbox = ttk.Checkbutton(
            options_frame, text="Show planned paths", variable=self.show_path_var
        )
        self.show_path_checkbox.pack(anchor="w")
        
        self.detection_toggle = ttk.Button(
            options_frame, text="Toggle Detection", command=self._toggle_detection
        )
        self.detection_toggle.pack(fill=tk.X, pady=(10, 0))
        
        # Log panel
        log_frame = ttk.LabelFrame(parent, text="📋 Activity Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Log with scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(
            log_container, wrap=tk.WORD, height=15, width=35,
            font=('Consolas', 9), bg='#2c3e50', fg='#ecf0f1',
            insertbackground='#ecf0f1', selectbackground='#34495e'
        )
        scrollbar = ttk.Scrollbar(log_container, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _update_status_indicator(self, status: str):
        """Update status indicator circle"""
        self.status_indicator.delete("all")
        colors = {
            "ready": "#95a5a6",
            "running": "#27ae60", 
            "stopped": "#e74c3c",
            "error": "#e67e22"
        }
        color = colors.get(status, "#95a5a6")
        self.status_indicator.create_oval(2, 2, 18, 18, fill=color, outline=color)
    
    def _initialize_systems(self):
        """Initialize all systems"""
        self.log("🔧 Initializing bot systems...")
        
        # Detect resolution
        resolution = self._detect_screen_resolution()
        self.log(f"🖥️ Screen resolution: {resolution}")
        self.resolution_info.config(text=f"Resolution: {resolution}")
        
        # Initialize templates
        self.template_manager.initialize(resolution)
        self.template_info.config(text=f"Templates: {resolution} loaded")
        
        # Load soil detector templates
        self.soil_detector.load_templates(self.template_manager.template_dir)
        self.log("🌾 Detection system ready")
        
        # Initialize managers with separate stop events
        self.detection_manager = DetectionManager(
            self.config, self.screen_capture, self.soil_detector,
            self.template_manager, self.detection_state, self.bot_state,
            self.detection_lock, self.detection_stop_event, self.log,
            self._update_detection_status, self._update_storage_status
        )
        
        self.bot_controller = BotController(
            self.config, self.screen_capture, self.template_manager,
            self.detection_state, self.bot_state, self.detection_lock,
            self.bot_stop_event, self.log, self.update_status
        )
        
        # Start detection
        self._start_detection_thread()
        self.log("✅ All systems ready!")
    
    def _detect_screen_resolution(self) -> str:
        """Detect screen resolution"""
        temp_root = tk.Tk()
        width = temp_root.winfo_screenwidth()
        height = temp_root.winfo_screenheight()
        temp_root.destroy()
        
        if width >= self.config.RESOLUTION_2K_WIDTH and height >= self.config.RESOLUTION_2K_HEIGHT:
            return "2K"
        else:
            return "1K"
    
    def _setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        if not KEYBOARD_AVAILABLE:
            self.log("⚠️ Keyboard shortcuts not available")
            return
            
        try:
            keyboard.add_hotkey(self.config.START_BOT_HOTKEY, self._hotkey_start_bot)
            keyboard.add_hotkey(self.config.STOP_BOT_HOTKEY, self._hotkey_stop_bot)
            self.log(f"⌨️ Hotkeys: {self.config.START_BOT_HOTKEY} = Start, {self.config.STOP_BOT_HOTKEY} = Stop")
        except Exception as e:
            self.log(f"⚠️ Could not setup hotkeys: {e}")
    
    def _hotkey_start_bot(self):
        """Hotkey handler for start bot"""
        self.root.after(0, self.start_bot)
    
    def _hotkey_stop_bot(self):
        """Hotkey handler for stop bot"""
        self.root.after(0, self.stop_bot)
    
    def _start_detection_thread(self):
        """Start detection thread with visual display"""
        if self.detection_thread is None or not self.detection_thread.is_alive():
            self.detection_thread = threading.Thread(
                target=self.detection_manager.detection_loop, 
                args=(self.visual_display,), daemon=True
            )
            self.detection_thread.start()
            self.log("👁️ Detection system started")
    
    def _toggle_detection(self):
        """Toggle detection on/off"""
        self.bot_state.detection_active = not self.bot_state.detection_active
        
        if self.bot_state.detection_active:
            self.log("👁️ Detection enabled")
            self.detection_toggle.config(text="Disable Detection")
        else:
            self.log("👁️ Detection disabled")
            self.detection_toggle.config(text="Enable Detection")
            if self.visual_display:
                self.visual_display.show_disabled_message()
    
    def start_bot(self):
        """Start the bot"""
        if self.bot_controller.start_bot():
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self._update_status_indicator("running")
            self.main_status.config(text="Bot is running")
    
    def stop_bot(self):
        """Stop the bot"""
        self.bot_controller.stop_bot()
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self._update_status_indicator("stopped")
        self.main_status.config(text="Bot stopped")
    
    def update_status(self, status: str, color: str = "black"):
        """Update status label"""
        self.root.after(0, lambda: self.main_status.config(text=status))
        if "running" in status.lower():
            self.root.after(0, lambda: self._update_status_indicator("running"))
        elif "stopped" in status.lower():
            self.root.after(0, lambda: self._update_status_indicator("stopped"))
    
    def _update_detection_status(self, cx: Optional[int], cy: Optional[int]):
        """Update detection status"""
        if cx is not None and cy is not None:
            self.root.after(0, lambda: self.detection_status.config(
                text="✅ Field detected", style='Status.TLabel'
            ))
            self.root.after(0, lambda: self.field_status.config(
                text=f"Center: ({cx}, {cy})"
            ))
            if self.visual_display:
                screen = self.screen_capture.capture_screen()
                with self.detection_lock:
                    contour = self.detection_state.contour
                self.visual_display.update_display(screen, cx, cy, contour)
        else:
            self.root.after(0, lambda: self.detection_status.config(
                text="❌ No field found", style='Error.TLabel'
            ))
            self.root.after(0, lambda: self.field_status.config(text="Center: None"))
    
    def _update_storage_status(self):
        """Update storage status"""
        with self.detection_lock:
            if self.detection_state.storage_full:
                status_text = f"🏗️ Storage full ({self.detection_state.storage_keyword})"
                style = 'Error.TLabel'
            else:
                status_text = "✅ Storage OK"
                style = 'Status.TLabel'
        
        self.root.after(0, lambda: self.storage_status.config(text=status_text, style=style))
    
    def log(self, message: str):
        """Add message to log"""
        self.root.after(0, lambda: self._update_log(message))
    
    def _update_log(self, message: str):
        """Update log text widget"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        
        # Keep log size manageable
        lines = int(self.log_text.index('end-1c').split('.')[0])
        if lines > 5000:
            self.log_text.delete('1.0', '100.0')
 