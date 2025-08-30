import tkinter as tk
from tkinter.font import Font

from monitoring import get_system_stats, get_temperatures
from utils import DEFAULT_REFRESH_INTERVAL_MS, logger


class SystemPerformanceMonitor(tk.Frame):
    """
    Класс для создания компактного монитора производительности системы.

    Отображает загрузку CPU, использование памяти и температуру компонентов.
    """

    def __init__(self, parent=None):
        """
        Инициализирует монитор производительности.

        Args:
            parent: Родительский tkinter виджет.
        """
        super().__init__(parent)
        self.parent = parent
        self.parent.title("Compact System Monitor")
        self.pack(fill=tk.BOTH, expand=True)
        self._create_compact_layout()
        self._update_data()

    def _create_compact_layout(self):
        """
        Создает компактный интерфейс для отображения системной информации.

        Использует темную цветовую схему для улучшения визуального восприятия.
        """
        # Цветовая палитра
        bg_color = "#2B2B2B"  # Тёмно-серый фон
        fg_color = "#FFFFFF"  # Белые надписи
        accent_color = "#4CAF50"  # Светло-зеленый акцент

        # Настройка шрифта
        font_style = Font(family="Roboto", size=14, weight="normal")

        # Заголовок окна
        title_frame = tk.Frame(self, bg=accent_color, padx=10, pady=10)
        title_frame.pack(side=tk.TOP, fill=tk.X)
        title_label = tk.Label(
            title_frame,
            text="System Performance Monitor",
            font=Font(family="Roboto", size=18, weight="bold"),
            bg=accent_color,
            fg=fg_color,
        )
        title_label.pack()

        # Фрейм для отображения результатов
        results_frame = tk.Frame(self, bg=bg_color, padx=10, pady=10)
        results_frame.pack(expand=True, fill=tk.BOTH)

        # Панель CPU
        cpu_frame = tk.Frame(results_frame, bg=bg_color)
        cpu_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
        cpu_title = tk.Label(cpu_frame, text="CPU Load", font=font_style, bg=bg_color, fg=fg_color)
        cpu_title.pack()
        self.cpu_value = tk.Label(cpu_frame, text="--%", font=font_style, bg=bg_color, fg=fg_color)
        self.cpu_value.pack()

        # Панель RAM
        mem_frame = tk.Frame(results_frame, bg=bg_color)
        mem_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
        mem_title = tk.Label(mem_frame, text="Memory Used", font=font_style, bg=bg_color, fg=fg_color)
        mem_title.pack()
        self.mem_value = tk.Label(mem_frame, text="-- MB", font=font_style, bg=bg_color, fg=fg_color)
        self.mem_value.pack()

        # Панель температуры
        temp_frame = tk.Frame(results_frame, bg=bg_color)
        temp_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
        temp_title = tk.Label(temp_frame, text="Temperature", font=font_style, bg=bg_color, fg=fg_color)
        temp_title.pack()
        self.temp_value = tk.Label(temp_frame, text="Loading...", font=font_style, bg=bg_color, fg=fg_color)
        self.temp_value.pack()

    def _update_data(self):
        """
        Обновляет отображаемые системные характеристики.

        Вызывается периодически для получения и отображения актуальных данных.
        """
        try:
            stats = get_system_stats()
            temps = get_temperatures()

            # Обновляем CPU и RAM
            self.cpu_value.config(text=f"{stats['cpu']:.1f}%")
            self.mem_value.config(text=f"{stats['memory']} MB")

            # Обновляем температуры
            temp_text = "\n".join([f"{key}: {value}C" for key, value in temps.items()])
            self.temp_value.config(text=temp_text)

        except Exception as e:
            logger.error(f"Ошибка при обновлении данных: {e}")
            self.temp_value.config(text="Ошибка получения данных")

        # Планируем следующее обновление
        self.after(DEFAULT_REFRESH_INTERVAL_MS, self._update_data)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("400x300")  # Компактные размеры окна
    app = SystemPerformanceMonitor(parent=root)
    root.mainloop()