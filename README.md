# SysPulse v2.0

Professional cross-platform system performance monitor built with Python and Tkinter. Real-time dashboards, process management, and hardware monitoring in a sleek dark-themed interface.

## Features

- **Real-Time Dashboard** - Live CPU, memory, disk, and network metrics with animated charts
- **Process Manager** - Sortable process table with search, filtering, and kill functionality
- **System Information** - Detailed OS, CPU, memory, and network interface details
- **Configurable Settings** - Toggle metrics visibility, adjust refresh intervals, temperature units
- **Modern Dark UI** - Professional dark theme with accent colors and smooth visualizations
- **Cross-Platform** - Works on Linux, Windows, and macOS

## Architecture

```
syspulse/
|-- __init__.py              # Package marker
|-- __main__.py              # Module entry point: python -m syspulse
|-- main.py                  # Application entry point
|-- requirements.txt         # Dependencies
|
|-- core/                    # Core business logic
|   |-- __init__.py
|   |-- config.py            # Constants, colors, paths
|   |-- logger.py            # Centralized logging setup
|   |-- settings_manager.py  # JSON-based user preferences
|
|-- services/                # Data layer
|   |-- __init__.py
|   |-- system_collector.py  # Background thread: CPU, memory, disk, network, temps, processes
|
|-- gui/                     # Presentation layer
|   |-- __init__.py
|   |-- app.py               # Main window, navigation, update loop
|   |-- dashboard_view.py    # Metrics cards, charts, disk table, temperatures
|   |-- processes_view.py    # Process table with sort, search, kill
|   |-- settings_view.py     # Toggle switches, interval selector, reset
|   |-- system_info_view.py  # Static system details + dynamic uptime
|   |-- widgets.py           # Reusable: MetricCard, ProgressBar, ToggleSwitch, ScrollableFrame
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python main.py

# Or as a module
python -m syspulse
```

## Requirements

- Python 3.8+
- psutil >= 7.0.0
- matplotlib >= 3.7.0

## Settings

User preferences are stored in `settings.json` and include:

- Visibility toggles for each metric section
- Refresh interval (0.5s / 1s / 2s)
- Chart display options
- Temperature unit (Celsius / Fahrenheit)
- Process kill confirmation
- Sort preferences for process table