"""
Processes view - displays running processes with sortable columns.
Provides process search, sorting, and kill functionality.
"""

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from core.config import COLORS
from core.settings_manager import SettingsManager
from services.system_collector import SystemCollector

logger = logging.getLogger(__name__)


class ProcessesView(tk.Frame):
    """
    Process manager tab showing all running processes.
    Supports search, multi-column sort, and process termination.
    """

    def __init__(self, parent, collector: SystemCollector, **kwargs):
        super().__init__(parent, **kwargs)
        self.config(bg=COLORS["bg_primary"])

        self.collector = collector
        self.settings = SettingsManager().settings

        self._all_processes = []
        self._search_term = ""
        self._sort_by = self.settings.processes_sort_by
        self._sort_desc = self.settings.processes_sort_descending

        self._build_layout()

    def _build_layout(self) -> None:
        """Build the processes tab UI."""
        # Toolbar
        toolbar = tk.Frame(self, bg=COLORS["bg_primary"], padx=20, pady=15)
        toolbar.pack(fill=tk.X)

        # Title
        tk.Label(
            toolbar, text="Processes", font=("Inter", 16, "bold"),
            bg=COLORS["bg_primary"], fg=COLORS["text_primary"]
        ).pack(side=tk.LEFT)

        # Search box
        search_frame = tk.Frame(toolbar, bg=COLORS["bg_secondary"], padx=10, pady=5)
        search_frame.pack(side=tk.RIGHT)

        self.search_var = tk.StringVar()

        search_entry = tk.Entry(
            search_frame, textvariable=self.search_var,
            font=("Inter", 10), bg=COLORS["bg_secondary"],
            fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"],
            relief=tk.FLAT, width=25
        )
        search_entry.pack(side=tk.LEFT)

        # Placeholder text behavior
        search_entry.insert(0, "Search...")
        search_entry.config(fg=COLORS["text_secondary"])
        search_entry.bind("<FocusIn>", lambda e: (
            search_entry.delete(0, tk.END),
            search_entry.config(fg=COLORS["text_primary"])
        ) if search_entry.get() == "Search..." else None)
        search_entry.bind("<FocusOut>", lambda e: (
            search_entry.insert(0, "Search..."),
            search_entry.config(fg=COLORS["text_secondary"])
        ) if not search_entry.get() else None)

        # Bind trace AFTER tree is created to avoid AttributeError during init
        self.search_var.trace_add("write", self._on_search)

        # Kill button
        self.kill_btn = tk.Button(
            toolbar, text="Kill Process", command=self._kill_selected,
            font=("Inter", 9, "bold"), bg=COLORS["danger"], fg=COLORS["text_primary"],
            activebackground=COLORS["accent_hover"], relief=tk.FLAT,
            padx=15, pady=5, cursor="hand2", state=tk.DISABLED
        )
        self.kill_btn.pack(side=tk.RIGHT, padx=(0, 15))

        # Refresh button
        refresh_btn = tk.Button(
            toolbar, text="Refresh", command=self._manual_refresh,
            font=("Inter", 9), bg=COLORS["bg_card"], fg=COLORS["text_primary"],
            activebackground=COLORS["bg_secondary"], relief=tk.FLAT,
            padx=15, pady=5, cursor="hand2"
        )
        refresh_btn.pack(side=tk.RIGHT, padx=(0, 10))

        # Process count label
        self.count_label = tk.Label(
            toolbar, text="0 processes",
            font=("Inter", 9), bg=COLORS["bg_primary"], fg=COLORS["text_secondary"]
        )
        self.count_label.pack(side=tk.RIGHT, padx=(0, 15))

        # Treeview (process table)
        tree_frame = tk.Frame(self, bg=COLORS["bg_primary"])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Inner padding frame (padx/pady as tuples work in pack/grid, not in widget creation)
        inner_frame = tk.Frame(tree_frame, bg=COLORS["bg_primary"])
        inner_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Style configuration for treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Treeview",
            background=COLORS["bg_secondary"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_secondary"],
            rowheight=26,
            borderwidth=0,
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            font=("Inter", 9, "bold"),
            relief=tk.FLAT,
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", COLORS["accent"])],
            foreground=[("selected", COLORS["text_primary"])],
        )
        style.map(
            "Custom.Treeview.Heading",
            background=[("active", COLORS["accent"])],
        )

        columns = ("pid", "name", "user", "status", "cpu", "memory", "threads")
        self.tree = ttk.Treeview(
            inner_frame, columns=columns, show="headings",
            style="Custom.Treeview", selectmode="browse"
        )

        # Define columns
        col_config = {
            "pid": ("PID", 70),
            "name": ("Name", 200),
            "user": ("User", 120),
            "status": ("Status", 80),
            "cpu": ("CPU %", 70),
            "memory": ("Memory %", 80),
            "threads": ("Threads", 70),
        }

        for col, (heading, width) in col_config.items():
            self.tree.heading(col, text=heading, command=lambda c=col: self._on_sort(c))
            self.tree.column(col, width=width, anchor="w" if col in ("name", "user") else "center")

        # Scrollbars
        vsb = ttk.Scrollbar(inner_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(inner_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        inner_frame.grid_rowconfigure(0, weight=1)
        inner_frame.grid_columnconfigure(0, weight=1)

        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._kill_selected())

        self._selected_pid = None

    def _on_search(self, *args) -> None:
        """Handle search input changes."""
        term = self.search_var.get()
        self._search_term = "" if term == "Search..." else term.lower()
        self._refresh_table()

    def _on_sort(self, column: str) -> None:
        """Toggle sort direction when column header is clicked."""
        if self._sort_by == column:
            self._sort_desc = not self._sort_desc
        else:
            self._sort_by = column
            self._sort_desc = True

        # Persist to settings
        self.settings.processes_sort_by = self._sort_by
        self.settings.processes_sort_descending = self._sort_desc
        SettingsManager().save()

        self._refresh_table()

    def _on_select(self, event=None) -> None:
        """Handle process selection in the table."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            try:
                self._selected_pid = int(item["values"][0])
                self.kill_btn.config(state=tk.NORMAL)
            except (IndexError, ValueError):
                self._selected_pid = None
                self.kill_btn.config(state=tk.DISABLED)
        else:
            self._selected_pid = None
            self.kill_btn.config(state=tk.DISABLED)

    def _kill_selected(self) -> None:
        """Terminate the selected process with confirmation."""
        if not self._selected_pid:
            return

        # Find process name
        name = "Unknown"
        for proc in self._all_processes:
            if proc.pid == self._selected_pid:
                name = proc.name
                break

        if self.settings.confirm_kill_process:
            result = messagebox.askyesno(
                "Confirm Kill",
                f"Are you sure you want to terminate process?\n\n"
                f"PID: {self._selected_pid}\n"
                f"Name: {name}",
                icon="warning"
            )
            if not result:
                return

        try:
            import psutil
            p = psutil.Process(self._selected_pid)
            p.terminate()
            logger.info("Terminated process %d (%s)", self._selected_pid, name)

            # Wait briefly then kill if still running
            import time
            time.sleep(0.5)
            if p.is_running():
                p.kill()
                logger.info("Force-killed process %d", self._selected_pid)

        except psutil.NoSuchProcess:
            logger.warning("Process %d no longer exists", self._selected_pid)
        except psutil.AccessDenied:
            messagebox.showerror("Access Denied", "Permission denied. Try running as administrator.")
        except Exception as e:
            logger.error("Failed to kill process %d: %s", self._selected_pid, e)
            messagebox.showerror("Error", f"Failed to terminate process: {e}")

        self._selected_pid = None
        self.kill_btn.config(state=tk.DISABLED)
        self._manual_refresh()

    def _manual_refresh(self) -> None:
        """Force refresh of process list."""
        self._all_processes = self.collector.processes
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Update treeview with filtered and sorted processes."""
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Filter
        filtered = self._all_processes
        if self._search_term:
            filtered = [
                p for p in filtered
                if (self._search_term in p.name.lower()
                    or self._search_term in str(p.pid)
                    or self._search_term in (p.username or "").lower())
            ]

        # Sort
        sort_key = {
            "pid": lambda p: p.pid,
            "name": lambda p: p.name.lower(),
            "user": lambda p: (p.username or "").lower(),
            "status": lambda p: p.status.lower(),
            "cpu": lambda p: p.cpu_percent,
            "memory": lambda p: p.memory_percent,
            "threads": lambda p: p.num_threads,
        }.get(self._sort_by, lambda p: p.cpu_percent)

        filtered.sort(key=sort_key, reverse=self._sort_desc)

        # Insert into treeview
        for proc in filtered:
            self.tree.insert(
                "", tk.END,
                values=(
                    proc.pid,
                    proc.name,
                    proc.username or "",
                    proc.status,
                    f"{proc.cpu_percent:.1f}",
                    f"{proc.memory_percent:.1f}",
                    proc.num_threads,
                )
            )

        self.count_label.config(text=f"{len(filtered)} processes")

    def update_display(self) -> None:
        """Refresh process list from collector. Called periodically."""
        self._all_processes = self.collector.processes
        self._refresh_table()
