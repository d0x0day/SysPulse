"""
Reusable custom widgets used across the application.
Provides metric cards, progress bars, and styled containers.
"""

import tkinter as tk
from tkinter import ttk

from core.config import COLORS


class MetricCard(tk.Frame):
    """
    A card widget displaying a metric with a title, value, and optional unit.
    Used on the dashboard for CPU, Memory, etc.
    """

    def __init__(
        self,
        parent,
        title: str,
        value: str = "--",
        unit: str = "",
        color: str = COLORS["accent"],
        **kwargs
    ):
        super().__init__(parent, **kwargs)

        self.config(bg=COLORS["bg_card"], padx=15, pady=12)

        # Title label
        self.title_label = tk.Label(
            self,
            text=title.upper(),
            font=("Inter", 9, "bold"),
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"],
        )
        self.title_label.pack(anchor="w")

        # Value container
        value_frame = tk.Frame(self, bg=COLORS["bg_card"])
        value_frame.pack(anchor="w", pady=(5, 0))

        self.value_label = tk.Label(
            value_frame,
            text=value,
            font=("Inter", 22, "bold"),
            bg=COLORS["bg_card"],
            fg=color,
        )
        self.value_label.pack(side=tk.LEFT)

        if unit:
            self.unit_label = tk.Label(
                value_frame,
                text=unit,
                font=("Inter", 10),
                bg=COLORS["bg_card"],
                fg=COLORS["text_secondary"],
                padx=5,
            )
            self.unit_label.pack(side=tk.LEFT, pady=(6, 0))

    def update_value(self, value: str, color: str = None) -> None:
        """Update the displayed value and optionally the color."""
        self.value_label.config(text=value)
        if color:
            self.value_label.config(fg=color)


class ProgressBar(tk.Canvas):
    """
    Custom horizontal progress bar with rounded corners.
    More visually appealing than standard ttk.Progressbar.
    """

    def __init__(self, parent, width=200, height=8, **kwargs):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=COLORS["bg_secondary"],
            highlightthickness=0,
            **kwargs,
        )
        self._width = width
        self._height = height
        self._progress = 0
        self._color = COLORS["success"]
        self._draw()

    def _draw(self) -> None:
        """Render the progress bar with current progress value."""
        self.delete("all")

        # Background bar
        self.create_rectangle(
            0, 0, self._width, self._height,
            fill=COLORS["border"], outline="", tags="bg"
        )

        # Progress fill
        fill_width = (self._progress / 100.0) * self._width
        if fill_width > 0:
            self.create_rectangle(
                0, 0, fill_width, self._height,
                fill=self._color, outline="", tags="fill"
            )

    def set_progress(self, value: float, color: str = None) -> None:
        """
        Update progress value (0-100) and optionally the bar color.
        Color automatically changes based on thresholds if not specified.
        """
        self._progress = max(0, min(100, value))

        if color:
            self._color = color
        else:
            # Auto-color based on thresholds
            if self._progress >= 90:
                self._color = COLORS["danger"]
            elif self._progress >= 70:
                self._color = COLORS["warning"]
            else:
                self._color = COLORS["success"]

        self._draw()


class SectionHeader(tk.Frame):
    """Header with accent line for section separation."""

    def __init__(self, parent, title: str, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=COLORS["bg_primary"])

        accent = tk.Frame(self, height=2, bg=COLORS["accent"])
        accent.pack(fill=tk.X, pady=(0, 8))

        label = tk.Label(
            self,
            text=title,
            font=("Inter", 12, "bold"),
            bg=COLORS["bg_primary"],
            fg=COLORS["text_primary"],
        )
        label.pack(anchor="w")


class ScrollableFrame(tk.Frame):
    """
    Scrollable frame container with auto-hiding scrollbar.
    Useful for content that may exceed window height.
    """

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.canvas = tk.Canvas(self, bg=COLORS["bg_primary"], highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=COLORS["bg_primary"])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self._on_scroll)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind("<Destroy>", self._on_destroy)

        # Track canvas resize
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_scroll(self, *args):
        """Show scrollbar only when needed."""
        self.scrollbar.set(*args)
        if float(args[0]) > 0 or float(args[1]) < 1:
            self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            self.scrollbar.pack_forget()

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_canvas_configure(self, event):
        """Ensure inner frame matches canvas width."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_destroy(self, _event):
        """Clean up bindings when widget is destroyed."""
        self.canvas.unbind_all("<MouseWheel>")
