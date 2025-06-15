"""
Core module for HayDay Bot

This package contains fundamental classes and utilities used throughout the bot.
"""

from .state import DetectionState, BotState
from .screen_capture import ScreenCapture
from .template_manager import TemplateManager
from .path_generator import PathGenerator
from .soil_detector import SoilDetector

__all__ = [
    'DetectionState',
    'BotState', 
    'ScreenCapture',
    'TemplateManager',
    'PathGenerator',
    'SoilDetector'
] 