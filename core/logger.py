"""
Centralized logging configuration.
Ensures consistent log format across all modules without duplication.
"""

import logging
import sys

from core.config import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL


def setup_logging() -> None:
    """
    Configure root logger with consistent formatting.
    Should be called once at application startup.
    """
    # Clear any existing handlers to prevent duplicate logs
    root = logging.getLogger()
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))

    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    root.addHandler(handler)

    # Reduce noise from third-party libraries
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
