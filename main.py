"""
SysPulse - Professional System Performance Monitor

Entry point for the application. Initializes logging,
loads settings, and launches the main GUI window.

Usage:
    python -m syspulse
    python main.py

Environment Variables:
    SYSPULSE_LOG_LEVEL: Set logging level (DEBUG, INFO, WARNING, ERROR)
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path for clean imports when running directly
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root.parent))

from core.logger import setup_logging
from core.config import APP_NAME, APP_VERSION
from gui.app import SysPulseApp

logger = logging.getLogger(__name__)


def main() -> int:
    """
    Application entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    setup_logging()

    try:
        logger.info("Starting %s v%s", APP_NAME, APP_VERSION)

        app = SysPulseApp()
        app.run()

        return 0

    except ImportError as e:
        logger.critical(
            "Missing required dependency: %s. "
            "Install with: pip install -r requirements.txt", e
        )
        return 1

    except Exception as e:
        logger.critical("Fatal error: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
