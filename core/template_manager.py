"""
Template management for HayDay Bot

This module handles loading and detection of template images used
for UI element recognition and bot navigation.
"""

import os
import cv2
import numpy as np
from typing import Dict, Optional, Tuple
from config import BotConfig


class TemplateManager:
    """Manages template loading and detection operations"""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.templates: Dict[str, np.ndarray] = {}
        self.template_dir: Optional[str] = None
        
    def initialize(self, resolution: str) -> None:
        """Initialize template system with resolution detection"""
        self.template_dir = self._get_template_directory(resolution)
        self._load_templates()
        
    def _get_template_directory(self, resolution: str) -> str:
        """Get appropriate template directory based on resolution"""
        base_dir = os.path.dirname(os.path.dirname(__file__))  # Go up one level from core/
        
        # Normalize resolution string to lowercase
        resolution = resolution.lower()
        
        if resolution == "2k":
            template_dir = os.path.join(base_dir, self.config.TEMPLATE_2K_DIR)
        elif resolution == "1k":
            template_dir = os.path.join(base_dir, self.config.TEMPLATE_1K_DIR)
        else:
            template_dir = os.path.join(base_dir, self.config.TEMPLATE_DEFAULT_DIR)
        
        # Fallback to default if resolution-specific directory doesn't exist
        if not os.path.exists(template_dir):
            template_dir = os.path.join(base_dir, self.config.TEMPLATE_DEFAULT_DIR)
        
        return template_dir
    
    def _load_templates(self) -> int:
        """Load all template images"""
        template_files = {
            # Page detection templates
            'main': 'main.png',
            'market': 'in_market.png',
            'in_offer': 'in_offer.png',
            'paper_page': 'paper_page.png',
            
            # UI element templates
            'silo': 'silo.png',
            'close': 'close.png',
            'collect': 'collect.png',
            'sold': 'sold.png',
            'loading': 'loading.png',
            'click': 'click.png',
            
            # Market-related templates
            'market_button': 'market.png',
            'offer': 'offer.png',
            'wheat_market': 'wheat_market.png',
            'newspaper': 'newspaper.png',
            'new_offer': 'new_offer.png',
            'insert_button': 'insert_button.png',
            
            # Button state templates
            'arrow_right_active': 'arrow_right_active.png',
            'arrow_right_deactive': 'arrow_right_deactive.png',
            'plus_button_active': 'plus_button_active.png',
            'plus_button_deactive': 'plus_button_deactive.png',
            
            # Advertisement templates
            'check_paper': 'check_paper.png',
            'paper_cooldown': 'paper_cooldown.png',
            'paper_button': 'paper_button.png',
            'paper_create': 'paper_create.png'
        }
        
        loaded_count = 0
        for name, filename in template_files.items():
            template_path = os.path.join(self.template_dir, filename)
            if os.path.exists(template_path):
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                if template is not None:
                    self.templates[name] = template
                    loaded_count += 1
        
        return loaded_count
    
    def find_template(self, screen: np.ndarray, template_name: str, threshold: float = 0.7) -> Tuple[Optional[int], Optional[int], float]:
        """Enhanced template matching with color and grayscale fallback"""
        if template_name not in self.templates:
            return None, None, 0
        
        template = self.templates[template_name]
        
        def _match_template(img: np.ndarray, tmpl: np.ndarray, method=cv2.TM_CCOEFF_NORMED) -> Tuple[Optional[int], Optional[int], float]:
            """Helper function to perform template matching"""
            result = cv2.matchTemplate(img, tmpl, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                h, w = tmpl.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return center_x, center_y, max_val
            return None, None, max_val
        
        # Try color matching first
        result = _match_template(screen, template)
        if result[0] is not None:
            return result
        
        # Try grayscale matching as backup
        screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        return _match_template(screen_gray, template_gray) 