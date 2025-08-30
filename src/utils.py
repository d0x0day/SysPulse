"""
utils.py - Общие утилиты и конфигурации для кроссплатформенного системного монитора.
"""

import logging
import os
from datetime import datetime

# Значение интервала обновления данных по умолчанию (в миллисекундах).
DEFAULT_REFRESH_INTERVAL_MS = 1000  # Обновление каждую секунду.

# Настройка логирования
log_level = os.environ.get("LOGLEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.StreamHandler(),  # Вывод логов в stdout.
    ],
)

# Получение экземпляра логгера
logger = logging.getLogger(__name__)


def convert_size(size_bytes: int) -> str:
    """
    Преобразует размер в байтах в более читаемый формат (КБ, МБ, ГБ).

    Args:
        size_bytes: Размер в байтах.

    Returns:
        Строка, представляющая размер в человекочитаемом формате.
    """
    units = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    idx = 0
    while size_bytes >= 1024 and idx < len(units) - 1:
        size_bytes /= 1024
        idx += 1
    return f"{size_bytes:.2f} {units[idx]}"


def format_timestamp(timestamp: float) -> str:
    """
    Форматирует timestamp в удобочитаемую строку.

    Args:
        timestamp: Timestamp (количество секунд с начала эпохи).

    Returns:
        Строка, представляющая дату и время в формате ГГГГ-ММ-ДД ЧЧ:ММ:СС.
    """
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    # Тестирование вспомогательных функций
    print(convert_size(1024 * 1024 * 512))  # Ожидаемый вывод: "512.00 MB"
    print(format_timestamp(1638367200))  # Ожидаемый вывод: "2021-12-01 12:00:00"

