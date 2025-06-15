import cv2
import numpy as np
import os
from typing import Optional, List, Dict, Tuple, Union
from config import BotConfig

class SoilDetector:
    def __init__(self) -> None:
        """Initialize soil detector with template-based detection"""
        self.config = BotConfig()
        
        # Initialize template variables (will be loaded later)
        self.field_template: Optional[np.ndarray] = None
        self.wheat_template: Optional[np.ndarray] = None
        self.templates_loaded: bool = False
    
    def load_templates(self, template_dir: str) -> None:
        """Load templates from the specified directory"""
        if self.templates_loaded:
            return
            
        # Load field template (soil/empty field)
        field_template_path = os.path.join(template_dir, 'field.png')
        if os.path.exists(field_template_path):
            self.field_template = cv2.imread(field_template_path)
        else:
            self.field_template = None
        
        # Load wheat template (grown wheat)
        wheat_template_path = os.path.join(template_dir, 'wheat.png')
        if os.path.exists(wheat_template_path):
            self.wheat_template = cv2.imread(wheat_template_path)
        else:
            self.wheat_template = None
            
        self.templates_loaded = True
    
    def find_template_matches(self, screen: np.ndarray, template: Optional[np.ndarray], threshold: float = 0.6) -> List[Dict[str, Union[int, float]]]:
        """Find all matches of a template in the screen"""
        if template is None:
            return []
        
        # Convert both to grayscale for better matching
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        # Template matching
        result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        
        # Find locations where the match exceeds threshold
        locations = np.where(result >= threshold)
        
        matches = []
        h, w = template_gray.shape
        
        for pt in zip(*locations[::-1]):  # Switch x and y coordinates
            x, y = pt
            confidence = result[y, x]
            matches.append({
                'x': x,
                'y': y,
                'w': w,
                'h': h,
                'center_x': x + w // 2,
                'center_y': y + h // 2,
                'confidence': confidence
            })
        
        return matches
    
    def get_centroid(self, contour: np.ndarray) -> Tuple[Optional[int], Optional[int]]:
        """Calculate the centroid of a contour"""
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            return cx, cy
        return None, None
    
    def detect_wheat(self, screen: np.ndarray) -> np.ndarray:
        """Detect grown wheat areas using HSV color detection for coverage calculation"""
        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)
        
        # Optimized HSV range for bright yellow/golden wheat (based on actual sampling)
        lower_wheat = np.array([15, 100, 150])  # Broad yellow range
        upper_wheat = np.array([35, 255, 255])  # Covers golden to bright yellow
        
        # Create mask for wheat
        mask = cv2.inRange(hsv, lower_wheat, upper_wheat)
        
        # Apply morphological operations to clean up the mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        # Filter out small noise - only keep significant wheat areas
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filtered_mask = np.zeros_like(mask)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.config.WHEAT_MIN_AREA:
                cv2.fillPoly(filtered_mask, [contour], 255)
        
        return filtered_mask
    
    def count_wheat_coverage(self, screen: np.ndarray, field_contour: Optional[np.ndarray]) -> float:
        """Count how much of the field is covered with grown wheat"""
        if field_contour is None:
            return 0.0
        
        wheat_mask = self.detect_wheat(screen)
        if wheat_mask is None:
            return 0.0
        
        # Create field mask from contour
        field_mask = np.zeros(wheat_mask.shape, dtype=np.uint8)
        cv2.fillPoly(field_mask, [field_contour.reshape(-1, 1, 2)], 255)
        
        # Find wheat within field boundaries only
        wheat_in_field = cv2.bitwise_and(wheat_mask, field_mask)
        
        # Calculate areas in pixels
        field_area_pixels = np.sum(field_mask > 0)
        wheat_area_pixels = np.sum(wheat_in_field > 0)
        
        # Prevent division by zero and ensure valid calculation
        if field_area_pixels > 0:
            coverage_percent = (wheat_area_pixels / field_area_pixels) * 100
            # Cap at 100% to prevent impossible values
            coverage_percent = min(coverage_percent, 100.0)
            return coverage_percent
        
        return 0.0
    
    def is_ready_for_harvest(self, screen: np.ndarray, field_contour: Optional[np.ndarray], threshold: float = 20.0) -> bool:
        """Check if field has enough grown wheat to harvest"""
        coverage = self.count_wheat_coverage(screen, field_contour)
        return coverage >= threshold
    
    def detect_field(self, screen: np.ndarray) -> Tuple[Optional[int], Optional[int], Optional[np.ndarray]]:
        """Main method to detect field using PNG template detection"""
        # Find field template matches (empty soil)
        field_matches = self.find_template_matches(screen, self.field_template, threshold=0.5)
        
        # Use HSV detection for wheat (for coverage calculation only)
        wheat_mask = self.detect_wheat(screen)
        wheat_contours, _ = cv2.findContours(wheat_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        wheat_areas = [cv2.contourArea(c) for c in wheat_contours if cv2.contourArea(c) > self.config.WHEAT_MIN_AREA]
        
        # Detection results obtained
        
        # Create combined mask
        mask = np.zeros((screen.shape[0], screen.shape[1]), dtype=np.uint8)
        
        # Add field template matches
        for match in field_matches:
            x, y, w, h = match['x'], match['y'], match['w'], match['h']
            cv2.rectangle(mask, (x, y), (x + w, y + h), 255, -1)
        
        # Add wheat areas
        mask = cv2.bitwise_or(mask, wheat_mask)
        
        # Find the largest contour from the combined mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None, None, None
        
        # Find the largest contour (main field)
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        # Check if the area is reasonable
        min_area = 1000
        max_area = screen.shape[0] * screen.shape[1] * 0.5
        
        if min_area < area < max_area:
            cx, cy = self.get_centroid(largest_contour)
            return cx, cy, largest_contour
        else:
            return None, None, None 