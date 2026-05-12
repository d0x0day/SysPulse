"""
System Information view.
Displays static and dynamic system details: OS, CPU specs,
memory totals, network interfaces, and boot time.
"""

import logging
import platform
import socket
from datetime import datetime

import psutil
import tkinter as tk

from core.config import COLORS
from gui.widgets import SectionHeader

logger = logging.getLogger(__name__)


class SystemInfoView(tk.Frame):
    """
    System information tab showing hardware and OS details.
    Combines static info (collected once) with dynamic uptime.
    """

    def __init__(self, parent, collector, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=COLORS["bg_primary"])

        self.collector = collector
        self._static_info = self._collect_static_info()

        self._build_layout()

    def _collect_static_info(self) -> dict:
        """Gather static system information once at initialization."""
        info = {
            "os": f"{platform.system()} {platform.release()}",
            "os_version": platform.version(),
            "hostname": socket.gethostname(),
            "architecture": platform.machine(),
            "processor": platform.processor() or "Unknown",
            "cpu_cores_physical": psutil.cpu_count(logical=False) or 0,
            "cpu_cores_logical": psutil.cpu_count(logical=True) or 0,
            "python_version": platform.python_version(),
        }

        # Memory info
        mem = psutil.virtual_memory()
        info["memory_total_gb"] = round(mem.total / (1024 ** 3), 2)

        # Disk info
        try:
            disk = psutil.disk_usage("/")
            info["disk_total_gb"] = round(disk.total / (1024 ** 3), 2)
        except Exception:
            info["disk_total_gb"] = 0

        # Network interfaces
        try:
            interfaces = []
            for name, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        interfaces.append(f"{name}: {addr.address}")
            info["network_interfaces"] = interfaces
        except Exception:
            info["network_interfaces"] = []

        return info

    def _build_layout(self) -> None:
        """Build the system info UI."""
        canvas = tk.Canvas(self, bg=COLORS["bg_primary"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=COLORS["bg_primary"])

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def on_resize(event):
            canvas.itemconfig(canvas_window, width=event.width)
        canvas.bind("<Configure>", on_resize)
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        content = tk.Frame(scrollable, bg=COLORS["bg_primary"], padx=30, pady=25)
        content.pack(fill=tk.BOTH, expand=True)

        # Header
        tk.Label(
            content, text="System Information",
            font=("Inter", 20, "bold"),
            bg=COLORS["bg_primary"], fg=COLORS["text_primary"]
        ).pack(anchor="w", pady=(0, 25))

        # OS Section
        SectionHeader(content, "Operating System").pack(fill=tk.X, pady=(0, 10))
        self._add_info_row(content, "OS", self._static_info["os"])
        self._add_info_row(content, "Version", self._static_info["os_version"])
        self._add_info_row(content, "Hostname", self._static_info["hostname"])
        self._add_info_row(content, "Architecture", self._static_info["architecture"])

        # CPU Section
        SectionHeader(content, "Processor").pack(fill=tk.X, pady=(15, 10))
        self._add_info_row(content, "Model", self._static_info["processor"])
        self._add_info_row(content, "Physical Cores", str(self._static_info["cpu_cores_physical"]))
        self._add_info_row(content, "Logical Cores", str(self._static_info["cpu_cores_logical"]))

        # Dynamic CPU freq
        freq_frame = tk.Frame(content, bg=COLORS["bg_primary"])
        freq_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(
            freq_frame, text="Current Frequency:",
            font=("Inter", 10), bg=COLORS["bg_primary"], fg=COLORS["text_secondary"], width=20, anchor="w"
        ).pack(side=tk.LEFT)
        self.freq_label = tk.Label(
            freq_frame, text="-- MHz",
            font=("Inter", 10, "bold"), bg=COLORS["bg_primary"], fg=COLORS["accent"]
        )
        self.freq_label.pack(side=tk.LEFT)

        # Memory Section
        SectionHeader(content, "Memory").pack(fill=tk.X, pady=(15, 10))
        self._add_info_row(content, "Total Memory", f"{self._static_info['memory_total_gb']} GB")

        # Disk Section
        SectionHeader(content, "Storage").pack(fill=tk.X, pady=(15, 10))
        self._add_info_row(content, "Total Disk Space", f"{self._static_info['disk_total_gb']} GB")

        # Network Section
        SectionHeader(content, "Network Interfaces").pack(fill=tk.X, pady=(15, 10))
        if self._static_info["network_interfaces"]:
            for iface in self._static_info["network_interfaces"]:
                self._add_info_row(content, "", iface)
        else:
            self._add_info_row(content, "", "No network interfaces detected")

        # Runtime Section
        SectionHeader(content, "Runtime").pack(fill=tk.X, pady=(15, 10))
        self._add_info_row(content, "Python Version", self._static_info["python_version"])

        # Dynamic uptime
        uptime_frame = tk.Frame(content, bg=COLORS["bg_primary"])
        uptime_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(
            uptime_frame, text="Uptime:",
            font=("Inter", 10), bg=COLORS["bg_primary"], fg=COLORS["text_secondary"], width=20, anchor="w"
        ).pack(side=tk.LEFT)
        self.uptime_label = tk.Label(
            uptime_frame, text="--",
            font=("Inter", 10, "bold"), bg=COLORS["bg_primary"], fg=COLORS["accent"]
        )
        self.uptime_label.pack(side=tk.LEFT)

        # Boot time
        boot_frame = tk.Frame(content, bg=COLORS["bg_primary"])
        boot_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(
            boot_frame, text="Boot Time:",
            font=("Inter", 10), bg=COLORS["bg_primary"], fg=COLORS["text_secondary"], width=20, anchor="w"
        ).pack(side=tk.LEFT)
        boot_time = datetime.fromtimestamp(self._static_info.get("boot_time", psutil.boot_time()))
        tk.Label(
            boot_frame, text=boot_time.strftime("%Y-%m-%d %H:%M:%S"),
            font=("Inter", 10, "bold"), bg=COLORS["bg_primary"], fg=COLORS["text_primary"]
        ).pack(side=tk.LEFT)

    def _add_info_row(self, parent, label: str, value: str) -> None:
        """Add a labeled info row."""
        frame = tk.Frame(parent, bg=COLORS["bg_primary"])
        frame.pack(fill=tk.X, pady=(0, 5))

        if label:
            tk.Label(
                frame, text=label + ":",
                font=("Inter", 10), bg=COLORS["bg_primary"],
                fg=COLORS["text_secondary"], width=20, anchor="w"
            ).pack(side=tk.LEFT)

        tk.Label(
            frame, text=value,
            font=("Inter", 10, "bold"), bg=COLORS["bg_primary"],
            fg=COLORS["text_primary"]
        ).pack(side=tk.LEFT)

    def update_display(self) -> None:
        """Update dynamic fields (uptime, CPU frequency)."""
        snapshot = self.collector.latest
        if not snapshot:
            return

        # Update CPU frequency
        if snapshot.cpu_freq_mhz > 0:
            self.freq_label.config(text=f"{snapshot.cpu_freq_mhz:.0f} MHz")

        # Update uptime
        uptime = snapshot.uptime_seconds
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        seconds = int(uptime % 60)
        self.uptime_label.config(text=f"{hours}h {minutes}m {seconds}s")
