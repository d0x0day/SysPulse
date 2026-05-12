"""
System data collection service.
Runs in a separate thread to avoid blocking the GUI main loop.
Collects CPU, memory, disk, network, temperature, and process data.
"""

import logging
import platform
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class SystemSnapshot:
    """Immutable snapshot of system metrics at a point in time."""
    timestamp: float = 0.0
    cpu_percent: float = 0.0
    cpu_count_physical: int = 0
    cpu_count_logical: int = 0
    cpu_freq_mhz: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_total_mb: float = 0.0
    memory_available_mb: float = 0.0
    disk_partitions: List[dict] = field(default_factory=list)
    disk_total_read_mb: float = 0.0
    disk_total_write_mb: float = 0.0
    net_sent_mb: float = 0.0
    net_recv_mb: float = 0.0
    net_sent_speed: float = 0.0  # MB/s
    net_recv_speed: float = 0.0  # MB/s
    temperatures: Dict[str, float] = field(default_factory=dict)
    boot_time: float = 0.0
    uptime_seconds: float = 0.0


@dataclass
class ProcessInfo:
    """Information about a single process."""
    pid: int = 0
    name: str = ""
    username: str = ""
    status: str = ""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    create_time: float = 0.0
    num_threads: int = 0


class SystemCollector(threading.Thread):
    """
    Background thread that continuously collects system metrics.
    Uses a deque for historical chart data and provides thread-safe access
    to the latest snapshot.
    """

    def __init__(self, history_length: int = 60):
        super().__init__(daemon=True)
        self._history_length = history_length
        self._running = False
        self._lock = threading.Lock()

        # Historical data for charts
        self.cpu_history: deque = deque(maxlen=history_length)
        self.memory_history: deque = deque(maxlen=history_length)

        # Latest snapshot
        self._latest: Optional[SystemSnapshot] = None

        # Process list
        self._processes: List[ProcessInfo] = []

        # Network counters for speed calculation
        self._last_net_sent = 0
        self._last_net_recv = 0
        self._last_net_time = 0

        # Disk counters for speed calculation
        self._last_disk_read = 0
        self._last_disk_write = 0
        self._last_disk_time = 0

        self._boot_time = psutil.boot_time()

    @property
    def latest(self) -> Optional[SystemSnapshot]:
        """Thread-safe access to the latest system snapshot."""
        with self._lock:
            return self._latest

    @property
    def processes(self) -> List[ProcessInfo]:
        """Thread-safe access to the latest process list."""
        with self._lock:
            return list(self._processes)

    def stop(self) -> None:
        """Signal the collector thread to stop."""
        self._running = False

    def run(self) -> None:
        """
        Main collection loop. Runs in background thread.
        Collects metrics at configured intervals without blocking GUI.
        """
        self._running = True
        logger.info("System collector started")

        # Initialize counters
        try:
            net_io = psutil.net_io_counters()
            self._last_net_sent = net_io.bytes_sent
            self._last_net_recv = net_io.bytes_recv
            self._last_net_time = time.time()

            disk_io = psutil.disk_io_counters()
            self._last_disk_read = disk_io.read_bytes
            self._last_disk_write = disk_io.write_bytes
            self._last_disk_time = time.time()
        except Exception as e:
            logger.warning("Failed to initialize IO counters: %s", e)

        while self._running:
            try:
                snapshot = self._collect()
                processes = self._collect_processes()

                with self._lock:
                    self._latest = snapshot
                    self._processes = processes
                    self.cpu_history.append(snapshot.cpu_percent)
                    self.memory_history.append(snapshot.memory_percent)

            except Exception as e:
                logger.error("Collection error: %s", e)

            # Dynamic sleep to achieve roughly 1-second intervals
            time.sleep(1.0)

        logger.info("System collector stopped")

    def _collect(self) -> SystemSnapshot:
        """Gather all system metrics into a snapshot."""
        now = time.time()

        # CPU - interval=0 uses previously calculated value, non-blocking
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count_physical = psutil.cpu_count(logical=False) or 0
        cpu_count_logical = psutil.cpu_count(logical=True) or 0

        try:
            cpu_freq = psutil.cpu_freq()
            cpu_freq_mhz = cpu_freq.current if cpu_freq else 0
        except Exception:
            cpu_freq_mhz = 0

        # Memory
        mem = psutil.virtual_memory()
        memory_used_mb = mem.used / (1024 ** 2)
        memory_total_mb = mem.total / (1024 ** 2)
        memory_available_mb = mem.available / (1024 ** 2)

        # Disk partitions
        disk_partitions = []
        try:
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disk_partitions.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total_gb": round(usage.total / (1024 ** 3), 2),
                        "used_gb": round(usage.used / (1024 ** 3), 2),
                        "free_gb": round(usage.free / (1024 ** 3), 2),
                        "percent": usage.percent,
                    })
                except (PermissionError, OSError):
                    continue
        except Exception as e:
            logger.debug("Disk partition collection error: %s", e)

        # Disk IO
        disk_read_mb = 0.0
        disk_write_mb = 0.0
        try:
            disk_io = psutil.disk_io_counters()
            if disk_io:
                disk_read_mb = disk_io.read_bytes / (1024 ** 2)
                disk_write_mb = disk_io.write_bytes / (1024 ** 2)
        except Exception as e:
            logger.debug("Disk IO collection error: %s", e)

        # Network
        net_sent_mb = 0.0
        net_recv_mb = 0.0
        net_sent_speed = 0.0
        net_recv_speed = 0.0
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                net_sent_mb = net_io.bytes_sent / (1024 ** 2)
                net_recv_mb = net_io.bytes_recv / (1024 ** 2)

                # Calculate speeds
                time_delta = now - self._last_net_time
                if time_delta > 0 and self._last_net_time > 0:
                    net_sent_speed = (net_io.bytes_sent - self._last_net_sent) / (1024 ** 2) / time_delta
                    net_recv_speed = (net_io.bytes_recv - self._last_net_recv) / (1024 ** 2) / time_delta

                self._last_net_sent = net_io.bytes_sent
                self._last_net_recv = net_io.bytes_recv
                self._last_net_time = now
        except Exception as e:
            logger.debug("Network collection error: %s", e)

        # Temperatures
        temperatures = self._collect_temperatures()

        return SystemSnapshot(
            timestamp=now,
            cpu_percent=cpu_percent,
            cpu_count_physical=cpu_count_physical,
            cpu_count_logical=cpu_count_logical,
            cpu_freq_mhz=cpu_freq_mhz,
            memory_percent=mem.percent,
            memory_used_mb=round(memory_used_mb, 2),
            memory_total_mb=round(memory_total_mb, 2),
            memory_available_mb=round(memory_available_mb, 2),
            disk_partitions=disk_partitions,
            disk_total_read_mb=round(disk_read_mb, 2),
            disk_total_write_mb=round(disk_write_mb, 2),
            net_sent_mb=round(net_sent_mb, 2),
            net_recv_mb=round(net_recv_mb, 2),
            net_sent_speed=round(net_sent_speed, 2),
            net_recv_speed=round(net_recv_speed, 2),
            temperatures=temperatures,
            boot_time=self._boot_time,
            uptime_seconds=round(now - self._boot_time, 0),
        )

    def _collect_processes(self) -> List[ProcessInfo]:
        """
        Collect process information. Skips processes that can't be accessed
        due to permissions.
        """
        processes = []
        for proc in psutil.process_iter(["pid", "name", "username", "status",
                                          "cpu_percent", "memory_percent",
                                          "memory_info", "create_time", "num_threads"]):
            try:
                info = proc.info
                mem_mb = 0.0
                if info.get("memory_info"):
                    mem_mb = info["memory_info"].rss / (1024 ** 2)

                processes.append(ProcessInfo(
                    pid=info.get("pid", 0),
                    name=info.get("name", "Unknown"),
                    username=info.get("username", ""),
                    status=info.get("status", ""),
                    cpu_percent=info.get("cpu_percent", 0.0) or 0.0,
                    memory_percent=info.get("memory_percent", 0.0) or 0.0,
                    memory_used_mb=round(mem_mb, 2),
                    create_time=info.get("create_time", 0) or 0,
                    num_threads=info.get("num_threads", 0) or 0,
                ))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
            except Exception as e:
                logger.debug("Process collection error: %s", e)
                continue

        return processes

    @staticmethod
    def _collect_temperatures() -> Dict[str, float]:
        """
        Collect hardware temperatures. Cross-platform implementation
        using psutil when available, with fallback to Linux sensors command.
        """
        temperatures = {}

        # Try psutil first (cross-platform)
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        for entry in entries:
                            label = entry.label or name
                            if entry.current:
                                key = f"{name}/{label}" if label != name else name
                                temperatures[key] = round(entry.current, 1)
                    return temperatures
        except Exception as e:
            logger.debug("psutil temperature error: %s", e)

        # Fallback to Linux sensors command
        if platform.system() == "Linux":
            try:
                result = subprocess.run(
                    ["sensors"], capture_output=True, text=True, check=True, timeout=5
                )
                for line in result.stdout.splitlines():
                    line = line.strip()
                    # Match patterns like "Core 0:  +45.0C" or "Tctl:  +52.1C"
                    import re
                    match = re.search(r"([\w\s]+):\s+\+([\d.]+)", line)
                    if match:
                        sensor_name = match.group(1).strip()
                        temp_value = float(match.group(2))
                        if sensor_name and temp_value > 0:
                            temperatures[sensor_name] = temp_value
            except (FileNotFoundError, subprocess.TimeoutExpired):
                logger.debug("sensors command not available")
            except subprocess.CalledProcessError as e:
                logger.debug("sensors command failed: %s", e)
            except Exception as e:
                logger.debug("Temperature fallback error: %s", e)

        return temperatures
