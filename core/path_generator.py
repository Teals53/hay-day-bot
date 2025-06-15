"""
Path generation utilities for HayDay Bot

This module provides efficient path generation algorithms for planting
and harvesting operations using linear patterns with straight lines.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional


class PathGenerator:
    """Generates efficient paths for planting and harvesting"""
    
    @staticmethod
    def create_linear_path(cx: int, cy: int, contour: Optional[np.ndarray], path_type: str = "plant") -> List[Tuple[int, int]]:
        """Create an efficient linear path with straight lines"""
        if contour is None:
            return [(cx, cy)]
        
        # Get contour bounds
        contour_points = contour.reshape(-1, 2)
        min_x, min_y = np.min(contour_points, axis=0)
        max_x, max_y = np.max(contour_points, axis=0)
        
        path = [(cx, cy)]  # Start from center
        
        # Configure spacing based on path type
        line_spacing = 45 if path_type == "plant" else 55
        line_step = 40 if path_type == "plant" else 50
        
        # Create horizontal lines from top to bottom
        start_y = int(min_y + line_spacing // 2)
        end_y = int(max_y - line_spacing // 2)
        y_positions = list(range(start_y, end_y + 1, line_spacing))
        
        for y in y_positions:
            # Find the leftmost and rightmost points at this y level within contour
            line_points = []
            for x in range(int(min_x), int(max_x) + 1, 10):
                if cv2.pointPolygonTest(contour, (float(x), float(y)), False) >= 0:
                    line_points.append(x)
            
            if line_points:
                left_x, right_x = min(line_points), max(line_points)
                # Add points along the horizontal line
                for x in range(left_x, right_x + 1, line_step):
                    if cv2.pointPolygonTest(contour, (float(x), float(y)), False) >= 0:
                        path.append((x, y))
        
        # Add vertical coverage lines for missed areas
        x_spacing = line_spacing * 2 if path_type == "plant" else line_spacing * 3
        x_positions = list(range(int(min_x + line_spacing // 2), int(max_x), x_spacing))
        
        for x in x_positions:
            line_points = []
            for y in range(int(min_y), int(max_y) + 1, 10):
                if cv2.pointPolygonTest(contour, (float(x), float(y)), False) >= 0:
                    line_points.append(y)
            
            if line_points:
                top_y, bottom_y = min(line_points), max(line_points)
                step_size = 50 if path_type == "plant" else 60
                for y in range(top_y, bottom_y + 1, step_size):
                    if cv2.pointPolygonTest(contour, (float(x), float(y)), False) >= 0:
                        path.append((x, y))
        
        path.append((cx, cy))  # End at center
        return path 