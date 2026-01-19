"""
Pages package for Intelligent Embedded Dashboard

This package contains all page modules for the dashboard application.
"""

from .new_dashboard.new_dashboard_page import get_new_dashboard_layout, register_new_dashboard_callbacks
from .existing_dashboard.existing_dashboard_page import get_existing_dashboard_layout, register_existing_dashboard_callbacks

__all__ = [
    'get_new_dashboard_layout',
    'register_new_dashboard_callbacks',
    'get_existing_dashboard_layout',
    'register_existing_dashboard_callbacks'
]

