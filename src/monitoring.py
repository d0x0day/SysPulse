import logging
import os
import platform
import psutil
import re
import subprocess

# Настройка логирования
LOG_LEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.StreamHandler(),  # Вывод в консоль
    ],
)

# Получаем экземпляр логгера для текущего модуля
logger = logging.getLogger(__name__)


def get_system_stats():
    """
    Собирает основные метрики производительности системы (загрузка ЦП, использование памяти).

    Returns:
        dict: Словарь с загрузкой ЦП (ключ 'cpu') и использованием памяти (ключ 'memory').
    """
    try:
        # Получаем загрузку ЦП (в процентах)
        cpu_load = psutil.cpu_percent(interval=1)

        # Получаем информацию об использовании памяти
        mem = psutil.virtual_memory()
        mem_used_mb = round(mem.used / (1024 ** 2), 2)  # Преобразуем в мегабайты

        return {"cpu": cpu_load, "memory": mem_used_mb}

    except Exception as e:
        logger.error(f"Ошибка при получении статистики системы: {e}")
        return {"cpu": None, "memory": None}  # Возвращаем None в случае ошибки


def get_temperatures():
    """
    Извлекает данные о температуре с аппаратных датчиков.

    Поддерживает Linux (использует утилиту 'sensors'). На Windows функциональность пока не реализована.

    Returns:
        dict: Словарь с названиями сенсоров в качестве ключей и значениями температуры в градусах Цельсия.
              Возвращает пустой словарь, если не удалось получить данные или если платформа не поддерживается.
    """
    temperatures = {}

    if platform.system() == "Linux":
        # Для Linux используем утилиту 'sensors'
        try:
            result = subprocess.run(['sensors'], capture_output=True, text=True, check=True)
            lines = result.stdout.split('\n')
            for line in lines:
                line = line.strip()  # Удаляем лишние пробелы
                match = re.search(r'^(\w+)\:\s+\+([\d\.]+)\°C$', line)
                if match:
                    sensor_name, temp_value = match.groups()
                    temperatures[sensor_name] = float(temp_value)
        except FileNotFoundError:
            logger.warning("Утилита 'sensors' не найдена. Пропуск сбора данных о температуре.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при выполнении 'sensors': {e}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при получении данных о температуре: {e}")

    elif platform.system() == "Windows":
        logger.warning("Сбор данных о температуре в настоящее время не поддерживается на Windows.")

    return temperatures