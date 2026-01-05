"""
Dashboard Management Functions Package

This package contains all dashboard-related modules for creation, deletion,
deployment, management, generation (AI and manual), and design infusion.
"""

from .dashboard_manager import DashboardManager
from .ai_dashboard_generator import generate_dashboard_background
from .design_infusion import extract_design_from_image, generate_design_from_prompt
from .manual_dashboard_config import register_manual_config_callbacks

__all__ = [
    'DashboardManager',
    'generate_dashboard_background',
    'extract_design_from_image',
    'generate_design_from_prompt',
    'register_manual_config_callbacks'
]

