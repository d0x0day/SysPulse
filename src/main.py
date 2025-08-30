import tkinter as tk

from gui import SystemPerformanceMonitor
from utils import DEFAULT_REFRESH_INTERVAL_MS, logger


def main():
    """
    Инициализирует приложение и запускает цикл обработки событий GUI.
    Обрабатывает корректное завершение работы при получении KeyboardInterrupt.
    """

    # Создаем главное окно приложения.
    root = tk.Tk()

    # Обработчик закрытия окна. Гарантирует корректное завершение работы приложения.
    root.protocol("WM_DELETE_WINDOW", root.destroy)

    # Создаем экземпляр класса SystemPerformanceMonitor, передавая главное окно в качестве родительского.
    app = SystemPerformanceMonitor(parent=root)

    try:
        # Запускаем главный цикл обработки событий GUI.
        root.mainloop()

    except KeyboardInterrupt:
        # Обработка прерывания с клавиатуры (Ctrl+C).
        logger.info("Получено прерывание с клавиатуры. Завершение работы...")
        root.destroy()


if __name__ == "__main__":
    try:
        # Запускаем основную функцию приложения.
        main()

    except Exception as e:
        # Обработка непредвиденных исключений.
        logger.critical(f"Произошла непредвиденная ошибка во время выполнения: {e}")
        exit(1)  # Выходим с кодом ошибки 1.