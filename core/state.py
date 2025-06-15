"""
Core state management classes for HayDay Bot

This module contains dataclasses and state management utilities
that encapsulate the bot's operational state and detection data.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np


@dataclass
class DetectionState:
    """Encapsulates detection state data"""
    screen: Optional[np.ndarray] = None
    center: Optional[Tuple[int, int]] = None
    contour: Optional[np.ndarray] = None
    wheat_coverage: float = 0
    is_wheat_ready: bool = False
    storage_full: bool = False
    storage_keyword: Optional[str] = None


@dataclass
class BotState:
    """Encapsulates bot state data"""
    running: bool = False
    detection_active: bool = True
    path_execution_active: bool = False
    silo_is_full: bool = False
    wheat_sold_this_session: bool = False 