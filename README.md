# 🤖 HayDay Bot - Clean & Fast

A lightweight, optimized farming bot for HayDay with a modern, clean interface designed for speed and efficiency.

![image](https://github.com/user-attachments/assets/dd14ae9c-2580-4355-a239-eae2180c03c6)

<video src="https://github.com/user-attachments/assets/47ae4656-64c3-4d53-bc1a-14420b78d5b8" width="352" height="720"></video>

## ✨ **Key Features**

### 🚀 **Performance Optimized**
- **Lightweight Dependencies**: Uses headless OpenCV for better performance
- **Fast Screen Capture**: Optimized MSS-based capture with intelligent caching (50ms)
- **Minimal Delays**: Reduced timing delays for faster operation (0.2s clicks, 0.05s movement)
- **Efficient Path Generation**: Streamlined linear path algorithms with smart threading

### 🎯 **Smart Automation**
- **Advanced Field Detection**: Template-based and HSV color detection for reliable field recognition
- **Wheat Management**: Automated planting and harvesting cycles with coverage analysis
- **Market Operations**: Automatic wheat selling, money collection, and advertisement management
- **Popup Handling**: Intelligent detection and dismissal of game popups with safe mode protection

### 🖥️ **Modern Clean GUI**
- **Minimalist Design**: Clean, modern interface with intuitive controls
- **Real-time Feedback**: Live field detection with visual overlays and path visualization
- **Status Indicators**: Clear visual status with color-coded indicators
- **Dark Theme Log**: Easy-to-read console-style activity log with progress tracking

### ⚡ **Fast & Lightweight**
- **Optimized Dependencies**: Minimal package requirements (6 core packages)
- **Smart Caching**: Intelligent screen capture caching and template management
- **Fast Operations**: Reduced click delays and optimized movement algorithms
- **Efficient Threading**: Proper thread management with graceful shutdown

## 🚀 **Quick Start**

### Installation
```powershell
# Run the installer (Windows)
install.bat

# Or install manually
pip install -r requirements.txt
```

### Running the Bot
```powershell
# Use the launcher
start.bat

# Or run directly
python main.py
```

### Basic Usage
1. **Launch HayDay** and position it clearly on screen
2. **Start the Bot** with the GUI button or press `F4`
3. **Monitor Progress** through the clean visual display
4. **Stop the Bot** with the GUI button or press `F5`

## ⚙️ **Configuration**

Key settings in `config.py`:

### 🕐 **Performance Settings**
```python
DEFAULT_CLICK_DELAY = 0.2      # Fast clicks
DEFAULT_MOVEMENT_SPEED = 0.05   # Quick mouse movement
DETECTION_UPDATE_INTERVAL = 0.3 # Faster detection updates
SCREEN_CENTER_DELAY = 2         # Reduced delay
```

### 🎯 **Detection Thresholds**
```python
MAIN_PAGE_THRESHOLD = 0.7       # Main page detection
SILO_POPUP_THRESHOLD = 0.7      # Silo full detection
WHEAT_MARKET_THRESHOLD = 0.8    # Market wheat detection
WHEAT_MIN_AREA = 2000          # Minimum wheat area for detection
```

### 📐 **UI Offsets**
```python
WHEAT_X_OFFSET = -100          # Wheat selection position
WHEAT_Y_OFFSET = -150
HARVEST_X_OFFSET = -260        # Harvest tool position
HARVEST_Y_OFFSET = -40
```

## 🏗️ **Architecture**

```
modular/
├── main.py                 # Clean entry point with error handling
├── config.py              # Centralized configuration management
├── core/                  # Core functionality modules
│   ├── __init__.py        # Module exports
│   ├── screen_capture.py  # Fast MSS-based screen capture
│   ├── template_manager.py # Template loading and management
│   ├── soil_detector.py   # Field detection with HSV + templates
│   ├── path_generator.py  # Optimized path generation algorithms
│   └── state.py          # Dataclass-based state management
├── bot/                   # Bot operations
│   ├── __init__.py        # Bot module exports
│   ├── operations.py     # Core farming operations
│   └── market.py         # Market management and trading
├── gui/                   # Modern GUI components
│   ├── __init__.py        # GUI module exports
│   ├── main_window.py    # Main application window
│   ├── visual_display.py # Real-time visual feedback
│   ├── bot_controller.py # Bot control logic
│   └── detection_manager.py # Detection state management
└── templates/             # Detection templates
    ├── 1ktemplates/      # 1080p resolution templates
    └── 2ktemplates/      # 2K resolution templates
```

## 🔧 **Code Quality Standards**

### **Type Safety**
- Full type annotations using `typing` module
- No usage of `Any` type - specific types used throughout
- Proper Optional and Union types for nullable values

### **Error Handling**
- Specific exception handling with proper error types
- Graceful degradation for missing dependencies
- Resource cleanup in finally blocks and context managers

### **Performance**
- Efficient algorithms with O(n) complexity where possible
- Smart caching strategies to reduce redundant operations
- Thread-safe implementations with proper synchronization

### **Code Organization**
- Modular architecture with clear separation of concerns
- Dataclass-based state management for immutability
- Centralized configuration management

## 🔧 **Optimizations Made**

### **Dependencies**
- Switched to `opencv-python-headless` for better performance
- Optimized dependency list with only essential packages
- Removed unnecessary packages for faster installation

### **Performance**
- Reduced screen capture cache to 50ms for faster updates
- Optimized mouse movement with minimal delays (0.05s)
- Streamlined path execution with faster movement algorithms
- Improved thread management and graceful shutdown (3s timeout)

### **GUI**
- Modern, clean interface with better styling and UX
- Reduced visual complexity while maintaining functionality
- Color-coded status indicators for quick feedback
- Compact layout with essential controls only

### **Code Quality**
- Cleaned up configuration with logical grouping
- Simplified error handling with specific exception types
- Reduced code complexity while maintaining features
- Better resource management and cleanup patterns

## 🎮 **Controls**

- **F4**: Start Bot
- **F5**: Stop Bot
- **Toggle Detection**: Enable/disable field detection
- **Show Paths**: Toggle path visualization
- **GUI Controls**: Start/Stop, Settings, Visual feedback

## 🛠️ **System Requirements**

- **Python 3.7+** with pip package managers
- **Windows 10/11** (PowerShell support)
- **HayDay** running in windowed or fullscreen mode
- **1080p or 2K resolution** (auto-detected with template switching)

## 🔍 **Troubleshooting**

### **"No field detected"**
- Ensure HayDay is visible and field is clear of decorations
- Check if correct resolution templates are loaded (1K/2K auto-detection)
- Verify field is not covered by UI elements or popups
- Try adjusting detection thresholds in config.py

### **Bot runs slowly**
- Close unnecessary applications to free up system resources
- Ensure HayDay has focus and is not minimized
- Check if antivirus is interfering with screen capture
- Verify Python and dependency versions are up to date

### **GUI not responding**
- Restart the application using start.bat
- Check Python and dependency versions with install.bat
- Run as administrator if needed for system access
- Check Windows PowerShell execution policy

### **Template Detection Issues**
- Ensure correct resolution templates are in use
- Check template files exist in templates/1ktemplates or templates/2ktemplates
- Verify game UI scaling matches template resolution
- Try adjusting detection thresholds for your specific setup
- Make sure the `click.png` template matches your farm’s visuals; if not, update it accordingly

### **Can't harvest or plant**
- Adjust the X and Y offsets in the config file to better align click positions with the game field
- Ensure the game is fully zoomed out for accurate detection and interaction

## 🤝 **Contributing**

Contributions are welcome! Areas for improvement:
- Additional template support for different languages
- Enhanced computer vision algorithms
- Performance optimizations
- Cross-platform compatibility
- Additional crop support beyond wheat

## 📄 **Legal Considerations**

This bot is created for **educational purposes** to demonstrate:
- Computer vision techniques in gaming
- Template-based UI automation
- Python automation libraries and GUI development
- Advanced configuration management

**⚠️ Important**: Do not use this bot to violate HayDay's terms of service. Use only in controlled environments for learning and research purposes.

---

**Made with ❤️ for the HayDay community** 

Special thanks to **erenmcl** for providing the 1K resolution samples and thorough testing.

*Last Update: 15.06.2025* 