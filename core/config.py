"""
Application configuration and constants.
Centralized config to avoid magic numbers and hardcoded values.
"""

import os
from pathlib import Path

# Application metadata
APP_NAME = "SysPulse"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Professional System Performance Monitor"

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

# Ensure assets directory exists
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Default UI settings
DEFAULT_WINDOW_WIDTH = 1100
DEFAULT_WINDOW_HEIGHT = 700
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

# Refresh intervals (milliseconds)
REFRESH_FAST = 500
REFRESH_NORMAL = 1000
REFRESH_SLOW = 2000
DEFAULT_REFRESH_INTERVAL = REFRESH_NORMAL

# Chart settings
CHART_HISTORY_LENGTH = 60  # Number of data points to keep for real-time charts
CHART_DPI = 100

# Process table settings
PROCESS_PAGE_SIZE = 50  # Number of processes per page

# Settings file path
SETTINGS_FILE = BASE_DIR / "settings.json"

# Logging configuration
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_LEVEL = os.environ.get("SYSPULSE_LOG_LEVEL", "INFO").upper()

# Color scheme (dark theme default)
COLORS = {
    "bg_primary": "#1a1a2e",
    "bg_secondary": "#16213e",
    "bg_card": "#0f3460",
    "accent": "#e94560",
    "accent_hover": "#ff6b6b",
    "text_primary": "#eaeaea",
    "text_secondary": "#a0a0a0",
    "success": "#4ecca3",
    "warning": "#f9a825",
    "danger": "#e94560",
    "info": "#3498db",
    "border": "#2a2a4a",
    "chart_bg": "#16213e",
    "chart_line_cpu": "#e94560",
    "chart_line_memory": "#3498db",
    "chart_grid": "#2a2a4a",
}
