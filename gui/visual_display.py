"""
Clean visual display for HayDay Bot
Lightweight detection overlay with modern styling
"""

import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
from typing import Optional

from core import PathGenerator
from config import BotConfig


class VisualDisplay:
    """Clean visual display with detection overlays"""
    
    def __init__(self, parent: ttk.Frame, config: BotConfig, show_path_var: tk.BooleanVar):
        self.config = config
        self.show_path_var = show_path_var
        
        # Setup display frame
        self.display_frame = ttk.LabelFrame(parent, text="🔍 Live Detection", padding=10)
        self.display_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for image display
        self.canvas = tk.Canvas(
            self.display_frame, bg="#2c3e50", width=600, height=400,
            highlightthickness=0, relief='flat'
        )
        self.canvas.pack(expand=True, pady=(0, 10))
        
        # Remove duplicate status indicators - field detection and center info 
        # are already shown in the main window's detection status section
        
        # Show initial message
        self.show_waiting_message()
    
    def show_waiting_message(self):
        """Show clean waiting message"""
        self.canvas.delete("all")
        self.canvas.create_text(
            300, 200, text="🔍 Detection Starting...\n\nPosition HayDay field clearly on screen", 
            fill="#ecf0f1", font=("Arial", 12), justify=tk.CENTER
        )
    
    def show_disabled_message(self):
        """Show disabled message"""
        self.canvas.delete("all")
        self.canvas.create_text(
            300, 200, text="👁️ Detection Disabled", 
            fill="#95a5a6", font=("Arial", 14)
        )
    
    def update_display(self, screen: np.ndarray, cx: Optional[int], cy: Optional[int], contour: Optional[np.ndarray]):
        """Update display with clean detection overlay"""
        try:
            # Resize for display
            height, width = screen.shape[:2]
            display_width = 600
            display_height = int((display_width / width) * height)
            if display_height > 400:
                display_height = 400
                display_width = int((display_height / height) * width)
            
            display_img = cv2.resize(screen, (display_width, display_height))
            
            # Draw detection overlay
            if cx is not None and cy is not None:
                self._draw_clean_overlay(display_img, cx, cy, contour, width, height, display_width, display_height)
            else:
                # No detection - show visual indicator only
                cv2.putText(display_img, "NO FIELD DETECTED", 
                           (display_width//2 - 80, display_height//2), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (52, 152, 219), 2)
            
            # Update canvas
            self._update_canvas(display_img)
            
        except Exception:
            # Silently handle display errors
            pass
    
    def _draw_clean_overlay(self, display_img: np.ndarray, cx: int, cy: int, contour: Optional[np.ndarray], 
                           orig_width: int, orig_height: int, display_width: int, display_height: int):
        """Draw clean, minimal overlay"""
        # Scale coordinates
        scale_x = display_width / orig_width
        scale_y = display_height / orig_height
        
        display_cx = int(cx * scale_x)
        display_cy = int(cy * scale_y)
        
        # Draw field center (clean green circle)
        cv2.circle(display_img, (display_cx, display_cy), 8, (46, 204, 113), -1)
        cv2.circle(display_img, (display_cx, display_cy), 10, (255, 255, 255), 2)
        
        # Draw field boundary if available
        if contour is not None:
            scaled_contour = contour.copy()
            scaled_contour[:, :, 0] = (scaled_contour[:, :, 0] * scale_x).astype(int)
            scaled_contour[:, :, 1] = (scaled_contour[:, :, 1] * scale_y).astype(int)
            cv2.drawContours(display_img, [scaled_contour], -1, (52, 152, 219), 2)
        
        # Draw UI positions (minimal)
        self._draw_ui_positions(display_img, display_cx, display_cy, scale_x, scale_y)
        
        # Show path if enabled
        if self.show_path_var.get():
            self._draw_simple_path(display_img, display_cx, display_cy, contour, scale_x, scale_y)
    
    def _draw_ui_positions(self, display_img: np.ndarray, display_cx: int, display_cy: int, 
                          scale_x: float, scale_y: float):
        """Draw clean UI element indicators"""
        # Wheat position
        wheat_x = display_cx + int(self.config.WHEAT_X_OFFSET * scale_x)
        wheat_y = display_cy + int(self.config.WHEAT_Y_OFFSET * scale_y)
        if 0 <= wheat_x < display_img.shape[1] and 0 <= wheat_y < display_img.shape[0]:
            cv2.circle(display_img, (wheat_x, wheat_y), 6, (241, 196, 15), -1)
            cv2.circle(display_img, (wheat_x, wheat_y), 8, (255, 255, 255), 1)
        
        # Harvest position
        harvest_x = display_cx + int(self.config.HARVEST_X_OFFSET * scale_x)
        harvest_y = display_cy + int(self.config.HARVEST_Y_OFFSET * scale_y)
        if 0 <= harvest_x < display_img.shape[1] and 0 <= harvest_y < display_img.shape[0]:
            cv2.circle(display_img, (harvest_x, harvest_y), 6, (230, 126, 34), -1)
            cv2.circle(display_img, (harvest_x, harvest_y), 8, (255, 255, 255), 1)
        
        # Clean connecting lines
        cv2.line(display_img, (display_cx, display_cy), (wheat_x, wheat_y), (241, 196, 15), 1)
        cv2.line(display_img, (display_cx, display_cy), (harvest_x, harvest_y), (230, 126, 34), 1)
    
    def _draw_simple_path(self, display_img: np.ndarray, display_cx: int, display_cy: int, 
                         contour: Optional[np.ndarray], scale_x: float, scale_y: float):
        """Draw simplified path visualization"""
        try:
            original_cx = int(display_cx / scale_x)
            original_cy = int(display_cy / scale_y)
            
            # Generate path
            path = PathGenerator.create_linear_path(original_cx, original_cy, contour, "plant")
            
            # Draw simplified path (every 10th point)
            prev_point = None
            for i, (x, y) in enumerate(path[::10]):  # Every 10th point for cleaner look
                scaled_x = int(x * scale_x)
                scaled_y = int(y * scale_y)
                
                if 0 <= scaled_x < display_img.shape[1] and 0 <= scaled_y < display_img.shape[0]:
                    if prev_point is not None:
                        cv2.line(display_img, prev_point, (scaled_x, scaled_y), (155, 89, 182), 1)
                    
                    cv2.circle(display_img, (scaled_x, scaled_y), 2, (155, 89, 182), -1)
                    prev_point = (scaled_x, scaled_y)
            
            # Path info
            cv2.putText(display_img, f"Path: {len(path)} points", 
                       (10, display_img.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (155, 89, 182), 1)
        except Exception:
            pass
    
    def _update_canvas(self, display_img: np.ndarray):
        """Update canvas with image"""
        try:
            # Convert to PIL and then to PhotoImage
            img_rgb = cv2.cvtColor(display_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            photo = ImageTk.PhotoImage(pil_img)
            
            # Update canvas
            self.canvas.delete("all")
            self.canvas.create_image(300, 200, image=photo)
            self.canvas.image = photo  # Keep reference
        except Exception:
            pass 