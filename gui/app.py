"""
Main application window.
Manages navigation between views and coordinates data updates.
"""

import logging
import tkinter as tk
from tkinter import ttk

from core.config import (
    APP_NAME, APP_VERSION, COLORS,
    DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
)
from core.settings_manager import SettingsManager
from gui.dashboard_view import DashboardView
from gui.processes_view import ProcessesView
from gui.settings_view import SettingsView
from gui.system_info_view import SystemInfoView

logger = logging.getLogger(__name__)


class SysPulseApp:
    """
    Main application class managing the window, navigation,
    view switching, and periodic data refresh.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}")
        self.root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.root.config(bg=COLORS["bg_primary"])

        # Initialize settings
        self.settings_mgr = SettingsManager()
        self.settings_mgr.load()
        self.settings = self.settings_mgr.settings

        # Data collector
        from services.system_collector import SystemCollector
        self.collector = SystemCollector(history_length=self.settings.chart_history_length)
        self.collector.start()
        logger.info("System collector thread started")

        # View references
        self._views = {}
        self._nav_buttons = {}
        self._current_view = None

        self._build_ui()

        # Start UI update loop
        self._schedule_update()

    def _build_ui(self) -> None:
        """Construct the main application layout with sidebar navigation."""
        # Main container
        main_container = tk.Frame(self.root, bg=COLORS["bg_primary"])
        main_container.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        sidebar = tk.Frame(
            main_container, bg=COLORS["bg_secondary"],
            width=200, padx=0, pady=0
        )
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # App title in sidebar
        title_frame = tk.Frame(sidebar, bg=COLORS["bg_secondary"], padx=20, pady=25)
        title_frame.pack(fill=tk.X)

        # Accent line
        tk.Frame(title_frame, height=3, bg=COLORS["accent"]).pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            title_frame, text=APP_NAME,
            font=("Inter", 18, "bold"),
            bg=COLORS["bg_secondary"], fg=COLORS["text_primary"]
        ).pack(anchor="w")

        tk.Label(
            title_frame, text=f"v{APP_VERSION}",
            font=("Inter", 9),
            bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"]
        ).pack(anchor="w")

        # Navigation buttons
        nav_frame = tk.Frame(sidebar, bg=COLORS["bg_secondary"], padx=15, pady=10)
        nav_frame.pack(fill=tk.BOTH, expand=True)

        nav_items = [
            ("dashboard", "Dashboard", self._show_dashboard),
            ("processes", "Processes", self._show_processes),
            ("system", "System Info", self._show_system_info),
            ("settings", "Settings", self._show_settings),
        ]

        for nav_id, label, command in nav_items:
            btn = tk.Button(
                nav_frame, text=label, command=lambda cid=nav_id, cmd=command: self._switch_view(cid, cmd),
                font=("Inter", 11), bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"],
                activebackground=COLORS["bg_card"], activeforeground=COLORS["text_primary"],
                relief=tk.FLAT, anchor="w", padx=15, pady=10, cursor="hand2",
                width=20
            )
            btn.pack(fill=tk.X, pady=2)
            self._nav_buttons[nav_id] = btn

        # Content area
        self.content_frame = tk.Frame(main_container, bg=COLORS["bg_primary"])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Initialize views
        self._views["dashboard"] = DashboardView(self.content_frame, self.collector)
        self._views["processes"] = ProcessesView(self.content_frame, self.collector)
        self._views["system"] = SystemInfoView(self.content_frame, self.collector)
        self._views["settings"] = SettingsView(self.content_frame)

        # Show dashboard by default
        self._switch_view("dashboard", self._show_dashboard)

        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _switch_view(self, view_id: str, command) -> None:
        """Switch between views and update navigation styling."""
        # Hide all views
        for view in self._views.values():
            view.pack_forget()

        # Show selected view
        command()
        self._current_view = view_id

        # Update nav button styles
        for nav_id, btn in self._nav_buttons.items():
            if nav_id == view_id:
                btn.config(
                    bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                    font=("Inter", 11, "bold")
                )
            else:
                btn.config(
                    bg=COLORS["bg_secondary"], fg=COLORS["text_secondary"],
                    font=("Inter", 11)
                )

    def _show_dashboard(self) -> None:
        self._views["dashboard"].pack(fill=tk.BOTH, expand=True)

    def _show_processes(self) -> None:
        self._views["processes"].pack(fill=tk.BOTH, expand=True)

    def _show_system_info(self) -> None:
        self._views["system"].pack(fill=tk.BOTH, expand=True)

    def _show_settings(self) -> None:
        self._views["settings"].pack(fill=tk.BOTH, expand=True)

    def _schedule_update(self) -> None:
        """
        Schedule periodic UI updates based on settings refresh interval.
        Uses the Tkinter after() method for non-blocking periodic execution.
        """
        # Update current view
        if self._current_view and self._current_view in self._views:
            try:
                self._views[self._current_view].update_display()
            except Exception as e:
                logger.error("View update error: %s", e)

        # Schedule next update
        interval = self.settings.refresh_interval
        self.root.after(interval, self._schedule_update)

    def _on_close(self) -> None:
        """Graceful shutdown: stop collector and close window."""
        logger.info("Shutting down %s", APP_NAME)
        self.collector.stop()
        self.collector.join(timeout=2.0)
        self.root.destroy()

    def run(self) -> None:
        """Start the application main loop."""
        logger.info("%s v%s started", APP_NAME, APP_VERSION)
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            self._on_close()
