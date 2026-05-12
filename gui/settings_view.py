"""
Settings view - allows users to configure displayed metrics,
refresh intervals, and application behavior.
"""

import logging
import tkinter as tk
from tkinter import messagebox

from core.config import COLORS, REFRESH_FAST, REFRESH_NORMAL, REFRESH_SLOW
from core.settings_manager import SettingsManager

logger = logging.getLogger(__name__)


class ToggleSwitch(tk.Canvas):
    """
    Custom animated toggle switch widget.
    Provides modern ON/OFF toggle with smooth visual feedback.
    """

    def __init__(self, parent, width=44, height=24, initial=False, **kwargs):
        super().__init__(
            parent, width=width, height=height,
            bg=COLORS["bg_primary"], highlightthickness=0,
            **kwargs
        )
        self._width = width
        self._height = height
        self._active = initial
        self._callback = None
        self.bind("<Button-1>", self._toggle)
        self._draw()

    def _draw(self) -> None:
        """Render the toggle switch."""
        self.delete("all")

        # Background pill
        bg_color = COLORS["accent"] if self._active else COLORS["border"]
        radius = self._height // 2
        self.create_oval(0, 0, self._height, self._height, fill=bg_color, outline="")
        self.create_oval(
            self._width - self._height, 0, self._width, self._height,
            fill=bg_color, outline=""
        )
        self.create_rectangle(
            radius, 0, self._width - radius, self._height,
            fill=bg_color, outline=""
        )

        # Circle knob
        knob_x = self._width - radius - 2 if self._active else radius + 2
        self.create_oval(
            knob_x - radius + 4, 4, knob_x + radius - 4, self._height - 4,
            fill=COLORS["text_primary"], outline=""
        )

    def _toggle(self, event=None) -> None:
        """Toggle switch state and invoke callback."""
        self._active = not self._active
        self._draw()
        if self._callback:
            self._callback(self._active)

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, value: bool) -> None:
        self._active = value
        self._draw()

    def on_change(self, callback) -> None:
        """Register state change callback."""
        self._callback = callback


class SettingsView(tk.Frame):
    """
    Settings tab with toggle switches for metric visibility,
    refresh interval selector, and application preferences.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=COLORS["bg_primary"])

        self.settings_mgr = SettingsManager()
        self.settings = self.settings_mgr.settings

        self._build_layout()

    def _build_layout(self) -> None:
        """Construct settings UI with sections."""
        # Main container with scrollbar
        canvas = tk.Canvas(self, bg=COLORS["bg_primary"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=COLORS["bg_primary"])

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_canvas_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_canvas_resize)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Content padding
        content = tk.Frame(scrollable, bg=COLORS["bg_primary"], padx=30, pady=25)
        content.pack(fill=tk.BOTH, expand=True)

        # Header
        tk.Label(
            content, text="Settings",
            font=("Inter", 20, "bold"),
            bg=COLORS["bg_primary"], fg=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 25))

        # === Displayed Metrics Section ===
        self._add_section_header(content, "Displayed Metrics")
        metrics_frame = tk.Frame(content, bg=COLORS["bg_primary"])
        metrics_frame.pack(fill=tk.X, pady=(0, 20))

        self.toggles = {}
        metrics = [
            ("show_cpu", "CPU Usage", True),
            ("show_memory", "Memory Usage", True),
            ("show_disk", "Disk Information", True),
            ("show_network", "Network Statistics", True),
            ("show_temperature", "Temperature Sensors", True),
            ("show_processes", "Process Manager", True),
            ("show_system_info", "System Information", True),
        ]

        for attr, label, default in metrics:
            row = tk.Frame(metrics_frame, bg=COLORS["bg_primary"])
            row.pack(fill=tk.X, pady=4)

            toggle = ToggleSwitch(row, initial=getattr(self.settings, attr, default))
            toggle.pack(side=tk.RIGHT)

            tk.Label(
                row, text=label, font=("Inter", 11),
                bg=COLORS["bg_primary"], fg=COLORS["text_primary"]
            ).pack(side=tk.LEFT)

            # Store reference and bind change
            self.toggles[attr] = toggle
            toggle.on_change(lambda val, a=attr: self._on_toggle(a, val))

        # === Refresh Interval Section ===
        self._add_section_header(content, "Refresh Interval")
        interval_frame = tk.Frame(content, bg=COLORS["bg_primary"])
        interval_frame.pack(fill=tk.X, pady=(0, 20))

        self.interval_var = tk.IntVar(value=self.settings.refresh_interval)
        intervals = [
            (REFRESH_FAST, "Fast (0.5s)"),
            (REFRESH_NORMAL, "Normal (1s)"),
            (REFRESH_SLOW, "Slow (2s)"),
        ]

        for val, text in intervals:
            rb = tk.Radiobutton(
                interval_frame, text=text, variable=self.interval_var,
                value=val, command=self._on_interval_change,
                font=("Inter", 10), bg=COLORS["bg_primary"],
                fg=COLORS["text_primary"], selectcolor=COLORS["bg_secondary"],
                activebackground=COLORS["bg_primary"],
                activeforeground=COLORS["text_primary"],
            )
            rb.pack(anchor="w", pady=3)

        # === Chart Options Section ===
        self._add_section_header(content, "Chart Options")
        chart_frame = tk.Frame(content, bg=COLORS["bg_primary"])
        chart_frame.pack(fill=tk.X, pady=(0, 20))

        # Show charts toggle
        row = tk.Frame(chart_frame, bg=COLORS["bg_primary"])
        row.pack(fill=tk.X, pady=4)
        self.toggles["show_charts"] = ToggleSwitch(row, initial=self.settings.show_charts)
        self.toggles["show_charts"].pack(side=tk.RIGHT)
        self.toggles["show_charts"].on_change(lambda val: self._on_toggle("show_charts", val))
        tk.Label(
            row, text="Show Real-Time Charts", font=("Inter", 11),
            bg=COLORS["bg_primary"], fg=COLORS["text_primary"]
        ).pack(side=tk.LEFT)

        # Temperature unit
        row = tk.Frame(chart_frame, bg=COLORS["bg_primary"])
        row.pack(fill=tk.X, pady=8)
        tk.Label(
            row, text="Temperature Unit:", font=("Inter", 11),
            bg=COLORS["bg_primary"], fg=COLORS["text_primary"]
        ).pack(side=tk.LEFT)

        self.temp_unit_var = tk.StringVar(value=self.settings.temperature_unit)
        for val, text in [("celsius", "Celsius (C)"), ("fahrenheit", "Fahrenheit (F)")]:
            rb = tk.Radiobutton(
                row, text=text, variable=self.temp_unit_var,
                value=val, command=self._on_temp_unit_change,
                font=("Inter", 10), bg=COLORS["bg_primary"],
                fg=COLORS["text_primary"], selectcolor=COLORS["bg_secondary"],
                activebackground=COLORS["bg_primary"],
                activeforeground=COLORS["text_primary"],
            )
            rb.pack(side=tk.LEFT, padx=(15, 0))

        # === Behavior Section ===
        self._add_section_header(content, "Behavior")
        behavior_frame = tk.Frame(content, bg=COLORS["bg_primary"])
        behavior_frame.pack(fill=tk.X, pady=(0, 20))

        row = tk.Frame(behavior_frame, bg=COLORS["bg_primary"])
        row.pack(fill=tk.X, pady=4)
        self.toggles["confirm_kill"] = ToggleSwitch(row, initial=self.settings.confirm_kill_process)
        self.toggles["confirm_kill"].pack(side=tk.RIGHT)
        self.toggles["confirm_kill"].on_change(lambda val: self._on_toggle("confirm_kill_process", val))
        tk.Label(
            row, text="Confirm before killing process", font=("Inter", 11),
            bg=COLORS["bg_primary"], fg=COLORS["text_primary"]
        ).pack(side=tk.LEFT)

        # === Danger Zone ===
        danger_header = tk.Frame(content, bg=COLORS["danger"], height=2)
        danger_header.pack(fill=tk.X, pady=(30, 10))
        tk.Label(
            content, text="Danger Zone",
            font=("Inter", 12, "bold"),
            bg=COLORS["bg_primary"], fg=COLORS["danger"]
        ).pack(anchor="w")

        reset_btn = tk.Button(
            content, text="Reset All Settings to Default",
            command=self._confirm_reset,
            font=("Inter", 10), bg=COLORS["danger"],
            fg=COLORS["text_primary"], activebackground=COLORS["accent_hover"],
            relief=tk.FLAT, padx=20, pady=8, cursor="hand2"
        )
        reset_btn.pack(anchor="w", pady=(10, 0))

    def _add_section_header(self, parent, title: str) -> None:
        """Add a styled section header."""
        accent = tk.Frame(parent, height=2, bg=COLORS["accent"])
        accent.pack(fill=tk.X, pady=(20, 8))

        tk.Label(
            parent, text=title,
            font=("Inter", 12, "bold"),
            bg=COLORS["bg_primary"], fg=COLORS["text_primary"]
        ).pack(anchor="w")

    def _on_toggle(self, attr: str, value: bool) -> None:
        """Handle toggle switch changes."""
        setattr(self.settings, attr, value)
        self.settings_mgr.save()
        self.settings_mgr.notify_change()
        logger.debug("Setting '%s' changed to %s", attr, value)

    def _on_interval_change(self) -> None:
        """Handle refresh interval radio button change."""
        self.settings.refresh_interval = self.interval_var.get()
        self.settings_mgr.save()
        self.settings_mgr.notify_change()
        logger.info("Refresh interval changed to %d ms", self.settings.refresh_interval)

    def _on_temp_unit_change(self) -> None:
        """Handle temperature unit change."""
        self.settings.temperature_unit = self.temp_unit_var.get()
        self.settings_mgr.save()
        self.settings_mgr.notify_change()
        logger.info("Temperature unit changed to %s", self.settings.temperature_unit)

    def _confirm_reset(self) -> None:
        """Show confirmation dialog before resetting settings."""
        result = messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to default values?\n\n"
            "This action cannot be undone.",
            icon="warning"
        )
        if result:
            self.settings_mgr.reset_to_defaults()
            self._rebuild_ui()
            logger.info("Settings reset to defaults")

    def _rebuild_ui(self) -> None:
        """Rebuild the entire settings UI after reset."""
        for widget in self.winfo_children():
            widget.destroy()
        self.settings = self.settings_mgr.settings
        self.toggles = {}
        self._build_layout()
