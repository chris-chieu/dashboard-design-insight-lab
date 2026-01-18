"""
Dashboard Management Functions Package

This package contains all dashboard-related modules for creation, deletion,
deployment, management, generation (AI and manual), and design infusion.
"""

from .dashboard_manager import DashboardManager
from .ai_dashboard_generator import generate_dashboard_background
from .design_infusion import (
    extract_design_from_image, 
    generate_design_from_prompt,
    analyze_dashboard_layout,
    generate_design_with_analysis,
    refine_design_from_feedback
)
# from .manual_dashboard_config import register_manual_config_callbacks

__all__ = [
    'DashboardManager',
    'generate_dashboard_background',
    'extract_design_from_image',
    'generate_design_from_prompt',
    'analyze_dashboard_layout',
    'generate_design_with_analysis',
    'refine_design_from_feedback',
    # 'register_manual_config_callbacks'
]

