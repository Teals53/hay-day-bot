"""
HayDay Bot - Clean & Fast
Lightweight automated farming bot with modern GUI
"""

import tkinter as tk
import time
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui import HayDayBotGUI
    from config import BotConfig
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all required modules are available.")
    sys.exit(1)

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


def main():
    """Main application entry point"""
    print("🤖 HayDay Bot - Clean & Fast")
    print("=" * 40)
    
    # Create main window
    root = tk.Tk()
    
    try:
        # Initialize the bot GUI
        app = HayDayBotGUI(root)
        
        # Window close handler
        def on_closing():
            if app.bot_state.running:
                if tk.messagebox.askokcancel("Quit", "Bot is running. Stop and quit?"):
                    app.stop_bot()
                    time.sleep(0.5)
                    root.destroy()
            else:
                # Clean up resources safely
                try:
                    if KEYBOARD_AVAILABLE:
                        keyboard.clear_all_hotkeys()
                except Exception:
                    pass
                
                try:
                    if hasattr(app, 'screen_capture'):
                        app.screen_capture.cleanup()
                except Exception:
                    pass
                
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Start the application
        print("✅ Bot initialized successfully")
        print("🚀 Starting GUI...")
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("👋 HayDay Bot closed")


if __name__ == "__main__":
    main() 