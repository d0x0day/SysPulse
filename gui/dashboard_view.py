"""
Dashboard view - the main monitoring screen.
Displays metric cards, progress bars, and real-time matplotlib charts.
"""

import logging
import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.config import COLORS
from core.settings_manager import SettingsManager
from gui.widgets import MetricCard, ProgressBar, SectionHeader, ScrollableFrame

logger = logging.getLogger(__name__)


class DashboardView(tk.Frame):
    """
    Primary dashboard showing system overview with cards and charts.
    Updates in real-time based on collector data.
    """

    def __init__(self, parent, collector, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=COLORS["bg_primary"])

        self.collector = collector
        self.settings = SettingsManager().settings

        self._chart_figures = []
        self._chart_canvases = []

        self._build_layout()

    def _build_layout(self) -> None:
        """Construct the dashboard UI components."""
        # Main scrollable container
        scroll_container = ScrollableFrame(self)
        scroll_container.pack(fill=tk.BOTH, expand=True)
        container = scroll_container.scrollable_frame

        # Add padding inside scrollable frame
        inner_pad = tk.Frame(container, bg=COLORS["bg_primary"])
        inner_pad.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        container = inner_pad

        # Header
        header = tk.Label(
            container,
            text="Dashboard",
            font=("Inter", 20, "bold"),
            bg=COLORS["bg_primary"],
            fg=COLORS["text_primary"],
        )
        header.pack(anchor="w", pady=(0, 20))

        # Metric cards row
        cards_frame = tk.Frame(container, bg=COLORS["bg_primary"])
        cards_frame.pack(fill=tk.X, pady=(0, 20))

        # Configure grid weights for responsive layout
        for i in range(4):
            cards_frame.columnconfigure(i, weight=1)

        self.cpu_card = MetricCard(
            cards_frame, title="CPU Usage", value="--", unit="%",
            color=COLORS["accent"]
        )
        self.cpu_card.grid(row=0, column=0, padx=(0, 10), sticky="nsew")

        self.mem_card = MetricCard(
            cards_frame, title="Memory", value="--", unit="%",
            color=COLORS["info"]
        )
        self.mem_card.grid(row=0, column=1, padx=(5, 5), sticky="nsew")

        self.disk_card = MetricCard(
            cards_frame, title="Disk Read", value="--", unit="MB",
            color=COLORS["success"]
        )
        self.disk_card.grid(row=0, column=2, padx=(5, 5), sticky="nsew")

        self.net_card = MetricCard(
            cards_frame, title="Network Down", value="--", unit="MB/s",
            color=COLORS["warning"]
        )
        self.net_card.grid(row=0, column=3, padx=(10, 0), sticky="nsew")

        # Progress bars section
        progress_section = tk.Frame(container, bg=COLORS["bg_primary"])
        progress_section.pack(fill=tk.X, pady=(0, 20))

        # CPU Progress
        cpu_progress_frame = tk.Frame(progress_section, bg=COLORS["bg_primary"])
        cpu_progress_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            cpu_progress_frame, text="CPU", font=("Inter", 10, "bold"),
            bg=COLORS["bg_primary"], fg=COLORS["text_primary"], width=8, anchor="w"
        ).pack(side=tk.LEFT)

        self.cpu_progress = ProgressBar(cpu_progress_frame, height=10)
        self.cpu_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        # Memory Progress
        mem_progress_frame = tk.Frame(progress_section, bg=COLORS["bg_primary"])
        mem_progress_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            mem_progress_frame, text="RAM", font=("Inter", 10, "bold"),
            bg=COLORS["bg_primary"], fg=COLORS["text_primary"], width=8, anchor="w"
        ).pack(side=tk.LEFT)

        self.mem_progress = ProgressBar(mem_progress_frame, height=10)
        self.mem_progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))

        # Charts section
        charts_section = tk.Frame(container, bg=COLORS["bg_primary"])
        charts_section.pack(fill=tk.BOTH, expand=True)
        charts_section.columnconfigure(0, weight=1)
        charts_section.columnconfigure(1, weight=1)
        charts_section.rowconfigure(1, weight=1)

        SectionHeader(charts_section, "Real-Time Charts").grid(
            row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10)
        )

        # CPU Chart
        cpu_chart_frame = tk.Frame(charts_section, bg=COLORS["bg_secondary"], padx=10, pady=10)
        cpu_chart_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        self.cpu_fig = Figure(figsize=(5, 2.5), dpi=100, facecolor=COLORS["bg_secondary"])
        self.cpu_fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.2)
        self.cpu_ax = self.cpu_fig.add_subplot(111)
        self.cpu_ax.set_facecolor(COLORS["bg_secondary"])
        self.cpu_ax.set_title("CPU Usage %", color=COLORS["text_primary"], fontsize=10)
        self.cpu_ax.tick_params(colors=COLORS["text_secondary"], labelsize=8)
        self.cpu_ax.set_ylim(0, 100)
        self.cpu_ax.grid(True, color=COLORS["chart_grid"], alpha=0.3)
        self.cpu_line, = self.cpu_ax.plot([], [], color=COLORS["chart_line_cpu"], linewidth=1.5)

        self.cpu_chart_canvas = FigureCanvasTkAgg(self.cpu_fig, master=cpu_chart_frame)
        self.cpu_chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Memory Chart
        mem_chart_frame = tk.Frame(charts_section, bg=COLORS["bg_secondary"], padx=10, pady=10)
        mem_chart_frame.grid(row=1, column=1, sticky="nsew", padx=(10, 0))

        self.mem_fig = Figure(figsize=(5, 2.5), dpi=100, facecolor=COLORS["bg_secondary"])
        self.mem_fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.2)
        self.mem_ax = self.mem_fig.add_subplot(111)
        self.mem_ax.set_facecolor(COLORS["bg_secondary"])
        self.mem_ax.set_title("Memory Usage %", color=COLORS["text_primary"], fontsize=10)
        self.mem_ax.tick_params(colors=COLORS["text_secondary"], labelsize=8)
        self.mem_ax.set_ylim(0, 100)
        self.mem_ax.grid(True, color=COLORS["chart_grid"], alpha=0.3)
        self.mem_line, = self.mem_ax.plot([], [], color=COLORS["chart_line_memory"], linewidth=1.5)

        self.mem_chart_canvas = FigureCanvasTkAgg(self.mem_fig, master=mem_chart_frame)
        self.mem_chart_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Disk partitions section
        self.disk_section = tk.Frame(container, bg=COLORS["bg_primary"])
        self.disk_section.pack(fill=tk.X, pady=(20, 0))

        SectionHeader(self.disk_section, "Disk Partitions").pack(fill=tk.X)

        # Disk table headers
        disk_table_frame = tk.Frame(self.disk_section, bg=COLORS["bg_primary"])
        disk_table_frame.pack(fill=tk.X, pady=(10, 0))

        headers = ["Device", "Mount", "Type", "Total", "Used", "Free", "Usage"]
        widths = [15, 15, 8, 10, 10, 10, 20]
        for i, (header, width) in enumerate(zip(headers, widths)):
            tk.Label(
                disk_table_frame, text=header, font=("Inter", 9, "bold"),
                bg=COLORS["bg_primary"], fg=COLORS["text_secondary"], width=width, anchor="w"
            ).grid(row=0, column=i, padx=(0, 5))

        self.disk_rows_frame = tk.Frame(self.disk_section, bg=COLORS["bg_primary"])
        self.disk_rows_frame.pack(fill=tk.X)

        # Temperature section
        self.temp_section = tk.Frame(container, bg=COLORS["bg_primary"])
        self.temp_section.pack(fill=tk.X, pady=(20, 0))

        SectionHeader(self.temp_section, "Temperatures").pack(fill=tk.X)

        self.temp_labels_frame = tk.Frame(self.temp_section, bg=COLORS["bg_primary"])
        self.temp_labels_frame.pack(fill=tk.X, pady=(10, 0))

    def update_display(self) -> None:
        """
        Refresh all dashboard widgets with latest collector data.
        Called periodically by the main application loop.
        """
        snapshot = self.collector.latest
        if not snapshot:
            return

        # Update metric cards
        self.cpu_card.update_value(f"{snapshot.cpu_percent:.1f}")
        self.mem_card.update_value(f"{snapshot.memory_percent:.1f}")
        self.disk_card.update_value(f"{snapshot.disk_total_read_mb:.1f}")
        self.net_card.update_value(f"{snapshot.net_recv_speed:.2f}")

        # Update progress bars
        self.cpu_progress.set_progress(snapshot.cpu_percent)
        self.mem_progress.set_progress(snapshot.memory_percent)

        # Update charts
        cpu_hist = list(self.collector.cpu_history)
        mem_hist = list(self.collector.memory_history)

        if cpu_hist:
            x = list(range(len(cpu_hist)))
            self.cpu_line.set_data(x, cpu_hist)
            self.cpu_ax.set_xlim(0, max(len(cpu_hist), self.collector._history_length))
            self.cpu_ax.relim()
            self.cpu_ax.set_ylim(0, 100)
            self.cpu_chart_canvas.draw_idle()

        if mem_hist:
            x = list(range(len(mem_hist)))
            self.mem_line.set_data(x, mem_hist)
            self.mem_ax.set_xlim(0, max(len(mem_hist), self.collector._history_length))
            self.mem_ax.relim()
            self.mem_ax.set_ylim(0, 100)
            self.mem_chart_canvas.draw_idle()

        # Update disk partitions
        self._update_disk_table(snapshot.disk_partitions)

        # Update temperatures
        self._update_temperatures(snapshot.temperatures)

    def _update_disk_table(self, partitions: list) -> None:
        """Refresh the disk partitions table."""
        # Check if we need to rebuild or just update
        existing_rows = len(self.disk_rows_frame.winfo_children())
        has_data = bool(partitions)
        
        # If data availability changed, clear and rebuild structure
        if has_data != (existing_rows > 0 and not isinstance(self.disk_rows_frame.winfo_children()[0], tk.Label)):
            for widget in self.disk_rows_frame.winfo_children():
                widget.destroy()
            existing_rows = 0

        if not partitions:
            if existing_rows == 0:
                tk.Label(
                    self.disk_rows_frame, text="No disk information available",
                    font=("Inter", 9), bg=COLORS["bg_primary"], fg=COLORS["text_secondary"]
                ).pack(anchor="w", pady=5)
            return

        # Clear placeholder if it exists
        if existing_rows == 1 and isinstance(self.disk_rows_frame.winfo_children()[0], tk.Label):
            if self.disk_rows_frame.winfo_children()[0].cget("text") == "No disk information available":
                for widget in self.disk_rows_frame.winfo_children():
                    widget.destroy()
                existing_rows = 0

        widths = [15, 15, 8, 10, 10, 10, 20]
        num_cols = len(widths)

        for row_idx, part in enumerate(partitions):
            values = [
                part.get("device", ""),
                part.get("mountpoint", ""),
                part.get("fstype", ""),
                f"{part.get('total_gb', 0):.1f} GB",
                f"{part.get('used_gb', 0):.1f} GB",
                f"{part.get('free_gb', 0):.1f} GB",
                f"{part.get('percent', 0)}%",
            ]

            # Reuse existing row widgets if available
            row_widgets = []
            if row_idx < existing_rows:
                # Get all widgets in this row (they were packed in grid)
                # We need to find widgets by grid position
                for widget in self.disk_rows_frame.winfo_children():
                    if int(widget.grid_info().get("row", -1)) == row_idx:
                        row_widgets.append(widget)
                row_widgets.sort(key=lambda w: int(w.grid_info().get("column", 0)))
            else:
                # Create new labels for this row
                for col_idx in range(num_cols):
                    lbl = tk.Label(
                        self.disk_rows_frame, text="", font=("Inter", 9),
                        bg=COLORS["bg_primary"], fg=COLORS["text_primary"],
                        width=widths[col_idx], anchor="w"
                    )
                    lbl.grid(row=row_idx, column=col_idx, padx=(0, 5), pady=2)
                    row_widgets.append(lbl)

                # Usage bar (canvas)
                bar_width = 100
                bar = tk.Canvas(
                    self.disk_rows_frame, width=bar_width, height=6,
                    bg=COLORS["border"], highlightthickness=0
                )
                bar.grid(row=row_idx, column=num_cols - 1, padx=(0, 5), pady=2)
                row_widgets.append(bar)

            # Update values
            for col_idx, value in enumerate(values):
                if col_idx < len(row_widgets):
                    row_widgets[col_idx].config(text=value)

            # Update progress bar
            bar = row_widgets[-1] if row_widgets else None
            if isinstance(bar, tk.Canvas):
                bar.delete("all")
                pct = part.get("percent", 0)
                fill_w = (pct / 100) * 100
                color = COLORS["success"] if pct < 70 else COLORS["warning"] if pct < 90 else COLORS["danger"]
                if fill_w > 0:
                    bar.create_rectangle(0, 0, fill_w, 6, fill=color, outline="")

        # Remove excess rows
        for widget in self.disk_rows_frame.winfo_children():
            row = int(widget.grid_info().get("row", -1))
            if row >= len(partitions):
                widget.destroy()

    def _update_temperatures(self, temperatures: dict) -> None:
        """Refresh temperature display."""
        existing_frames = [w for w in self.temp_labels_frame.winfo_children() if isinstance(w, tk.Frame)]
        has_data = bool(temperatures)

        # Show placeholder if no data
        if not temperatures:
            if not existing_frames:
                # Check if placeholder already exists
                has_placeholder = False
                for w in self.temp_labels_frame.winfo_children():
                    if isinstance(w, tk.Label) and w.cget("text") == "No temperature sensors detected":
                        has_placeholder = True
                        break
                if not has_placeholder:
                    for w in self.temp_labels_frame.winfo_children():
                        w.destroy()
                    tk.Label(
                        self.temp_labels_frame,
                        text="No temperature sensors detected",
                        font=("Inter", 9), bg=COLORS["bg_primary"], fg=COLORS["text_secondary"]
                    ).pack(anchor="w", pady=5)
            else:
                for w in self.temp_labels_frame.winfo_children():
                    w.destroy()
                tk.Label(
                    self.temp_labels_frame,
                    text="No temperature sensors detected",
                    font=("Inter", 9), bg=COLORS["bg_primary"], fg=COLORS["text_secondary"]
                ).pack(anchor="w", pady=5)
            return

        # Remove placeholder if exists
        for w in list(self.temp_labels_frame.winfo_children()):
            if isinstance(w, tk.Label):
                w.destroy()

        temp_items = list(temperatures.items())

        for idx, (name, temp) in enumerate(temp_items):
            if idx < len(existing_frames):
                frame = existing_frames[idx]
                # Update existing frame
                labels = [w for w in frame.winfo_children() if isinstance(w, tk.Label)]
                if len(labels) >= 2:
                    labels[0].config(text=name)
                    
                    if temp >= 80:
                        color = COLORS["danger"]
                    elif temp >= 60:
                        color = COLORS["warning"]
                    else:
                        color = COLORS["success"]
                    
                    labels[1].config(text=f"{temp}°C", fg=color)
            else:
                frame = tk.Frame(self.temp_labels_frame, bg=COLORS["bg_primary"])
                frame.pack(side=tk.LEFT, padx=(0, 20), pady=5)

                if temp >= 80:
                    color = COLORS["danger"]
                elif temp >= 60:
                    color = COLORS["warning"]
                else:
                    color = COLORS["success"]

                tk.Label(
                    frame, text=name, font=("Inter", 8),
                    bg=COLORS["bg_primary"], fg=COLORS["text_secondary"]
                ).pack(anchor="w")

                tk.Label(
                    frame, text=f"{temp}°C", font=("Inter", 12, "bold"),
                    bg=COLORS["bg_primary"], fg=color
                ).pack(anchor="w")

        # Remove excess frames
        for idx, frame in enumerate(existing_frames):
            if idx >= len(temp_items):
                frame.destroy()
