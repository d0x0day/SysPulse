"""
Settings manager handles persistence of user preferences.
Uses JSON file for simple and human-readable configuration.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List

from core.config import SETTINGS_FILE, DEFAULT_REFRESH_INTERVAL, REFRESH_FAST, REFRESH_SLOW

logger = logging.getLogger(__name__)


@dataclass
class UserSettings:
    """
    Data class representing all user-configurable settings.
    Each field maps to a toggle or option in the Settings tab.
    """
    # Visible metrics toggles
    show_cpu: bool = True
    show_memory: bool = True
    show_disk: bool = True
    show_network: bool = True
    show_temperature: bool = True
    show_processes: bool = True
    show_system_info: bool = True

    # Refresh interval in ms
    refresh_interval: int = DEFAULT_REFRESH_INTERVAL

    # Chart display options
    show_charts: bool = True
    chart_history_length: int = 60

    # Process display options
    processes_sort_by: str = "cpu_percent"  # cpu_percent, memory_percent, name, pid
    processes_sort_descending: bool = True

    # UI preferences
    confirm_kill_process: bool = True
    start_minimized: bool = False

    # Temperature unit
    temperature_unit: str = "celsius"  # celsius, fahrenheit

    def to_dict(self) -> dict:
        """Serialize settings to dictionary for JSON storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "UserSettings":
        """Deserialize settings from dictionary with safe defaults."""
        # Filter only known fields to prevent injection of unexpected keys
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered)


class SettingsManager:
    """
    Singleton manager responsible for loading, saving, and providing access
    to user settings. Ensures settings persist between application sessions.
    """

    _instance = None

    def __new__(cls):
        # Singleton pattern to ensure single settings instance across the app
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings = UserSettings()
            cls._instance._callbacks = []
        return cls._instance

    def __init__(self):
        # __new__ handles actual initialization; this prevents re-init
        pass

    @property
    def settings(self) -> UserSettings:
        """Current user settings instance."""
        return self._settings

    def load(self) -> None:
        """
        Load settings from JSON file. If file doesn't exist or is corrupt,
        falls back to default settings.
        """
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._settings = UserSettings.from_dict(data)
                logger.info("Settings loaded from %s", SETTINGS_FILE)
            else:
                logger.info("No settings file found, using defaults")
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.warning("Failed to parse settings file: %s. Using defaults.", e)
            self._settings = UserSettings()

    def save(self) -> None:
        """Persist current settings to JSON file."""
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings.to_dict(), f, indent=2)
            logger.info("Settings saved to %s", SETTINGS_FILE)
        except OSError as e:
            logger.error("Failed to save settings: %s", e)

    def subscribe(self, callback) -> None:
        """
        Subscribe to settings changes. Callback will be invoked
        whenever settings are updated.
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def unsubscribe(self, callback) -> None:
        """Remove a settings change subscriber."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def notify_change(self) -> None:
        """Notify all subscribers that settings have changed."""
        for callback in self._callbacks:
            try:
                callback()
            except Exception as e:
                logger.error("Settings change callback failed: %s", e)

    def reset_to_defaults(self) -> None:
        """Reset all settings to factory defaults."""
        self._settings = UserSettings()
        self.save()
        self.notify_change()
        logger.info("Settings reset to defaults")
